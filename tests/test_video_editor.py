"""Actual local video cuts and exports, bounded work and read-only input files."""
import hashlib,io,json,shutil,subprocess,sys,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch,MagicMock
from backend.video_editor import VideoEditor
@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'FFmpeg fixture tools not installed')
class VideoEditorTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.editor=VideoEditor(self.root);self.addCleanup(self.editor.close)
  self.source=self.root/'source.mp4';subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i','color=red:s=320x180:r=30:d=1','-f','lavfi','-i','color=blue:s=320x180:r=30:d=1','-filter_complex','[0:v][1:v]concat=n=2:v=1:a=0[v]','-map','[v]','-c:v','libx264','-threads','1',str(self.source)],check=True,capture_output=True)
  self.asset=self.editor.import_paths([str(self.source)])[0];self.original=hashlib.sha256(self.source.read_bytes()).hexdigest()
 def wait(self,job):
  self.editor.worker.join(45);self.assertFalse(self.editor.worker.is_alive());return self.editor.jobs[job['id']]
 def test_real_both_formats_correct_selected_frames_and_audio_track(self):
  job=self.editor.start({'cuts':[{'asset':self.asset['id'],'start':1,'end':2}],'formats':['youtube','shorts'],'budget_minutes':1,'short_seconds':5});result=self.wait(job);self.assertEqual(result['state'],'completed',result);self.assertEqual(len(result['outputs']),2)
  for output in result['outputs']:
   self.assertEqual((output['width'],output['height']),(1920,1080) if output['format']=='youtube' else (1080,1920));self.assertTrue(output['audio']);self.assertAlmostEqual(output['duration'],1,delta=.2);path,_=self.editor.file(job['id'],output['format']);pixel=subprocess.run(['ffmpeg','-v','error','-ss','0.4','-i',str(path),'-vf','scale=1:1','-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True,check=True).stdout;self.assertGreater(pixel[2],pixel[0]+150,'Selected blue second must replace red first second')
  self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(),self.original);self.assertNotIn('path',self.asset)
 def test_deadline_stops_real_process_and_preserves_verified_first_output(self):
  before=time.monotonic()
  with self.assertRaises(TimeoutError):self.editor._command([sys.executable,'-c','import time;time.sleep(10)'],time.monotonic()+.15)
  self.assertLess(time.monotonic()-before,3);self.assertIsNone(self.editor.process)
  original=self.editor._ffmpeg
  def render(cuts,kind,path,tools,deadline,job=None):
   if kind=='shorts':path.write_bytes(b'partial');raise TimeoutError('limit')
   return original(cuts,kind,path,tools,deadline,job=job)
  with patch.object(self.editor,'_ffmpeg',side_effect=render):result=self.wait(self.editor.start({'cuts':[{'asset':self.asset['id'],'start':0,'end':.5}],'formats':['youtube','shorts'],'budget_minutes':1}))
  self.assertEqual(result['state'],'timed_out');self.assertEqual(len(result['outputs']),1);self.assertTrue(self.editor.file(result['id'],'youtube')[0].is_file());self.assertFalse(list((self.editor.root/result['id']).glob('*.partial.mp4')))
 def test_silence_analysis_removes_only_middle_pause(self):
  path=self.root/'speech.mp4';subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i','color=green:s=160x90:r=30:d=2.2','-f','lavfi','-i','sine=frequency=500:duration=0.5','-f','lavfi','-i','anullsrc=r=44100:cl=mono:d=1.2','-f','lavfi','-i','sine=frequency=500:duration=0.5','-filter_complex','[1:a][2:a][3:a]concat=n=3:v=0:a=1[a]','-map','0:v','-map','[a]','-c:v','libx264','-threads','1','-c:a','aac',str(path)],check=True,capture_output=True);asset=self.editor.import_paths([str(path)])[0];cuts=self.editor._silence({'asset':asset['id'],'start':0,'end':2.2},self.editor.tools(),time.monotonic()+20);duration=sum(c['end']-c['start'] for c in cuts);self.assertGreater(duration,1);self.assertLess(duration,1.7);self.assertEqual(len(cuts),2)
 def test_invalid_cut_paths_and_nonfinite_times_are_rejected(self):
  for cuts in [[{'asset':'../../etc/passwd','start':0,'end':1}],[{'asset':self.asset['id'],'start':float('nan'),'end':1}],[{'asset':self.asset['id'],'start':1.5,'end':1}]]:
   with self.assertRaises(ValueError):self.editor.start({'cuts':cuts,'formats':['youtube']})
  with self.assertRaises(ValueError):self.editor.file('../../private','youtube')

 def test_stream_upload_and_interrupted_import_cleanup(self):
  data=self.source.read_bytes();assets=self.editor.upload(io.BytesIO(data),len(data),'Mein Clip.mp4');asset=assets[0]
  self.assertEqual(asset['name'],'Mein Clip.mp4');self.assertEqual(self.editor.file(asset['id'])[0].read_bytes(),data)
  before=set((self.editor.root/'imports').iterdir())
  with self.assertRaises(ValueError):self.editor.upload(io.BytesIO(b'short'),100,'broken.mp4')
  self.assertEqual(set((self.editor.root/'imports').iterdir()),before)
  with self.assertRaises(ValueError):self.editor.upload(io.BytesIO(data),len(data),'script.py')
 def test_local_ai_plan_executes_valid_cut_and_rejects_unselected_source(self):
  app=MagicMock();app.store.settings.return_value={'ai_provider':'llamacpp','local_model':'small'}
  app.llamacpp.transport.return_value={'done':True,'message':{'content':json.dumps({'cuts':[{'clip':1,'start':1,'end':2}],'remove_silence':False})}}
  result=self.editor.assist(app,{'assets':[self.asset['id']],'instruction':'Entferne die erste Sekunde','formats':['youtube'],'budget_minutes':1})
  job=self.wait(result['job']);self.assertEqual(job['state'],'completed');self.assertEqual(job['cuts'][0]['start'],1)
  app.llamacpp.transport.return_value={'done':True,'message':{'content':json.dumps({'cuts':[{'clip':99,'start':0,'end':1}],'remove_silence':False})}}
  with self.assertRaises(ValueError):self.editor.assist(app,{'assets':[self.asset['id']],'instruction':'Schneide'})
  app.llamacpp.transport.return_value={'done':True,'message':{'content':'Anfrage erfüllt'}}
  with self.assertRaises(ValueError):self.editor.assist(app,{'assets':[self.asset['id']],'instruction':'Schneide'})
 def test_mp4_metadata_without_any_native_framework_including_fragmented(self):
  from backend.video_metadata import probe
  for fragmented in [False,True]:
   target=self.root/('fragment.mp4' if fragmented else 'regular.mov')
   args=['ffmpeg','-v','error','-y','-i',str(self.source),'-c','copy']
   if fragmented:args+=['-movflags','frag_keyframe+empty_moov']
   subprocess.run(args+[str(target)],capture_output=True,check=True)
   metadata=probe(target);self.assertAlmostEqual(metadata['duration'],2,delta=.15);self.assertEqual(metadata['width'],320)
   with patch.object(self.editor,'tools',return_value={'engine':'avfoundation','ffprobe':None}),patch('backend.video_editor.subprocess.run') as native:
    self.assertAlmostEqual(self.editor.probe(target)['duration'],2,delta=.15);native.assert_not_called()
  broken=self.root/'broken.mp4';broken.write_bytes(b'\x00\x00\xff\xffmoovbad')
  with self.assertRaises(ValueError):probe(broken)
 def test_real_subtitles_color_effect_and_tempo_are_in_exported_pixels(self):
  job=self.editor.start({'cuts':[{'asset':self.asset['id'],'start':0,'end':2}],'formats':['youtube'],'budget_minutes':1,'style':{'look':'mono','speed':2,'vignette':True},'captions':[{'start':0,'end':1,'text':'Hallo Maxine!'}]});result=self.wait(job);self.assertEqual(result['state'],'completed',result);output=result['outputs'][0];self.assertAlmostEqual(output['duration'],1,delta=.2)
  path,_=self.editor.file(job['id'],'youtube');frame=subprocess.run(['ffmpeg','-v','error','-ss','0.35','-i',str(path),'-vf','crop=1600:260:160:800,scale=320:52','-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True,check=True).stdout
  pixels=list(zip(frame[::3],frame[1::3],frame[2::3]));self.assertGreater(sum(min(p)>210 for p in pixels),20,'Caption must be burned into video pixels');self.assertLess(max(abs(p[0]-p[2]) for p in pixels),15,'Monochrome look must affect the actual video')
  from backend.video_style import ass,validate
  text=ass([{'start':0,'end':1,'text':r'{\pos(0,0)} Test'}],1920,1080,'clean');self.assertNotIn(r'{\pos',text)
  with self.assertRaises(ValueError):validate({'look':'arbitrary filter;command'})
 def test_plan_only_needs_no_native_export_and_keeps_validated_effects(self):
  with patch.object(self.editor,'tools',return_value={'engine':'avfoundation','silence':False}):
   plan=self.editor.start({'cuts':[{'asset':self.asset['id'],'start':0,'end':1}],'formats':['youtube'],'style':{'look':'neon'},'captions':[{'start':0,'end':1,'text':'Sir'}]},plan_only=True)
  self.assertEqual(plan['style']['look'],'neon');self.assertEqual(len(self.editor.jobs),0);self.assertIsNone(self.editor.worker)
