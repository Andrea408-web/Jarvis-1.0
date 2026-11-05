"""The user's fixed Thorsten preference survives legacy clients and restarts."""
import tempfile,threading,time,unittest
from unittest.mock import Mock,patch
from backend.server import Application
from backend.storage import Store

class ThorstenPreferenceTests(unittest.TestCase):
 def test_defaults_legacy_value_and_legacy_updates_all_use_thorsten(self):
  with tempfile.TemporaryDirectory() as folder:
   store=Store(folder);self.assertEqual(store.settings()['voice_engine'],'natural')
   with store._connect() as db:db.execute("INSERT OR REPLACE INTO settings(name,value) VALUES('voice_engine','\"bundled\"')")
   self.assertEqual(Store(folder).settings()['voice_engine'],'natural')
   self.assertEqual(store.update_settings({'voice_engine':'bundled'})['voice_engine'],'natural')
   self.assertEqual(Store(folder).settings()['voice_engine'],'natural')
 def test_setup_is_single_flight_and_activates_only_a_verified_voice(self):
  with tempfile.TemporaryDirectory() as folder:
   app=Application(folder);entered=threading.Event();release=threading.Event();voice=Mock();voice.status.return_value={'installed':True}
   def install(data_dir):self.assertEqual(str(data_dir),folder);entered.set();release.wait(2);return voice
   try:
    with patch('platform.system',return_value='Darwin'),patch('backend.natural_voice.install',side_effect=install) as setup:
     self.assertEqual(app.install_thorsten()['state'],'running');self.assertTrue(entered.wait(1));self.assertEqual(app.install_thorsten()['state'],'running');release.set()
     deadline=time.monotonic()+2
     while app.voice_install_state['state']=='running' and time.monotonic()<deadline:time.sleep(.01)
     self.assertEqual(app.voice_install_state['state'],'done');setup.assert_called_once();self.assertIs(app.natural_voice,voice);self.assertTrue(app.store.settings()['voice_enabled'])
   finally:release.set();app.office.stop()
