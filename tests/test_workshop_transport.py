import io,json,unittest,urllib.error
from unittest.mock import Mock,patch
from backend.llamacpp import request_local
from backend.providers import ProviderError

class WorkshopTransportTests(unittest.TestCase):
 def test_schema_and_context_failures_have_actionable_messages(self):
  for detail,word in [('Failed to parse json schema grammar','strukturierte'),('request exceeds context size','Kontext')]:
   error=urllib.error.HTTPError('http://127.0.0.1:8081',400,'bad request',{},io.BytesIO(json.dumps({'error':{'message':detail}}).encode()))
   opener=Mock();opener.open.side_effect=error
   with patch('backend.llamacpp.urllib.request.build_opener',return_value=opener),self.assertRaisesRegex(ProviderError,word)as result:request_local('/v1/chat/completions',{'messages':[]})
   self.assertEqual(result.exception.status,422)
 def test_slow_model_is_not_reported_as_missing_installation(self):
  opener=Mock();opener.open.side_effect=TimeoutError()
  with patch('backend.llamacpp.urllib.request.build_opener',return_value=opener),self.assertRaisesRegex(ProviderError,'120 Sekunden')as result:request_local('/v1/chat/completions',{'messages':[]})
  self.assertEqual(result.exception.status,504)
 def test_unexpected_http_error_body_does_not_escape_as_traceback(self):
  error=urllib.error.HTTPError('http://127.0.0.1:8081',400,'bad request',{},io.BytesIO(b'[]'));opener=Mock();opener.open.side_effect=error
  with patch('backend.llamacpp.urllib.request.build_opener',return_value=opener),self.assertRaises(ProviderError):request_local('/v1/chat/completions',{'messages':[]})
