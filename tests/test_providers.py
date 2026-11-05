import base64
import errno
import io
import os
import socket
import ssl
import unittest
import urllib.error
from unittest.mock import patch

from backend.ai import GeminiClient
from backend.providers import ProviderError, _NoRedirect, provider_status, request_json, safe_network_message
from backend.voice import VoiceClient


class FakeStore:
    def __init__(self, **settings):
        self.config = {
            "cloud_enabled": True,
            "gemini_model": "gemini-2.5-flash",
            "gemini_daily_limit": 2,
            "elevenlabs_enabled": True,
            "elevenlabs_voice_id": "test_voice",
            "elevenlabs_daily_char_limit": 100,
            **settings,
        }
        self.messages = [{"role": "user", "text": "Ich heiße Alex."}, {"role": "assistant", "text": "Verstanden, Sir."}]
        self.used = {}

    def settings(self):
        return self.config

    def history(self, conversation):
        return list(self.messages)

    def memory_epoch(self):
        return 0

    def append(self, role, text, conversation, expected_epoch=None):
        self.messages.append({"role": role, "text": text, "conversation": conversation})

    def reserve_usage(self, service, amount, limit):
        total = self.used.get(service, 0) + amount
        if total > limit:
            raise ValueError("quota")
        self.used[service] = total
        return {"used": total}


def answer(text="Sie heißen Alex, Sir."):
    return {"candidates": [{"content": {"parts": [{"text": text}]}}]}


class GeminiTests(unittest.TestCase):
    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-secret"})
    def test_context_and_header_auth_and_recording(self):
        captured = []
        store = FakeStore()

        def transport(url, payload, headers):
            captured.append((url, payload, headers))
            return answer()

        result = GeminiClient(store, transport).chat("Wie heiße ich?", "test")
        self.assertIn("Alex", result["reply"])
        url, payload, headers = captured[0]
        self.assertNotIn("test-secret", url)
        self.assertEqual(headers["x-goog-api-key"], "test-secret")
        self.assertEqual([m["role"] for m in payload["contents"]], ["user", "model", "user"])
        self.assertIn("Alex", payload["contents"][0]["parts"][0]["text"])
        self.assertEqual(store.messages[-2]["text"], "Wie heiße ich?")
        self.assertEqual(store.messages[-1]["role"], "assistant")

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-secret"})
    def test_quota_prevents_request_and_failed_calls_count(self):
        calls = []
        store = FakeStore(gemini_daily_limit=1)

        def fail(*args):
            calls.append(args)
            raise ProviderError("Nicht erreichbar", 502)

        client = GeminiClient(store, fail)
        with self.assertRaises(ProviderError):
            client.chat("Erster Versuch")
        with self.assertRaises(ProviderError) as caught:
            client.chat("Zweiter Versuch")
        self.assertEqual(caught.exception.status, 429)
        self.assertEqual(len(calls), 1)
        self.assertEqual(len(store.messages), 2)

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-secret"})
    def test_tools_are_proposals_and_completion_claim_replaced(self):
        response = {"candidates": [{"content": {"parts": [
            {"text": "Ich habe den Rechner bereits geöffnet."},
            {"functionCall": {"name": "open_app", "args": {"app": "Calculator"}}},
        ]}}]}
        result = GeminiClient(FakeStore(), lambda *_: response).chat("Öffne den Rechner")
        self.assertEqual(result["proposed_actions"], [{"kind": "open_app", "app": "Calculator"}])
        self.assertIn("Ausgeführt wurde noch nichts", result["reply"])
        self.assertNotIn("bereits geöffnet", result["reply"])

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-secret"})
    def test_unknown_function_and_extra_args_rejected(self):
        for call in [
            {"name": "run_shell", "args": {"command": "bad"}},
            {"name": "open_app", "args": {"app": "Calculator", "command": "bad"}},
            {"name": "open_app", "args": {"app": "Terminal"}},
        ]:
            with self.subTest(call=call):
                response = {"candidates": [{"content": {"parts": [{"functionCall": call}]}}]}
                store = FakeStore()
                with self.assertRaises(ProviderError):
                    GeminiClient(store, lambda *_: response).chat("Bitte ausführen")
                self.assertEqual(len(store.messages), 2)

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_key_and_disabled_provider_do_not_call(self):
        def forbidden(*args):
            self.fail("No request expected")
        for store in [FakeStore(), FakeStore(cloud_enabled=False)]:
            with self.assertRaises(ProviderError) as caught:
                GeminiClient(store, forbidden).chat("Hallo")
            self.assertEqual(caught.exception.status, 409)
            self.assertEqual(store.used, {})

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-secret"})
    def test_invalid_model_cannot_change_destination(self):
        with self.assertRaises(ProviderError):
            GeminiClient(FakeStore(gemini_model="../../evil.test"), lambda *_: answer()).chat("Hallo")

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-secret"})
    def test_empty_and_blocked_provider_response_has_clear_error(self):
        for response in [{}, {"candidates": []}, {"promptFeedback": {"blockReason": "SAFETY"}}]:
            with self.subTest(response=response), self.assertRaises(ProviderError) as caught:
                GeminiClient(FakeStore(), lambda *_: response).chat("Hallo")
            self.assertEqual(caught.exception.status, 502)


