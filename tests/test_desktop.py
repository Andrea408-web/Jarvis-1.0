import tempfile
import time
import unittest
from unittest.mock import patch
from backend.desktop import Desktop,validate_steps
from backend.server import Application
from backend.hub import parse_news_api

class DesktopTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory();self.app=Application(self.folder.name);self.app.store.update_settings({'ai_provider':'llamacpp'})
        self.events=[]
        outer=self
        class Driver:
            def execute(self,step):outer.events.append(step)
        self.desktop=Desktop(self.app,Driver)
    def tearDown(self):
        self.desktop.stop()
        if self.desktop.thread:self.desktop.thread.join(5)
        self.app.office.stop();self.folder.cleanup()
    def plan(self):return self.desktop.prepare({'goal':'Testnotiz','steps':[{'type':'open','app':'Notizen'},{'type':'text','text':'Hallo'}]})['plan']
    def test_prepare_never_executes_and_plan_is_private_copy(self):
        plan=self.plan();plan['steps'][0]['app']='Safari';self.assertEqual(self.events,[]);self.assertEqual(self.desktop.snapshot()['plan']['steps'][0]['app'],'Notizen')
    def test_actual_driver_steps_and_mute_does_not_cancel(self):
        plan=self.plan();self.desktop.start(plan['id']);self.desktop.speech(True);self.desktop.thread.join(5)
        self.assertEqual([s['type'] for s in self.events],['open','text']);self.assertEqual(self.desktop.snapshot()['plan']['state'],'done');self.assertTrue(self.desktop.snapshot()['muted'])
    def test_stop_during_countdown_prevents_input_and_replay(self):
        plan=self.plan();self.desktop.start(plan['id']);self.desktop.stop();self.desktop.thread.join(5)
        self.assertEqual(self.events,[]);self.assertEqual(self.desktop.snapshot()['plan']['state'],'stopped')
        with self.assertRaises(ValueError):self.desktop.start(plan['id'])
    def test_permission_error_leaves_review(self):
        self.desktop.driver=lambda:(_ for _ in ()).throw(ValueError('permission denied'));plan=self.plan()
        with self.assertRaises(ValueError):self.desktop.start(plan['id'])
        self.assertEqual(self.desktop.snapshot()['plan']['state'],'review')
    def test_invalid_plans_rejected(self):
        bad=[[{'type':'shell','command':'echo x'}],[{'type':'text','text':'oops'}],[{'type':'open','app':[]}],[{'type':[]}],[{'type':'open','app':'Terminal'}],[{'type':'open','app':'Notizen'},{'type':'click','x':float('nan'),'y':0}],[{'type':'open','app':'Notizen'},{'type':'key','key':'n','modifiers':[{}]}]]
        for steps in bad:
            with self.subTest(steps=steps),self.assertRaises(ValueError):validate_steps(steps)
    def test_model_does_not_get_to_execute_or_invent_coordinates(self):
        self.app.llamacpp.chat=lambda *a,**k:{'reply':'{"steps":[{"type":"open","app":"Notizen"},{"type":"click","x":0.3,"y":0.2}]}'}
        with self.assertRaises(ValueError):self.desktop.prepare({'goal':'Schreib eine Notiz'})
        self.assertEqual(self.events,[])
    def test_unstructured_or_unsupported_model_output_is_not_success(self):
        for text in ['Okay Sir, fertig!','{"unsupported":true}']:
            self.app.llamacpp.chat=lambda *a,**k:{'reply':text}
            with self.assertRaises(ValueError):self.desktop.prepare({'goal':'Baue ein komplexes 3D-Modell'})
            self.assertEqual(self.events,[])
    def test_news_json_fallback_keeps_real_links_and_country(self):
        import json
        raw=json.dumps({'news':[{'title':'Deutschland: Meldung','detailsweb':'https://www.tagesschau.de/test.html','firstSentence':'Quelle','teaserImage':{'imageVariants':{'small':'https://images.tagesschau.de/test.jpg'}}},{'title':'Unsafe','detailsweb':'javascript:alert(1)'}]}).encode()
        items=parse_news_api(raw);self.assertEqual(len(items),1);self.assertEqual(items[0]['countries'],['DE']);self.assertEqual(items[0]['image'],'https://images.tagesschau.de/test.jpg')
    def test_existing_data_survives_loading(self):
        self.app.store.append('user','behalten');self.plan();self.assertEqual(self.app.store.history()[-1]['text'],'behalten')

class DesktopHTTPTests(unittest.TestCase):
    def test_token_and_checked_plan_id_are_required_before_execution(self):
        import http.client,json,threading
        from backend.server import JarvisServer
        with tempfile.TemporaryDirectory() as folder:
            app=Application(folder);server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            def request(path,body,authorized=True):
                client=http.client.HTTPConnection(*server.server_address,timeout=3);headers={'Content-Type':'application/json'}
                if authorized:headers['X-Jarvis-Token']=app.token
                try:
                    client.request('POST',path,json.dumps(body),headers);r=client.getresponse();return r.status,json.loads(r.read())
                finally:client.close()
            try:
                self.assertEqual(request('/api/desktop/prepare',{'goal':'öffne Notizen'},False)[0],401)
                status,data=request('/api/desktop/prepare',{'goal':'öffne Notizen'});self.assertEqual(status,200);self.assertEqual(data['plan']['state'],'review');self.assertEqual(data['plan']['steps'],[{'type':'open','app':'Notizen'}])
                self.assertEqual(request('/api/desktop/start',{'id':'wrong'})[0],400)
                self.assertEqual(request('/api/desktop/start',{'id':data['plan']['id'],'shell':'no'})[0],400)
                self.assertEqual(request('/api/desktop/speech',{'muted':'yes'})[0],400)
                self.assertEqual(app.desktop.snapshot()['plan']['state'],'review')
            finally:app.desktop.stop();app.office.stop();server.shutdown();server.server_close();thread.join(3)
