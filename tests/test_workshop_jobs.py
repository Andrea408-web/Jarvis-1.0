"""Real worker threading, cancellation, ownership and actual provider payloads."""
import copy,json,tempfile,threading,time,unittest
from unittest.mock import Mock
from backend.server import Application
from backend.workshop import DEFAULT
from backend.workshop_jobs import WorkshopCancelled,checkpoint
from backend.workshop_schema import design_schema
from tests.test_workshop_free import RAW

class WorkshopJobsTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.app=Application(self.tmp.name);self.addCleanup(self.app.office.stop);self.addCleanup(self.app.workshop.stop);self.app.store.update_settings({'ai_provider':'llamacpp'});self.payloads=[]
  def transport(path,payload=None):
   self.payloads.append(payload);return {'choices':[{'finish_reason':'stop','message':{'content':json.dumps(RAW)}}]}
  self.app.llamacpp.endpoint_transport=transport;self.room=self.app.workshop
 def body(self,key='1'*32):return {'id':key,'request':{'spec':DEFAULT,'free_design':True,'request':'Baue mir einen runden Beistelltisch'}}
 def done(self,key='1'*32):
  end=time.monotonic()+3
  while time.monotonic()<end:
   data=self.room.status(key,'owner')
   if self.room.running is None:return data
   time.sleep(.005)
  self.fail('worker did not finish')
 def test_actual_llamacpp_payload_has_bounded_schema_and_completed_result(self):
  first=self.room.submit(self.body(),'owner');self.assertEqual(first['state'],'running');data=self.done();self.assertEqual(data['state'],'done');self.assertEqual(data['result']['title'],RAW['title']);self.assertEqual(len(self.payloads),1)
  format=self.payloads[0]['response_format'];self.assertEqual(format['type'],'json_schema');self.assertEqual(format['json_schema']['schema'],design_schema());self.assertFalse(self.app.chat_lock.locked());self.assertNotIn('owner',data);self.assertNotIn('cancel',data)
 def test_ollama_receives_schema_in_format_not_only_json_mode(self):
  self.app.store.update_settings({'ai_provider':'ollama','local_model':'qwen2.5:0.5b'});calls=[]
  self.app.local_ai.transport=lambda path,payload:(calls.append(payload),{'done':True,'message':{'content':json.dumps(RAW)}})[1]
  self.room.submit(self.body(),'owner');self.assertEqual(self.done()['state'],'done');self.assertEqual(calls[0]['format'],design_schema());self.assertEqual(calls[0]['options']['num_ctx'],4096)
 def test_stop_during_generation_discards_result_and_never_retries(self):
  started=threading.Event();release=threading.Event();calls=[]
  def generate(*args,**kwargs):calls.append(args);started.set();release.wait(2);return 'not JSON'
  self.app.code_room._generate=generate;self.room.submit(self.body(),'owner');self.assertTrue(started.wait(1));self.assertEqual(self.room.cancel('1'*32,'owner')['state'],'cancelled');release.set();data=self.done();self.assertEqual(data['state'],'cancelled');self.assertNotIn('result',data);self.assertEqual(len(calls),1);self.assertFalse(self.app.chat_lock.locked())
 def test_cancel_before_create_is_a_tombstone_not_a_new_execution(self):
  self.room.cancel('1'*32,'owner');self.assertEqual(self.room.submit(self.body(),'owner')['state'],'cancelled');self.assertEqual(self.payloads,[])
 def test_owner_is_checked_for_status_cancel_and_idempotent_submit(self):
  self.room.submit(self.body(),'owner');self.done()
  for action in [lambda:self.room.status('1'*32,'other'),lambda:self.room.cancel('1'*32,'other'),lambda:self.room.submit(self.body(),'other')]:
   with self.assertRaises(ValueError):action()
  self.room.submit(self.body(),'owner');self.assertEqual(len(self.payloads),1)
 def test_invalid_responses_fail_with_specific_details_and_no_result(self):
  self.app.code_room._generate=Mock(return_value=json.dumps({'title':'Missing parts'}));self.room.submit(self.body(),'owner');data=self.done();self.assertEqual(data['state'],'error');self.assertIn('Pflichtfelder fehlen',data['error']);self.assertIn('parts',data['error']);self.assertNotIn('result',data);self.assertEqual(self.app.code_room._generate.call_count,2);self.assertFalse(self.app.chat_lock.locked())
 def test_bounded_memory_and_no_executable_model_code(self):
  for i in range(35):self.room.cancel(f'{i:032x}','owner')
  self.assertLessEqual(len(self.room.jobs),24)
  for body in [{'id':'../x','request':{}},{'id':'f'*32,'request':{'blob':'x'*210000}},{'id':'f'*32,'request':{'number':float('nan')}}]:
   with self.assertRaises(ValueError):self.room.submit(body,'owner')
 def test_checkpoint_cancel_is_not_a_repairable_value_error(self):
  with self.assertRaises(WorkshopCancelled):checkpoint(None,lambda:True,'phase','message')
