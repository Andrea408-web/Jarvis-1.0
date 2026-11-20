"""Actual authenticated HTTP job lifecycle, including large contour edit payloads."""
import json,threading,time,unittest
from tests import test_server as http_tests
from tests.test_workshop_free import RAW

class WorkshopHTTPTests(unittest.TestCase):
 setUp=http_tests.LiveServerTests.setUp
 stop_server=http_tests.LiveServerTests.stop_server
 def request(self,*args,**kwargs):
  status,data,_=http_tests.LiveServerTests.request(self,*args,**kwargs);return status,data
 def prepare(self):
  self.app.store.update_settings({'ai_provider':'llamacpp'});self.addCleanup(self.app.workshop.stop);self.addCleanup(self.app.office.stop);self.calls=[]
  def generate(*args,**kwargs):self.calls.append((args,kwargs));return json.dumps(RAW)
  self.app.code_room._generate=generate
 def body(self,key='a'*32):return {'id':key,'request':{'spec':{'template':'custom','material':'wood','width':240,'height':180,'depth':100,'thickness':12,'days':3},'request':'Ein runder Beistelltisch','free_design':True}}
 def done(self,key='a'*32):
  for _ in range(100):
   code,data=self.request('POST','/api/workshop/jobs/status',{'id':key})
   if data['state']!='running':return data
   time.sleep(.005)
  self.fail('job did not finish')
 def test_jobs_require_token_and_do_not_execute_unauthenticated(self):
  self.prepare()
  for path,body in [('/api/workshop/jobs',self.body()),('/api/workshop/jobs/status',{'id':'a'*32}),('/api/workshop/jobs/cancel',{'id':'a'*32})]:
   code,_=self.request('POST',path,body,token=False);self.assertEqual(code,401)
  self.assertFalse(self.calls)
 def test_create_status_cancel_and_private_owner_scope(self):
  self.prepare();code,created=self.request('POST','/api/workshop/jobs',self.body());self.assertEqual(code,202);data=self.done();self.assertEqual(data['state'],'done');self.assertEqual(data['result']['title'],RAW['title'])
  for path in ['/api/workshop/jobs/status','/api/workshop/jobs/cancel']:
   code,_=self.request('POST',path,{'id':'a'*32},headers={'Cookie':'different-context'});self.assertEqual(code,400)
  code,same=self.request('POST','/api/workshop/jobs',self.body());self.assertEqual(code,202);self.assertEqual(same['state'],'done');self.assertEqual(len(self.calls),1)
 def test_large_model_payload_passes_body_limit_and_gets_a_validation_error(self):
  self.prepare();body=self.body();body['request']['previous']={'title':'x'*40000};self.assertGreater(len(json.dumps(body)),32768)
  code,_=self.request('POST','/api/workshop/jobs',body);self.assertEqual(code,202);data=self.done();self.assertEqual(data['state'],'error');self.assertNotIn('Größenlimit',data['error']);self.assertFalse(self.calls)
 def test_waiting_job_can_be_cancelled_and_discards_late_model_answer(self):
  self.prepare();started=threading.Event();release=threading.Event();self.addCleanup(release.set)
  def generate(*args,**kwargs):started.set();release.wait(2);return json.dumps(RAW)
  self.app.code_room._generate=generate;code,_=self.request('POST','/api/workshop/jobs',self.body());self.assertEqual(code,202);self.assertTrue(started.wait(1));code,cancelled=self.request('POST','/api/workshop/jobs/cancel',{'id':'a'*32});self.assertEqual(code,200);self.assertEqual(cancelled['state'],'cancelled');release.set();self.assertNotIn('result',self.done())
