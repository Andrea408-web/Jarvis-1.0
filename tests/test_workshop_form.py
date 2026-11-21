"""Explicit curved wishes cannot silently succeed as a beveled box."""
import copy,json,unittest
from backend.workshop import DEFAULT,design
from backend.workshop_free import assembly
from backend.workshop_requirements import form_request,form_error,unpack_form
from backend.workshop_schema import design_schema
from tests.test_workshop_free import FreeWorkshopTests,RAW as ROUND
from tests.test_workshop_contours import RAW as CURVED
try:
 from jsonschema import Draft202012Validator,ValidationError
except ImportError:Draft202012Validator=None

BOX={'title':'Ein Kasten','parts':[{'name':'Rundes Gehäuse','shape':'box','size':[240,180,100],'position':[0,90,0],'material':'plastic'}],'steps':['Maße prüfen.'],'features':['Formidee']}
class FormTests(unittest.TestCase):
 setUp=FreeWorkshopTests.setUp
 def test_intent_uses_original_round_wish_but_respects_new_square_goal(self):
  self.assertEqual(form_request('Ein rundes Tischgerät'),'round')
  self.assertEqual(form_request('Nicht wieder nur ein Viereck'),'custom')
  self.assertEqual(form_request('Neuer Entwurf',{'brief':'Ein rundes Tischgerät'}),'round')
  self.assertIsNone(form_request('Ich will eine rechteckige Kiste',{'brief':'Ein rundes Tischgerät'}))
  self.assertIsNone(form_request('Eine Kiste mit abgerundeten Kanten'))
 def test_round_wish_retries_box_and_returns_generated_round_shape(self):
  self.model.side_effect=[json.dumps(BOX),json.dumps(ROUND)]
  data=design({'spec':DEFAULT,'request':'Ein rundes Tischgerät','free_design':True},self.app)
  self.assertEqual(self.model.call_count,2);self.assertEqual(data['parts'][0]['shape'],'cylinder');self.assertIn('runde Form fehlt',self.model.call_args.args[1][0]['content']);self.assertFalse(self.app.chat_lock.locked())
 def test_second_box_is_error_and_previous_design_is_not_replaced(self):
  self.model.return_value=json.dumps(ROUND);old=design({'spec':DEFAULT,'request':'Ein runder Tisch','free_design':True},self.app);before=copy.deepcopy(old);self.model.reset_mock();self.model.return_value=json.dumps(BOX)
  with self.assertRaisesRegex(ValueError,'runde Form fehlt'):design({'spec':old['spec'],'request':'Neuer Entwurf','previous':old},self.app)
  self.assertEqual(self.model.call_count,2);self.assertEqual(old,before);self.assertFalse(self.app.chat_lock.locked())
 def test_tiny_ornament_does_not_hide_box_body_and_light_is_not_form(self):
  raw=copy.deepcopy(BOX);raw['parts'].append({'name':'Zierkugel','shape':'sphere','size':[10,10,10],'position':[0,180,0],'material':'plastic'});self.assertTrue(form_error(assembly(raw)['parts'],'round'))
  raw['parts'][1].update(size=[240,180,100],material='light');self.assertTrue(form_error(assembly(raw)['parts'],'round'))
 def test_authored_contour_is_used_without_stock_fallback(self):
  raw=copy.deepcopy(CURVED);raw['form']=raw['parts'].pop(0);self.model.return_value=json.dumps(raw)
  data=design({'spec':DEFAULT,'request':'Eine eigene geschwungene Form mit Kabelöffnung','free_design':True},self.app)
  self.assertEqual(self.model.call_count,1);self.assertEqual(data['parts'][0]['shape'],'extrude');self.assertGreater(len(data['parts'][0]['outline']),20);self.assertEqual(len(data['parts']),2)
  self.assertEqual(unpack_form(raw,'custom')['parts'][0],CURVED['parts'][0])
 def test_smoothing_four_corners_does_not_satisfy_custom_form(self):
  raw=copy.deepcopy(BOX);raw['parts'][0].update(shape='extrude',outline=[[-.5,-.5],[.5,-.5],[.5,.5],[-.5,.5]],smooth=True)
  checked=assembly(raw);self.assertGreater(len(checked['parts'][0]['outline']),5)
  self.assertTrue(form_error(checked['parts'],'custom',raw['parts']))
 def test_requested_camera_must_be_shown_as_actual_part(self):
  from backend.workshop_requirements import camera_error,camera_request
  raw=copy.deepcopy(ROUND);self.assertTrue(camera_request('Mit Handtracking'));self.assertFalse(camera_request('Ohne Kamera'));self.assertTrue(camera_error(raw['parts'],True))
  camera={'name':'Kameramodul','shape':'box','size':[20,15,10],'position':[0,180,0],'material':'plastic'};raw['parts'].append(camera);self.model.side_effect=[json.dumps(ROUND),json.dumps(raw)]
  data=design({'spec':DEFAULT,'request':'Ein rundes Gerät mit Handgesten','free_design':True},self.app);self.assertEqual(self.model.call_count,2);self.assertTrue(any(p['name']=='Kameramodul'for p in data['parts']))
 @unittest.skipUnless(Draft202012Validator,'optional schema check')
 def test_runtime_schema_requires_nonbox_form_and_reserves_capacity(self):
  for kind,source in [('round',ROUND),('custom',CURVED)]:
   raw=copy.deepcopy(source);raw['form']=raw['parts'].pop(0);v=Draft202012Validator(design_schema(6,form=kind));v.validate(raw)
   for mutate in [lambda d:d.pop('form'),lambda d:d['form'].update(shape='box'),lambda d:d['form'].update(material='light')]:
    bad=copy.deepcopy(raw);mutate(bad)
    with self.assertRaises(ValidationError):v.validate(bad)
