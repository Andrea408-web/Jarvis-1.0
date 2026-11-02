import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import Mock, patch
from backend.local_ai import LocalClient, local_request, local_status, validate_model
from backend.providers import ProviderError
from backend.server import Application
from backend.storage import Store


class LocalAITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.store=Store(self.temp.name)
        self.store.update_settings({'ai_provider':'ollama','cloud_enabled':False})

    def test_chat_without_key_or_cloud_uses_context_no_billing_or_tools(self):
        self.store.append('user','Ich heiße Alex.')
        transport=Mock(return_value={'done':True,'message':{'content':'Guten Tag Alex, Sir.'}})
        with patch.dict('os.environ',{},clear=True):
            result=LocalClient(self.store,transport).chat('Hallo')
        path,payload=transport.call_args.args
        self.assertEqual(path,'/api/chat');self.assertFalse(payload['stream'])
        self.assertEqual(payload['messages'][1]['content'],'Ich heiße Alex.')
        self.assertNotIn('tools',payload);self.assertNotIn('Authorization',json.dumps(payload))
        self.assertEqual(result['proposed_actions'],[])
        self.assertEqual(self.store.usage()['openai_requests'],0)
        self.assertEqual(self.store.usage()['gemini_requests'],0)
        self.assertIn('Alex',self.store.history()[-1]['text'])

    def test_selected_local_provider_never_calls_paid_client(self):
        app=Application(self.temp.name)
        app.ai.chat=Mock(side_effect=AssertionError('cloud'))
        app.openai.chat=Mock(side_effect=AssertionError('cloud'))
        app.local_ai.transport=Mock(return_value={'done':True,'message':{'content':'Lokal beantwortet.'}})
        self.assertEqual(app.chat('Wie geht es dir?')['reply'],'Lokal beantwortet.')
        app.ai.chat.assert_not_called();app.openai.chat.assert_not_called()

    def test_cloud_models_and_external_addresses_rejected_atomically(self):
        for value in ['gpt-oss:120b-cloud','https://example.test/model','../model',None,'model\nquit']:
            with self.subTest(value=value),self.assertRaises(ValueError):
                self.store.update_settings({'cloud_enabled':True,'local_model':value})
            self.assertFalse(self.store.settings()['cloud_enabled'])
        validate_model('qwen2.5:1.5b')

    def test_missing_or_unfinished_result_and_images_never_claim_success(self):
        for result in [{},{'done':False,'message':{'content':'partial'}},{'done':True,'message':{'content':'','tool_calls':[]}}]:
            with self.subTest(result=result),self.assertRaises(ProviderError):
                LocalClient(self.store,Mock(return_value=result)).chat('Hallo')
        transport=Mock()
        with self.assertRaises(ProviderError):LocalClient(self.store,transport).analyze_image('Bild',b'anything')
        transport.assert_not_called();self.assertEqual(self.store.history(),[])

    def test_status_explicitly_reports_missing_runtime_and_filters_cloud_models(self):
        with patch('backend.local_ai.local_request',side_effect=ProviderError('offline')):
            self.assertFalse(local_status()['ok'])
        with patch('backend.local_ai.local_request',return_value={'models':[{'name':'qwen2.5:1.5b'},{'name':'bad:cloud'}]}):
            self.assertEqual(local_status()['models'],['qwen2.5:1.5b'])

    def test_real_loopback_transport_and_redirect_refusal(self):
        seen=[]
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_POST(self):
                seen.append((self.path,json.loads(self.rfile.read(int(self.headers['Content-Length']))),dict(self.headers)))
                data=b'{"done":true,"message":{"content":"local test"}}'
                self.send_response(200);self.end_headers();self.wfile.write(data)
            def do_GET(self):
                self.send_response(302);self.send_header('Location','https://example.invalid/private');self.end_headers()
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            with patch('backend.local_ai.BASE','http://127.0.0.1:'+str(server.server_port)):
                result=local_request('/api/chat',{'model':'test','messages':[]})
                self.assertTrue(result['done'])
                with self.assertRaises(ProviderError):local_request('/api/tags')
                with self.assertRaises(ValueError):local_request('/api/pull',{'name':'model'})
            self.assertEqual(len(seen),1)
            self.assertNotIn('Authorization',seen[0][2]);self.assertEqual(seen[0][0],'/api/chat')
        finally:
            server.shutdown();server.server_close();thread.join()

if __name__=='__main__':unittest.main()
