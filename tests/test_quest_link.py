import json,subprocess,unittest
from unittest.mock import Mock,patch
from backend.quest_link import connect
class QuestLinkTests(unittest.TestCase):
 def test_usb_forward_uses_only_known_local_port_and_verified_meta_device(self):
  response=Mock();response.__enter__=Mock(return_value=response);response.__exit__=Mock(return_value=False);response.read.return_value=json.dumps({'token':'not-to-print'}).encode();opener=Mock();opener.open.return_value=response
  results=[Mock(stdout='List of devices attached\nQUEST1\tdevice\n'),Mock(stdout='Oculus\n'),Mock(stdout=''),Mock(stdout='Starting')]
  with patch('backend.quest_link.find_adb',return_value='/test/adb'),patch('backend.quest_link.subprocess.run',side_effect=results) as run,patch('backend.quest_link.urllib.request.build_opener',return_value=opener):result=connect()
  self.assertNotIn('not-to-print',result);self.assertIn('localhost:8765',result);self.assertEqual(run.call_args_list[2].args[0],['/test/adb','-s','QUEST1','reverse','tcp:8765','tcp:8765']);self.assertIn('com.oculus.browser',run.call_args.args[0]);opener.open.assert_called_once_with('http://127.0.0.1:8765/api/session',timeout=5)
 def test_no_forward_for_unapproved_multiple_or_non_meta_devices(self):
  for devices in ['List\nQ\tunauthorized\n','List\nQ\tdevice\nB\tdevice\n','List\n']:
   with patch('backend.quest_link.find_adb',return_value='/test/adb'),patch('backend.quest_link.subprocess.run',return_value=Mock(stdout=devices)) as run,self.assertRaises(ValueError):connect()
   self.assertEqual(run.call_count,1)
  with patch('backend.quest_link.find_adb',return_value='/test/adb'),patch('backend.quest_link.subprocess.run',side_effect=[Mock(stdout='List\nPHONE\tdevice\n'),Mock(stdout='Other\n')]) as run,self.assertRaisesRegex(ValueError,'Meta'):connect()
  self.assertEqual(run.call_count,2)
 def test_disconnect_removes_forward_without_network_or_browser(self):
  with patch('backend.quest_link.find_adb',return_value='/test/adb'),patch('backend.quest_link.subprocess.run',side_effect=[Mock(stdout='List\nQ\tdevice\n'),Mock(stdout='Meta'),Mock(stdout='')]) as run,patch('backend.quest_link.urllib.request.build_opener') as network:connect(True)
  self.assertEqual(run.call_args.args[0][-3:],['reverse','--remove','tcp:8765']);network.assert_not_called()
