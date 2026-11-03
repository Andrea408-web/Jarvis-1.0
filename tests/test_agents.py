"""Actual local task lifecycle, restart behavior and resource isolation."""
import tempfile
import threading
import time
import unittest
from unittest.mock import Mock

from backend.server import Application
from backend.agents import AgentOffice
from backend.providers import ProviderError

class AgentTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory();self.app=Application(self.folder.name)
        self.app.store.update_settings({'ai_provider':'llamacpp','cloud_enabled':False})
        self.app.ai.chat=Mock(side_effect=AssertionError('No cloud'))
        self.app.openai.chat=Mock(side_effect=AssertionError('No cloud'))
    def tearDown(self):
        self.app.office.stop();self.folder.cleanup()
    def wait(self,identifier,status):
        deadline=time.monotonic()+4
        while time.monotonic()<deadline:
            item=next(job for job in self.app.office.snapshot()['jobs'] if job['id']==identifier)
            if item['status']==status:return item
            time.sleep(.01)
        self.fail('Expected '+status+', got '+item['status'])
    def test_real_local_result_persisted_without_polluting_chat_or_cloud(self):
        self.app.llamacpp.endpoint_transport=Mock(return_value={'choices':[{'finish_reason':'stop','message':{'content':'1. Ziel klären. 2. Üben.'}}]})
        job=self.app.office.submit({'role':'planner','task':'Plane meinen Lernnachmittag'})
        result=self.wait(job['id'],'completed');self.assertIn('Ziel klären',result['result'])
        self.assertEqual(self.app.store.history(),[])
        self.assertEqual(len(self.app.store.history('agent_'+job['id'])),2)
        self.app.ai.chat.assert_not_called();self.app.openai.chat.assert_not_called()
        restored=Application(self.folder.name)
        self.assertEqual(restored.office.snapshot()['jobs'][0]['result'],result['result']);restored.office.stop()
    def test_failure_is_never_completed(self):
        self.app.llamacpp.endpoint_transport=Mock(side_effect=ProviderError('Lokale KI fehlt.',503))
        job=self.app.office.submit({'role':'writer','task':'Schreib einen Entwurf'})
        self.assertIn('fehlt',self.wait(job['id'],'failed')['result'])
    def test_cancel_queued_and_running_discards_late_result(self):
        started=threading.Event();release=threading.Event()
        def transport(*args,**kwargs):
            started.set();release.wait(3)
            return {'choices':[{'finish_reason':'stop','message':{'content':'Spätes Ergebnis'}}]}
        self.app.llamacpp.endpoint_transport=transport
        try:
            first=self.app.office.submit({'role':'writer','task':'Entwurf'})
            self.assertTrue(started.wait(2));self.wait(first['id'],'running')
            second=self.app.office.submit({'role':'reviewer','task':'Prüfe: Hallo'})
            self.app.office.cancel(second['id']);self.app.office.cancel(first['id']);release.set()
            self.wait(first['id'],'cancelled');self.wait(second['id'],'cancelled')
            self.app.office.stop()
            for job in self.app.office.snapshot()['jobs']:self.assertNotIn('Spätes Ergebnis',job['result'])
        finally:release.set()
    def test_queue_capacity_and_chat_lock_are_shared(self):
        self.app.chat_lock.acquire()
        try:
            identifiers=[self.app.office.submit({'role':'planner','task':str(i)})['id'] for i in range(8)]
            with self.assertRaises(ProviderError):self.app.office.submit({'role':'planner','task':'too much'})
            self.assertTrue(all(job['status']=='queued' for job in self.app.office.snapshot()['jobs']))
            for identifier in identifiers:self.app.office.cancel(identifier)
        finally:self.app.chat_lock.release()
    def test_provider_and_invalid_input_never_start_a_cloud_job(self):
        for data in [{'role':'bad','task':'Hi'},{'role':[],'task':'Hi'},{'role':'planner','task':''},{'role':'planner','task':'a'*3001}]:
            with self.assertRaises(ValueError):self.app.office.submit(data)
        self.app.store.update_settings({'ai_provider':'openai','cloud_enabled':True})
        with self.assertRaises(ProviderError):self.app.office.submit({'role':'planner','task':'Plan'})
        self.assertIsNone(self.app.office.thread);self.assertEqual(self.app.office.snapshot()['jobs'],[])
    def test_restart_marks_unfinished_jobs_interrupted_without_resuming(self):
        with self.app.store._connect() as db:
            db.execute("INSERT INTO agent_jobs(id,role,task,status,created_at,updated_at) VALUES('test','planner','unfinished','running','now','now')")
        restored=AgentOffice(self.app)
        self.assertEqual(restored.snapshot()['jobs'][0]['status'],'interrupted');self.assertIsNone(restored.thread);restored.stop()
    def test_voice_presets_validate_atomically(self):
        for value in ['jarvis','clear','system']:self.app.store.update_settings({'voice_preset':value})
        for value in ['remote',None,{},True]:
            with self.assertRaises(ValueError):self.app.store.update_settings({'voice_preset':value,'cloud_enabled':True})
            self.assertFalse(self.app.store.settings()['cloud_enabled'])

