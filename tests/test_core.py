import concurrent.futures
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from backend.automations import create_timer, due_reminders
from backend.mac_control import PendingActions
from backend.security import new_token, token_matches, validate_host, validate_origin
from backend.storage import Store
from backend.system_info import snapshot


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = Store(self.temp.name)

    def test_settings_are_private_explicit_and_persistent(self):
        self.assertFalse(self.store.settings()["cloud_enabled"])
        with self.assertRaises(ValueError):
            self.store.update_settings({"GEMINI_API_KEY": "not-a-key"})
        for data in [{"cloud_enabled": "yes"}, {"gemini_daily_limit": True},
                     {"gemini_daily_limit": -1}, {"elevenlabs_daily_char_limit": 99999999},
                     {"gemini_model": "../../example"}]:
            with self.assertRaises(ValueError):
                self.store.update_settings(data)
        self.store.update_settings({"cloud_enabled": True, "gemini_daily_limit": 5})
        other = Store(self.temp.name)
        self.assertTrue(other.settings()["cloud_enabled"])
        self.assertEqual(other.settings()["gemini_daily_limit"], 5)
        self.assertEqual(os.stat(other.path).st_mode & 0o777, 0o600)

    def test_conversation_isolation_and_order(self):
        self.store.append("user", "Frage", "one")
        self.store.append("assistant", "Antwort", "one")
        self.store.append("user", "Andere Frage", "two")
        self.assertEqual([r["text"] for r in self.store.history("one")], ["Frage", "Antwort"])
        self.store.clear_history("one")
        self.assertEqual(self.store.history("one"), [])
        self.assertEqual(len(self.store.history("two")), 1)

    def test_budget_is_atomic_under_concurrency(self):
        def attempt(_):
            try:
                self.store.reserve_usage("gemini_requests", 1, 6)
                return True
            except ValueError:
                return False
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(attempt, range(25)))
        self.assertEqual(sum(results), 6)
        self.assertEqual(self.store.usage()["gemini_requests"], 6)
        with self.assertRaises(ValueError):
            self.store.reserve_usage("elevenlabs_characters", 1, 0)
        self.assertEqual(self.store.usage()["elevenlabs_characters"], 0)

    def test_reminders_are_persistent_and_no_ambiguous_local_time(self):
        with self.assertRaises(ValueError):
            self.store.create_reminder("Unsicher", "2030-01-01T12:00:00")
        row = create_timer(self.store, 60, "Tee")
        self.assertEqual(Store(self.temp.name).reminders()[0]["text"], "Tee")
        self.assertEqual(due_reminders(self.store), [])
        self.assertEqual(self.store.update_reminder(row["id"], "done")["status"], "done")
        with self.assertRaises(ValueError):
            self.store.update_reminder(row["id"], "done")


class ActionsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = Store(self.temp.name)
        self.actions = PendingActions(self.store, file_root=Path(self.temp.name) / "files")

    def confirm(self, action, arguments):
        return self.actions.confirm(self.actions.prepare(action, arguments)["id"])

    def test_no_execution_before_confirmation_and_no_replay(self):
        proposal = self.actions.prepare("create_text", {"path": "hello.txt", "content": "Sir"})
        target = self.actions.file_root / "hello.txt"
        self.assertFalse(target.exists())
        self.assertTrue(self.actions.confirm(proposal["id"])["ok"])
        self.assertEqual(target.read_text(), "Sir")
        with self.assertRaises(ValueError):
            self.actions.confirm(proposal["id"])

    def test_creation_never_overwrites(self):
        self.assertTrue(self.confirm("create_folder", {"path": "notes"})["ok"])
        self.assertTrue(self.confirm("create_text", {"path": "notes/day.txt", "content": "Original"})["ok"])
        self.assertFalse(self.confirm("create_text", {"path": "notes/day.txt", "content": "Overwrite"})["ok"])
        self.assertEqual(self.confirm("read_text", {"path": "notes/day.txt"})["content"], "Original")
        listing = self.confirm("list_files", {"path": "notes"})
        self.assertEqual(listing["entries"][0]["name"], "day.txt")

    def test_traversal_symlinks_and_shell_are_rejected(self):
        for path in ["../outside.txt", "/etc/passwd", "notes/../../outside.txt", "x\\y.txt"]:
            with self.assertRaises(ValueError):
                self.actions.prepare("read_text", {"path": path})
        with self.assertRaises(ValueError):
            self.actions.prepare("shell", {"command": "touch surprise"})
        outside = Path(self.temp.name) / "private"
        outside.mkdir()
        (outside / "secret.txt").write_text("private")
        (self.actions.file_root / "escape").symlink_to(outside, target_is_directory=True)
        result = self.confirm("read_text", {"path": "escape/secret.txt"})
        self.assertFalse(result["ok"])
        (self.actions.file_root / "secret.txt").symlink_to(outside / "secret.txt")
        self.assertFalse(self.confirm("read_text", {"path": "secret.txt"})["ok"])
        # A directory replaced after the preview must still be rejected.
        regular = self.actions.file_root / "swapped"
        regular.mkdir()
        proposal = self.actions.prepare("create_text", {"path": "swapped/new.txt", "content": "test"})
        regular.rmdir()
        regular.symlink_to(outside, target_is_directory=True)
        self.assertFalse(self.actions.confirm(proposal["id"])["ok"])
        self.assertFalse((outside / "new.txt").exists())

    def test_hardlink_and_binary_reads_rejected(self):
        outside = Path(self.temp.name) / "private.txt"
        outside.write_text("private")
        os.link(outside, self.actions.file_root / "hardlink.txt")
        self.assertFalse(self.confirm("read_text", {"path": "hardlink.txt"})["ok"])
        (self.actions.file_root / "binary.txt").write_bytes(b"\xff\xfe")
        self.assertFalse(self.confirm("read_text", {"path": "binary.txt"})["ok"])

    def test_expired_and_cancelled_confirmations_fail(self):
        with patch("backend.mac_control.time.time", return_value=100):
            proposal = self.actions.prepare("create_folder", {"path": "old"})
        with patch("backend.mac_control.time.time", return_value=221):
            with self.assertRaisesRegex(ValueError, "abgelaufen"):
                self.actions.confirm(proposal["id"])
        self.assertFalse((self.actions.file_root / "old").exists())
        cancelled = self.actions.prepare("open_app", {"app": "Calculator"})
        self.assertTrue(self.actions.cancel(cancelled["id"])["cancelled"])
        with self.assertRaises(ValueError):
            self.actions.confirm(cancelled["id"])

    def test_mac_success_only_after_native_confirmation(self):
        with patch("backend.mac_control.platform.system", return_value="Linux"):
            self.assertFalse(self.confirm("open_app", {"app": "Calculator"})["ok"])
        with patch("backend.mac_control.platform.system", return_value="Darwin"):
            with patch("backend.mac_control.subprocess.run") as run:
                run.return_value.returncode = 0
                result = self.confirm("open_app", {"app": "Calculator"})
                self.assertTrue(result["ok"])
                self.assertEqual(run.call_args.args[0], ["/usr/bin/open", "-b", "com.apple.calculator"])
                run.return_value.returncode = 1
                self.assertFalse(self.confirm("open_app", {"app": "Calculator"})["ok"])

    def test_unsafe_urls_fail_and_arguments_are_private_copies(self):
        for url in ["file:///etc/passwd", "javascript:alert(1)", "https://user:pass@example.com", "https://example.com\n"]:
            with self.assertRaises(ValueError):
                self.actions.prepare("open_url", {"url": url})
        proposal = self.actions.prepare("create_text", {"path": "safe.txt", "content": "safe"})
        proposal["arguments"]["path"] = "../unsafe.txt"
        self.assertTrue(self.actions.confirm(proposal["id"])["ok"])
        self.assertTrue((self.actions.file_root / "safe.txt").exists())


class BoundaryAndTelemetryTests(unittest.TestCase):
    def test_request_boundary(self):
        self.assertTrue(validate_host("127.0.0.1:8765", 8765))
        self.assertFalse(validate_host("evil.example:8765", 8765))
        self.assertFalse(validate_host("localhost:80", 8765))
        self.assertTrue(validate_origin("http://localhost:8765", "localhost:8765"))
        self.assertFalse(validate_origin("http://evil.example", "localhost:8765"))
        self.assertFalse(validate_origin("null", "localhost:8765"))
        token = new_token()
        self.assertTrue(token_matches(token, token))
        self.assertFalse(token_matches(None, token))
        self.assertFalse(token_matches("ä", token))

    def test_real_host_snapshot_with_explicit_unavailable_values(self):
        first = snapshot()
        second = snapshot()
        self.assertIn(first["system"], {"Linux", "Darwin", "Windows"})
        self.assertGreater(first["disk_total_bytes"], 0)
        self.assertIsInstance(first["python"], str)
        self.assertEqual(first["machine"], first["architecture"])
        self.assertIn("percent", first["memory"])
        if second["cpu_percent"] is not None:
            self.assertGreaterEqual(second["cpu_percent"], 0)
            self.assertLessEqual(second["cpu_percent"], 100)


if __name__ == "__main__":
    unittest.main()
