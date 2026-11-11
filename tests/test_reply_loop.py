import tempfile,unittest
from unittest.mock import Mock
from backend.server import Application
from backend.local_ai import LocalClient

BAD='Master, für eins plus eins zuverlässig bestätigen.'
class ReplyLoopTests(unittest.TestCase):
 def setUp(self):self.temp=tempfile.TemporaryDirectory();self.app=Application(self.temp.name);self.app.store.update_settings({'ai_provider':'ollama'})
 def tearDown(self):self.app.office.stop();self.temp.cleanup()
 def test_bad_old_turn_is_excluded_and_regenerated_bad_reply_is_not_repeated(self):
  for text,reply in [('Was kann ich machen?',BAD),('Bestätigen',BAD)]:self.app.store.append('user',text);self.app.store.append('assistant',reply)
  transport=Mock(return_value={'done':True,'message':{'content':BAD}});self.app.local_ai.transport=transport
  result=self.app.chat('Was kann ich machen?');self.assertNotIn('eins plus eins',result['reply']);self.assertNotIn('bestätigen',result['reply']);self.assertIn('Kreatives',result['reply'])
  payload=transport.call_args.args[1];self.assertEqual(len(payload['messages']),2);self.assertEqual(payload['messages'][-1]['content'],'Was kann ich machen?')
  confirmed=self.app.chat('Bestätigen');self.assertIn('keine Aktion',confirmed['reply']);self.assertNotEqual(confirmed['reply'],result['reply']);self.assertEqual(transport.call_count,1);self.assertIsNone(self.app.desktop.plan)
 def test_valid_answer_and_relevant_context_are_preserved(self):
  self.app.store.append('user','Ich lerne Gitarre.');self.app.store.append('assistant','Wir können Akkorde üben.')
  transport=Mock(return_value={'done':True,'message':{'content':'Übe zuerst einen einfachen Akkordwechsel, Master.'}})
  result=LocalClient(self.app.store,transport).chat('Wie übe ich das?');self.assertIn('Akkordwechsel',result['reply']);self.assertEqual(len(transport.call_args.args[1]['messages']),4)
 def test_real_note_content_and_background_task_text_are_not_changed(self):
  self.app.chat('Erstelle eine Notiz');self.assertEqual(self.app.chat('Bestätigen')['desktop']['plan']['note']['body'],'Bestätigen')
  transport=Mock(return_value={'done':True,'message':{'content':BAD}})
  self.assertEqual(LocalClient(self.app.store,transport).chat('Zitiere den Satz',conversation='agent_test')['reply'],BAD)
 def test_a_real_prepared_action_is_not_claimed_executed_by_a_bare_confirmation(self):
  self.app.desktop.prepare({'goal':'Öffne Finder'});result=self.app.chat('Bestätigen');self.assertIn('Start-',result['reply']);self.assertEqual(self.app.desktop.plan['state'],'review')
