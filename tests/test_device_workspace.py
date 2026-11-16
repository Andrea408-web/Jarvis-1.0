"""Integrity, explicit transfer and local-only device-chat boundaries."""
import hashlib,http.client,json,tempfile,threading,unittest
from pathlib import Path
from unittest.mock import Mock,patch
from backend.device_ai import DeviceAI,MAX_MODEL
from backend.brands import Brands
from backend.mobile import DeviceAuth
from backend.server import Application,JarvisServer

class DeviceDataTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
 def test_existing_model_integrity_and_no_paths_in_manifest(self):
  path=self.root/'small.gguf';raw=b'GGUF'+b'x'*512;path.write_bytes(raw);ai=DeviceAI(self.root,locator=lambda:path)
  manifest=ai.status();self.assertEqual(manifest['model']['sha256'],hashlib.sha256(raw).hexdigest());self.assertEqual(manifest['model']['chunks'],[hashlib.sha256(raw).hexdigest()]);self.assertNotIn(str(self.root),json.dumps(manifest));self.assertFalse(manifest['runtime_ready'])
  path.write_bytes(b'bad');self.assertIsNone(ai.status()['model'])
 def test_model_size_limit_and_missing_model_fail_before_network(self):
  path=self.root/'large.gguf'
  with path.open('wb') as out:out.write(b'GGUF');out.truncate(MAX_MODEL+1)
  ai=DeviceAI(self.root,locator=lambda:path);download=Mock()
  with self.assertRaises(ValueError):ai.prepare(download)
  download.assert_not_called();self.assertFalse(ai.root.exists())
 def test_invalid_archive_never_installs_executable_assets(self):
  path=self.root/'small.gguf';path.write_bytes(b'GGUFfixture');ai=DeviceAI(self.root,locator=lambda:path)
  with self.assertRaisesRegex(ValueError,'Prüfsumme'):ai.prepare(lambda package:b'not a verified archive')
  self.assertEqual(list(ai.root.iterdir()),[])
  with self.assertRaises(ValueError):ai.asset('../../secrets')
 def test_brand_revision_conflicts_preserve_data(self):
  brands=Brands(self.root);one=brands.save({'profile':{'id':'brand-1','name':'Lumen','colors':['#123abc']}})
  self.assertEqual(one['revision'],1)
  with self.assertRaisesRegex(ValueError,'geändert'):brands.save({'profile':{'id':'brand-1','name':'Overwrite'},'expected_revision':0})
  self.assertEqual(brands.all()['profiles'][0]['name'],'Lumen')
  two=brands.save({'profile':{'id':'brand-1','name':'Updated'},'expected_revision':1});self.assertEqual(two['revision'],2)
  self.assertEqual(Brands(self.root).all()['profiles'][0]['name'],'Updated');self.assertEqual(brands.path.stat().st_mode&0o777,0o600)
 def test_bad_brand_input_and_corruption_do_not_overwrite(self):
  brands=Brands(self.root)
  for profile in [{'name':''},{'name':'X','id':'../../secret'},{'name':'X','colors':['red']},{'name':'X','unknown':True}]:
   with self.assertRaises(ValueError):brands.save({'profile':profile})
  brands.path.write_text('broken')
  with self.assertRaises(ValueError):brands.save({'profile':{'name':'new'}})
  self.assertEqual(brands.path.read_text(),'broken')

class DeviceApiTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.app=Application(self.tmp.name);self.server=JarvisServer(('127.0.0.1',0),self.app);self.thread=threading.Thread(target=self.server.serve_forever,kwargs={'poll_interval':.01},daemon=True);self.thread.start();self.addCleanup(self.close)
 def close(self):
  self.app.office.stop();self.app.desktop.stop();self.server.shutdown();self.server.server_close();self.thread.join(3)
 def request(self,method,path,body=None,token=True):
  conn=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=10);headers={'Content-Type':'application/json'}
  if token:headers['X-Jarvis-Token']=self.app.token
  conn.request(method,path,None if body is None else json.dumps(body),headers);response=conn.getresponse();raw=response.read();out=(response.status,raw,dict(response.getheaders()));conn.close();return out
 def test_model_and_brand_require_session_and_pairing(self):
  for path in ['/api/device-ai/status','/api/device-ai/model','/api/brands']:
   self.assertEqual(self.request('GET',path,token=False)[0],401)
  self.server.device_auth=DeviceAuth(Path(self.tmp.name)/'device.json')
  for path in ['/device-runtime/3.13.0/wllama.js','/api/device-ai/model','/api/brands']:
   self.assertEqual(self.request('GET',path)[0],401)
  status,body,_=self.request('GET','/tablet',token=False);self.assertEqual(status,200);self.assertIn(b'pair-form',body);self.assertNotIn(b'device-chat-form',body)
 def test_tablet_has_scoped_wasm_policy_and_brand_transfer(self):
  status,raw,headers=self.request('GET','/tablet',token=False);self.assertEqual(status,200);self.assertIn("'wasm-unsafe-eval'",headers['Content-Security-Policy']);self.assertIn("worker-src 'self' blob:",headers['Content-Security-Policy']);self.assertNotIn("'unsafe-eval'",headers['Content-Security-Policy'])
  self.assertNotIn('wasm-unsafe-eval',self.request('GET','/index.html')[2]['Content-Security-Policy'])
  self.assertEqual(self.request('POST','/api/brands',{'profile':{'name':'Lumen'}})[0],200)
  self.assertEqual(json.loads(self.request('GET','/api/brands')[1])['profiles'][0]['name'],'Lumen')
 def test_device_chat_never_uses_cloud_or_desktop_actions(self):
  self.app.store.update_settings({'ai_provider':'gemini','cloud_enabled':True})
  with patch.object(self.app.ai,'chat',side_effect=AssertionError('Cloud forbidden')):
   status,raw,_=self.request('POST','/api/device-ai/chat',{'text':'Hi','history':[],'mode':'astra'});self.assertEqual(status,400);self.assertIn('lokale',raw.decode().lower())
  self.app.store.update_settings({'ai_provider':'llamacpp'})
  with patch.object(self.app.llamacpp,'transport',return_value={'done':True,'message':{'content':'Hallo Sir.'}}) as chat:
   status,raw,_=self.request('POST','/api/device-ai/chat',{'text':'Hallo','history':[],'mode':'aeris'});self.assertEqual(status,200);self.assertIn('AERIS',str(chat.call_args));self.assertIsNone(self.app.desktop.plan)
