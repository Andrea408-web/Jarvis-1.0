import copy,json,unittest
from tests.test_workshop_free import FreeWorkshopTests,RAW
from backend.workshop import DEFAULT,design
from backend.workshop_feedback import wants_new_design,geometry_signature
from backend.workshop_free import assembly

class FeedbackTests(unittest.TestCase):
 setUp=FreeWorkshopTests.setUp
 def test_intent_distinguishes_redesign_from_specific_edit(self):
  for text in ['Das gefällt mir nicht','Mach einen neuen Entwurf','Ganz anders bitte','Das sieht nicht gut aus']:
   self.assertTrue(wants_new_design(text),text)
  for text in ['Kein neuer Entwurf, nur kleiner','Das gefällt mir nicht, mach es kleiner','Behalte den Entwurf']:
   self.assertFalse(wants_new_design(text),text)
 def test_signature_ignores_renaming_and_scaling_but_detects_layout(self):
  a=assembly(RAW)['parts'];b=copy.deepcopy(a)
  for p in b:
   p['name']='Anderer Name';p['size']=[n*2 for n in p['size']];p['position']=[n*2 for n in p['position']]
  self.assertEqual(geometry_signature(a),geometry_signature(b[::-1]));b[0]['position'][0]+=80;self.assertNotEqual(geometry_signature(a),geometry_signature(b))
 def test_feedback_retries_repeated_geometry_and_preserves_original(self):
  old=design({'spec':DEFAULT,'free_design':True,'request':'Ein Beistelltisch aus schwarzem Holz'},self.app);before=copy.deepcopy(old)
  fresh=copy.deepcopy(RAW);fresh['parts'][1]['position'][0]=70;fresh['explanation']='Der versetzte Fuß schafft seitlich mehr Beinfreiheit.'
  self.model.reset_mock();self.model.side_effect=[json.dumps(RAW),json.dumps(fresh)]
  new=design({'spec':old['spec'],'request':'Das gefällt mir nicht','previous':old},self.app)
  self.assertEqual(self.model.call_count,2);self.assertEqual(new['revision_kind'],'new');self.assertEqual(new['brief'],old['brief']);self.assertEqual(new['explanation'],fresh['explanation']);self.assertEqual(old,before);self.assertIn('Korrektur',self.model.call_args.args[1][0]['content']);self.assertFalse(self.app.chat_lock.locked())
 def test_two_repetitions_fail_without_replacing_old(self):
  old=design({'spec':DEFAULT,'free_design':True,'request':'Tisch'},self.app);before=copy.deepcopy(old);self.model.reset_mock()
  with self.assertRaisesRegex(ValueError,'unverändert'):design({'spec':old['spec'],'request':'Neuer Entwurf','previous':old},self.app)
  self.assertEqual(self.model.call_count,2);self.assertEqual(old,before);self.assertFalse(self.app.chat_lock.locked())
 def test_led_request_requires_actual_parts(self):
  lit=copy.deepcopy(RAW);lit['parts'].append({'name':'LED-Ring','shape':'torus','size':[80,80,5],'position':[0,160,0],'material':'light'})
  self.model.side_effect=[json.dumps(RAW),json.dumps(lit)]
  data=design({'spec':DEFAULT,'free_design':True,'request':'Tisch mit LED-Ring'},self.app);self.assertEqual(data['led_count'],1);self.assertEqual(self.model.call_count,2)
  self.model.side_effect=None;self.model.return_value=json.dumps(RAW)
  with self.assertRaisesRegex(ValueError,'LED'):design({'spec':DEFAULT,'free_design':True,'request':'Lampe mit LEDs'},self.app)
 def test_negated_new_and_specific_feedback_are_direct_edits(self):
  old=design({'spec':DEFAULT,'free_design':True,'request':'Tisch'},self.app);self.model.reset_mock()
  for text in ['Kein neuer Entwurf, nur kleiner','Das gefällt mir nicht, mach es kleiner']:
   new=design({'spec':old['spec'],'request':text,'previous':old},self.app);self.assertLess(new['spec']['width'],old['spec']['width'])
  self.model.assert_not_called()

 def test_incomplete_output_is_retried_and_validated(self):
  for bad in ['{"title":"unvollständig"}', '```json\n{"parts":[] }\n```', 'kein JSON']:
   self.model.reset_mock();self.model.side_effect=[bad,json.dumps(RAW)]
   data=design({'spec':DEFAULT,'free_design':True,'request':'Beistelltisch'},self.app)
   self.assertEqual(data['title'],RAW['title']);self.assertEqual(self.model.call_count,2);self.assertFalse(self.app.chat_lock.locked())
 def test_truncation_is_retried_and_fences_are_accepted(self):
  self.model.side_effect=[ValueError('Das lokale Modell hat keine fertige Ausgabe geliefert.'),'```json\n'+json.dumps(RAW)+'\n```']
  data=design({'spec':DEFAULT,'free_design':True,'request':'Beistelltisch'},self.app)
  self.assertEqual(data['title'],RAW['title']);self.assertEqual(self.model.call_count,2)
