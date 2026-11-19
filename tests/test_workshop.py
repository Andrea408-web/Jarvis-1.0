import unittest
from backend.workshop import DEFAULT,design,blueprint,validate
class WorkshopTests(unittest.TestCase):
 def test_wood_light_request_has_measured_parts_and_schedule(self):
  data=design({'spec':DEFAULT,'request':'Ich will etwas aus Holz bauen das leuchtet, dreißig Zentimeter breit, in vier Tagen'})
  self.assertEqual(data['spec']['width'],300);self.assertEqual(data['spec']['days'],4);self.assertEqual(len(data['parts']),7);self.assertEqual(data['parts'][0]['size'],[300,12,100]);self.assertEqual(data['schedule'][-1]['day'],4);self.assertTrue(any(p['material']=='light'for p in data['parts']));self.assertIn('5-V',data['steps'][4])
 def test_material_and_changes_preserve_previous_dimensions(self):
  data=design({'spec':DEFAULT,'request':'aus Metall, breiter'});self.assertEqual(data['spec']['thickness'],2);self.assertEqual(data['spec']['width'],288);self.assertEqual(data['spec']['height'],180)
 def test_all_templates_produce_positive_size_parts_and_matching_list(self):
  for template in ['light','box','stand','shelf']:
   for material,t in [('wood',12),('metal',2),('plastic',5)]:
    data=blueprint(validate({**DEFAULT,'template':template,'material':material,'thickness':t}));self.assertEqual([p['size']for p in data['parts']],[p['size']for p in data['supplies']]);self.assertTrue(all(all(n>0 for n in p['size'])for p in data['parts']))
 def test_invalid_dimensions_and_unknown_wishes_never_silently_succeed(self):
  for change in [{'width':float('nan')},{'days':True},{'width':-1},{'thickness':30,'width':100},{'material':[]},{'template':'rocket'}]:
   with self.subTest(change=change),self.assertRaises(ValueError):design({'spec':{**DEFAULT,**change},'request':''})
  for request in ['Baue mir einen funktionierenden Sportwagen','Ich will ein Flugzeug aus Holz in 4 Tagen bauen']:
   with self.assertRaises(ValueError):design({'spec':DEFAULT,'request':request})
 def test_automatic_mode_makes_material_and_dimension_choices(self):
  data=design({'spec':DEFAULT,'request':'Ich will eine moderne Lampe bauen','automatic':True});self.assertTrue(data['automatic']);self.assertEqual(data['spec']['depth'],145);self.assertEqual(data['spec']['width'],220);self.assertTrue(data['decisions']);self.assertEqual(data['spec']['variant'],'desk');self.assertTrue(any(p.get('shape')=='cylinder'for p in data['parts']))
 def test_automatic_mode_never_replaces_explicit_material_or_dimensions(self):
  data=design({'spec':DEFAULT,'request':'Ich will eine Lampe aus Metall, 30 cm breit, in vier Tagen','automatic':True});self.assertEqual(data['spec']['width'],300);self.assertEqual(data['spec']['material'],'metal');self.assertEqual(data['spec']['thickness'],2);self.assertEqual(data['spec']['days'],4)
 def test_delegation_works_without_item_by_item_instructions(self):
  data=design({'spec':DEFAULT,'request':'Übernimm den Entwurf und mach ihn schöner','automatic':True});self.assertIn('vorgeschlagen',data['reply']);self.assertTrue(any(p['material']=='diffuser'for p in data['parts']))
  with self.assertRaises(ValueError):design({'spec':DEFAULT,'request':'Ich will einen Sportwagen aus Metall bauen','automatic':True})

 def test_alternative_request_changes_the_actual_part_dimensions(self):
  data=design({'spec':DEFAULT,'request':'Übernimm den Entwurf und zeig mir eine Alternative','automatic':True});self.assertEqual(data['spec']['width'],220);self.assertEqual(data['spec']['height'],320);self.assertEqual(data['parts'][0]['size'][0],220)

 def test_new_project_with_relative_clause_resets_alternative_defaults(self):
  alt=design({'spec':DEFAULT,'request':'Übernimm den Entwurf und zeig eine Alternative','automatic':True})
  data=design({'spec':alt['spec'],'request':'Ich will ein Leuchtpaneel aus Holz, 30 cm breit, in 4 Tagen','automatic':True});self.assertEqual(data['spec']['depth'],70);self.assertEqual(data['spec']['width'],300)
