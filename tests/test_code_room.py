import io
import json
import tempfile
import threading
import time
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from backend.code_room import CodeRoom,files_from_reply,validate_files
from backend.providers import ProviderError

class CodeRoomTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.calls=[];self.release=None
  self.reply=json.dumps({'summary':'Ein echter Entwurf. Noch nicht ausgeführt.','files':[{'path':'index.html','content':'<!doctype html><h1>Hallo Sir</h1><button onclick="this.textContent=\'Fertig\'">Start</button>'}]})
  self.app=SimpleNamespace(store=SimpleNamespace(data_dir=Path(self.tmp.name)),chat_lock=threading.Lock(),llamacpp=SimpleNamespace(endpoint_transport=self.transport),local_ai=SimpleNamespace(transport=self.ollama))
  self.room=CodeRoom(self.app)
 def transport(self,path,payload=None):
  if path=='/health':return {'status':'ok'}
  self.calls.append(payload)
  if self.release:self.release.wait(3)
  return {'choices':[{'finish_reason':'stop','message':{'content':self.reply if len(self.calls)%2 else 'Prüfe die Schaltfläche im Browser.'}}]}
 def ollama(self,path,payload=None):
  if path=='/api/tags':return {'models':[{'name':'qwen2.5:0.5b'},{'name':'remote-cloud:latest'},{'name':'https://evil.test/x'}]}
  self.calls.append(payload);return {'done':True,'message':{'content':self.reply}}
 def submit(self,**kw):
  body={'task':'Erstelle eine Website','model':'llamacpp','level':'medium','boost':False,'access':'ask','references':[]};body.update(kw)
  return self.room.submit(body,'owner')['id']
 def done(self,key):
  deadline=time.monotonic()+4
  while time.monotonic()<deadline:
   j=self.room.snapshot(key,'owner')
   if j['status'] not in {'queued','running','saving'}:return j
   time.sleep(.01)
  self.fail('job timed out')
 def test_ask_writes_only_after_explicit_save_and_exports_exact_bytes(self):
  key=self.submit();j=self.done(key);self.assertEqual(j['status'],'awaiting');self.assertFalse(self.room.root.exists());self.assertNotIn('owner',j)
  with self.assertRaises(ValueError):self.room.action(key,'another-device','save')
  saved=self.room.action(key,'owner','save');path=Path(saved['saved_path']);self.assertEqual(path.parent,self.room.root);self.assertEqual((path/'index.html').read_text(),j['files'][0]['content']);self.assertEqual(saved['status'],'saved')
  with self.assertRaises(ValueError):self.room.action(key,'owner','save')
  with zipfile.ZipFile(io.BytesIO(self.room.archive(key,'owner')))as z:self.assertEqual(z.read('index.html').decode(),j['files'][0]['content'])
  with self.assertRaises(ValueError):self.room.preview(key,'another-device')
 def test_draft_cannot_write_but_zip_requires_explicit_call(self):
  key=self.submit(access='draft');self.assertEqual(self.done(key)['status'],'draft');self.assertFalse(self.room.root.exists())
  with self.assertRaises(ValueError):self.room.action(key,'owner','save')
  self.assertTrue(self.room.archive(key,'owner').startswith(b'PK'))
 def test_project_permission_auto_writes_new_directory(self):
  key=self.submit(access='project');j=self.done(key);self.assertEqual(j['status'],'saved');self.assertTrue((self.room.root/key/'index.html').exists())
 def test_cancel_in_flight_discards_response_and_never_saves(self):
  self.release=threading.Event();key=self.submit(access='project')
  deadline=time.monotonic()+2
  while not self.calls and time.monotonic()<deadline:time.sleep(.01)
  self.room.action(key,'owner','cancel');self.release.set();self.app.chat_lock.acquire(timeout=2);self.app.chat_lock.release();j=self.room.snapshot(key,'owner');self.assertEqual(j['status'],'cancelled');self.assertEqual(j['files'],[]);self.assertFalse(self.room.root.exists())
 def test_real_levels_and_boost_change_requests(self):
  key=self.submit(level='high');self.assertEqual(self.done(key)['status'],'awaiting');self.assertEqual(len(self.calls),2);self.assertEqual(self.calls[0]['max_tokens'],1792);self.assertEqual(self.calls[1]['max_tokens'],512);self.assertEqual(self.calls[0]['response_format'],{'type':'json_object'});self.assertNotIn('response_format',self.calls[1])
  self.calls=[];key=self.submit(level='high',boost=True);self.done(key);self.assertEqual(len(self.calls),1);self.assertEqual(self.calls[0]['max_tokens'],768)
 def test_actual_installed_models_and_selection_without_download(self):
  models=self.room.models()['models'];self.assertEqual([m['id'] for m in models],['llamacpp','ollama:qwen2.5:0.5b'])
  key=self.submit(model='ollama:qwen2.5:0.5b',level='light');self.assertEqual(self.done(key)['status'],'awaiting');self.assertEqual(self.calls[0]['model'],'qwen2.5:0.5b');self.assertEqual(self.calls[0]['options']['num_predict'],768);self.assertEqual(self.calls[0]['format'],'json')
  with self.assertRaises(ValueError):self.submit(model='ollama:not-installed')
 def test_malformed_output_is_error_not_fake_completed(self):
  self.reply='Auftrag erfüllt.';key=self.submit(access='project');j=self.done(key);self.assertEqual(j['status'],'error');self.assertFalse(self.room.root.exists());self.assertEqual(j['files'],[])
 def test_syntax_failure_and_truncated_model_output_never_write(self):
  self.reply=json.dumps({'summary':'Test','files':[{'path':'bad.py','content':'if :'}]});key=self.submit(access='project');self.assertEqual(self.done(key)['status'],'error');self.assertFalse(self.room.root.exists())
  self.app.llamacpp.endpoint_transport=lambda p,b=None:{'status':'ok'} if p=='/health' else {'choices':[{'finish_reason':'length','message':{'content':self.reply}}]}
  key=self.submit(access='project');self.assertEqual(self.done(key)['status'],'error');self.assertFalse(self.room.root.exists())
 def test_path_validation_blocks_traversal_hidden_aliases_and_exec_files(self):
  for name in ['../a.js','a/../b.js','/tmp/a.js','.env','a//b.js','a/./b.js','setup.command','script.sh','C:/a.js','a\\b.js','x.html\x00']:
   with self.subTest(name=name),self.assertRaises(ValueError):validate_files([{'path':name,'content':'x'}])
  with self.assertRaises(ValueError):validate_files([{'path':'A.js','content':''},{'path':'a.js','content':''}])
  with self.assertRaises(ValueError):validate_files([{'path':'a.js','content':'x'*80001}])
 def test_symlink_root_refused_and_existing_directory_not_overwritten(self):
  other=Path(self.tmp.name)/'private';other.mkdir();self.room.root.symlink_to(other,target_is_directory=True)
  key=self.submit(access='project');self.assertEqual(self.done(key)['status'],'error');self.assertEqual(list(other.iterdir()),[])
 def test_preview_inlines_local_assets_but_not_external_dependencies(self):
  self.reply=json.dumps({'summary':'Test','files':[{'path':'web/index.html','content':'<link href="style.css"><script src="app.js"></script><script src="https://evil.test/a.js"></script>'},{'path':'web/style.css','content':'body{color:red}'},{'path':'web/app.js','content':'document.body.dataset.ready="yes"'}]});key=self.submit();self.done(key);preview=self.room.preview(key,'owner').decode();self.assertIn('<style>body{color:red}</style>',preview);self.assertIn('document.body.dataset.ready',preview);self.assertNotIn('evil.test',preview)
 def test_invalid_permissions_types_and_reference_limits(self):
  for change in [{'access':'full-system'},{'access':[]},{'level':[]},{'boost':1},{'model':[]},{'references':[{'path':'x.txt','content':'a'*3501}]}]:
   with self.subTest(change=change),self.assertRaises(ValueError):self.submit(**change)

 def test_existing_target_is_not_overwritten_and_partial_save_rolls_back(self):
  key=self.submit();self.done(key);target=self.room.root/key;target.mkdir(parents=True);(target/'mine.txt').write_text('private')
  with self.assertRaises(ValueError):self.room.action(key,'owner','save')
  self.assertEqual((target/'mine.txt').read_text(),'private');self.assertEqual(self.room.snapshot(key,'owner')['status'],'awaiting')
  self.calls=[];self.reply=json.dumps({'summary':'Conflict','files':[{'path':'a.js','content':'one'},{'path':'a.js/b.js','content':'two'}]})
  other=self.submit();self.done(other)
  with self.assertRaises(OSError):self.room.action(other,'owner','save')
  self.assertFalse((self.room.root/(other+'.tmp')).exists());self.assertFalse((self.room.root/other).exists())
 def test_recent_jobs_are_owner_scoped_and_no_model_is_invented(self):
  key=self.submit();self.done(key);self.assertEqual(self.room.recent('owner')['jobs'][0]['id'],key);self.assertEqual(self.room.recent('other')['jobs'],[])
  def offline(*args):raise ProviderError('not running',503)
  self.app.llamacpp.endpoint_transport=offline;self.app.local_ai.transport=offline
  self.assertEqual(self.room.models()['models'],[])
  with self.assertRaises(ValueError):self.submit()
 def test_talk_before_work_uses_local_model_without_file_writes(self):
  self.reply='Sir, wir können eine Website planen.';answer=self.room.talk('owner',{'id':None,'model':'llamacpp','text':'Wie fange ich an?','kind':'talk','history':[]});self.assertIn('Sir',answer['reply']);self.assertFalse(self.room.root.exists());self.assertNotIn('response_format',self.calls[0])
 def test_busy_status_and_steering_are_real_and_revised(self):
  ready=threading.Event();release=threading.Event();payloads=[]
  def transport(path,payload=None):
   if path=='/health':return {'status':'ok'}
   payloads.append(payload)
   if len(payloads)==1:ready.set();release.wait(3)
   return {'choices':[{'finish_reason':'stop','message':{'content':self.reply}}]}
  self.app.llamacpp.endpoint_transport=transport;key=self.submit();self.assertTrue(ready.wait(1));body={'id':key,'model':'llamacpp','text':'Wie weit bist du?','kind':'talk','history':[]};self.assertIn('Sir',self.room.talk('owner',body)['reply']);self.assertEqual(len(payloads),1)
  body.update(text='Bitte heller gestalten',kind='steer');self.assertTrue(self.room.talk('owner',body)['queued']);release.set();j=self.done(key);self.assertEqual(j['status'],'awaiting');self.assertTrue(j['instructions'][0]['applied']);self.assertEqual(len(payloads),2);self.assertIn('Bitte heller gestalten',payloads[1]['messages'][-1]['content'])
  with self.assertRaises(ValueError):self.room.talk('other',body)
  with self.assertRaises(ValueError):self.room.talk('owner',body)
