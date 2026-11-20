import copy,unittest
from backend.workshop_schema import design_schema
from tests.test_workshop_contours import RAW
try:
 from jsonschema import Draft202012Validator,ValidationError
except ImportError:
 Draft202012Validator=None

@unittest.skipUnless(Draft202012Validator,'jsonschema is optional verification tooling, not an app dependency')
class WorkshopSchemaTests(unittest.TestCase):
 def setUp(self):
  self.schema=design_schema();Draft202012Validator.check_schema(self.schema);self.validator=Draft202012Validator(self.schema)
 def test_contours_holes_lathe_and_questions_are_valid(self):
  self.validator.validate(RAW);self.validator.validate({'questions':['Welche Funktion soll dein Objekt haben?']})
 def test_missing_geometry_extra_code_and_unbounded_arrays_are_rejected(self):
  for mutate in [lambda r:r.pop('parts'),lambda r:r['parts'][0].pop('outline'),lambda r:r['parts'][0].update(script='execute this'),lambda r:r.update(parts=r['parts']*5),lambda r:r['parts'][0].update(material='script'),lambda r:r['parts'][0].update(size=[0,100,100]),lambda r:r['parts'][1].update(profile=[[-1,0],[.5,.5],[0,.5]])]:
   data=copy.deepcopy(RAW);mutate(data)
   with self.assertRaises(ValidationError):self.validator.validate(data)
 def test_retry_contract_is_smaller_but_preserves_custom_contours(self):
  Draft202012Validator(design_schema(4)).validate(RAW)
  data=copy.deepcopy(RAW);data['parts']=data['parts']*3
  self.validator.validate(data)
  with self.assertRaises(ValidationError):Draft202012Validator(design_schema(4)).validate(data)
