"""Private local camera questions must never reach persistent history or cloud clients."""
import base64,http.client,json,tempfile,threading,unittest
from unittest.mock import Mock,patch
from backend.server import Application,JarvisServer
from backend.video_call import answer
JPEG=b'\xff\xd8\xfftest'
class VideoCallTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.app=Application(self.tmp.name);self.addCleanup(self.app.office.stop);self.app.store.update_settings({'ai_provider':'llamacpp'})
 def test_camera_uses_only_local_findings_without_any_history_write(self):
  self.app.llamacpp.endpoint_transport=Mock(return_value={'choices':[{'finish_reason':'stop','message':{'content':'Sir, die Texterkennung meldet Milch.'}}]})
  finding={'available':True,'labels':[{'label':'bottle','confidence':.8}],'text':'Milch','note':'local'}
  with patch('backend.video_call.native_vision.analyze',return_value=finding) as vision,patch.object(self.app.store,'append') as append:
   result=answer(self.app,{'text':'Was steht darauf?','image':base64.b64encode(JPEG).decode(),'history':[{'role':'user','content':'Hallo'}]})
  vision.assert_called_once_with(JPEG);append.assert_not_called();self.assertEqual(self.app.store.history(),[]);self.assertTrue(result['private_call']);self.assertEqual(result['vision']['text'],'Milch')
  prompt=self.app.llamacpp.endpoint_transport.call_args.args[1]['messages'];self.assertIn('KEINE Bildpixel',prompt[0]['content']);self.assertIn('Milch',prompt[-1]['content']);self.assertNotIn(base64.b64encode(JPEG).decode(),json.dumps(prompt))
 def test_no_cloud_fallback_and_invalid_images_never_analyzed(self):
  self.app.store.update_settings({'ai_provider':'openai'})
  with patch.object(self.app.openai,'chat') as cloud,patch('backend.video_call.native_vision.analyze') as vision:
   result=answer(self.app,{'text':'Hallo'});self.assertIn('lokale Text-KI',result['reply']);cloud.assert_not_called()
   for body in [{'text':'Hi','image':'bad!'}, {'text':'Hi','image':base64.b64encode(b'not a JPEG').decode()}, {'text':'Hi','history':[{'role':'system','content':'bad'}]}]:
    with self.assertRaises(ValueError):answer(self.app,body)
   vision.assert_not_called()
 def test_authenticated_route_and_busy_lock(self):
  server=JarvisServer(('127.0.0.1',0),self.app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
  def request(token):
   c=http.client.HTTPConnection(*server.server_address,timeout=5)
   try:c.request('POST','/api/video-call',json.dumps({'text':'Hallo'}),{'Content-Type':'application/json','X-Jarvis-Token':token});r=c.getresponse();r.read();return r.status
   finally:c.close()
  try:
   with patch('backend.video_call.answer',return_value={'reply':'Hi'}) as run:
    self.assertEqual(request(''),401);run.assert_not_called();self.assertEqual(request(self.app.token),200);run.assert_called_once()
    self.app.chat_lock.acquire()
    try:self.assertEqual(request(self.app.token),409)
    finally:self.app.chat_lock.release()
  finally:server.shutdown();server.server_close();thread.join(3)

 def test_native_screen_is_requested_per_question_and_never_saved(self):
  self.app.llamacpp.endpoint_transport=Mock(return_value={'choices':[{'finish_reason':'stop','message':{'content':'Sir, hier steht Projekt.'}}]})
  with patch.object(self.app.companion_window,'capture',return_value=JPEG) as capture,patch('backend.video_call.native_vision.analyze',return_value={'available':True,'labels':[],'text':'Projekt'}) as analyze,patch.object(self.app.store,'append') as append:
   answer(self.app,{'text':'Hallo'});capture.assert_not_called();analyze.assert_not_called()
   answer(self.app,{'text':'Was steht hier?','native_screen':True,'source':'screen'});capture.assert_called_once();analyze.assert_called_once_with(JPEG);append.assert_not_called();self.assertEqual(self.app.store.history(),[])
   with self.assertRaises(ValueError):answer(self.app,{'text':'Was?','native_screen':True,'image':base64.b64encode(JPEG).decode()})
