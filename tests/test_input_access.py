import json,tempfile,unittest
from unittest.mock import Mock,patch
from backend.input_access import label_point,status
from backend.server import Application
from backend.desktop import MacInput

class InputAccessTests(unittest.TestCase):
 def test_labels_are_data_and_ambiguous_or_missing_controls_are_rejected(self):
  with patch('backend.input_access.subprocess.run',return_value=Mock(returncode=0,stdout=json.dumps([{'x':100,'y':200}]))) as run:
   self.assertEqual(label_point('com.apple.finder','Speichern "Test"'),{'x':100,'y':200});self.assertEqual(run.call_args.args[0][-2:],['com.apple.finder','Speichern "Test"'])
  for points in [[],[{'x':1,'y':2},{'x':3,'y':4}]]:
   with patch('backend.input_access.subprocess.run',return_value=Mock(returncode=0,stdout=json.dumps(points))),self.assertRaises(ValueError):label_point('com.apple.finder','Speichern')
 def test_named_click_has_concrete_steps_and_permission_failure_keeps_review(self):
  with tempfile.TemporaryDirectory() as folder:
   app=Application(folder)
   try:
    plan=app.desktop.prepare({'goal':'Klicke auf Speichern in Notizen'})['plan'];self.assertEqual(plan['steps'][-1],{'type':'click_label','label':'Speichern'})
    with patch('backend.desktop.platform.system',return_value='Darwin'),patch.object(MacInput,'ensure_input',side_effect=ValueError('Bedienungshilfen fehlen')):
     with self.assertRaisesRegex(ValueError,'Bedienungshilfen'):app.desktop.start(plan['id'])
    self.assertEqual(app.desktop.snapshot()['plan']['state'],'review');self.assertIsNone(app.desktop.thread)
   finally:app.office.stop()
 def test_no_native_support_is_reported_explicitly(self):
  with patch('backend.input_access.platform.system',return_value='Linux'):self.assertFalse(status()['supported'])
