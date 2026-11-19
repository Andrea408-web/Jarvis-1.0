import tempfile,unittest
from unittest.mock import Mock
from backend.video_editor import VideoEditor
class AutoVideoTests(unittest.TestCase):
 def test_dynamic_recipe_is_bounded_executes_real_plan_and_keeps_originals(self):
  with tempfile.TemporaryDirectory()as folder:
   editor=VideoEditor(folder);editor.assets={'a':{'id':'a','name':'source.mp4','duration':30,'path':'never-modified.mp4'}};editor.tools=lambda:{'silence':False};editor.start=Mock(side_effect=lambda body,**kw:body)
   data=editor.assist(None,{'assets':['a'],'auto_edit':'dynamic','hook':'Das hätte ich nicht erwartet','formats':['youtube','shorts']},plan_only=True)
   self.assertEqual(len(data['job']['cuts']),3);self.assertEqual(data['job']['style']['transition'],'fade');self.assertTrue(data['job']['style']['zoom']);self.assertEqual(data['job']['captions'][0]['text'],'Das hätte ich nicht erwartet');self.assertTrue(editor.start.call_args.kwargs['plan_only']);self.assertIn('Keine automatische inhaltliche',data['message'])
 def test_full_recipe_keeps_all_selected_duration(self):
  with tempfile.TemporaryDirectory()as folder:
   editor=VideoEditor(folder);editor.assets={'a':{'id':'a','name':'long.mp4','duration':600}};editor.tools=lambda:{'silence':False};editor.start=Mock(side_effect=lambda body,**kw:body)
   data=editor.assist(None,{'assets':['a'],'auto_edit':'full'},plan_only=True);self.assertEqual(data['job']['cuts'],[{'asset':'a','start':0,'end':600}]);self.assertIn('Keine Wort-Untertitel',data['message'])

 def test_hook_keeps_original_subtitle_words(self):
  with tempfile.TemporaryDirectory()as folder:
   editor=VideoEditor(folder);editor.assets={'a':{'id':'a','name':'source.mp4','duration':30}};editor.tools=lambda:{'silence':False};editor.start=Mock(side_effect=lambda body,**kw:body)
   data=editor.assist(None,{'assets':['a'],'auto_edit':'dynamic','hook':'Schau genau hin','captions':[{'start':0,'end':5,'text':'Meine gesprochenen Wörter'}]},plan_only=True)
   captions=data['job']['captions'];self.assertIn('Meine gesprochenen Wörter',captions[0]['text']);self.assertEqual(captions[1],{'start':2.8,'end':5,'text':'Meine gesprochenen Wörter'})

 def test_automatic_recipe_exports_actual_video(self):
  import shutil,subprocess
  from pathlib import Path
  if not shutil.which('ffmpeg')or not shutil.which('ffprobe'):self.skipTest('FFmpeg not installed')
  with tempfile.TemporaryDirectory()as folder:
   source=Path(folder)/'input.mp4';subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i','color=blue:s=320x180:r=30:d=1','-c:v','libx264','-threads','1',str(source)],check=True,capture_output=True)
   editor=VideoEditor(Path(folder)/'edits');asset=editor.import_paths([str(source)])[0]
   try:
    data=editor.assist(None,{'assets':[asset['id']],'auto_edit':'dynamic','hook':'Mein erster Schnitt','formats':['youtube'],'budget_minutes':1});editor.worker.join(45);job=editor.jobs[data['job']['id']];self.assertEqual(job['state'],'completed',job);self.assertTrue(job['outputs']);self.assertTrue(source.exists())
   finally:editor.close()
