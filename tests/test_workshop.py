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
