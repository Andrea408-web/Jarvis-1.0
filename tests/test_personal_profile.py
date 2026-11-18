"""User-entered personal memory, optimistic edits, deletion and local-only prompts."""
import http.client,json,tempfile,threading,unittest
from unittest.mock import Mock
from backend.storage import Store
from backend.personal_profile import EMPTY,PersonalProfile,validate,context
from backend.providers import ProviderError
from backend.server import Application,JarvisServer
from backend.video_call import answer
from backend.persona import instruction

class PersonalProfileTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.store=Store(self.tmp.name);self.memory=PersonalProfile(self.store)
 def profile(self,**fields):return dict(EMPTY,name='Alex',humor='dry',style='short',interests='Technik und Schach',**fields)
 def test_explicit_persistence_and_one_source_of_truth(self):
  initial=self.memory.read();self.assertFalse(initial['saved']);result=self.memory.save(self.profile(),initial['expected']);self.assertTrue(result['saved']);self.assertEqual(PersonalProfile(self.store).read(),result)
  with self.store._connect()as db:data=json.loads(db.execute('SELECT data FROM personal_profile').fetchone()[0])
  self.assertNotIn('name',data);self.assertNotIn('address',data);self.assertEqual(self.store.settings()['user_name'],'Alex')
  self.store.update_settings({'user_name':'Maxine'});self.assertEqual(self.memory.read()['profile']['name'],'Maxine')
 def test_stale_edits_and_external_setting_change_are_not_overwritten(self):
  initial=self.memory.read();self.memory.save(self.profile(),initial['expected'])
  with self.assertRaises(ProviderError):self.memory.save(self.profile(about='stale'),initial['expected'])
  fresh=self.memory.read();self.store.update_settings({'user_address':'Boss'})
  with self.assertRaises(ProviderError):self.memory.save(fresh['profile'],fresh['expected'])
  self.assertEqual(self.memory.read()['profile']['address'],'Boss')
 def test_delete_invalidates_old_edits_preserves_chats_and_other_records(self):
  self.store.append('user','Meine alte Nachricht');self.store.add_reminder('Milch','2099-01-01T10:00:00+00:00');saved=self.memory.save(self.profile(about='Nur im Profil'),self.memory.read()['expected']);deleted=self.memory.forget(saved['expected']);self.assertFalse(deleted['saved']);self.assertEqual(deleted['profile'],EMPTY);self.assertEqual(len(self.store.history()),1)
  with self.store._connect()as db:self.assertEqual(json.loads(db.execute('SELECT data FROM personal_profile').fetchone()[0]),{})
  with self.assertRaises(ProviderError):self.memory.save(saved['profile'],saved['expected'])
 def test_strict_validation(self):
  for change in [{'version':True},{'name':'Alex123'},{'address':''},{'about':'a'*1501},{'humor':[]},{'style':'random'},{'interests':'bad\x00value'}]:
   with self.subTest(change=change),self.assertRaises(ValueError):validate({**EMPTY,**change})
  with self.assertRaises(ValueError):validate({**EMPTY,'secret':'no'})
 def test_context_only_for_selected_local_providers(self):
  self.memory.save(self.profile(),self.memory.read()['expected']);self.assertEqual(context(self.store),'');self.store.update_settings({'ai_provider':'llamacpp'});self.assertIn('trockener Humor',instruction(self.store));self.assertIn('Alex',context(self.store));self.store.update_settings({'ai_provider':'openai'});self.assertEqual(context(self.store),'');self.assertNotIn('trockener Humor',instruction(self.store))

class ProfileApiTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.app=Application(self.tmp.name);self.addCleanup(self.app.office.stop);self.app.store.update_settings({'ai_provider':'llamacpp'});self.server=JarvisServer(('127.0.0.1',0),self.app);self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start();self.addCleanup(self.close)
 def close(self):self.server.shutdown();self.server.server_close();self.thread.join(3)
 def request(self,method,body=None,token=True,path='/api/personal-profile'):
  c=http.client.HTTPConnection(*self.server.server_address,timeout=5)
  try:
   c.request(method,path,json.dumps(body)if body is not None else None,{'Content-Type':'application/json',**({'X-Jarvis-Token':self.app.token}if token else {})});r=c.getresponse();return r.status,json.loads(r.read())
  finally:c.close()
 def test_authenticated_crud_and_real_delete_body(self):
  for method in ['GET','PUT','DELETE']:self.assertEqual(self.request(method,{},False)[0],401)
  status,initial=self.request('GET');self.assertEqual(status,200);status,saved=self.request('PUT',{'profile':{**EMPTY,'name':'Alex','humor':'dry'},'expected':initial['expected']});self.assertEqual(status,200);self.assertEqual(saved['profile']['name'],'Alex');self.assertEqual(self.request('PUT',{'profile':EMPTY,'expected':initial['expected']})[0],409);status,deleted=self.request('DELETE',{'expected':saved['expected']});self.assertEqual(status,200);self.assertFalse(deleted['saved']);self.assertEqual(self.request('DELETE',{})[0],400)
 def test_device_override_used_without_becoming_persisted_profile(self):
  transport=Mock(return_value={'done':True,'message':{'content':'Boss, lass uns überlegen.'}});self.app.llamacpp.transport=transport;profile={**EMPTY,'name':'Alex','address':'Boss','humor':'dry'}
  status,result=self.request('POST',{'text':'Eine Idee bitte','mode':'astra','profile':profile},path='/api/device-ai/chat');self.assertEqual(status,200,result);prompt=transport.call_args.args[1]['messages'][0]['content'];self.assertIn('ASTRA',prompt);self.assertIn('Anrede: Boss',prompt);self.assertIn('trockener Humor',prompt);self.assertFalse(self.app.personal_profile.read()['saved']);self.assertEqual(self.app.store.history(),[])
  self.assertEqual(self.request('POST',{'text':'Hi','profile':{'secret':1}},path='/api/device-ai/chat')[0],400)
