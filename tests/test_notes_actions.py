import tempfile,threading,unittest
from unittest.mock import Mock,patch
from backend.server import Application
from backend.notes import request,create,SCRIPT
from backend.local_ai import LocalClient

class NotesTests(unittest.TestCase):
 def test_notes_intent_preserves_3d_or_game_words_as_content(self):
  self.assertEqual(request('Astra, erstelle eine Notiz: 3D-Modell und Videospiel später')['body'],'3D-Modell und Videospiel später')
  self.assertIsNone(request('Öffne Notizen'))
  self.assertIsNone(request('Was können Notizen?'))
  self.assertIsNone(request('Tippe Hallo in Notizen'))
  self.assertIsNone(request('Erstelle einen 3D-Roboter'))
  self.assertIsNone(request('Erstelle eine Notiz')['body'])
 def test_no_language_model_is_used_for_note_or_missing_content(self):
  with tempfile.TemporaryDirectory() as folder:
   app=Application(folder);app.selected_client=Mock(side_effect=AssertionError('No language model for notes'))
   try:
    app.store.append('user','Baue ein 3D-Spiel');app.store.append('assistant','Hier ist dein Videospiel')
    reply=app.chat('Erstelle eine Notiz');self.assertIn('Was soll',reply['reply']);self.assertNotIn('desktop',reply)
    result=app.chat('Erstelle eine Notiz: Morgen Milch kaufen');self.assertEqual(result['desktop']['plan']['kind'],'note');self.assertEqual(result['desktop']['plan']['note']['body'],'Morgen Milch kaufen');self.assertNotIn('note_id',result['desktop']['plan']);app.selected_client.assert_not_called()
   finally:app.office.stop()
 @patch('backend.notes.platform.system',return_value='Darwin')
 def test_native_notes_uses_fixed_script_and_escaped_data(self,_):
  with patch('backend.notes.subprocess.run',return_value=Mock(returncode=0,stdout='x-coredata://fixture/ICNote/p1\n')) as run:
   result=create('Test','<script>\n"Hallo"');self.assertEqual(result['id'],'x-coredata://fixture/ICNote/p1');args=run.call_args.args[0];self.assertEqual(args[:3],['/usr/bin/osascript','-e',SCRIPT]);self.assertIn('&lt;script&gt;',args[-1]);self.assertNotIn('<script>',args[-1])
 @patch('backend.notes.platform.system',return_value='Darwin')
 def test_failure_or_empty_ack_is_not_a_created_note(self,_):
  for result in [Mock(returncode=1,stdout=''),Mock(returncode=0,stdout=''),Mock(returncode=0,stdout='okay')]:
   with patch('backend.notes.subprocess.run',return_value=result),self.assertRaises(ValueError):create('Test','Hallo')
 def test_worker_reports_done_only_after_real_adapter_ack(self):
  with tempfile.TemporaryDirectory() as folder:
   app=Application(folder)
   try:
    plan=app.desktop.prepare({'goal':'Schreibe eine Notiz: Milch kaufen'})['plan']
    with patch('backend.desktop.create_note',return_value={'id':'x-coredata://test/ICNote/p1','message':'Bestätigte Notiz'}) as native:
     app.desktop.start(plan['id']);app.desktop.thread.join(5);native.assert_called_once_with(title='Milch kaufen',body='Milch kaufen')
     saved=app.desktop.snapshot()['plan'];self.assertEqual(saved['state'],'done');self.assertIn('note_id',saved)
   finally:app.desktop.stop();app.office.stop()
 def test_new_independent_task_omits_old_game_and_3d_context(self):
  with tempfile.TemporaryDirectory() as folder:
   app=Application(folder)
   try:
    app.store.append('user','Baue ein 3D-Modell');app.store.append('assistant','Ich biete dir ein Videospiel an')
    seen=[]
    client=LocalClient(app.store,lambda path,payload:(seen.append(payload) or {'done':True,'message':{'content':'Ein neuer Entwurf'}}))
    client.chat('Schreibe eine Einkaufsliste');self.assertEqual(len(seen[0]['messages']),2);self.assertEqual(seen[0]['messages'][-1]['content'],'Schreibe eine Einkaufsliste');self.assertEqual(len(app.store.history()),4)
   finally:app.office.stop()
