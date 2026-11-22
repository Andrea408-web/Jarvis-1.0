"""IRIS is the conversational name of the compatible stored aeris mode."""
import tempfile,unittest
from unittest.mock import Mock,patch
from backend.server import Application
from backend import persona
from backend.video_call import answer

class IrisIdentityTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.app=Application(self.tmp.name)
  self.addCleanup(self.app.office.stop);self.addCleanup(self.app.workshop.stop);self.addCleanup(self.app.desktop.stop)
 def test_stored_legacy_mode_is_named_iris_without_changing_identity_key(self):
  self.app.store.update_settings({'assistant_identity':'aeris'})
  self.assertEqual(persona.name(self.app.store),'IRIS');self.assertEqual(self.app.store.settings()['assistant_identity'],'aeris')
  self.assertIn('Du bist IRIS',persona.instruction(self.app.store));self.assertIn('Techniklabor',persona.instruction(self.app.store))
 def test_iris_repairs_old_names_but_jarvis_and_astra_remain_distinct(self):
  self.app.store.update_settings({'assistant_identity':'aeris'})
  for identity in ['aeris','AERIS','iris','IRIS']:
   with self.subTest(identity=identity):self.assertEqual(persona.correct_identity('Ich bin AERIS. Hier ist Jarvis.',self.app.store,'Hallo',identity=identity),'Ich bin IRIS. Hier ist IRIS.')
  self.assertEqual(persona.correct_identity('Ich bin IRIS.',self.app.store,'Hallo',identity='jarvis'),'Ich bin JARVIS.')
  self.assertEqual(persona.correct_identity('Ich bin IRIS.',self.app.store,'Hallo',identity='astra'),'Ich bin ASTRA.')
 def test_device_chat_uses_iris_persona_local_transport_and_does_not_write_history(self):
  self.app.store.update_settings({'ai_provider':'llamacpp','assistant_identity':'astra'})
  transport=Mock(return_value={'choices':[{'finish_reason':'stop','message':{'content':'Ich bin AERIS. Wir können deine Idee besprechen.'}}]})
  self.app.llamacpp.endpoint_transport=transport
  with patch.object(self.app.store,'append')as append:
   data=answer(self.app,{'text':'Wer bist du?','history':[]},identity='aeris',text_only=True)
  self.assertIn('Ich bin IRIS.',data['reply']);self.assertIn('Du bist IRIS',transport.call_args.args[1]['messages'][0]['content']);append.assert_not_called();self.assertEqual(self.app.store.history(),[]);self.assertEqual(self.app.store.settings()['assistant_identity'],'astra')
 def test_explicit_named_recipient_is_not_replaced_with_user_address(self):
  self.app.store.update_settings({'assistant_identity':'aeris'})
  result=persona.correct_identity('Hallo Iris, hier ist eine Idee.',self.app.store,'Schreibe einen Brief an Iris')
  self.assertIn('Hallo Iris',result)
