import tempfile
import unittest
from unittest.mock import Mock,patch
from backend.system_check import explain,requested
from backend.server import Application

class SystemCheckTests(unittest.TestCase):
 def test_pressure_gets_concrete_steps_without_actions(self):
  result=explain({'is_macos':True,'cpu_percent':95,'memory_used_bytes':15*1073741824,'memory_total_bytes':16*1073741824,'disk_free_bytes':5*1073741824,'disk_total_bytes':100*1073741824})
  self.assertIn('Aktivitätsanzeige',result['reply']);self.assertIn('Speicherdruck',result['reply']);self.assertIn('vor dem Löschen',result['reply']);self.assertEqual(result['proposals'],[])
 def test_missing_values_and_remote_host_are_honest(self):
  reply=explain({'system':'Linux','is_macos':False})['reply']
  self.assertIn('kein Mac',reply);self.assertIn('Noch keine Messung',reply);self.assertNotIn('0.0',reply)
 def test_natural_question_routes_without_language_model(self):
  with tempfile.TemporaryDirectory() as folder:
   app=Application(folder)
   try:
    app.selected_client=Mock(side_effect=AssertionError('Not a model task'))
    with patch('backend.server.snapshot',return_value={'system':'Darwin','is_macos':True,'cpu_percent':20}):
     result=app.chat('Warum ist mein Mac so langsam?')
    self.assertIn('20.0',result['reply']);self.assertEqual(result['proposals'],[])
   finally:app.office.stop();app.workshop.stop();app.desktop.stop()
  self.assertFalse(requested('Erkläre mir, wie eine CPU funktioniert'))
