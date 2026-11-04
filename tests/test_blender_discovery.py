import plistlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock,patch
from backend.desktop import resolve_app,MacInput,Desktop
from backend.server import Application
from backend.storage import Store
from backend.local_ai import LocalClient

class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.home=Path(self.temp.name);self.bundle=self.home/'Downloads'/'Blender 4.5.app'
        contents=self.bundle/'Contents';contents.mkdir(parents=True)
        (contents/'Info.plist').write_bytes(plistlib.dumps({'CFBundleIdentifier':'org.blenderfoundation.blender','CFBundleName':'Blender'}))
        executable=contents/'MacOS/Blender';executable.parent.mkdir();executable.write_text('test fixture, not executable')
        self.platform=patch('backend.desktop.platform.system',return_value='Darwin');self.platform.start()
        self.homepatch=patch('backend.desktop.Path.home',return_value=self.home);self.homepatch.start()
    def tearDown(self):self.homepatch.stop();self.platform.stop();self.temp.cleanup()
    def test_downloaded_versioned_bundle_is_found_by_canonical_name(self):
        result=resolve_app('Blender');self.assertEqual(result['bundle'],'org.blenderfoundation.blender')
        # A known registered bundle may not need downloads until LaunchServices fails.
        result=resolve_app('Blender',True);self.assertEqual(Path(result['path']),self.bundle.resolve())
        self.assertEqual(resolve_app('Blender 4.5.app')['path'],str(self.bundle.resolve()))
    def test_launchservices_failure_retries_actual_downloaded_app_path(self):
        with patch('backend.desktop.subprocess.run',side_effect=[Mock(returncode=1),Mock(returncode=0)]) as run,patch('backend.desktop.ctypes.CDLL') as graphics:
            driver=MacInput();driver.execute({'type':'open','app':'Blender'})
            self.assertEqual(run.call_args.args[0],['/usr/bin/open','-a',str(self.bundle.resolve())]);graphics.assert_not_called()
    def test_model_builder_finds_executable_in_downloaded_bundle(self):
        app=Mock();desktop=Desktop(app);self.assertEqual(desktop.blender_binary(),str(self.bundle/'Contents/MacOS/Blender'))

class ProfileTests(unittest.TestCase):
    def test_open_blender_is_not_misrouted_as_a_modelling_request(self):
        with tempfile.TemporaryDirectory() as folder:
            app=Application(folder)
            try:
                app.desktop.model_scene=Mock(side_effect=AssertionError('Opening must not call the model planner'))
                for goal in ['Öffne Blender','Kannst du Blender öffnen?']:
                    self.assertEqual(app.desktop.prepare({'goal':goal})['plan']['steps'],[{'type':'open','app':'Blender'}])
            finally:app.office.stop()
    def test_user_name_is_saved_separately_and_wrong_greeting_corrected(self):
        with tempfile.TemporaryDirectory() as folder:
            app=Application(folder)
            try:
                app.store.update_settings({'assistant_identity':'astra'})
                reply=app.chat('Astrid, ich heiße Maxine')['reply'];self.assertIn('Maxine',reply)
                self.assertEqual(Store(folder).settings()['user_name'],'Maxine');self.assertEqual(app.chat('Astra, wie heiße ich?')['reply'],'Du heißt Maxine.')
                seen=[]
                def transport(path,payload):seen.append(payload);return {'done':True,'message':{'content':'Hallo Astrid, wie geht es dir?'}}
                client=LocalClient(app.store,transport)
                self.assertEqual(client.chat('Hallo')['reply'],'Hallo Master, wie geht es dir?')
                self.assertIn('Der Mensch heißt Maxine',seen[0]['messages'][0]['content'])
                self.assertIn('Du bist ASTRA',seen[0]['messages'][0]['content'])
                self.assertEqual(client.chat('Schreib einen Brief an Astrid')['reply'],'Hallo Astrid, wie geht es dir?')
            finally:app.office.stop()
