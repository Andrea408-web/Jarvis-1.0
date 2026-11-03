"""Offline image attachment flow. Native macOS inference remains device-only."""
import base64
import json
import tempfile
import time
import unittest
from unittest.mock import Mock,patch
from backend.server import Application
from backend import native_vision

PNG=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jkF8AAAAASUVORK5CYII=')

class NativeVisionTests(unittest.TestCase):
    def test_other_platform_reports_unavailable_without_loading_frameworks(self):
        with patch('backend.native_vision.platform.system',return_value='Linux'),patch('backend.native_vision.ctypes.CDLL') as loader:
            result=native_vision.analyze(PNG)
        self.assertFalse(result['available']);loader.assert_not_called()

    def test_attachment_private_storage_local_findings_and_prompt(self):
        with tempfile.TemporaryDirectory() as folder:
            app=Application(folder);app.store.update_settings({'ai_provider':'llamacpp'})
            transport=Mock(return_value={'choices':[{'finish_reason':'stop','message':{'content':'Ein Produkttext'}}]});app.llamacpp.endpoint_transport=transport
            findings={'available':True,'labels':[{'label':'bottle','confidence':.8}],'text':'Mein Produkt','note':'Testbefund'}
            try:
                with patch('backend.agents.analyze_local_image',return_value=findings) as vision:
                    job=app.office.submit({'role':'studio','task':'Werbung für meine Flasche','image':base64.b64encode(PNG).decode(),'mime':'image/png'})
                    deadline=time.monotonic()+3
                    while time.monotonic()<deadline:
                        item=app.office.snapshot()['jobs'][0]
                        if item['status'] not in {'queued','running'}:break
                        time.sleep(.01)
                self.assertEqual(item['status'],'completed');self.assertEqual(item['stage'],'Ergebnis gespeichert')
                self.assertEqual(json.loads(item['vision']),findings);vision.assert_called_once_with(PNG)
                data,mime=app.office.image(job['id']);self.assertEqual(data,PNG);self.assertEqual(mime,'image/png')
                self.assertEqual((app.office.asset_dir/(job['id']+'.image')).stat().st_mode&0o777,0o600)
                prompt=transport.call_args.args[1]['messages'][-1]['content'];self.assertIn('bottle',prompt);self.assertIn('Du siehst keine Bildpixel',prompt)
                with self.assertRaises(ValueError):app.office.image('../../private')
            finally:app.office.stop()

    def test_invalid_image_rejected_before_queue(self):
        with tempfile.TemporaryDirectory() as folder:
            app=Application(folder);app.store.update_settings({'ai_provider':'llamacpp'})
            try:
                for image,mime in [('not base64','image/png'),(base64.b64encode(b'not an image').decode(),'image/jpeg'),(base64.b64encode(PNG).decode(),'text/html')]:
                    with self.assertRaises(ValueError):app.office.submit({'role':'studio','task':'Ad','image':image,'mime':mime})
                self.assertEqual(app.office.snapshot()['jobs'],[])
            finally:app.office.stop()