class ImageTests(unittest.TestCase):
    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-secret"})
    def test_inline_image_context_and_no_binary_retention(self):
        image = b"\x89PNG\r\n\x1a\n" + b"image-content"
        captured = []
        store = FakeStore()

        def transport(url, payload, headers):
            captured.append(payload)
            return answer("Das Bild zeigt eine technische Anzeige.")

        result = GeminiClient(store, transport).analyze_image("Was ist zu sehen?", image, "image/png", "photos")
        self.assertIn("technische Anzeige", result["reply"])
        self.assertEqual(result["proposed_actions"], [])
        payload = captured[0]
        self.assertNotIn("tools", payload)
        image_part = payload["contents"][-1]["parts"][-1]["inlineData"]
        self.assertEqual(image_part["mimeType"], "image/png")
        self.assertEqual(base64.b64decode(image_part["data"]), image)
        self.assertIn("Alex", payload["contents"][0]["parts"][0]["text"])
        self.assertEqual(store.used["gemini_requests"], 1)
        self.assertIn("Bilddaten werden nicht gespeichert", store.messages[-2]["text"])
        self.assertNotIn(image_part["data"], repr(store.messages))
        self.assertNotIn("image-content", repr(store.messages))

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-secret"})
    def test_invalid_images_never_consume_quota_or_call_provider(self):
        invalid = [
            (b"not-a-png", "image/png"),
            (b"\xff\xd8\xffJPEG", "image/png"),
            (b"GIF89a", "image/gif"),
            (b"RIFFbad", "image/webp"),
            (b"", "image/jpeg"),
            ("text", "image/jpeg"),
            (b"\xff\xd8\xff" + b"0" * (4 * 1024 * 1024), "image/jpeg"),
        ]
        for image, mime in invalid:
            with self.subTest(mime=mime, size=len(image)):
                store = FakeStore()
                def forbidden(*args):
                    self.fail("Invalid image must not be sent")
                with self.assertRaises(ProviderError):
                    GeminiClient(store, forbidden).analyze_image("Beschreiben", image, mime)
                self.assertEqual(store.used, {})

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-secret"})
    def test_jpeg_and_webp_supported_and_empty_prompt_default(self):
        for image, mime in [(b"\xff\xd8\xffJPEG", "image/jpeg"), (b"RIFF\x04\x00\x00\x00WEBP", "image/webp")]:
            with self.subTest(mime=mime):
                store = FakeStore()
                result = GeminiClient(store, lambda *_: answer()).analyze_image("", image, mime)
                self.assertEqual(result["conversation"], "default")
                self.assertIn("Beschreibe dieses Bild", store.messages[-2]["text"])

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-secret"})
    def test_image_path_rejects_unexpected_action(self):
        response = {"candidates": [{"content": {"parts": [{"functionCall": {"name": "open_app", "args": {"app": "Calculator"}}}]}}]}
        store = FakeStore()
        with self.assertRaises(ProviderError) as caught:
            GeminiClient(store, lambda *_: response).analyze_image("Beschreibe", b"\xff\xd8\xffJPEG")
        self.assertEqual(caught.exception.status, 502)
        self.assertEqual(len(store.messages), 2)

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-secret"})
    def test_image_respects_cloud_opt_in_and_shared_quota(self):
        for settings in [{"cloud_enabled": False}, {"gemini_daily_limit": 0}]:
            store = FakeStore(**settings)
            with self.assertRaises(ProviderError):
                GeminiClient(store, lambda *_: self.fail("No request expected")).analyze_image("Bild", b"\xff\xd8\xffJPEG")
            self.assertEqual(store.used, {})


class VoiceTests(unittest.TestCase):
    @patch.dict(os.environ, {"ELEVENLABS_API_KEY": "voice-secret"})
    def test_real_audio_protocol_and_character_quota(self):
        captured = []
        store = FakeStore(elevenlabs_daily_char_limit=5)

        def transport(url, payload, headers, **options):
            captured.append((url, payload, headers, options))
            return b"ID3-audio"

        client = VoiceClient(store, transport)
        self.assertEqual(client.synthesize("Hallo"), b"ID3-audio")
        self.assertEqual(store.used["elevenlabs_characters"], 5)
        with self.assertRaises(ProviderError) as caught:
            client.synthesize("Noch")
        self.assertEqual(caught.exception.status, 429)
        self.assertEqual(len(captured), 1)
        url, payload, headers, options = captured[0]
        self.assertTrue(url.startswith("https://api.elevenlabs.io/v1/text-to-speech/test_voice"))
        self.assertNotIn("voice-secret", url)
        self.assertEqual(headers["xi-api-key"], "voice-secret")
        self.assertEqual(options["expected_type"], "audio/mpeg")

    @patch.dict(os.environ, {"ELEVENLABS_API_KEY": "voice-secret"})
    def test_invalid_voice_or_opt_in_blocked_before_request(self):
        for settings in [{"elevenlabs_voice_id": "../users"}, {"elevenlabs_enabled": False}]:
            store = FakeStore(**settings)
            with self.assertRaises(ProviderError):
                VoiceClient(store, lambda *_: self.fail("No request expected")).synthesize("Hallo")
            self.assertEqual(store.used, {})


