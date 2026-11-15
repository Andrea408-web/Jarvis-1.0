import json,tempfile,unittest
from pathlib import Path
from unittest.mock import Mock,patch
from backend.companion_window import CompanionWindow
from backend.screen_view import ScreenView
class CompanionTests(unittest.TestCase):
 def test_floating_window_config_has_no_image_or_token_and_mode_changes_reuse_process(self):
  with tempfile.TemporaryDirectory() as folder:
   panel=CompanionWindow(folder);process=Mock();process.poll.return_value=None
   with patch('backend.companion_window.platform.system',return_value='Darwin'),patch('backend.companion_window.subprocess.Popen',side_effect=lambda *args,**kwargs:((Path(folder)/'jarvis-companion.ready').write_text('visible') and process)) as spawn:
    panel.open('http://localhost:8765/companion?native=1','helper');panel.change('island');self.assertEqual(spawn.call_count,1);data=json.loads((Path(folder)/'jarvis-companion.json').read_text());self.assertEqual(data['mode'],'island');self.assertEqual(set(data),{'url','mode','sequence','wandering'});self.assertNotIn('#',data['url']);self.assertEqual((Path(folder)/'jarvis-companion.json').stat().st_mode&0o777,0o600);panel.close();process.terminate.assert_called_once();self.assertFalse(panel.screen.enabled)
 def test_invalid_modes_and_closed_window_never_capture(self):
  with tempfile.TemporaryDirectory() as folder:
   panel=CompanionWindow(folder)
   with self.assertRaises(ValueError):panel.open('http://localhost','invalid')
   with self.assertRaises(ValueError):panel.change('island')
   panel.screen.enabled=True
   with patch.object(panel.screen,'capture') as image,self.assertRaises(ValueError):panel.capture()
   image.assert_not_called();self.assertFalse(panel.screen.enabled)
 def test_screen_requires_opt_in_and_revoked_permission_stops_before_capture(self):
  screen=ScreenView()
  with patch.object(screen,'_graphics') as load,self.assertRaises(ValueError):screen.capture()
  load.assert_not_called()
  graphics=Mock();graphics.CGPreflightScreenCaptureAccess.return_value=False
  with patch.object(screen,'_graphics',return_value=graphics):self.assertFalse(screen.start()['active']);graphics.CGRequestScreenCaptureAccess.assert_called_once()
  screen.enabled=True
  with patch.object(screen,'_graphics',return_value=graphics),self.assertRaisesRegex(ValueError,'entzogen'):screen.capture()
  self.assertFalse(screen.enabled);graphics.CGDisplayCreateImage.assert_not_called()

 def test_late_os_permission_response_cannot_reenable_after_stop(self):
  screen=ScreenView();graphics=Mock();graphics.CGPreflightScreenCaptureAccess.side_effect=[False,True];graphics.CGRequestScreenCaptureAccess.side_effect=lambda:screen.stop()
  with patch.object(screen,'_graphics',return_value=graphics):self.assertFalse(screen.start()['active'])
  self.assertFalse(screen.enabled)

 def test_invalid_motion_state_never_changes_setting(self):
  with tempfile.TemporaryDirectory() as folder:
   panel=CompanionWindow(folder)
   with self.assertRaises(ValueError):panel.motion('no')
   panel.motion(False);self.assertFalse(json.loads((Path(folder)/'jarvis-companion.json').read_text())['wandering'])

 def test_failed_native_launch_is_never_reported_as_open(self):
  with tempfile.TemporaryDirectory() as folder:
   panel=CompanionWindow(folder);process=Mock();process.poll.return_value=1
   with patch('backend.companion_window.platform.system',return_value='Darwin'),patch('backend.companion_window.subprocess.Popen',return_value=process):
    with self.assertRaisesRegex(ValueError,'konnte nicht starten'):panel.open('http://localhost:8765/companion?native=1')
   self.assertIsNone(panel.process)
 def test_invisible_native_window_times_out_and_stops_process(self):
  with tempfile.TemporaryDirectory() as folder:
   panel=CompanionWindow(folder);process=Mock();process.poll.return_value=None
   with patch('backend.companion_window.platform.system',return_value='Darwin'),patch('backend.companion_window.subprocess.Popen',return_value=process),patch('backend.companion_window.time.monotonic',side_effect=[0,7]):
    with self.assertRaisesRegex(ValueError,'kein sichtbares'):panel.open('http://localhost:8765/companion?native=1',_simple=True)
   process.terminate.assert_called_once();self.assertIsNone(panel.process)
 def test_native_window_uses_python_tk_instead_of_osascript(self):
  import sys
  with tempfile.TemporaryDirectory() as folder:
   panel=CompanionWindow(folder);working=Mock();working.poll.return_value=None;calls=[]
   def spawn(args,**kwargs):
    calls.append(args);(Path(folder)/'jarvis-companion.ready').write_text('visible');return working
   with patch('backend.companion_window.platform.system',return_value='Darwin'),patch('backend.companion_window.subprocess.Popen',side_effect=spawn):self.assertTrue(panel.open('http://localhost:8765/companion?native=1')['visible'])
   self.assertEqual(calls[0][:3],[sys.executable,'-m','backend.companion_tk']);self.assertFalse(any('osascript' in arg for arg in calls[0]));panel.close()
