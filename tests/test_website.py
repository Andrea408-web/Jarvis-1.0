import json,tempfile,time,unittest
from pathlib import Path
from backend.server import Application
from backend.website import build,requested

class WebsiteTests(unittest.TestCase):
 def test_real_html_file_escapes_model_text_and_reports_real_stages(self):
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'site.html';stages=[]
   reply=json.dumps({'title':'Mein <script>Projekt</script>','intro':'Hallo!','sections':[{'title':'Idee','text':'<img src=x onerror=alert(1)>'},{'title':'Kontakt','text':'Deine Kontaktdaten ergänzen.'}]})
   result=build(reply,'Website',path,stages.append);data=path.read_text();self.assertIn('Echte HTML-Datei',result);self.assertIn('&lt;script&gt;',data);self.assertNotIn('<script>',data);self.assertEqual(len(stages),4);self.assertIn('section-1',data)
 def test_plain_request_creates_real_job_and_file_without_model_success_claim(self):
  with tempfile.TemporaryDirectory() as folder:
   app=Application(folder);app.store.update_settings({'ai_provider':'llamacpp'})
   app.llamacpp.chat=lambda *a,**k:{'reply':json.dumps({'title':'Mein Radladen','intro':'Willkommen','sections':[{'title':'Service','text':'Reparaturen nach Absprache.'}]})}
   try:
    app.chat('Erstelle eine Notiz')
    result=app.chat('Erstelle mir eine Website für meinen Radladen');self.assertEqual(result['artifact'],'website')
    deadline=time.monotonic()+4
    while time.monotonic()<deadline:
     job=app.office.snapshot()['jobs'][0]
     if job['status'] not in {'running','queued'}:break
     time.sleep(.01)
    self.assertEqual(job['status'],'completed');self.assertEqual(job['artifact'],'website');self.assertIn(b'Mein Radladen',app.office.site(result['job_id']))
   finally:app.office.stop()
 def test_invalid_spec_fails_and_plain_prose_is_labelled_basic_draft(self):
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'site.html'
   with self.assertRaises(ValueError):build('{"title":"Invalid"}','Website',path,lambda _:None)
   self.assertFalse(path.exists());result=build('Ein Textentwurf.','Meine Website',path,lambda _:None);self.assertIn('Grundentwurf',result);self.assertTrue(path.is_file())
 def test_no_accidental_dispatch_of_explanations_or_open_requests(self):
  self.assertTrue(requested('Kannst du eine Website erstellen?'))
  self.assertTrue(requested('Erstelle eine Website für meine Band'))
  self.assertFalse(requested('Öffne eine Website'));self.assertFalse(requested('Wie erstelle ich eine Website?'))
