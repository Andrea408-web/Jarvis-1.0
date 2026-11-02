import os
import subprocess
import unittest
from unittest.mock import Mock, patch

from backend.credentials import configure, load_saved_keys


GEMINI_FIXTURE = "fixture-gemini-key_12345"
VOICE_FIXTURE = "fixture-voice-key_12345"


class CredentialTests(unittest.TestCase):
    @patch.dict(os.environ, {}, clear=True)
    @patch("backend.credentials.platform.system", return_value="Linux")
    @patch("backend.credentials.subprocess.run")
    def test_linux_session_only_sets_memory_without_native_command(self, run, _platform):
        result = configure("gemini", GEMINI_FIXTURE, persist=False)
        self.assertEqual(os.environ["GEMINI_API_KEY"], GEMINI_FIXTURE)
        self.assertEqual(result["provider"], "gemini")
        self.assertFalse(result["persisted"])
        self.assertTrue(result["configured"])
        self.assertNotIn(GEMINI_FIXTURE, repr(result))
        run.assert_not_called()

    @patch.dict(os.environ, {}, clear=True)
    @patch("backend.credentials.platform.system", return_value="Linux")
    @patch("backend.credentials.subprocess.run")
    def test_linux_persistence_rejected_without_activation(self, run, _platform):
        with self.assertRaises(ValueError) as caught:
            configure("gemini", GEMINI_FIXTURE)
        self.assertIn("Sitzung", str(caught.exception))
        self.assertNotIn("GEMINI_API_KEY", os.environ)
        run.assert_not_called()

    @patch.dict(os.environ, {}, clear=True)
    @patch("backend.credentials.platform.system", return_value="Darwin")
    @patch("backend.credentials.subprocess.run")
    def test_keychain_write_uses_stdin_not_argv_and_verifies_readback(self, run, _platform):
        run.side_effect = [Mock(returncode=0, stdout="", stderr=""), Mock(returncode=0, stdout=VOICE_FIXTURE + "\n", stderr="")]
        result = configure("elevenlabs", VOICE_FIXTURE)
        write, read = run.call_args_list
        self.assertEqual(write.args[0], ["/usr/bin/security", "-i"])
        self.assertNotIn(VOICE_FIXTURE, repr(write.args))
        self.assertIn(VOICE_FIXTURE, write.kwargs["input"])
        self.assertIn("-s com.jarvis.elevenlabs", write.kwargs["input"])
        self.assertNotIn(VOICE_FIXTURE, repr(read.args))
        self.assertTrue(write.kwargs["capture_output"])
        self.assertEqual(write.kwargs["timeout"], 10)
        self.assertEqual(os.environ["ELEVENLABS_API_KEY"], VOICE_FIXTURE)
        self.assertTrue(result["persisted"])
        self.assertNotIn(VOICE_FIXTURE, repr(result))

    @patch.dict(os.environ, {"GEMINI_API_KEY": "existing-working-binding"}, clear=True)
    @patch("backend.credentials.platform.system", return_value="Darwin")
    @patch("backend.credentials.subprocess.run")
    def test_keychain_failure_keeps_existing_environment_and_hides_details(self, run, _platform):
        for failure in [Mock(returncode=1, stdout=GEMINI_FIXTURE, stderr=GEMINI_FIXTURE), OSError(GEMINI_FIXTURE), subprocess.TimeoutExpired("security", 10, output=GEMINI_FIXTURE)]:
            with self.subTest(failure=type(failure).__name__):
                run.reset_mock()
                if isinstance(failure, Exception):
                    run.side_effect = failure
                else:
                    run.side_effect = None
                    run.return_value = failure
                with self.assertRaises(ValueError) as caught:
                    configure("gemini", GEMINI_FIXTURE)
                self.assertNotIn(GEMINI_FIXTURE, str(caught.exception))
                self.assertEqual(os.environ["GEMINI_API_KEY"], "existing-working-binding")

    @patch.dict(os.environ, {}, clear=True)
    @patch("backend.credentials.platform.system", return_value="Darwin")
    @patch("backend.credentials.subprocess.run")
    def test_interactive_success_exit_with_wrong_readback_is_not_activated(self, run, _platform):
        run.side_effect = [Mock(returncode=0, stdout="", stderr="command failed"), Mock(returncode=0, stdout="different-saved-key\n", stderr="")]
        with self.assertRaises(ValueError):
            configure("gemini", GEMINI_FIXTURE)
        self.assertNotIn("GEMINI_API_KEY", os.environ)

    @patch.dict(os.environ, {}, clear=True)
    @patch("backend.credentials.subprocess.run")
    def test_invalid_key_provider_and_choice_rejected_before_update(self, run):
        for key in [None, 42, "", "short", "x" * 513, "secret;injection", "abcdefghij\nquit", "abcdefghij\r", "abcdefghij key", "Schlüssel12345"]:
            with self.subTest(key_type=type(key).__name__, length=len(key) if isinstance(key, str) else None):
                with self.assertRaises(ValueError):
                    configure("gemini", key, persist=False)
        for provider in [None, {}, "unknown", "gemini\nquit"]:
            with self.subTest(provider_type=type(provider).__name__):
                with self.assertRaises(ValueError):
                    configure(provider, GEMINI_FIXTURE, persist=False)
        for choice in [None, 1, "true"]:
            with self.assertRaises(ValueError):
                configure("gemini", GEMINI_FIXTURE, persist=choice)
        self.assertNotIn("GEMINI_API_KEY", os.environ)
        run.assert_not_called()

    @patch.dict(os.environ, {"GEMINI_API_KEY": "existing-injected-binding"}, clear=True)
    @patch("backend.credentials.platform.system", return_value="Darwin")
    @patch("backend.credentials.subprocess.run")
    def test_load_keeps_injected_binding_and_loads_other_provider(self, run, _platform):
        run.return_value = Mock(returncode=0, stdout=VOICE_FIXTURE + "\n", stderr="")
        result = load_saved_keys()
        self.assertEqual(os.environ["GEMINI_API_KEY"], "existing-injected-binding")
        self.assertEqual(os.environ["ELEVENLABS_API_KEY"], VOICE_FIXTURE)
        run.assert_called_once()
        self.assertIn("com.jarvis.elevenlabs", run.call_args.args[0])
        self.assertEqual(result, {"gemini_key_configured": True, "elevenlabs_key_configured": True})
        self.assertNotIn(VOICE_FIXTURE, repr(result))

    @patch.dict(os.environ, {}, clear=True)
    @patch("backend.credentials.platform.system", return_value="Darwin")
    @patch("backend.credentials.subprocess.run")
    def test_missing_locked_or_invalid_keychain_allows_local_startup(self, run, _platform):
        for value in [Mock(returncode=44, stdout="", stderr="locked"), Mock(returncode=0, stdout="invalid key with spaces\n", stderr=""), OSError("not available")]:
            run.reset_mock()
            if isinstance(value, Exception):
                run.side_effect = value
            else:
                run.side_effect = None
                run.return_value = value
            self.assertEqual(load_saved_keys(), {"gemini_key_configured": False, "elevenlabs_key_configured": False})
            self.assertNotIn("GEMINI_API_KEY", os.environ)
            self.assertNotIn("ELEVENLABS_API_KEY", os.environ)

    @patch.dict(os.environ, {"GEMINI_API_KEY": GEMINI_FIXTURE}, clear=True)
    @patch("backend.credentials.platform.system", return_value="Linux")
    @patch("backend.credentials.subprocess.run")
    def test_linux_load_does_not_access_keychain(self, run, _platform):
        self.assertEqual(load_saved_keys(), {"gemini_key_configured": True, "elevenlabs_key_configured": False})
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
