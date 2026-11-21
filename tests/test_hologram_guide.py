"""Readable physical instructions do not require a model or silently pick a phone."""
import math,unittest
from backend.hologram_project import guide,design
from tests import test_server as http_tests

class HologramGuideTests(unittest.TestCase):
 def test_full_guide_is_readable_without_model_or_inventory(self):
  data=guide({});self.assertEqual(data['budget'],40);self.assertEqual(len(data['sections']),8)
  text=' '.join(s['text']+' '+' '.join(s['steps'])for s in data['sections'])
  for detail in ['45°','Pappdreiecke','113,1','Handtracking','kein eigenständiges','Modellnamen','schwarzem Hintergrund']:
   self.assertIn(detail,text)
  self.assertNotIn('phone_reflector',str(data));self.assertIn('noch nicht',data['summary'])
  self.assertGreater(sum(len(s['steps'])for s in data['sections']),30)
 def test_budget_and_inventory_are_explicit_data_not_persisted_capabilities(self):
  data=guide({'budget':75.5,'inventory':'Alter Monitor und USB-Kamera'});self.assertEqual(data['budget'],75.5);self.assertEqual(data['inventory'],'Alter Monitor und USB-Kamera');self.assertIn('75.5 Euro',data['sections'][1]['text']);self.assertIn('Alter Monitor und USB-Kamera',' '.join(data['sections'][1]['steps']));self.assertNotIn('40-Euro',data['summary'])
 def test_unknown_or_invalid_input_is_rejected(self):
  for body in [None,[],{'budget':True},{'budget':0},{'budget':-1},{'budget':math.inf},{'budget':math.nan},{'budget':'40'},{'inventory':5},{'inventory':'x'*1501},{'execute':True}]:
   with self.subTest(body=body),self.assertRaises(ValueError):guide(body)
 def test_old_phone_reflector_remains_explicit_and_separate(self):
  self.assertEqual(design({})['project_kind'],'phone_reflector')

class HologramGuideHTTPTests(unittest.TestCase):
 setUp=http_tests.LiveServerTests.setUp
 stop_server=http_tests.LiveServerTests.stop_server
 def request(self,*args,**kwargs):
  status,data,_=http_tests.LiveServerTests.request(self,*args,**kwargs);return status,data
 def test_token_and_readable_no_model_path(self):
  self.app.code_room._generate=lambda *a,**k:(_ for _ in ()).throw(AssertionError('Guide must not need model inference'))
  code,_=self.request('POST','/api/workshop/hologram-guide',{},token=False);self.assertEqual(code,401)
  code,data=self.request('POST','/api/workshop/hologram-guide',{'budget':40,'inventory':'Kein Display'});self.assertEqual(code,200);self.assertEqual(data['budget'],40);self.assertEqual(len(data['sections']),8)
  code,_=self.request('POST','/api/workshop/hologram-guide',{'budget':False});self.assertEqual(code,400)
