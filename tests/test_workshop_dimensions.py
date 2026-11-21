"""Dimension transport normalization preserves authored geometry, never guesses sizes."""
import copy,json,tempfile,unittest
from unittest.mock import Mock
from backend.workshop import DEFAULT,design
from backend.workshop_free import assembly
from backend.workshop_requirements import normalize_dimensions
from backend.server import Application
from tests.test_workshop_free import RAW

class WorkshopDimensionTests(unittest.TestCase):
 def test_fractional_transport_preserves_shape_positions_and_original(self):
  raw=copy.deepcopy(RAW);raw['parts'][0]['size']=[280,'0.5','120.125'];raw['parts'][0]['position']=[0,-10,0]
  before=copy.deepcopy(raw);normalized,notes=normalize_dimensions(raw)
  self.assertEqual(raw,before);self.assertEqual(normalized['parts'][0]['size'],[280,.5,120.125]);self.assertEqual(normalized['parts'][0]['shape'],'cylinder');self.assertEqual(normalized['parts'][0]['position'],[0,-10,0]);self.assertFalse(notes)
  assembly(normalized)
 def test_numeric_sizes_and_zero_positions_remain_unchanged(self):
  raw=copy.deepcopy(RAW);raw['parts'][0]['size']=[280,.5,120.125];raw['parts'][0]['position']=[0,0,0]
  normalized,notes=normalize_dimensions(raw)
  self.assertEqual(normalized,raw);self.assertFalse(notes)
 def test_zero_negative_and_nonfinite_numeric_sizes_are_not_clamped(self):
  for number in [0,-1,float('nan'),float('inf'),True]:
   with self.subTest(number=number):
    raw=copy.deepcopy(RAW);raw['parts'][0]['size'][1]=number
    normalized,_=normalize_dimensions(raw)
    if number!=number:self.assertNotEqual(normalized['parts'][0]['size'][1],normalized['parts'][0]['size'][1])
    else:self.assertEqual(normalized['parts'][0]['size'][1],number)
    with self.assertRaises(ValueError):assembly(normalized)
 def test_invalid_dimension_strings_fail_without_coercion(self):
  for value in ['0','-0.5','NaN','Infinity','1 mm','1e2',' 1.5','1.5 ','0.0001','1200.001','1.2345','1,5','']:
   with self.subTest(value=value):
    raw=copy.deepcopy(RAW);raw['parts'][0]['size'][0]=value
    with self.assertRaises(ValueError):normalize_dimensions(raw)
    self.assertEqual(raw['parts'][0]['size'][0],value)
 def test_real_generation_path_accepts_half_mm_without_replacing_shape(self):
  with tempfile.TemporaryDirectory()as folder:
   app=Application(folder);app.store.update_settings({'ai_provider':'llamacpp'});raw=copy.deepcopy(RAW);raw['parts'][0]['size'][1]='0.5';app.code_room._generate=Mock(return_value=json.dumps(raw))
   try:
    result=design({'spec':DEFAULT,'request':'Baue mir einen Beistelltisch','free_design':True},app)
    self.assertEqual(app.code_room._generate.call_count,1);self.assertEqual(result['parts'][0]['shape'],'cylinder');self.assertEqual(result['parts'][0]['size'],[280,.5,280]);self.assertFalse(result['corrections']);self.assertFalse(app.chat_lock.locked())
   finally:app.workshop.stop();app.office.stop();app.desktop.stop()
 def test_missing_negative_dimension_retry_has_actual_value_in_feedback(self):
  with tempfile.TemporaryDirectory()as folder:
   app=Application(folder);app.store.update_settings({'ai_provider':'llamacpp'});raw=copy.deepcopy(RAW);raw['parts'][0]['size'][1]=0;app.code_room._generate=Mock(side_effect=[json.dumps(raw),json.dumps(RAW)])
   try:
    result=design({'spec':DEFAULT,'request':'Baue mir einen Beistelltisch','free_design':True},app)
    self.assertEqual(app.code_room._generate.call_count,2);self.assertEqual(result['parts'][0]['size'],RAW['parts'][0]['size']);self.assertFalse(app.chat_lock.locked())
    prompt=app.code_room._generate.call_args.args[1][0]['content'];self.assertIn('Bauteil 1, Höhe (size[1]) ist 0 mm',prompt);self.assertIn('Null ist nur bei Positionen zulässig',prompt)
   finally:app.workshop.stop();app.office.stop();app.desktop.stop()
