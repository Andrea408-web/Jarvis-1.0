import copy,json,math,tempfile,unittest
from unittest.mock import Mock
from backend.workshop_contours import contour,profile
from backend.workshop_free import assembly
from backend.workshop import DEFAULT,design
from backend.server import Application
OUTLINE=[[-.45,-.5],[.45,-.5],[.49,-.43],[.46,-.36],[.2,-.30],[.13,-.18],[.10,.05],[.12,.28],[.30,.33],[.42,.40],[.39,.48],[.26,.5],[-.26,.5],[-.39,.48],[-.42,.40],[-.30,.33],[-.12,.28],[-.10,.05],[-.13,-.18],[-.2,-.30],[-.46,-.36],[-.49,-.43]]
HOLE=[[.12*math.cos(i*math.pi/12),.405+.035*math.sin(i*math.pi/12)]for i in range(24)]
RAW={'title':'Geschwungener Ständer mit Kabelöffnung','parts':[{'name':'Eigene Seitenkontur mit Kabelöffnung','shape':'extrude','smooth':True,'outline':OUTLINE,'holes':[HOLE],'size':[180,230,30],'position':[0,130,0],'material':'wood'},{'name':'Sockel nach eigenem Drehprofil','shape':'lathe','profile':[[0,-.5],[.42,-.5],[.5,-.2],[.5,.15],[.44,.5],[0,.5]],'size':[220,15,140],'position':[0,7.5,0],'material':'wood'}],'steps':['Kontur und Ausschnitt anhand eines Pappmodells prüfen.','Die Seitenkontur mit Ausschnitt und den Sockel als fachgerecht gefräste/gefertigte Teile anfragen.','Verbindung zwischen Sockel und Seitenkontur passend auslegen und vor einer Nutzung prüfen.'],'features':['Eigene geschwungene Kontur','Durchgehender Kabelausschnitt']}
class ContourTests(unittest.TestCase):
 def test_custom_outline_keeps_real_hole(self):
  p=assembly(RAW)['parts'][0];self.assertEqual(p['shape'],'extrude');self.assertEqual(len(p['holes'][0]),24);self.assertAlmostEqual(max(v[0]for v in p['outline']),.5)
 def test_crossing_contours_or_outside_holes_fail(self):
  for change in [{'outline':[[-.5,-.5],[.5,.5],[-.5,.5],[.5,-.5]]},{'holes':[[[.4,-.1],[.49,-.1],[.49,.1],[.4,.1]]]},{'holes':[HOLE,HOLE]}]:
   with self.subTest(change=change),self.assertRaises(ValueError):contour({**RAW['parts'][0],**change})
 def test_lathe_profile_is_bounded(self):
  self.assertEqual(len(profile(RAW['parts'][1]['profile'])),6)
  with self.assertRaises(ValueError):profile([[.1,.5],[.2,0],[.1,-.5]])
 def test_free_mode_is_used_even_for_recognized_lamp_words(self):
  with tempfile.TemporaryDirectory()as d:
   app=Application(d);app.store.update_settings({'ai_provider':'llamacpp'});app.code_room._generate=Mock(return_value=json.dumps(RAW))
   try:
    data=design({'spec':DEFAULT,'request':'Eine Leuchte nach eigener Kontur aus schwarzem Holz','free_design':True},app);app.code_room._generate.assert_called_once();self.assertEqual(data['spec']['template'],'custom');self.assertEqual(data['parts'][0]['shape'],'extrude');self.assertIn('schwarz',' '.join(data['steps']))
   finally:app.office.stop()
 def test_questions_do_not_create_an_arbitrary_object(self):
  with tempfile.TemporaryDirectory()as d:
   app=Application(d);app.store.update_settings({'ai_provider':'llamacpp'});app.code_room._generate=Mock(return_value=json.dumps({'questions':['Welche Funktion soll dein Objekt haben?']}))
   try:
    data=design({'spec':DEFAULT,'request':'Baue etwas','free_design':True},app);self.assertTrue(data['needs_details']);self.assertNotIn('parts',data);self.assertFalse(app.chat_lock.locked())
   finally:app.office.stop()
