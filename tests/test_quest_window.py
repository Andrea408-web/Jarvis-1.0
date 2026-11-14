import http.client,tempfile,threading,unittest
from http.server import ThreadingHTTPServer
from unittest.mock import patch
from backend.quest_window import StaticHandler,QuestWindow
class QuestWindowTests(unittest.TestCase):
 def test_public_studio_never_serves_app_api_or_private_files(self):
  server=ThreadingHTTPServer(('127.0.0.1',0),StaticHandler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
  def request(path,method='GET'):
   c=http.client.HTTPConnection(*server.server_address,timeout=5)
   try:c.request(method,path);r=c.getresponse();return r.status,r.read(),dict(r.getheaders())
   finally:c.close()
  try:
   code,body,headers=request('/aeris');self.assertEqual(code,200);self.assertIn(b'data-headset-window="true"',body);self.assertIn(b'/headset-window.js',body);self.assertNotIn(b'<script src="/mobile-app.js"',body);self.assertNotIn('Set-Cookie',headers)
   for path in ['/api/session','/api/settings','/api/natural-voice/speak','/api/history']:self.assertEqual(request(path)[0],403)
   for path in ['/backend/server.py','/.env','/../README.md','/aeris-sw.js']:self.assertEqual(request(path)[0],404)
   self.assertEqual(request('/api/chat','POST')[0],403);self.assertEqual(request('/aeris-model.js')[0],200)
  finally:server.shutdown();server.server_close();thread.join(3)
 def test_start_reports_window_mode_and_stop_closes_listener(self):
  real=ThreadingHTTPServer
  with patch('backend.quest_window.private_ip',return_value='127.0.0.1'),patch('backend.quest_window.ThreadingHTTPServer',side_effect=lambda address,handler:real((address[0],0),handler)):
   link=QuestWindow()
   try:
    data=link.start();self.assertEqual(data['mode'],'browser-window');self.assertIn('keine KI',data['message']);self.assertIsNotNone(link.server)
   finally:link.stop()
   self.assertIsNone(link.server)
