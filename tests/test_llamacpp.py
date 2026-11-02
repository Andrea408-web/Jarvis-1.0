import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock,patch
from backend.llamacpp import LlamaCppClient,status,request_local
from backend.server import Application
from backend.storage import Store
from backend.small_model import locate,start,MODEL
from backend.providers import ProviderError

class SmallAITests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.store=Store(self.root/'data')
        self.store.update_settings({'ai_provider':'llamacpp','cloud_enabled':False})

    def test_real_protocol_without_key_model_fetch_or_cloud(self):
        transport=Mock(return_value={'choices':[{'finish_reason':'stop','message':{'content':'Eine lokale Antwort.'}}]})
        self.store.append('user','Ich heiße Alex.')
        with patch.dict('os.environ',{},clear=True):result=LlamaCppClient(self.store,transport).chat('Hallo')
        path,payload=transport.call_args.args
        self.assertEqual(path,'/v1/chat/completions');self.assertEqual(payload['max_tokens'],512)
        self.assertFalse(payload['stream']);self.assertNotIn('model',payload);self.assertNotIn('tools',payload)
        self.assertIn('Alex',json.dumps(payload));self.assertEqual(result['proposed_actions'],[])
        self.assertEqual(self.store.usage()['openai_requests'],0)

    def test_dispatch_does_not_use_ollama_or_paid_providers(self):
        app=Application(self.store.data_dir)
        app.ai.chat=app.openai.chat=app.local_ai.chat=Mock(side_effect=AssertionError('wrong provider'))
        app.llamacpp.endpoint_transport=Mock(return_value={'choices':[{'finish_reason':'stop','message':{'content':'Lokal.'}}]})
        self.assertEqual(app.chat('Erzähl einen Witz')['reply'],'Lokal.')
        app.ai.chat.assert_not_called()

    def test_status_and_incomplete_responses_do_not_claim_ready(self):
        for response in [{'status':'loading'},{}]:
            with patch('backend.llamacpp.request_local',return_value=response):self.assertFalse(status()['ok'])
        with patch('backend.llamacpp.request_local',side_effect=ProviderError('offline')):self.assertFalse(status()['ok'])
        for response in [{},{'choices':[{'finish_reason':'tool_calls','message':{'content':'Done'}}]}]:
            with self.assertRaises(ProviderError):LlamaCppClient(self.store,Mock(return_value=response)).chat('Hallo')
        with self.assertRaises(ValueError):request_local('/api/pull',{})

    @patch('backend.small_model.platform.system',return_value='Linux')
    @patch('backend.small_model.subprocess.run')
    def test_non_mac_never_runs_or_installs(self,run,_):
        with self.assertRaises(ValueError):start()
        run.assert_not_called()

    def prepare(self,size=1_000_001,magic=b'GGUF'):
        (self.root/'runtime').mkdir();(self.root/'runtime'/'llama-server').write_text('fixture only')
        (self.root/'models').mkdir()
        with (self.root/'models'/MODEL).open('wb') as f:f.write(magic);f.truncate(size)

    @patch('backend.small_model.platform.system',return_value='Darwin')
    def test_small_file_guard_and_fixed_loopback_launch(self,_):
        self.prepare()
        with patch('backend.small_model.ROOT',self.root),patch('backend.small_model.subprocess.run',return_value=Mock(returncode=0)) as run:
            start();args=run.call_args.args[0]
            self.assertEqual(args[args.index('--host')+1],'127.0.0.1')
            self.assertEqual(args[args.index('--port')+1],'8081')
            self.assertNotIn('-hf',args);self.assertNotIn('--model-url',args)
            self.assertNotIn('shell',run.call_args.kwargs)
            with (self.root/'models'/MODEL).open('r+b') as f:f.truncate(501*1024*1024)
            run.reset_mock()
            with self.assertRaises(ValueError):start()
            run.assert_not_called()

    @patch('backend.small_model.platform.system',return_value='Darwin')
    def test_missing_runtime_or_html_model_never_executes(self,_):
        with patch('backend.small_model.ROOT',self.root),patch('backend.small_model.shutil.which',return_value=None),patch('backend.small_model.subprocess.run') as run:
            with self.assertRaises(ValueError):start()
            self.prepare(magic=b'HTML')
            with self.assertRaises(ValueError):start()
            run.assert_not_called()

if __name__=='__main__':unittest.main()
