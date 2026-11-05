import tempfile,threading,unittest
from backend.server import Application
from backend.local_ai import LocalClient

class DialogueTests(unittest.TestCase):
 def setUp(self):self.temp=tempfile.TemporaryDirectory();self.app=Application(self.temp.name)
 def tearDown(self):self.app.office.stop();self.temp.cleanup()
 def test_note_question_accepts_next_plain_reply_without_language_model(self):
  self.app.selected_client=lambda:(_ for _ in ()).throw(AssertionError('No language model'))
  result=self.app.chat('Erstelle eine Notiz');self.assertEqual(result['pending']['kind'],'note')
  result=self.app.chat('morgen Milch kaufen');self.assertEqual(result['desktop']['plan']['note']['body'],'morgen Milch kaufen');self.assertIsNone(self.app.dialogue.get())
 def test_question_for_other_apps_and_websites(self):
  self.assertEqual(self.app.chat('Astra, öffne eine App')['pending']['kind'],'app')
  self.assertEqual(self.app.chat('Spotify')['desktop']['plan']['steps'],[{'type':'open','app':'Spotify'}])
  self.assertEqual(self.app.chat('Öffne eine Webseite')['pending']['kind'],'website')
  self.assertEqual(self.app.chat('youtube.com')['desktop']['plan']['steps'],[{'type':'website','url':'https://youtube.com'}])
 def test_typing_followup_app_is_a_concrete_input_plan(self):
  self.assertEqual(self.app.chat('Tippe Hallo Master')['pending']['kind'],'typing_app')
  result=self.app.chat('Notizen');self.assertEqual(result['desktop']['plan']['steps'][-1],{'type':'text','text':'Hallo Master'})
 def test_clear_removes_all_model_histories_pending_name_and_queued_messages(self):
  self.app.store.append('user','Blender');self.app.store.append('assistant','Spiel','astra-desktop-plan');self.app.store.update_settings({'user_name':'Maxine'})
  self.app.chat('Erstelle eine Notiz');self.app.desktop.companion({'command':'send','text':'alter Auftrag'})
  self.app.chat('Jarvis, vergiss alles');self.assertEqual(self.app.store.history(),[]);self.assertEqual(self.app.store.history('astra-desktop-plan'),[]);self.assertEqual(self.app.store.settings()['user_name'],'');self.assertIsNone(self.app.dialogue.get());self.assertEqual(self.app.desktop.commands,[])
 def test_late_model_response_cannot_restore_deleted_context(self):
  started=threading.Event();release=threading.Event();errors=[]
  def transport(*a):started.set();release.wait(3);return {'done':True,'message':{'content':'Alte Antwort'}}
  def worker():
   try:LocalClient(self.app.store,transport).chat('Hallo')
   except Exception as error:errors.append(str(error))
  thread=threading.Thread(target=worker);thread.start();self.assertTrue(started.wait(1));self.app.clear_chat();release.set();thread.join(3);self.assertTrue(errors);self.assertEqual(self.app.store.history(),[])
 def test_cancel_followup_does_not_turn_into_note_content(self):
  self.app.chat('Erstelle eine Notiz');self.app.chat('Abbrechen');self.assertIsNone(self.app.dialogue.get());self.assertIsNone(self.app.desktop.snapshot()['plan'])
