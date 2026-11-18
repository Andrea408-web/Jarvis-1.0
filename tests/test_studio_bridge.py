import json
import urllib.request
import urllib.error
import unittest
import xml.etree.ElementTree as ET
from backend.studio_bridge import StudioBridge,scene
class StudioBridgeTests(unittest.TestCase):
 def setUp(self):self.bridge=StudioBridge();self.addCleanup(self.bridge.stop)
 def prepare(self):
  data=self.bridge.prepare('owner');xml=ET.fromstring(data['plugin']);source=xml.find('.//ProtectedString').text;self.assertIn('127.0.0.1',source);self.assertNotIn('__BRIDGE_KEY__',source);return self.bridge.sessions['owner']['key']
 def test_scene_has_bounded_real_playable_parts(self):
  plan=scene({'name':'Mein Spiel','platforms':10,'coins':True});self.assertEqual(len(plan['parts']),22);self.assertEqual(plan['parts'][0]['kind'],'spawn');self.assertEqual(plan['parts'][-1]['kind'],'goal')
  for p in plan['parts']:self.assertEqual(len(p['position']),3);self.assertTrue(all(v>0 for v in p['size']))
  for bad in [{'name':'x','platforms':200,'coins':True},{'name':'x','platforms':True,'coins':True},{'name':'x','platforms':3,'coins':True,'lua':'print(1)'}]:
   with self.assertRaises(ValueError):scene(bad)
 def test_pairing_delivery_progress_and_actual_completion_required(self):
  key=self.prepare();self.assertFalse(self.bridge.status('owner')['connected'])
  with self.assertRaises(ValueError):self.bridge.queue('owner',{'name':'x','platforms':3,'coins':False})
  self.bridge.poll(key);self.assertTrue(self.bridge.status('owner')['connected']);self.assertFalse(self.bridge.status('other')['connected']);self.bridge.queue('owner',{'name':'x','platforms':3,'coins':False});j=self.bridge.poll(key)['job'];self.assertEqual(j['status'],'building');self.assertIsNone(self.bridge.poll(key)['job'])
  with self.assertRaises(ValueError):self.bridge.result(key,{'id':j['id'],'status':'done','count':1,'message':'fake done'})
  self.bridge.result(key,{'id':j['id'],'status':'progress','count':2,'message':'2 Teile erstellt'});self.assertEqual(self.bridge.status('owner')['job']['status'],'building')
  self.bridge.result(key,{'id':j['id'],'status':'done','count':5,'message':'fertig'});self.assertEqual(self.bridge.status('owner')['job']['status'],'done');self.bridge.disconnect('owner')
  with self.assertRaises(ValueError):self.bridge.poll(key)
 def test_reprepare_revokes_old_key_and_no_generated_lua_execution(self):
  key=self.prepare();new=self.prepare();self.assertNotEqual(key,new)
  with self.assertRaises(ValueError):self.bridge.poll(key)
  self.assertNotIn('loadstring(',self.bridge.prepare('another')['plugin'])
 def test_loopback_http_requires_secret_rejects_web_origin(self):
  key=self.prepare();url='http://127.0.0.1:'+str(self.bridge.server.server_port)+'/poll'
  for headers in [{},{'X-Jarvis-Studio':key,'Origin':'https://attacker.invalid'}]:
   with self.assertRaises(urllib.error.HTTPError):urllib.request.urlopen(urllib.request.Request(url,headers=headers))
  with urllib.request.urlopen(urllib.request.Request(url,headers={'X-Jarvis-Studio':key}))as r:self.assertEqual(json.load(r),{'job':None})
