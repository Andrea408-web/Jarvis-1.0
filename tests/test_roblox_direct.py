import json,tempfile,time,threading,unittest
from pathlib import Path
from types import SimpleNamespace
from backend.studio_bridge import StudioBridge
from backend.code_room import CodeRoom
from backend.roblox_plan import city,wants_studio,from_task
class DirectStudioTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);self.bridge=StudioBridge(self.root);self.addCleanup(self.bridge.stop)
  self.app=SimpleNamespace(store=SimpleNamespace(data_dir=self.root),chat_lock=threading.Lock(),studio_bridge=self.bridge,llamacpp=None,local_ai=None);self.room=CodeRoom(self.app)
 def connect(self,version=2):self.bridge.prepare('owner');key=self.bridge.sessions['owner']['key'];self.bridge.poll(key,version);return key
 def submit(self,access='ask',task='Baue ein Roblox-Spiel wie Miles Morales',target='auto'):
  key=self.room.submit({'task':task,'model':'','level':'medium','boost':False,'access':access,'references':[],'target':target},'owner')['id'];limit=time.monotonic()+2
  while time.monotonic()<limit:
   j=self.room.snapshot(key,'owner')
   if j['status'] not in {'queued','running'}:return j
   time.sleep(.01)
  self.fail('timeout')
 def test_direct_plan_is_reviewed_and_builds_no_script_files(self):
  key=self.connect();j=self.submit();self.assertEqual(j['destination'],'studio');self.assertEqual(j['status'],'awaiting');self.assertEqual(j['files'],[]);self.assertFalse(self.room.root.exists());self.assertIsNone(self.bridge.poll(key,2)['job']);self.room.action(j['id'],'owner','save');build=self.bridge.poll(key,2)['job'];self.assertEqual(build['scene']['kind'],'hero-city');self.assertGreater(len(build['scene']['parts']),30)
  self.bridge.result(key,{'id':build['id'],'status':'progress','count':5,'message':'5 Teile bestätigt'});self.assertEqual(self.room.snapshot(j['id'],'owner')['status'],'building')
  complete={'id':build['id'],'status':'done','count':len(build['scene']['parts']),'message':'Im Studio aufgebaut','gameplay_ready':True};self.bridge.result(key,complete);self.assertEqual(self.room.snapshot(j['id'],'owner')['status'],'built');self.assertFalse(self.room.root.exists())
  with self.assertRaises(ValueError):self.room.archive(j['id'],'owner')
 def test_old_plugin_or_missing_connection_cannot_fake_city_success(self):
  self.connect(1);j=self.submit('project');self.assertEqual(j['status'],'error');self.assertIn('v2',j['error']);self.assertIsNone(self.bridge.status('owner')['job']);self.bridge.disconnect('owner');j=self.submit('project');self.assertEqual(j['status'],'error');self.assertFalse(self.room.root.exists())
 def test_city_completion_requires_gameplay_and_cancel_stops_plugin(self):
  key=self.connect();j=self.submit('project');build=self.bridge.poll(key,2)['job'];payload={'id':build['id'],'status':'done','count':len(build['scene']['parts']),'message':'done'}
  with self.assertRaises(ValueError):self.bridge.result(key,payload)
  self.room.action(j['id'],'owner','cancel');self.assertTrue(self.bridge.result(key,{'id':build['id'],'status':'progress','count':1,'message':'late'})['cancelled']);self.assertEqual(self.room.snapshot(j['id'],'owner')['status'],'cancelled')
 def test_durable_plugin_reconnect_after_server_restart_without_new_download(self):
  key=self.connect();port=self.bridge.server.server_port;self.bridge.stop();restored=StudioBridge(self.root);self.addCleanup(restored.stop);state=restored.status('new-owner');self.assertTrue(state['prepared']);self.assertEqual(restored.server.server_port,port);self.assertEqual(restored.sessions['new-owner']['key'],key);restored.poll(key,2);self.assertTrue(restored.status('new-owner')['connected']);restored.disconnect('new-owner');self.assertFalse(restored.status('new-owner')['prepared']);restored.reconnect('new-owner');restored.poll(key,2);self.assertTrue(restored.status('new-owner')['connected']);self.assertEqual((self.root/'studio-link.json').stat().st_mode&0o777,0o600)
 def test_corrupt_optional_configuration_does_not_stop_jarvis(self):
  (self.root/'studio-link.json').write_text('invalid');b=StudioBridge(self.root);self.addCleanup(b.stop);self.assertIsNotNone(b.status('owner')['diagnostic'])
 def test_geometry_is_bounded_and_websites_do_not_accidentally_build(self):
  self.assertTrue(wants_studio('Roblox Spiel bauen'));self.assertFalse(wants_studio('Website für mein Roblox Spiel'));self.assertFalse(wants_studio('Roblox Skript','files'))
  for n in [8,16,24]:
   plan=city({'name':'Eigene Stadt','buildings':n});self.assertLessEqual(len(plan['parts']),256);self.assertEqual(sum(p['kind']=='checkpoint'for p in plan['parts']),8);self.assertEqual(sum(p['kind']=='building'for p in plan['parts']),n)
   for p in plan['parts']:self.assertTrue(all(-3000<=v<=3000 for v in p['position']));self.assertTrue(all(0<v<=500 for v in p['size']))
  with self.assertRaises(ValueError):from_task('Baue ein Roblox Rennspiel')
