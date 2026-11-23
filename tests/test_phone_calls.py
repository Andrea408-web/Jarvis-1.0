"""Native telephone handoff validation; never place a real call in tests."""
import subprocess,unittest
from unittest.mock import Mock,patch
from backend import phone_calls

class PhoneCallTests(unittest.TestCase):
 def test_number_normalization_keeps_only_explicit_dial_number(self):
  self.assertEqual(phone_calls.normalize_number('+49 (30) 123-456'),'+4930123456')
  self.assertEqual(phone_calls.normalize_number('０３０１２３４５６'),'030123456')
  for value in ['',None,True,'+','12','1'*16,'tel:+4930123456','+49;rm -rf /','*123#','123 ext 45','javascript:alert(1)','12\n345','+49?body=x']:
   with self.subTest(value=value),self.assertRaises(ValueError):phone_calls.normalize_number(value)
 def test_mac_handoff_uses_fixed_argv_and_never_reports_connected(self):
  with patch.object(phone_calls.platform,'system',return_value='Darwin'),patch.object(phone_calls.subprocess,'run',return_value=Mock(returncode=0))as run:
   result=phone_calls.start({'number':'+49 (30) 123-456'})
  run.assert_called_once_with(['/usr/bin/open','tel:+4930123456'],capture_output=True,timeout=10)
  self.assertEqual(result['state'],'handoff');self.assertNotIn('connected',result)
 def test_facetime_is_explicit_distinct_method(self):
  with patch.object(phone_calls.platform,'system',return_value='Darwin'),patch.object(phone_calls.subprocess,'run',return_value=Mock(returncode=0))as run:
   phone_calls.start({'number':'030123456','method':'facetime'})
  self.assertEqual(run.call_args.args[0],['/usr/bin/open','facetime-audio:030123456'])
 def test_invalid_bodies_and_non_mac_never_launch(self):
  for body in [{},{'number':'030123456','method':'other'},{'number':'030123456','confirmed':True},None]:
   with self.subTest(body=body),patch.object(phone_calls.subprocess,'run')as run:
    with self.assertRaises(ValueError):phone_calls.start(body)
    run.assert_not_called()
  with patch.object(phone_calls.platform,'system',return_value='Linux'),patch.object(phone_calls.subprocess,'run')as run:
   with self.assertRaises(ValueError):phone_calls.start({'number':'030123456'})
   run.assert_not_called()
 def test_failures_do_not_expose_process_output(self):
  for outcome in [Mock(returncode=1,stdout='private',stderr='private'),OSError('private'),subprocess.TimeoutExpired('private',10)]:
   with self.subTest(outcome=outcome),patch.object(phone_calls.platform,'system',return_value='Darwin'),patch.object(phone_calls.subprocess,'run',side_effect=outcome if isinstance(outcome,Exception)else None,return_value=outcome):
    with self.assertRaises(ValueError)as caught:phone_calls.start({'number':'030123456'})
    self.assertNotIn('private',str(caught.exception))
