import http.client,tempfile,threading,unittest
from pathlib import Path
from backend.server import Application,JarvisServer
from backend.mobile import DeviceAuth
class OfflineEntryTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.app=Application(self.temp.name);self.server=JarvisServer(('127.0.0.1',0),self.app);self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start();self.addCleanup(self.close)
 def close(self):self.app.studio_bridge.stop();self.app.office.stop();self.app.desktop.stop();self.server.shutdown();self.server.server_close();self.thread.join(2)
 def get(self,path,agent='TestDesktop'):
  c=http.client.HTTPConnection('127.0.0.1',self.server.server_port);c.request('GET',path,headers={'User-Agent':agent});r=c.getresponse();out=r.status,r.read(),dict(r.getheaders());c.close();return out
 def test_phone_root_is_actual_offline_workspace_with_scoped_wasm_policy(self):
  status,body,headers=self.get('/','Mozilla/5.0 iPhone');self.assertEqual(status,200);self.assertIn(b'data-device-app',body);self.assertIn(b'offline-ready.js',body);self.assertIn(b'device-startup',body);self.assertIn("'wasm-unsafe-eval'",headers['Content-Security-Policy'])
  status,body,headers=self.get('/');self.assertIn(b'app-shell',body);self.assertNotIn('wasm-unsafe-eval',headers['Content-Security-Policy'])
 def test_pairing_and_api_guards_are_not_bypassed_for_offline_preparation(self):
  self.server.device_auth=DeviceAuth(Path(self.temp.name)/'device.json');status,body,_=self.get('/','iPhone');self.assertEqual(status,200);self.assertIn(b'pair-form',body);self.assertNotIn(b'device-chat-form',body)
  for path in ['/offline-ready.js','/offline-ready.css','/api/session','/api/history']:
   self.assertEqual(self.get(path,'iPhone')[0],401)
 def test_offline_assets_are_real_static_files_on_local_authenticated_host(self):
  for path in ['/offline-ready.js','/offline-ready.css','/aeris-sw.js']:
   status,body,headers=self.get(path);self.assertEqual(status,200);self.assertGreater(len(body),20);self.assertEqual(headers['Cache-Control'],'no-store')
