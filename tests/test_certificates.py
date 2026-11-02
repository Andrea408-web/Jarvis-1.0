from contextlib import ExitStack, redirect_stderr, redirect_stdout
import io
from pathlib import Path
import stat
import subprocess
import unittest
from unittest.mock import Mock, patch

from backend.certificates import _official_script, repair_certificates
from backend.server import main


VERSION = "3.13"
PREFIX = Path("/Library/Frameworks/Python.framework/Versions/3.13")
SCRIPT = Path("/Applications/Python 3.13/Install Certificates.command")
PRIVATE_OUTPUT = "fixture-private-registry-auth-do-not-echo"


class CertificateRepairTests(unittest.TestCase):
    @patch("backend.certificates.platform.system", return_value="Linux")
    @patch("backend.certificates._runtime_layout")
    @patch("backend.certificates._official_script")
    @patch("backend.certificates.subprocess.run")
    def test_non_mac_rejected_before_files_or_subprocess(self, run, locate, layout, _platform):
        with self.assertRaises(ValueError) as caught:
            repair_certificates()
        self.assertIn("nur auf dem Mac", str(caught.exception))
        layout.assert_not_called()
        locate.assert_not_called()
        run.assert_not_called()

    @patch("backend.certificates.platform.system", return_value="Darwin")
    @patch("backend.certificates._runtime_layout")
    @patch("backend.certificates._official_script")
    @patch("backend.certificates.subprocess.run")
    def test_homebrew_and_mismatched_framework_rejected_before_script(self, run, locate, layout, _platform):
        for version, prefix in [
            (VERSION, Path("/opt/homebrew/opt/python@3.13/Frameworks/Python.framework/Versions/3.13")),
            (VERSION, Path("/Library/Frameworks/Python.framework/Versions/3.12")),
            ("3.13/../../other", PREFIX),
            (VERSION, Path("/usr/bin")),
        ]:
            with self.subTest(prefix=str(prefix), version=version):
                layout.return_value = (version, prefix)
                with self.assertRaises(ValueError):
                    repair_certificates()
        locate.assert_not_called()
        run.assert_not_called()

    @patch("backend.certificates.platform.system", return_value="Darwin")
    @patch("backend.certificates._runtime_layout", return_value=(VERSION, PREFIX))
    @patch("backend.certificates.Path.lstat", side_effect=FileNotFoundError)
    @patch("backend.certificates.subprocess.run")
    def test_missing_exact_version_script_starts_nothing(self, run, _stat, _layout, _platform):
        with self.assertRaises(ValueError) as caught:
            repair_certificates()
        self.assertIn("nicht gefunden", str(caught.exception))
        run.assert_not_called()

    @patch("backend.certificates.Path.resolve")
    @patch("backend.certificates.Path.lstat")
    def test_script_must_be_regular_and_not_redirected(self, metadata, resolve):
        for mode in [stat.S_IFLNK | 0o777, stat.S_IFDIR | 0o755, stat.S_IFIFO | 0o600]:
            metadata.return_value = Mock(st_mode=mode)
            with self.assertRaises(ValueError):
                _official_script(VERSION)
        metadata.return_value = Mock(st_mode=stat.S_IFREG | 0o755)
        resolve.return_value = Path("/tmp/untrusted-installer")
        with self.assertRaises(ValueError):
            _official_script(VERSION)
        resolve.return_value = SCRIPT
        self.assertEqual(_official_script(VERSION), SCRIPT)

    @patch("backend.certificates.platform.system", return_value="Darwin")
    @patch("backend.certificates._runtime_layout", return_value=(VERSION, PREFIX))
    @patch("backend.certificates._official_script", return_value=SCRIPT)
    @patch("backend.certificates.subprocess.run")
    def test_success_uses_exact_official_path_and_does_not_claim_connectivity(self, run, locate, _layout, _platform):
        run.return_value = Mock(returncode=0, stdout=PRIVATE_OUTPUT, stderr=PRIVATE_OUTPUT)
        message = repair_certificates()
        locate.assert_called_once_with(VERSION)
        run.assert_called_once_with([str(SCRIPT)], capture_output=True, text=True, timeout=120, check=False)
        self.assertNotIn("shell", run.call_args.kwargs)
        self.assertNotIn("env", run.call_args.kwargs)
        self.assertNotIn(PRIVATE_OUTPUT, message)
        self.assertIn("abgeschlossen", message)
        self.assertIn("noch nicht auf Erreichbarkeit geprüft", message)

    @patch("backend.certificates.platform.system", return_value="Darwin")
    @patch("backend.certificates._runtime_layout", return_value=(VERSION, PREFIX))
    @patch("backend.certificates._official_script", return_value=SCRIPT)
    @patch("backend.certificates.subprocess.run")
    def test_failures_do_not_expose_registry_output_or_disable_tls(self, run, _locate, _layout, _platform):
        failures = [
            Mock(returncode=1, stdout=PRIVATE_OUTPUT, stderr=PRIVATE_OUTPUT),
            OSError(PRIVATE_OUTPUT),
            subprocess.TimeoutExpired(str(SCRIPT), 120, output=PRIVATE_OUTPUT, stderr=PRIVATE_OUTPUT),
        ]
        for failure in failures:
            with self.subTest(failure=type(failure).__name__):
                run.reset_mock()
                if isinstance(failure, Exception):
                    run.side_effect = failure
                else:
                    run.side_effect = None
                    run.return_value = failure
                with self.assertRaises(ValueError) as caught:
                    repair_certificates()
                self.assertNotIn(PRIVATE_OUTPUT, str(caught.exception))
                run.assert_called_once()


