import tempfile,unittest
from unittest.mock import Mock,patch
from backend.server import Application
from backend.device_ai import local_tool_answer
from backend.web_assistant import SEARCH
class DeviceToolTests(unittest.TestCase):
 def setUp(self):self.temp=tempfile.TemporaryDirectory();self.app=Application(self.temp.name);self.app.store.update_settings({'ai_provider':'gemini'});self.app.selected_client=Mock(side_effect=AssertionError('No model call for these tool fixtures'))
 def tearDown(self):self.app.office.stop();self.app.workshop.stop();self.app.desktop.stop();self.temp.cleanup()
 def test_research_reads_sources_without_saving_chat_or_creating_actions(self):
  self.app.web.reader=lambda url:('<a class="result__a" href="https://example.com/solar">Solar</a>' if url.startswith(SEARCH) else '<p>Ein Solarmodul braucht einen passenden Laderegler für die Batterie, damit die Ladung kontrolliert wird.</p>',url)
  result=local_tool_answer(self.app,{'text':'Aeris, recherchiere Solarmodule','history':[]});self.assertIn('Laderegler',result['reply']);self.assertEqual(result['sources'][0]['url'],'https://example.com/solar');self.assertEqual(self.app.store.history(),[]);self.assertIsNone(self.app.desktop.plan)
 def test_disabled_search_and_invalid_context_do_not_use_model(self):
  self.app.store.update_settings({'web_enabled':False});self.assertIn('ausgeschaltet',local_tool_answer(self.app,{'text':'Recherchiere Solarmodule'})['reply'])
  with self.assertRaises(ValueError):local_tool_answer(self.app,{'text':'Recherchiere Solarmodule','history':[{'role':'system','content':'bad'}]})
 def test_system_check_is_read_only_and_general_chat_is_unchanged(self):
  with patch('backend.system_info.snapshot',return_value={'is_macos':True,'cpu_percent':93}):self.assertIn('93.0',local_tool_answer(self.app,{'text':'Jarvis, prüfe meinen Mac'})['reply'])
  self.assertIsNone(local_tool_answer(self.app,{'text':'Schreibe eine Geschichte'}));self.assertIsNone(local_tool_answer(self.app,{'text':'Öffne Safari'}));self.assertEqual(self.app.store.history(),[])