class TransportTests(unittest.TestCase):
    def assert_transport_failure(self, error, expected, provider="ElevenLabs"):
        url = "https://api.elevenlabs.io/v1/text-to-speech/private-voice?private=secret-value"
        with patch("backend.providers._open_request", side_effect=error) as request:
            with self.assertRaises(ProviderError) as caught:
                request_json(url, {"private-text": "secret-value"}, {"xi-api-key": "secret-value"})
        message = str(caught.exception)
        self.assertIn(expected, message)
        self.assertIn(provider, message)
        self.assertNotIn("secret-value", message)
        self.assertNotIn("private-voice", message)
        self.assertNotIn("https://", message)
        self.assertEqual(caught.exception.status, 502)
        request.assert_called_once()
        return message

    def test_nested_certificate_failure_has_actionable_safe_diagnosis(self):
        error = urllib.error.URLError(urllib.error.URLError(ssl.SSLCertVerificationError(1, "secret-value")))
        message = self.assert_transport_failure(error, "HTTPS-Zertifikat")
        self.assertIn("python.org", message)
        self.assertIn("macOS", message)
        self.assertIn("Install Certificates.command", message)
        self.assertIn("Zertifikatsprüfung bleibt aktiviert", message)

    def test_timeout_dns_refused_and_other_tls_are_distinct(self):
        cases = [
            (urllib.error.URLError(TimeoutError("secret-value")), "Wartezeit"),
            (socket.gaierror(socket.EAI_NONAME, "secret-value"), "DNS"),
            (urllib.error.URLError(ConnectionRefusedError(errno.ECONNREFUSED, "secret-value")), "abgelehnt"),
            (ssl.SSLError(1, "secret-value"), "sichere HTTPS-Verbindung"),
            (ConnectionResetError(errno.ECONNRESET, "secret-value"), "unterbrochen"),
            (OSError(errno.ENETUNREACH, "secret-value"), "keine Netzwerkverbindung"),
            (urllib.error.URLError("secret-value"), "momentan nicht erreichbar"),
        ]
        for error, expected in cases:
            with self.subTest(error=type(error).__name__, category=expected):
                self.assert_transport_failure(error, expected)

    def test_provider_name_only_comes_from_exact_host_allowlist(self):
        cause = urllib.error.URLError(TimeoutError("secret-value"))
        self.assertIn("Google Gemini", safe_network_message("https://generativelanguage.googleapis.com/v1beta/models", cause))
        message = safe_network_message("https://api.elevenlabs.io.attacker.invalid/private?key=secret-value", cause)
        self.assertIn("Der Anbieter", message)
        self.assertNotIn("ElevenLabs", message)
        self.assertNotIn("attacker.invalid", message)
        self.assertNotIn("secret-value", message)

    def test_key_refusal_is_not_misclassified_as_network_failure(self):
        error = urllib.error.HTTPError("https://api.elevenlabs.io/private", 401, "secret-value", {}, io.BytesIO(b"secret-value"))
        message = self.assert_transport_failure(error, "Zugriff abgelehnt")
        self.assertNotIn("momentan nicht erreichbar", message)
        self.assertIn("Schlüssel", message)

    def test_diagnostic_exception_cycles_terminate_without_raw_data(self):
        error = urllib.error.URLError("secret-value")
        error.reason = error
        error.__cause__ = error
        message = safe_network_message("https://api.elevenlabs.io", error)
        self.assertIn("momentan nicht erreichbar", message)
        self.assertNotIn("secret-value", message)

    def test_upstream_error_body_never_exposed(self):
        secret = "sensitive-upstream-secret"
        error = urllib.error.HTTPError("https://example.test", 403, secret, {}, io.BytesIO(secret.encode()))
        with patch("backend.providers._open_request", side_effect=error):
            with self.assertRaises(ProviderError) as caught:
                request_json("https://example.test", {}, {"x-api-key": secret})
        self.assertNotIn(secret, str(caught.exception))
        self.assertEqual(caught.exception.status, 502)

    def test_redirects_cannot_forward_credentials(self):
        request = __import__("urllib.request", fromlist=["Request"]).Request("https://example.test", headers={"x-api-key": "a-secret"})
        with self.assertRaises(urllib.error.HTTPError):
            _NoRedirect().redirect_request(request, None, 302, "Found", {}, "https://other.test")

    @patch.dict(os.environ, {"GEMINI_API_KEY": "a-secret", "ELEVENLABS_API_KEY": "another-secret"})
    def test_status_only_reveals_presence(self):
        self.assertEqual(provider_status(), {"gemini_key_configured": True, "elevenlabs_key_configured": True})


if __name__ == "__main__":
    unittest.main()
