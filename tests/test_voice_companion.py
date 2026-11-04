import tempfile,threading,time,unittest
from pathlib import Path
from unittest.mock import patch
from backend.server import Application
from backend.natural_voice import NaturalVoice

class ReliabilityTests(unittest.TestCase):
 def test_cancel_releases_natural_voice_without_canceling_background(self):
  with tempfile.TemporaryDirectory() as folder:
   voice=NaturalVoice(folder);voice.root.mkdir();voice.record={'executable':'exe','model':'model','tokens':'tokens','data_dir':'data'};voice.signatures={};started=threading.Event();errors=[]
   def generate(*a,**kw):
    started.set();event=kw['cancel_event'];event.wait(2)
    if event.is_set():raise ValueError('gestoppt')
    return b'audio'
   def speak():
    try:voice.synthesize('Hallo',request_id='test')
    except Exception as error:errors.append(str(error))
   with patch('backend.natural_voice.generate',side_effect=generate):
    worker=threading.Thread(target=speak);worker.start();self.assertTrue(started.wait(1));voice.cancel('test');worker.join(2);self.assertFalse(worker.is_alive());self.assertTrue(errors);self.assertTrue(voice.lock.acquire(False));voice.lock.release()
 def test_companion_heartbeat_queue_and_busy_delivery(self):
  with tempfile.TemporaryDirectory() as folder:
   app=Application(folder)
   try:
    self.assertFalse(app.desktop.snapshot()['companion_active']);app.desktop.companion({'command':'send','text':'Hallo'});self.assertTrue(app.desktop.snapshot()['companion_active'])
    self.assertEqual(app.desktop.sync_ui({'busy':True,'mode':'thinking','conversation':True})['commands'],[])
    self.assertEqual(app.desktop.sync_ui({'busy':False,'mode':'idle','conversation':True})['commands'][0]['text'],'Hallo')
    self.assertEqual(app.desktop.sync_ui({'busy':False,'mode':'idle','conversation':True})['commands'],[])
   finally:app.office.stop()
 def test_group_creates_real_queued_jobs_with_cap(self):
  with tempfile.TemporaryDirectory() as folder:
   app=Application(folder);app.store.update_settings({'ai_provider':'llamacpp'})
   try:
    with patch.object(app.office,'_run',lambda:app.office.closed.wait(2)):
     result=app.office.submit_group({'count':40,'task':'Plane ein Projekt'});self.assertEqual(len(result['jobs']),40);self.assertEqual(len(app.office.snapshot()['jobs']),40)
     with self.assertRaises(Exception):app.office.submit_group({'count':1,'task':'weiter'})
   finally:app.office.stop()
