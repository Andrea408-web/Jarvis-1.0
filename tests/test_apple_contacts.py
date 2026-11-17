"""Explicit one-person Apple selection; no contact persistence or free-form script."""
import json,tempfile,unittest
from unittest.mock import Mock,patch
from backend import apple_contacts as apple
class AppleContactTests(unittest.TestCase):
 def test_unsupported_platform_does_not_start_process(self):
  with patch.object(apple.platform,'system',return_value='Linux'),patch.object(apple.subprocess,'run') as run:
   with self.assertRaises(ValueError):apple.selected()
   run.assert_not_called()
 def test_only_selected_contact_and_constant_script(self):
  result=Mock(returncode=0,stdout=json.dumps({'selection':True,'name':'Private Example','phones':['+49 000 111'],'emails':['private@example.com']}))
  with patch.object(apple.platform,'system',return_value='Darwin'),patch.object(apple.subprocess,'run',return_value=result) as run:
   p=apple.selected();self.assertTrue(p['temporary']);self.assertEqual(p['name'],'Private Example');self.assertNotIn('id',p);self.assertEqual(run.call_args.args[0],['/usr/bin/osascript','-l','JavaScript','-']);self.assertEqual(run.call_args.kwargs['input'],apple.SCRIPT);self.assertNotIn('every person',apple.SCRIPT)
 def test_missing_selection_and_permission_errors_do_not_expose_output(self):
  for result in [Mock(returncode=1,stdout='private',stderr='Private Error'),Mock(returncode=0,stdout='{"selection":false}'),Mock(returncode=0,stdout='bad Private data')]:
   with patch.object(apple.platform,'system',return_value='Darwin'),patch.object(apple.subprocess,'run',return_value=result):
    with self.assertRaises(ValueError) as caught:apple.selected()
    self.assertNotIn('Private',str(caught.exception))
