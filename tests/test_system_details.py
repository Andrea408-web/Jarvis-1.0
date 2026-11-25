import unittest
from unittest.mock import patch
from backend import system_info as info

class SystemDetailsTests(unittest.TestCase):
 def test_mac_memory_categories_and_last_cpu_sample_are_real_measurements(self):
  vm='Mach Virtual Memory Statistics: (page size of 16384 bytes)\nPages free: 10.\nPages inactive: 20.\nPages speculative: 5.\nPages wired down: 30.\nPages occupied by compressor: 7.\n'
  def command(args):
   if args[-1]=='machdep.cpu.brand_string':return 'Test CPU'
   if args[-1]=='hw.memsize':return str(16384*1000)
   if args[0].endswith('vm_stat'):return vm
   if args[0].endswith('top'):return 'CPU usage: 1.0% user, 2.0% sys, 97.0% idle\nCPU usage: 10.0% user, 5.0% sys, 85.0% idle'
   return None
  with patch.object(info,'_command',side_effect=command):data=info._mac_metrics()
  self.assertEqual(data['memory_available_bytes'],35*16384);self.assertEqual(data['memory_free_bytes'],15*16384);self.assertEqual(data['memory_compressed_bytes'],7*16384);self.assertEqual(data['memory_wired_bytes'],30*16384)
  self.assertEqual(data['cpu_percent'],15);self.assertEqual(data['cpu_user_percent'],10);self.assertEqual(data['cpu_system_percent'],5);self.assertEqual(data['cpu_idle_percent'],85)
 def test_missing_mac_fields_are_not_fabricated_as_zero(self):
  def command(args):
   if args[-1]=='hw.memsize':return '16384000'
   if args[0].endswith('vm_stat'):return 'Mach Virtual Memory Statistics: (page size of 16384 bytes)\nPages free: 10.\nPages inactive: 20.\n'
   return None
  with patch.object(info,'_command',side_effect=command):data=info._mac_metrics()
  self.assertIsNone(data['memory_compressed_bytes']);self.assertIsNone(data['memory_wired_bytes']);self.assertNotIn('cpu_percent',data)
 def test_linux_cpu_user_system_idle_are_deltas_not_lifetime_averages(self):
  readings=iter(['cpu 100 0 40 500 10 5 5 0','cpu 130 0 50 560 10 5 5 0'])
  def read(path,*args,**kwargs):
   name=str(path)
   if name=='/proc/stat':return next(readings)
   if name=='/proc/meminfo':return 'MemTotal: 1000 kB\nMemAvailable: 600 kB\nMemFree: 200 kB'
   raise OSError('unavailable')
  with patch.object(info,'_previous_cpu',None),patch.object(info.Path,'read_text',read):
   first=info._linux_metrics();second=info._linux_metrics()
  self.assertNotIn('cpu_percent',first);self.assertEqual(second['cpu_percent'],40);self.assertEqual(second['cpu_user_percent'],30);self.assertEqual(second['cpu_system_percent'],10);self.assertEqual(second['cpu_idle_percent'],60);self.assertEqual(second['memory_free_bytes'],200*1024)
