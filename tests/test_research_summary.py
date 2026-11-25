import json,tempfile,unittest
from unittest.mock import Mock
from backend.local_ai import LocalClient
from backend.llamacpp import LlamaCppClient
from backend.server import Application
from backend.web_assistant import SEARCH

class ResearchSummaryTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.app=Application(self.temp.name)
 def tearDown(self):
  self.app.office.stop();self.app.workshop.stop();self.app.desktop.stop();self.temp.cleanup()
 def test_edit_keeps_referent_but_independent_task_drops_old_context(self):
  for text in ['Mach es kürzer','Schreibe daraus eine Einkaufsliste','Mach die Antwort einfacher']:
   with self.subTest(text=text):
    self.app.store.clear_all_history();self.app.store.append('user','Erkläre mir eine Solarlampe');self.app.store.append('assistant','Du brauchst ein Solarmodul, einen Laderegler und eine LED.')
    transport=Mock(return_value={'done':True,'message':{'content':'Eine Solarlampe lädt tagsüber.'}})
    LocalClient(self.app.store,transport).chat(text)
    self.assertEqual(len(transport.call_args.args[1]['messages']),4)
  transport=Mock(return_value={'done':True,'message':{'content':'Milch und Brot.'}})
  LocalClient(self.app.store,transport).chat('Schreibe eine Einkaufsliste')
  self.assertEqual(len(transport.call_args.args[1]['messages']),2)
 def test_bounded_summary_has_no_history_side_effects_and_rejects_tools_and_bad_citations(self):
  for reply in [{'content':'Wichtig ist der Laderegler. [1]'}, {'content':'Nicht belegbar. [8]'}, {'content':'Keine Quellen'}, {'content':'Erledigt [1]','tool_calls':[{'name':'open_app'}]}]:
   transport=Mock(return_value={'done':True,'message':reply});client=LocalClient(self.app.store,transport)
   result=client.summarize_sources('Was brauche ich?', [{'title':'Quelle','text':'Laderegler '+('a'*4000)}])
   self.assertEqual(isinstance(result,str),reply['content']=='Wichtig ist der Laderegler. [1]')
   payload=transport.call_args.args[1];self.assertEqual(len(json.loads(payload['messages'][1]['content'])['quellen'][0]['text']),700);self.assertEqual(self.app.store.history(),[])
 def test_llamacpp_summary_uses_only_fixed_local_completion_transport(self):
  transport=Mock(return_value={'choices':[{'finish_reason':'stop','message':{'content':'Du brauchst einen Laderegler. [1]'}}]})
  result=LlamaCppClient(self.app.store,transport).summarize_sources('Was brauche ich?', [{'title':'Quelle','text':'Du brauchst einen Laderegler.'}])
  self.assertIn('[1]',result);self.assertEqual(transport.call_args.args[0],'/v1/chat/completions')
 def test_web_uses_summary_and_sources_but_falls_back_if_unavailable(self):
  self.app.store.update_settings({'ai_provider':'llamacpp'})
  def reader(url):
   return ('<a class="result__a" href="https://example.com/solar">Quelle</a>' if url.startswith(SEARCH) else '<p>Für die Solarlampe brauchst du ein Solarmodul und einen passenden Laderegler für die Batterie.</p>'),url
  self.app.web.reader=reader;client=Mock();self.app.selected_client=Mock(return_value=client)
  client.summarize_sources.return_value='Für die Batterie brauchst du einen passenden Laderegler. [1]'
  result=self.app.chat('Recherchiere eine Solarlampe')
  self.assertIn('KI-Zusammenfassung',result['reply']);self.assertEqual(result['sources'][0]['url'],'https://example.com/solar')
  client.summarize_sources.return_value=None
  result=self.app.chat('Recherchiere eine Solarlampe');self.assertIn('Quellenauszüge',result['reply']);self.assertNotIn('hier ist die lokale KI-Zusammenfassung',result['reply'])
