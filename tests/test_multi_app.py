import tempfile,unittest
from unittest.mock import Mock
from backend.server import Application
class MultiAppTests(unittest.TestCase):
 def setUp(self):self.temp=tempfile.TemporaryDirectory();self.app=Application(self.temp.name);self.app.selected_client=Mock(side_effect=AssertionError('Deterministic app opening must not call a model'))
 def tearDown(self):self.app.desktop.stop();self.app.office.stop();self.app.workshop.stop();self.temp.cleanup()
 def test_concrete_apps_are_reviewable_and_not_started_by_preparing(self):
  data=self.app.desktop.prepare({'goal':'Öffne Safari und Notizen'})
  self.assertEqual(data['plan']['state'],'review');self.assertTrue(data['plan']['explicit_multi']);self.assertEqual(data['plan']['completed'],0);self.assertEqual(data['plan']['steps'],[{'type':'open','app':'Safari'},{'type':'open','app':'Notizen'}]);self.app.selected_client.assert_not_called()
 def test_comma_list_does_not_need_json_planning(self):
  plan=self.app.desktop.prepare({'goal':'Öffne Safari, Notizen und Spotify'})['plan'];self.assertEqual(len(plan['steps']),3);self.assertTrue(all(s['type']=='open' for s in plan['steps']))
 def test_invalid_name_and_excess_apps_cannot_start_partial_plan(self):
  for text in ['Öffne Safari und NichtInstallierteTestApp','Öffne Safari und Terminal','Öffne Safari, Notizen, Spotify, Kalender und Rechner']:
   with self.subTest(text=text),self.assertRaises(ValueError):self.app.desktop.prepare({'goal':text})
  self.assertIsNone(self.app.desktop.plan);self.app.selected_client.assert_not_called()
