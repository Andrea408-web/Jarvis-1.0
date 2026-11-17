import struct,unittest
from backend.object_models import model_url,load_model,MAX_MODEL,NoRedirect
class ObjectModelTests(unittest.TestCase):
 def test_only_explicit_https_model_hosts_and_direct_paths(self):
  good='https://raw.githubusercontent.com/example/models/main/car.glb';self.assertEqual(model_url(good),good)
  self.assertEqual(model_url('https://github.com/example/models/blob/main/car.glb'),good)
  for url in ['http://raw.githubusercontent.com/a/b.glb','https://localhost/car.glb','https://127.0.0.1/car.glb','https://[::1]/car.glb','file:///tmp/car.glb','https://raw.githubusercontent.com.evil.test/car.glb','https://user:secret@raw.githubusercontent.com/a/car.glb','https://raw.githubusercontent.com:8000/a/car.glb','https://raw.githubusercontent.com/a/index.html','https://raw.githubusercontent.com/a/car.glb?token=secret','https://raw.githubusercontent.com/a/../car.glb']:
   with self.subTest(url=url),self.assertRaises(ValueError):model_url(url)
 def test_bounded_glb_and_no_request_for_invalid_url(self):
  calls=[];good=struct.pack('<III',0x46546c67,2,20)+b'12345678'
  self.assertEqual(load_model('https://threejs.org/examples/car.glb',lambda *args:(calls.append(args),good)[1]),good)
  self.assertEqual(calls[0][1],MAX_MODEL)
  for bad in [b'<html>not a model</html>',struct.pack('<III',0x46546c67,1,20)+b'12345678',good+b'x',b'x'*(MAX_MODEL+1)]:
   with self.assertRaises(ValueError):load_model('https://threejs.org/car.glb',lambda *a:bad)
  with self.assertRaises(ValueError):load_model('https://localhost/car.glb',lambda *a:self.fail('Invalid target reached transport'))
 def test_redirect_does_not_follow_to_private_or_other_host(self):
  with self.assertRaises(ValueError):NoRedirect().redirect_request(None,None,None,None,None,'https://127.0.0.1/private.glb')
