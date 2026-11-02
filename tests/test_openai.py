import json
import os
import tempfile
import unittest
from unittest.mock import patch, Mock

from backend.openai_client import OpenAIClient
from backend.providers import ProviderError
from backend.storage import Store
from backend.server import Application
from backend.credentials import configure


def answer(text='Guten Tag, Sir.'):
    return {'choices': [{'message': {'role': 'assistant', 'content': text}}]}


@patch.dict(os.environ, {'OPENAI_API_KEY': 'test-openai-key-not-real'}, clear=True)
class OpenAITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = Store(self.temp.name)
        self.store.update_settings({'cloud_enabled': True, 'ai_provider': 'openai', 'openai_daily_limit': 1})

    def test_real_protocol_context_auth_and_separate_budget(self):
        self.store.append('user', 'Ich heiße Alex.')
        transport = Mock(return_value=answer())
        client = OpenAIClient(self.store, transport)
        self.assertIn('Sir', client.chat('Hallo')['reply'])
        url, payload, headers = transport.call_args.args
        self.assertEqual(url, 'https://api.openai.com/v1/chat/completions')
        self.assertNotIn(os.environ['OPENAI_API_KEY'], json.dumps(payload))
        self.assertEqual(headers['Authorization'], 'Bearer ' + os.environ['OPENAI_API_KEY'])
        self.assertEqual(payload['messages'][1]['content'], 'Ich heiße Alex.')
        self.assertEqual(payload['model'], 'gpt-4o-mini')
        self.assertFalse(payload['store'])
        self.assertEqual(self.store.usage()['openai_requests'], 1)
        self.assertEqual(self.store.usage()['gemini_requests'], 0)
        with self.assertRaises(ProviderError): client.chat('Nochmal')
        self.assertEqual(transport.call_count, 1)

    def test_disabled_missing_key_and_zero_quota_never_call(self):
        transport = Mock()
        self.store.update_settings({'cloud_enabled': False})
        with self.assertRaises(ProviderError): OpenAIClient(self.store, transport).chat('Hallo')
        self.store.update_settings({'cloud_enabled': True})
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(ProviderError):
            OpenAIClient(self.store, transport).chat('Hallo')
        self.store.update_settings({'openai_daily_limit': 0})
        with self.assertRaises(ProviderError): OpenAIClient(self.store, transport).chat('Hallo')
        transport.assert_not_called()

    def test_tool_is_pending_proposal_and_payload_has_json_schema(self):
        transport = Mock(return_value={'choices': [{'message': {'content': 'Schon ausgeführt!', 'tool_calls': [{'function': {'name': 'open_app', 'arguments': '{"app":"Calculator"}'}}]}}]})
        result = OpenAIClient(self.store, transport).chat('Öffne den Rechner bitte')
        self.assertEqual(result['proposed_actions'], [{'kind': 'open_app', 'app': 'Calculator'}])
        self.assertNotIn('Schon ausgeführt', result['reply'])
        self.assertEqual(transport.call_args.args[1]['tools'][0]['function']['parameters']['type'], 'object')

    def test_image_validated_and_not_persisted(self):
        transport = Mock(return_value=answer())
        client = OpenAIClient(self.store, transport)
        with self.assertRaises(ProviderError):client.analyze_image('Bild', b'not-an-image')
        transport.assert_not_called()
        client.analyze_image('Bild', b'\xff\xd8\xfftest', 'image/jpeg')
        self.assertNotIn('tools', transport.call_args.args[1])
        self.assertEqual(transport.call_args.args[1]['messages'][-1]['content'][1]['type'], 'image_url')
        self.assertNotIn('/9j/', json.dumps(self.store.history()))

    def test_dispatch_credential_presence_and_immutable_cloud_opt_in(self):
        app = Application(self.temp.name)
        app.openai.transport = Mock(return_value=answer())
        app.ai.chat = Mock(side_effect=AssertionError('Gemini must not be called'))
        result = app.chat('Erzähl etwas')
        self.assertIn('Sir', result['reply'])
        configure('openai', 'test-replacement-key-not-real', persist=False)
        metadata = app.settings()
        self.assertTrue(metadata['providers']['openai_configured'])
        self.assertNotIn('test-replacement-key-not-real', json.dumps(metadata))
        self.assertNotIn('OPENAI_API_KEY', self.store.settings())

    def test_invalid_configuration_does_not_partially_enable_cloud(self):
        self.store.update_settings({'cloud_enabled': False})
        for values in [{'ai_provider': 'bad'}, {'openai_model': '../secret'}, {'openai_daily_limit': True}]:
            with self.assertRaises(ValueError):self.store.update_settings({'cloud_enabled': True, **values})
            self.assertFalse(self.store.settings()['cloud_enabled'])
