import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock,patch
from backend.server import Application
from backend.desktop import MacInput,Desktop
from backend.models import recipe,validate_scene,part
from backend.local_ai import LocalClient
from backend.storage import Store

class AstraFixTests(unittest.TestCase):
    def setUp(self):self.folder=tempfile.TemporaryDirectory();self.app=Application(self.folder.name)
    def tearDown(self):self.app.desktop.stop();self.app.office.stop();self.folder.cleanup()
    @patch('backend.desktop.platform.system',return_value='Darwin')
    def test_open_app_and_web_do_not_require_input_frameworks_or_accessibility(self,_):
        with patch('backend.desktop.ctypes.CDLL') as libraries,patch('backend.desktop.subprocess.run',return_value=Mock(returncode=0)) as run:
            driver=MacInput();driver.execute({'type':'open','app':'Spotify'});driver.execute({'type':'website','url':'https://example.com/app'})
            libraries.assert_not_called()
            self.assertEqual(run.call_args_list[0].args[0],['/usr/bin/open','-b','com.spotify.client'])
            self.assertEqual(run.call_args_list[1].args[0],['/usr/bin/open','-b','com.apple.Safari','https://example.com/app'])
    @patch('backend.desktop.platform.system',return_value='Darwin')
    def test_missing_native_spotify_can_open_its_web_app(self,_):
        with patch('backend.desktop.subprocess.run',side_effect=[Mock(returncode=1),Mock(returncode=0)]) as run:
            driver=MacInput();driver.execute({'type':'open','app':'Spotify'});self.assertIn('Web-App',driver.last_message);self.assertEqual(run.call_args.args[0][-1],'https://open.spotify.com')
    def test_spotify_and_web_commands_prepare_without_model(self):
        for goal,kind in [('Öffne Spotify','open'),('Öffne spotify im Browser','website'),('öffne example.com/app','website'),('öffne https://example.com/app?q=1','website')]:
            with self.subTest(goal=goal):
                plan=self.app.desktop.prepare({'goal':goal})['plan'];self.assertEqual(plan['steps'][0]['type'],kind);self.assertEqual(plan['state'],'review')
        with self.assertRaises(ValueError):self.app.desktop.prepare({'goal':'bad','steps':[{'type':'website','url':'javascript:alert(1)'}]})
    def test_astra_identity_is_persistent_and_sent_to_local_model(self):
        self.app.store.update_settings({'assistant_identity':'astra'});self.assertEqual(Store(self.folder.name).settings()['assistant_identity'],'astra')
        seen=[]
        def transport(path,payload):seen.append(payload);return {'done':True,'message':{'content':'Ich bin JARVIS, Sir.'}}
        result=LocalClient(self.app.store,transport).chat('Sag etwas über dich')
        self.assertIn('Du bist ASTRA',seen[0]['messages'][0]['content']);self.assertEqual(result['reply'],'Ich bin ASTRA, Sir.')
        self.assertEqual(self.app.chat('Wie heißt du?')['reply'],'Ich bin ASTRA, Sir.')
        self.app.store.update_settings({'assistant_identity':'jarvis'});self.assertEqual(self.app.chat('Wer bist du?')['reply'],'Ich bin JARVIS, Sir.')
    def test_known_model_is_prepared_without_claiming_execution(self):
        plan=self.app.desktop.prepare({'goal':'Erstelle ein 3D Auto in Blender'})['plan'];self.assertEqual(plan['kind'],'model');self.assertEqual(plan['state'],'review');self.assertEqual(len(plan['scene']['parts']),6);self.assertNotIn('artifact',plan)
    def test_geometry_limits_reject_unknown_code_and_nonfinite_coordinates(self):
        for invalid in [{'name':'x','parts':[dict(part('x'),shape='exec')]},{'name':'x','parts':[dict(part('x'),location=[0,float('nan'),0])]},{'name':'x','parts':[dict(part('x'),python='evil')]}]:
            with self.subTest(invalid=invalid),self.assertRaises(ValueError):validate_scene(invalid)
    def test_local_scene_model_is_data_and_has_no_cloud_fallback(self):
        scene=recipe('3D Roboter');self.app.store.update_settings({'ai_provider':'llamacpp'});seen=[]
        def local(path,payload):seen.append(payload);return {'choices':[{'message':{'content':json.dumps(scene)}}]}
        self.app.llamacpp.endpoint_transport=local
        plan=self.app.desktop.prepare({'goal':'Modelliere eine Fantasieskulptur in Blender'})['plan'];self.assertEqual(plan['scene'],scene);self.assertEqual(seen[0]['response_format'],{'type':'json_object'})
        self.app.store.update_settings({'ai_provider':'gemini'})
        with self.assertRaises(ValueError):self.app.desktop.model_scene('unknown object')
    @patch('backend.desktop.platform.system',return_value='Darwin')
    def test_native_panel_early_exit_is_error_instead_of_fake_success(self,_):
        with patch('backend.desktop.subprocess.Popen',return_value=Mock(poll=Mock(return_value=1))),patch('backend.desktop.time.sleep'):
            with self.assertRaises(ValueError):self.app.desktop.open_panel('http://127.0.0.1:8765/astra-panel.html')
        self.assertEqual(self.app.desktop.snapshot()['panel']['state'],'failed')
        self.assertTrue((Path(self.folder.name)/'astra-panel.log').is_file())
    @patch('backend.desktop.platform.system',return_value='Darwin')
    def test_unresponsive_panel_has_timeout_and_ready_ack_clears_error(self,_):
        self.app.desktop.panel=Mock(poll=Mock(return_value=None));self.app.desktop.panel_state='opening';self.app.desktop.panel_started=-100
        self.assertEqual(self.app.desktop.snapshot()['panel']['state'],'failed');self.app.desktop.panel_ready();self.assertEqual(self.app.desktop.snapshot()['panel']['state'],'ready')