class AgentHTTPTests(unittest.TestCase):
    def test_job_endpoints_require_session_and_return_actual_local_result(self):
        import http.client
        import json
        from backend.server import JarvisServer
        with tempfile.TemporaryDirectory() as folder:
            app=Application(folder);app.store.update_settings({'ai_provider':'llamacpp'})
            app.llamacpp.endpoint_transport=Mock(return_value={'choices':[{'finish_reason':'stop','message':{'content':'HTTP-Entwurf'}}]})
            server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            def request(path,method='GET',body=None,authorized=True):
                client=http.client.HTTPConnection(*server.server_address,timeout=3)
                headers={'Content-Type':'application/json'}
                if authorized:headers['X-Jarvis-Token']=app.token
                try:
                    client.request(method,path,json.dumps(body) if body is not None else None,headers);response=client.getresponse();return response.status,json.loads(response.read())
                finally:client.close()
            try:
                self.assertEqual(request('/api/agents',authorized=False)[0],401)
                self.assertEqual(request('/api/agents','POST',{'role':'writer','task':'Hi'},False)[0],401)
                self.assertEqual(request('/api/agents','POST',{'role':'writer','task':'Hi','url':'https://example.org'})[0],400)
                status,job=request('/api/agents','POST',{'role':'writer','task':'Begrüßung'})
                self.assertEqual(status,202)
                deadline=time.monotonic()+3
                while time.monotonic()<deadline:
                    status,data=request('/api/agents')
                    if data['jobs'][0]['status']=='completed':break
                    time.sleep(.01)
                self.assertEqual(data['jobs'][0]['result'],'HTTP-Entwurf')
                self.assertEqual(request('/api/agents/cancel','POST',{'id':job['id']})[0],400)
            finally:app.office.stop();server.shutdown();server.server_close();thread.join(timeout=3)


class TaskRoutingTests(unittest.TestCase):
    def test_natural_requests_and_negation(self):
        from backend.task_router import task_request
        for text in ['Beauftrage einen Agenten, der eine Einkaufsliste erstellt','Lass einen Agenten einen Lernplan machen','Ein Agent soll einen Text schreiben','Kannst du einen Agenten beauftragen, eine Werbung zu erstellen?']:
            self.assertIsNotNone(task_request(text))
        self.assertEqual(task_request('Beauftrage Atlas: Schreibe einen Plan')['role'],'planner')
        for text in ['Beauftrage keinen Agenten','Warum beauftragt der Agent nichts?','Zeig meine Agenten','Was machen meine Agenten?','Zeig was die Agenten gemacht haben','Hallo']:
            self.assertIsNone(task_request(text))
    def test_chat_creates_job_instead_of_model_promise(self):
        with tempfile.TemporaryDirectory() as folder:
            app=Application(folder);app.store.update_settings({'ai_provider':'llamacpp'})
            app.llamacpp.endpoint_transport=Mock(return_value={'choices':[{'finish_reason':'stop','message':{'content':'Ein Lernplan'}}]})
            try:
                response=app.chat('Beauftrage einen Agenten, der einen Lernplan erstellt')
                self.assertIn('job_id',response)
                self.assertEqual(response['view'],'office')
                self.assertEqual(app.office.snapshot()['jobs'][0]['id'],response['job_id'])
            finally:app.office.stop()
