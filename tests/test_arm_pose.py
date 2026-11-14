import base64,http.client,json,tempfile,threading,unittest
from unittest.mock import patch
from backend.server import Application,JarvisServer
from backend.arm_pose import detect
class ArmPoseTests(unittest.TestCase):
 def test_unsupported_platform_never_returns_fake_joints(self):
  with patch('backend.arm_pose.platform.system',return_value='Linux'),self.assertRaisesRegex(ValueError,'Mac'):detect(b'\xff\xd8\xfftest')
 def test_frames_require_session_and_are_not_saved_to_history(self):
  with tempfile.TemporaryDirectory() as folder:
   app=Application(folder);server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
   def send(data,token=True):
    c=http.client.HTTPConnection(*server.server_address,timeout=5)
    try:
     c.request('POST','/api/aeris/pose',json.dumps(data),{'Content-Type':'application/json','X-Jarvis-Token':app.token if token else ''});r=c.getresponse();return r.status,json.loads(r.read())
    finally:c.close()
   try:
    payload={'image':base64.b64encode(b'\xff\xd8\xfftest').decode()}
    with patch('backend.arm_pose.detect',return_value={'arms':{},'message':'Kein Körper erkannt.'}) as model:
     self.assertEqual(send(payload,False)[0],401);model.assert_not_called();self.assertEqual(send(payload)[0],200);model.assert_called_once();self.assertEqual(app.store.history(),[])
     app.pose_lock.acquire()
     try:self.assertEqual(send(payload)[0],409)
     finally:app.pose_lock.release()
     self.assertEqual(send({'image':'invalid!!'})[0],400)
   finally:app.office.stop();server.shutdown();server.server_close();thread.join(3)
