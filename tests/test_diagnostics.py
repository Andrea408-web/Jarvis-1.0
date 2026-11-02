import io
import os
import ssl
import unittest
import urllib.error
from contextlib import redirect_stdout
from unittest.mock import patch, Mock

from backend.diagnostics import check_connection


class DiagnosticTests(unittest.TestCase):
    @patch.dict(os.environ, {'GEMINI_API_KEY': 'never-send-this-value', 'ELEVENLABS_API_KEY': 'another-secret'})
    def test_catalog_probe_has_no_key_no_generation_and_closes_response(self):
        response = Mock(status=200)
        calls = []

        def opener(request, **options):
            calls.append((request, options))
            return response

        result = check_connection('elevenlabs', opener)
        request, options = calls[0]
        self.assertEqual(request.get_method(), 'GET')
        self.assertEqual(request.full_url, 'https://api.elevenlabs.io/v1/voices')
        self.assertEqual(options, {'timeout': 10})
        self.assertIsNone(request.data)
        self.assertNotIn('xi-api-key', str(request.headers).lower())
        self.assertNotIn('another-secret', str(request.headers))
        self.assertTrue(result['ok'])
        self.assertIn('nicht geprüft', result['message'])
        response.close.assert_called_once()
        response.read.assert_not_called()

    def test_unauthenticated_401_confirms_https_without_claiming_valid_key(self):
        stream = io.BytesIO(b'private error body')
        error = urllib.error.HTTPError('https://not-returned', 401, 'secret detail', {}, stream)
        result = check_connection('gemini', Mock(side_effect=error))
        self.assertTrue(result['ok'])
        self.assertEqual(result['http_status'], 401)
        self.assertIn('keinen API-Schlüssel', result['message'])
        self.assertNotIn('secret', result['message'])
        self.assertTrue(stream.closed)

    def test_policy_403_does_not_establish_provider_readiness(self):
        error = urllib.error.HTTPError('https://not-returned', 403, 'private proxy value', {}, io.BytesIO())
        result = check_connection('gemini', Mock(side_effect=error))
        self.assertFalse(result['ok'])
        self.assertIn('Netzrichtlinie', result['message'])
        self.assertNotIn('private proxy value', result['message'])

    def test_certificate_failure_is_specific_and_does_not_echo_raw_error(self):
        error = urllib.error.URLError(ssl.SSLCertVerificationError(1, 'SECRET CERTIFICATE_VERIFY_FAILED'))
        result = check_connection('elevenlabs', Mock(side_effect=error))
        self.assertFalse(result['ok'])
        self.assertIsNone(result['http_status'])
        self.assertIn('Zertifikat', result['message'])
        self.assertNotIn('SECRET', result['message'])

    def test_provider_allowlist_blocks_arbitrary_destinations_before_call(self):
        opener = Mock()
        for value in ['https://private.test', 'unknown', None, {}, 'elevenlabs/../other']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                check_connection(value, opener)
        opener.assert_not_called()

    def test_explicit_cli_diagnostic_does_not_load_credentials_or_start_server(self):
        from backend.server import main
        result = {'message': 'Verbindung geprüft, keine Generierung.'}
        with patch('backend.server.check_connection', return_value=result) as check, \
             patch('backend.server.load_saved_keys') as credentials, \
             patch('backend.server.Application') as app, redirect_stdout(io.StringIO()) as output:
            main(['--check-connection', 'elevenlabs'])
        check.assert_called_once_with('elevenlabs')
        credentials.assert_not_called()
        app.assert_not_called()
        self.assertIn(result['message'], output.getvalue())


if __name__ == '__main__':
    unittest.main()
