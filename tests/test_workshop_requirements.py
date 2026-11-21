import copy,json,unittest
from backend.workshop import DEFAULT,design
from backend.workshop_requirements import normalize_emitters,complex_goal,validate_concept,unpack_lighting
from backend.workshop_schema import design_schema
from tests import test_workshop_free as free_tests
from tests.workshop_complex_fixture import ARM
try:
 from jsonschema import Draft202012Validator,ValidationError
except ImportError:Draft202012Validator=None

class RequirementTests(unittest.TestCase):
 setUp=free_tests.FreeWorkshopTests.setUp
 def test_existing_named_led_keeps_geometry_and_is_classified_as_light(self):
  raw=copy.deepcopy(ARM);raw['parts'][0]['material']='plastic';before=copy.deepcopy(raw)
  fixed,notes=normalize_emitters(raw,True);self.assertEqual(fixed['parts'][0]['material'],'light');self.assertEqual(fixed['parts'][0]['position'],raw['parts'][0]['position']);self.assertEqual(fixed['parts'][0]['size'],raw['parts'][0]['size']);self.assertEqual(raw,before);self.assertEqual(len(notes),1)
 def test_brackets_diffusers_and_unrequested_lights_are_not_reclassified(self):
  for name in ['LED-Halter','LED-Gehäuse','LED-Diffusor','LED-Streifen-Kabelkanal','Sockel für LED-Ring']:
   raw=copy.deepcopy(ARM);raw['parts'][0].update(name=name,material='plastic');fixed,notes=normalize_emitters(raw,True);self.assertEqual(fixed,raw);self.assertFalse(notes)
  raw=copy.deepcopy(ARM);raw['parts'][0]['material']='plastic'
  for flag in [False,None]:self.assertEqual(normalize_emitters(raw,flag),(raw,[]))
 def test_reported_missing_light_failure_is_repaired_without_inventing_a_part(self):
  raw=copy.deepcopy(ARM);raw['parts'][0]['material']='plastic';self.model.return_value=json.dumps(raw)
  data=design({'spec':DEFAULT,'request':'Mini-Roboterarm mit Säulen und LED','free_design':True},self.app);self.model.assert_called_once();self.assertEqual(data['led_count'],1);self.assertEqual(len(data['parts']),len(raw['parts']));self.assertTrue(data['corrections']);self.assertEqual(data['concept'],ARM['concept']);self.assertIn('nicht ausgelegt',data['limits'])
 def test_complex_concept_is_required_and_survives_direct_edits(self):
  self.model.return_value=json.dumps(ARM);data=design({'spec':DEFAULT,'request':'Ein komplexer Mechanismus mit Motor und LED','free_design':True},self.app);self.assertIn('concept',data);self.model.reset_mock();updated=design({'spec':data['spec'],'request':'kleiner','previous':data},self.app);self.model.assert_not_called();self.assertEqual(updated['concept'],data['concept'])
  missing=copy.deepcopy(ARM);missing.pop('concept');self.model.return_value=json.dumps(missing)
  with self.assertRaisesRegex(ValueError,'Baugruppen'):design({'spec':DEFAULT,'request':'Roboterarm mit LED','free_design':True},self.app)
 def test_concept_metadata_is_bounded_not_executable(self):
  self.assertTrue(complex_goal('Mini-Roboterarm mit Säulen'));self.assertFalse(complex_goal('Eine kleine Ablage'))
  for change in [{'systems':[]},{'unresolved':['x']*7},{'workflow':['x'*301]},{'script':'run code'}]:
   with self.assertRaises(ValueError):validate_concept({**ARM['concept'],**change})
 @unittest.skipUnless(Draft202012Validator,'optional schema verification')
 def test_requested_light_cannot_be_omitted_or_replaced_by_other_material(self):
  schema=design_schema(10,lighting=True,complex_design=True);Draft202012Validator.check_schema(schema);v=Draft202012Validator(schema)
  packed=copy.deepcopy(ARM);packed['lighting']=packed['parts'].pop(0);v.validate(packed)
  self.assertEqual(unpack_lighting(packed,True),ARM)
  for mutate in [lambda r:r['lighting'].update(material='plastic'),lambda r:r.pop('lighting'),lambda r:r.pop('concept')]:
   raw=copy.deepcopy(packed);mutate(raw)
   with self.assertRaises(ValidationError):v.validate(raw)
  raw=copy.deepcopy(ARM);raw['parts'].pop(0);Draft202012Validator(design_schema(10,lighting=False,complex_design=True)).validate(raw)
  with self.assertRaises(ValidationError):Draft202012Validator(design_schema(10,lighting=False,complex_design=True)).validate(ARM)
 def test_separate_required_lighting_is_used_at_its_generated_position(self):
  raw=copy.deepcopy(ARM);raw['lighting']=raw['parts'].pop(0);self.model.return_value=json.dumps(raw)
  data=design({'spec':DEFAULT,'request':'Roboterarm mit Säulen und LED','free_design':True},self.app);self.assertEqual(data['led_count'],1);self.assertEqual(len(data['parts']),10);self.assertEqual(data['parts'][0]['name'],'LED-Statusmodul');self.assertFalse(data['corrections'])

 def test_existing_misclassified_led_remains_a_requirement_on_redesign(self):
  self.model.return_value=json.dumps(ARM);old=design({'spec':DEFAULT,'request':'Roboterarm mit LED','free_design':True},self.app);old['parts'][0]['material']='plastic';before=copy.deepcopy(old);self.model.reset_mock()
  newraw=copy.deepcopy(ARM);newraw['parts'][5]['size'][0]=36;self.model.return_value=json.dumps(newraw)
  data=design({'spec':old['spec'],'request':'Das gefällt mir nicht, neuer Entwurf','previous':old},self.app)
  contract=self.model.call_args.kwargs['structured']['anyOf'][0];self.assertIn('lighting',contract['required']);self.assertEqual(data['led_count'],1);self.assertEqual(old,before)
