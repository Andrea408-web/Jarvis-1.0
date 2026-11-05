import tempfile,unittest
from unittest.mock import Mock
from backend.server import Application
from backend.local_ai import LocalClient
class CombinedBlenderTests(unittest.TestCase):
 def test_combined_lamborghini_request_produces_real_model_plan_in_both_word_orders(self):
  with tempfile.TemporaryDirectory() as folder:
   app=Application(folder)
   try:
    app.desktop.model_scene=Mock(side_effect=AssertionError('Known template does not need AI guesswork'))
    for goal in ['Öffne Blender und mach mir einen Lamborghini','Mach mir einen Lamborghini in Blender']:
     plan=app.desktop.prepare({'goal':goal})['plan'];self.assertEqual(plan['kind'],'model');self.assertTrue(plan['template']);self.assertEqual(len(plan['scene']['parts']),14);self.assertEqual(plan['state'],'review');self.assertNotIn('artifact',plan)
    result=app.chat('Öffne Blender und mach mir einen Lamborghini');self.assertEqual(result['view'],'desktop');self.assertIn('noch nicht ausgeführt',result['reply'])
   finally:app.office.stop()
 def test_unconfirmed_model_claim_is_not_reported_as_execution(self):
  with tempfile.TemporaryDirectory() as folder:
   app=Application(folder)
   try:
    client=LocalClient(app.store,lambda *a:{'done':True,'message':{'content':'Ich habe die App geöffnet und die Aufgabe erfüllt.'}})
    reply=client.chat('Öffne diese App')['reply'];self.assertIn('kein bestätigtes Werkzeugergebnis',reply)
   finally:app.office.stop()

 def test_explicit_pointer_and_typing_commands_are_executable_not_model_claims(self):
  with tempfile.TemporaryDirectory() as folder:
   app=Application(folder)
   try:
    plan=app.desktop.prepare({'goal':'Bewege die Maus nach links in Finder'})['plan'];self.assertEqual(plan['steps'][-1],{'type':'move','x':.25,'y':.5})
    plan=app.desktop.prepare({'goal':'Tippe Hallo Master in Notizen'})['plan'];self.assertEqual(plan['steps'][-1],{'type':'text','text':'Hallo Master'});self.assertEqual(plan['steps'][2],{'type':'key','key':'n','modifiers':['command']})
   finally:app.office.stop()
