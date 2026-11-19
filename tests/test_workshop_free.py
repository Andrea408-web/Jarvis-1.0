import copy,json,tempfile,unittest
from unittest.mock import Mock
from backend.workshop import DEFAULT,design
from backend.workshop_free import assembly,bounds
from backend.server import Application
RAW={'title':'Runder Beistelltisch','parts':[{'name':'Runde Tischplatte','shape':'cylinder','size':[280,12,280],'position':[0,180,0],'material':'wood'},{'name':'Rundfuß','shape':'cylinder','size':[60,170,60],'position':[0,85,0],'material':'metal'},{'name':'Sockel','shape':'cylinder','size':[180,10,180],'position':[0,5,0],'material':'wood'}],'steps':['Zuschnitte und Verbindungen mit dem Fachhandel klären.','Zuerst trocken aufstellen und die Stabilität prüfen.'],'features':['Runde Ablagefläche als ungeprüfter Vorentwurf']}
class FreeWorkshopTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.app=Application(self.tmp.name);self.addCleanup(self.app.office.stop);self.app.store.update_settings({'ai_provider':'llamacpp'});self.model=Mock(return_value=json.dumps(RAW));self.app.code_room._generate=self.model
 def test_unknown_goal_calls_real_local_generation_path_and_returns_round_parts(self):
  data=design({'spec':DEFAULT,'request':'Baue mir einen Beistelltisch aus schwarzem Holz'},self.app);self.model.assert_called_once();self.assertEqual(data['spec']['template'],'custom');self.assertEqual(data['spec']['finish'],'black');self.assertTrue(all(p['shape']=='cylinder'for p in data['parts']));self.assertIn('schwarz',' '.join(data['steps']));self.assertTrue(all('schwarz'in p['material']for p in data['supplies']));self.assertEqual(data['spec']['height'],186);self.assertFalse(self.app.chat_lock.locked())
 def test_malformed_or_executable_geometry_is_not_replaced_by_a_box(self):
  self.model.return_value='Anfrage erfüllt'
  with self.assertRaisesRegex(ValueError,'keine gültigen'):design({'spec':DEFAULT,'request':'Baue einen Beistelltisch'},self.app)
  self.assertFalse(self.app.chat_lock.locked())
  bad=copy.deepcopy(RAW);bad['parts'][0]['script']='rm anything'
  with self.assertRaises(ValueError):assembly(bad)
  for shape in ['javascript','<script>','mesh-url']:
   bad=copy.deepcopy(RAW);bad['parts'][0]['shape']=shape
   with self.assertRaises(ValueError):assembly(bad)
 def test_edit_preserves_custom_geometry_without_a_model_call(self):
  data=design({'spec':DEFAULT,'request':'Baue einen Beistelltisch'},self.app);self.model.reset_mock();updated=design({'spec':data['spec'],'request':'kleiner, schwarzes Holz','previous':data},self.app);self.model.assert_not_called();self.assertEqual(updated['spec']['template'],'custom');self.assertEqual(updated['parts'][0]['shape'],'cylinder');self.assertIn('schwarz',' '.join(updated['steps']));self.assertAlmostEqual(updated['spec']['width'],238)
 def test_no_cloud_fallback_and_busy_lock_is_preserved(self):
  self.app.store.update_settings({'ai_provider':'openai'})
  with self.assertRaises(ValueError):design({'spec':DEFAULT,'request':'Baue einen Beistelltisch'},self.app)
  self.model.assert_not_called();self.app.store.update_settings({'ai_provider':'llamacpp'});self.app.chat_lock.acquire()
  try:
   with self.assertRaises(Exception):design({'spec':DEFAULT,'request':'Baue einen Beistelltisch'},self.app)
   self.assertTrue(self.app.chat_lock.locked())
  finally:self.app.chat_lock.release()
 def test_finish_and_shape_are_distinct_in_recipes(self):
  lamp=design({'spec':DEFAULT,'request':'Ich will eine runde Tischlampe aus schwarzem Holz','automatic':True});panel=design({'spec':DEFAULT,'request':'Ich will ein Leuchtpaneel aus Holz','automatic':True});self.assertNotEqual([p['shape']for p in lamp['parts']],[p['shape']for p in panel['parts']]);self.assertEqual(lamp['spec']['finish'],'black');self.assertIn('schwarz',' '.join(lamp['steps']))
