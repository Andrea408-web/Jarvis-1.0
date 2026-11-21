import tempfile,unittest
from unittest.mock import Mock
from backend.server import Application
from backend.persona import correct_identity,instruction
from backend.video_call import answer

class BuildIdentityTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.app=Application(self.tmp.name);self.addCleanup(self.app.office.stop);self.app.store.update_settings({'ai_provider':'llamacpp','assistant_identity':'astra','user_address':'Master'})
 def test_text_workspace_uses_requested_identity_not_underlying_model_or_other_mode(self):
  self.app.llamacpp.endpoint_transport=Mock(return_value={'choices':[{'finish_reason':'stop','message':{'content':'Ich bin ChatGPT. Wir können deine Idee besprechen.'}}]})
  data=answer(self.app,{'text':'Welche Funktionen könnte mein Bauprojekt haben?'},identity='jarvis',text_only=True);self.assertEqual(data['reply'],'Ich bin JARVIS. Wir können deine Idee besprechen.');prompt=self.app.llamacpp.endpoint_transport.call_args.args[1]['messages'][0]['content'];self.assertIn('lokales Baustudio',prompt);self.assertIn('andere KI-Anbieter',prompt)
 def test_model_and_quoted_names_are_not_silently_rewritten(self):
  store=self.app.store
  self.assertEqual(correct_identity('Ich bin Qwen.',store,'Welches Modell wird verwendet?',identity='jarvis'),'Ich bin Qwen.')
  self.assertEqual(correct_identity('Ich bin Claude.',store,'Zitiere den Satz Ich bin Claude',identity='jarvis'),'Ich bin Claude.')
  self.assertEqual(correct_identity('Ich bin Claude.',store,'Hilf mir bei einer Lampe',identity='jarvis'),'Ich bin JARVIS.')
  self.assertEqual(correct_identity('Ich bin ChatGPT.',store,'Baue ein eigenes 3D-Modell',identity='jarvis'),'Ich bin JARVIS.')
 def test_real_tool_capabilities_are_in_general_persona(self):
  text=instruction(self.app.store);self.assertIn('eigene 3D-Konzepte',text);self.assertIn('andere KI-Anbieter',text);self.assertIn('ASTRA',text)
