"""Live HTTP integration checks: real sockets, SQLite, guards and execution flow.

No external service is contacted. Action tests either use the temporary local
file scope or force the unsupported platform path, never launching a real app.
"""
import base64
import contextlib
import http.client
import io
import json
import os
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from backend.ai import ProviderError
from backend.server import Application, JarvisServer, main
from backend.storage import Store


class LiveServerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        # Never inherit a user's granted folder into file-operation tests.
        with patch.dict(os.environ, {"JARVIS_ALLOWED_FOLDER": ""}):
            self.app = Application(self.temp.name)
        self.server = JarvisServer(("127.0.0.1", 0), self.app)
        self.port = self.server.server_port
        self.host = f"127.0.0.1:{self.port}"
        self.thread = threading.Thread(target=self.server.serve_forever,
                                       kwargs={"poll_interval": 0.01}, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop_server)

    def stop_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)

    def request(self, method, path, body=None, *, token=True, headers=None, raw=None):
        request_headers = {"Host": self.host}
        if token:
            request_headers["X-Jarvis-Token"] = self.app.token if token is True else token
        if raw is not None:
            payload = raw
            request_headers["Content-Type"] = "application/json"
        elif body is not None:
            payload = json.dumps(body).encode("utf-8")
            request_headers["Content-Type"] = "application/json"
        else:
            payload = None
        request_headers.update(headers or {})
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            connection.request(method, path, body=payload, headers=request_headers)
            response = connection.getresponse()
            data = response.read()
            response_headers = dict(response.getheaders())
            if "application/json" in response_headers.get("Content-Type", ""):
                data = json.loads(data)
            return response.status, data, response_headers
        finally:
            connection.close()

    def test_session_token_and_real_status(self):
        status, result, headers = self.request("GET", "/api/session", token=False)
        self.assertEqual(status, 200)
        self.assertEqual(result["token"], self.app.token)
        self.assertEqual(headers["Cache-Control"], "no-store")
        for candidate in [False, "wrong-token"]:
            status, _, _ = self.request("GET", "/api/status", token=candidate)
            self.assertEqual(status, 401)
        status, result, _ = self.request("GET", "/api/status")
        self.assertEqual(status, 200)
        self.assertIn("architecture", result["system"])
        self.assertFalse(result["settings"]["cloud_enabled"])
        self.assertIn("file_scope", result["capabilities"])

    def test_host_port_and_origin_guards_cover_session_bootstrap(self):
        hostile = [
            {"Host": f"evil.example:{self.port}"},
            {"Host": "127.0.0.1:1"},
            {"Host": f"user@127.0.0.1:{self.port}"},
            {"Origin": "https://evil.example"},
            {"Origin": "null"},
            {"Origin": f"http://127.0.0.1:{self.port+1}"},
            {"Sec-Fetch-Site": "cross-site"},
        ]
        for headers in hostile:
            with self.subTest(headers=headers):
                status, _, _ = self.request("GET", "/api/session", token=False, headers=headers)
                self.assertEqual(status, 403)
        status, _, _ = self.request("GET", "/api/session", token=False,
                                     headers={"Origin": "http://" + self.host})
        self.assertEqual(status, 200)

    def test_static_allowlist_never_serves_source_database_or_secrets(self):
        status, body, headers = self.request("GET", "/", token=False)
        self.assertEqual(status, 200)
        self.assertTrue(body.lower().startswith(b"<!doctype html>"))
        self.assertEqual(headers["X-Frame-Options"], "DENY")
        self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"])
        self.assertNotIn("Access-Control-Allow-Origin", headers)
        for path in ["/.env", "/backend/server.py", "/backend/storage.py", "/.git/config",
                     "/../backend/server.py", "/%2e%2e/backend/server.py", "/jarvis.sqlite3"]:
            with self.subTest(path=path):
                status, _, _ = self.request("GET", path)
                self.assertEqual(status, 404)

    def test_settings_update_validation_and_persistence(self):
        status, result, _ = self.request("PUT", "/api/settings", {"gemini_daily_limit": 7})
        self.assertEqual(status, 200)
        self.assertEqual(result["settings"]["gemini_daily_limit"], 7)
        self.assertEqual(Store(self.temp.name).settings()["gemini_daily_limit"], 7)
        for body in [{"GEMINI_API_KEY": "dummy-not-a-real-key"}, {"unknown": True},
                     {"cloud_enabled": "true"}, {"gemini_daily_limit": -1},
                     {"gemini_daily_limit": 10000000}, {"elevenlabs_daily_char_limit": True}]:
            with self.subTest(body=body):
                status, _, _ = self.request("PUT", "/api/settings", body)
                self.assertEqual(status, 400)
        self.assertEqual(self.app.store.settings()["gemini_daily_limit"], 7)
        self.assertNotIn("GEMINI_API_KEY", self.app.store.settings())

    def test_malformed_and_oversized_json_rejected_without_execution(self):
        for raw in [b"not json", b"[]", b"null"]:
            status, _, _ = self.request("POST", "/api/chat", raw=raw)
            self.assertEqual(status, 400)
        status, _, _ = self.request("POST", "/api/chat", {"text": "Status"},
                                     headers={"Content-Type": "text/plain"})
        self.assertEqual(status, 400)
        status, _, _ = self.request("POST", "/api/chat", raw=b"",
                                     headers={"Content-Length": "32769"})
        self.assertEqual(status, 400)
        self.assertEqual(self.app.store.history(), [])

    def test_local_command_proposes_then_reports_actual_platform_failure(self):
        with patch.object(self.app.ai, "chat", side_effect=AssertionError("local command must stay local")):
            status, result, _ = self.request("POST", "/api/chat", {"text": "Rechner öffnen"})
        self.assertEqual(status, 200)
        self.assertEqual(len(result["proposals"]), 1)
        proposal = result["proposals"][0]
        self.assertTrue(proposal["requires_confirmation"])
        self.assertEqual(proposal["action"], "open_app")
        self.assertNotIn("ausgeführt", result["reply"].lower())
        with patch("backend.mac_control.platform.system", return_value="Linux"):
            status, confirmation, _ = self.request("POST", "/api/actions/confirm", {"id": proposal["id"]})
        self.assertEqual(status, 200)
        self.assertFalse(confirmation["ok"])
        self.assertIn("nicht verfügbar", confirmation["message"])
        status, _, _ = self.request("POST", "/api/actions/confirm", {"id": proposal["id"]})
        self.assertEqual(status, 400)

    def test_model_proposals_map_to_safe_pending_actions(self):
        proposed = {"reply": "Bitte bestätigen, Sir.", "proposed_actions": [
            {"kind": "open_app", "app": "Calculator"},
            {"kind": "create_text", "path": "ai.txt", "text": "Text von Gemini"},
        ]}
        with patch.object(self.app.ai, "chat", return_value=proposed):
            status, result, _ = self.request("POST", "/api/chat", {"text": "Plane eine kleine Aufgabe"})
        self.assertEqual(status, 200)
        self.assertEqual(len(result["proposals"]), 2)
        file_proposal = result["proposals"][1]
        self.assertEqual(file_proposal["arguments"]["content"], "Text von Gemini")
        self.assertFalse((self.app.actions.file_root / "ai.txt").exists())
        status, result, _ = self.request("POST", "/api/actions/confirm", {"id": file_proposal["id"]})
        self.assertEqual(status, 200)
        self.assertTrue(result["ok"])
        self.assertEqual((self.app.actions.file_root / "ai.txt").read_text(), "Text von Gemini")

    def test_file_roundtrip_requires_token_and_explicit_confirmation(self):
        status, proposal, _ = self.request("POST", "/api/actions/prepare", {
            "action": "create_text", "arguments": {"path": "local.txt", "content": "Hallo, Sir."}})
        self.assertEqual(status, 200)
        target = self.app.actions.file_root / "local.txt"
        self.assertFalse(target.exists())
        status, _, _ = self.request("POST", "/api/actions/confirm", {"id": proposal["id"]}, token=False)
        self.assertEqual(status, 401)
        self.assertFalse(target.exists())
        status, result, _ = self.request("POST", "/api/actions/confirm", {"id": proposal["id"]})
        self.assertEqual(status, 200)
        self.assertTrue(result["ok"])
        status, proposal, _ = self.request("POST", "/api/actions/prepare", {
            "action": "read_text", "arguments": {"path": "local.txt"}})
        self.assertEqual(status, 200)
        status, result, _ = self.request("POST", "/api/actions/confirm", {"id": proposal["id"]})
        self.assertEqual(status, 200)
        self.assertEqual(result["content"], "Hallo, Sir.")
        status, _, _ = self.request("POST", "/api/actions/prepare", {
            "action": "read_text", "arguments": {"path": "../jarvis.sqlite3"}})
        self.assertEqual(status, 400)

    def test_action_cancellation_consumes_proposal(self):
        status, proposal, _ = self.request("POST", "/api/actions/prepare", {
            "action": "create_folder", "arguments": {"path": "cancelled"}})
        self.assertEqual(status, 200)
        status, result, _ = self.request("POST", "/api/actions/cancel", {"id": proposal["id"]})
        self.assertEqual(status, 200)
        self.assertTrue(result["ok"])
        status, _, _ = self.request("POST", "/api/actions/confirm", {"id": proposal["id"]})
        self.assertEqual(status, 400)
        self.assertFalse((self.app.actions.file_root / "cancelled").exists())

    def test_reminders_survive_store_reopen_and_validate_timezone(self):
        due_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        status, result, _ = self.request("POST", "/api/reminders", {"text": "Pause", "due_at": due_at})
        self.assertEqual(status, 201)
        self.assertEqual(Store(self.temp.name).reminders()[0]["text"], "Pause")
        status, listed, _ = self.request("GET", "/api/reminders")
        self.assertEqual(status, 200)
        self.assertEqual(listed["reminders"][0]["id"], result["id"])
        status, updated, _ = self.request("PATCH", f"/api/reminders/{result['id']}", {"status": "done"})
        self.assertEqual(status, 200)
        self.assertEqual(updated["status"], "done")
        status, _, _ = self.request("POST", "/api/reminders", {"text": "Unklar", "due_at": "2030-01-01T12:00"})
        self.assertEqual(status, 400)

    def test_delete_history_is_authenticated_and_busy_safe(self):
        self.request("POST", "/api/chat", {"text": "Hilfe"})
        self.assertEqual(len(self.app.store.history()), 2)
        status, _, _ = self.request("DELETE", "/api/history", token=False)
        self.assertEqual(status, 401)
        self.app.chat_lock.acquire()
        try:
            status, _, _ = self.request("DELETE", "/api/history")
            self.assertEqual(status, 409)
            self.assertEqual(len(self.app.store.history()), 2)
        finally:
            self.app.chat_lock.release()
        status, result, _ = self.request("DELETE", "/api/history")
        self.assertEqual(status, 200)
        self.assertTrue(result["ok"])
        self.assertEqual(self.request("GET", "/api/history")[1]["messages"], [])

    def test_provider_failure_status_is_preserved(self):
        with patch.object(self.app.ai, "chat", side_effect=ProviderError("Tageslimit erreicht.", 429)):
            status, result, _ = self.request("POST", "/api/chat", {"text": "Eine freie Frage"})
        self.assertEqual(status, 429)
        self.assertEqual(result["error"], "Tageslimit erreicht.")
        self.assertEqual(self.app.store.history(), [])

    def test_image_endpoint_rejects_invalid_base64_or_actual_image_content(self):
        for image, mime in [("%%%", "image/png"),
                            (base64.b64encode(b"not an actual image").decode(), "image/png"),
                            (base64.b64encode(b"test").decode(), "text/html")]:
            with self.subTest(mime=mime, image=image):
                status, _, _ = self.request("POST", "/api/image", {"text": "Beschreibe das Bild", "image": image, "mime": mime})
                self.assertEqual(status, 400)
        self.assertEqual(self.app.store.usage()["gemini_requests"], 0)
        self.assertEqual(self.app.store.history(), [])

    def test_password_gate_wraps_session_and_static_files(self):
        self.server.password = "local-test-password-long-enough"
        status, _, headers = self.request("GET", "/api/session", token=False)
        self.assertEqual(status, 401)
        self.assertIn("Basic realm=", headers["WWW-Authenticate"])
        auth = "Basic " + base64.b64encode(b"jarvis:local-test-password-long-enough").decode()
        status, result, _ = self.request("GET", "/api/session", token=False, headers={"Authorization": auth})
        self.assertEqual(status, 200)
        self.assertEqual(result["token"], self.app.token)


class CommandLineGuardTests(unittest.TestCase):
    def test_network_exposure_rejected_before_app_creation(self):
        invalid = [
            ["--host", "0.0.0.0"],
            ["--host", "8.8.8.8"],
            ["--host", "192.168.1.5"],
            ["--host", "192.168.1.5", "--cert", "/dummy/cert", "--key", "/dummy/key"],
            ["--host", "localhost", "--cert", "/dummy/cert"],
        ]
        with patch.dict(os.environ, {"JARVIS_ACCESS_PASSWORD": ""}):
            with patch("backend.server.Application") as constructor:
                for argv in invalid:
                    with self.subTest(argv=argv), contextlib.redirect_stderr(io.StringIO()):
                        with self.assertRaises(SystemExit) as error:
                            main(argv)
                        self.assertEqual(error.exception.code, 2)
                constructor.assert_not_called()


if __name__ == "__main__":
    unittest.main()
