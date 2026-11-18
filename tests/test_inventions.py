import copy,json,unittest
from types import SimpleNamespace
from backend.inventions import validate,design
SPEC={'title':'Durstsignal','purpose':'Eine Pflanze erinnert an Wasser.','how':'Ein Sensor liefert ein Signal an eine Anzeige.','components':[{'id':'sensor','name':'Feuchtesensor','purpose':'Feuchtigkeit messen'},{'id':'light','name':'Anzeige','purpose':'Hinweis zeigen'}],'links':[{'from':'sensor','to':'light','label':'Messsignal'}],'tests':['Messwerte mit trockener und feuchter Erde vergleichen.'],'limits':'Sensor und Stromversorgung müssen geprüft werden.'}
class InventionTests(unittest.TestCase):
 def test_concept_is_bounded_and_links_reference_existing_parts(self):
  self.assertEqual(validate(copy.deepcopy(SPEC)),SPEC)
  for mutate in [lambda s:s['links'][0].update(to='not-there'),lambda s:s.update(components=[]),lambda s:s['components'].append(s['components'][0]),lambda s:s.update(limits=''),lambda s:s.update(title='<script>'*100)]:
   spec=copy.deepcopy(SPEC);mutate(spec)
   with self.assertRaises(ValueError):validate(spec)
 def test_local_only_design_and_revision_with_no_chat_storage(self):
  calls=[];app=SimpleNamespace(store=SimpleNamespace(settings=lambda:{'ai_provider':'llamacpp','local_model':'x'}),code_room=SimpleNamespace(_generate=lambda *a,**k:(calls.append((a,k)),json.dumps(SPEC))[1]))
  result=design(app,{'idea':'Ein smarter Blumentopf','revision':'Ohne Akku','previous':SPEC});self.assertEqual(result['concept'],SPEC);self.assertTrue(calls[0][1]['structured']);self.assertIn('Ohne Akku',calls[0][0][1][-1]['content'])
  app.store.settings=lambda:{'ai_provider':'openai','local_model':'x'}
  with self.assertRaises(ValueError):design(app,{'idea':'x','revision':'','previous':None})
  self.assertEqual(len(calls),1)
  app.store.settings=lambda:{'ai_provider':'ollama','local_model':'remote-cloud:latest'}
  with self.assertRaises(ValueError):design(app,{'idea':'x','revision':'','previous':None})
  self.assertEqual(len(calls),1)
 def test_malformed_model_output_is_not_presented_as_a_sketch(self):
  app=SimpleNamespace(store=SimpleNamespace(settings=lambda:{'ai_provider':'llamacpp'}),code_room=SimpleNamespace(_generate=lambda *a,**k:'Auftrag erfüllt.'))
  with self.assertRaises(ValueError):design(app,{'idea':'Eine Erfindung','revision':'','previous':None})