class CertificateRepairCLITests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.repair = self.stack.enter_context(patch("backend.server.repair_certificates"))
        self.forbidden = [
            self.stack.enter_context(patch(name))
            for name in [
                "backend.server.Application",
                "backend.server.JarvisServer",
                "backend.server.load_saved_keys",
                "backend.server.check_connection",
                "backend.server.getpass.getpass",
                "backend.providers._open_request",
                "backend.certificates.subprocess.run",
                "webbrowser.open",
            ]
        ]

    def assert_repair_only(self):
        self.repair.assert_called_once_with()
        for other in self.forbidden:
            other.assert_not_called()

    def test_explicit_repair_cli_runs_helper_without_starting_other_services(self):
        safe_message = "Das Zertifikatsprogramm wurde abgeschlossen. Verbindung noch nicht geprüft."
        self.repair.return_value = safe_message
        output, errors = io.StringIO(), io.StringIO()
        with redirect_stdout(output), redirect_stderr(errors):
            result = main(["--repair-certificates", "--ask-keys", "--open-browser"])
        self.assertIsNone(result)
        self.assertEqual(output.getvalue(), safe_message + "\n")
        self.assertEqual(errors.getvalue(), "")
        self.assert_repair_only()

    def test_repair_cli_failure_exits_one_with_safe_message_and_no_traceback(self):
        safe_message = "Das Zertifikatsprogramm ist nicht verfügbar. Bitte die Python-Installation prüfen."
        failure = ValueError(safe_message)
        failure.__cause__ = OSError(PRIVATE_OUTPUT)
        self.repair.side_effect = failure
        output, errors = io.StringIO(), io.StringIO()
        with redirect_stdout(output), redirect_stderr(errors):
            with self.assertRaises(SystemExit) as caught:
                main(["--repair-certificates", "--ask-keys", "--open-browser"])
        self.assertEqual(caught.exception.code, 1)
        self.assertEqual(output.getvalue(), "")
        self.assertEqual(errors.getvalue(), safe_message + "\n")
        self.assertNotIn("Traceback", errors.getvalue())
        self.assertNotIn(PRIVATE_OUTPUT, output.getvalue() + errors.getvalue())
        self.assert_repair_only()


if __name__ == "__main__":
    unittest.main()
