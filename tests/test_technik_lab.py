"""Provided practical guides remain independent of inference and completion claims."""
import unittest
from backend.technik_lab import project
class TechnikLabTests(unittest.TestCase):
 def test_each_project_contains_materials_actions_checks_and_limits(self):
  for ident in ['stand','gripper','light']:
   with self.subTest(ident=ident):
    data=project({'id':ident});self.assertTrue(data['provided']);self.assertGreaterEqual(len(data['steps']),5);self.assertTrue(data['materials']);self.assertTrue(data['tools']);self.assertTrue(data['limits'])
    for step in data['steps']:self.assertTrue(step['title']);self.assertGreater(len(step['text']),50);self.assertTrue(step['check'])
 def test_templates_are_measurable_and_do_not_claim_electronics_or_vision(self):
  self.assertIn('80, 160 und 240',' '.join(s['text']for s in project({'id':'stand'})['steps']))
  self.assertIn('100 mm',' '.join(s['text']for s in project({'id':'gripper'})['steps']))
  light=project({'id':'light'});self.assertIn('Herstellerangaben',str(light));self.assertIn('unbeleuchtet',str(light));self.assertIn('Keine selbst gebaute Elektronik',str(light))
 def test_invalid_requests_and_unknown_ids_are_rejected(self):
  for body in [None,[],{}, {'id':1},{'id':'nope'},{'id':'stand','execute':True}]:
   with self.subTest(body=body),self.assertRaises(ValueError):project(body)
 def test_results_are_independent_and_aliases_are_compatible(self):
  first=project({'id':'stand'});first['steps'].clear();self.assertGreater(len(project({'id':'phone-stand'})['steps']),0)
