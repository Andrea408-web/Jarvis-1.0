"""TV entry preserves private-device pairing and offers a short remote-friendly code."""
import unittest
from unittest.mock import Mock
from tests import test_server as http_tests
from backend.mobile import DeviceAuth

class TVTests(unittest.TestCase):
 setUp=http_tests.LiveServerTests.setUp
 stop_server=http_tests.LiveServerTests.stop_server
 request=http_tests.LiveServerTests.request
 def test_tv_info_is_authenticated_and_no_usb_install_claim(self):
  status,_,_=self.request('GET','/api/tv/info',token=False);self.assertEqual(status,401)
  status,data,headers=self.request('GET','/api/tv/info');self.assertEqual(status,200);self.assertTrue(data['requires_local_ai_server']);self.assertFalse(data['usb_autostart']);self.assertEqual(headers['Cache-Control'],'no-store')
 def test_unpaired_tv_serves_pairing_and_never_session_or_assets(self):
  self.server.device_auth=DeviceAuth()
  status,page,_=self.request('GET','/tv',token=False);self.assertEqual(status,200);self.assertIn(b'pair-form',page)
  for path in ['/api/session','/api/tv/info','/tv.js','/tv.css']:
   status,_,_=self.request('GET',path,token=False);self.assertEqual(status,401)
 def test_six_digit_pairing_allows_tv_after_pair_and_rejects_reuse(self):
  auth=DeviceAuth();auth.issue();code=auth.code;self.server.device_auth=auth
  status,data,headers=self.request('POST','/api/mobile/pair',{'ticket':code},token=False);self.assertEqual(status,200);self.assertTrue(data['ok']);cookie=headers['Set-Cookie'].split(';',1)[0]
  status,session,_=self.request('GET','/api/session',token=False,headers={'Cookie':cookie});self.assertEqual(status,200);self.assertTrue(session['remote_device'])
  status,data,_=self.request('GET','/api/tv/info',headers={'Cookie':cookie});self.assertEqual(status,200)
  status,_,_=self.request('POST','/api/mobile/pair',{'ticket':code},token=False);self.assertEqual(status,400)
 def test_mobile_start_adds_tv_ticket_urls_entry_and_existing_code(self):
  self.app.mobile.auth.code='123456';self.app.mobile.start=Mock(return_value={'url':'https://jarvis.local:8766/#pair=secret','ip_url':'https://192.168.1.5:8766/#pair=secret','fingerprint':'example'})
  status,data,_=self.request('POST','/api/mobile/start',{});self.assertEqual(status,200);self.assertEqual(data['tv_url'],'https://jarvis.local:8766/tv#pair=secret');self.assertEqual(data['tv_ip_url'],'https://192.168.1.5:8766/tv#pair=secret');self.assertEqual(data['tv_entry_url'],'https://192.168.1.5:8766/tv');self.assertEqual(data['tv_code'],'123456')
 def test_paired_device_cannot_issue_new_tv_pairing_ticket(self):
  auth=DeviceAuth();auth.issue();token=auth.pair(auth.code);self.server.device_auth=auth;self.app.mobile.start=Mock()
  status,_,_=self.request('POST','/api/mobile/start',{},headers={'Cookie':'jarvis_device='+token});self.assertEqual(status,403);self.app.mobile.start.assert_not_called()

class TVLauncherTests(unittest.TestCase):
 def test_easy_tv_entry_forwards_mode_without_initializing_second_app(self):
  from unittest.mock import patch
  from backend.server import main
  with patch('backend.easy_start.run')as run,patch('backend.server.Application')as app:
   main(['--easy-local','--open-tv'])
  run.assert_called_once_with(setup=False,tv=True);app.assert_not_called()
 def test_easy_tv_start_opens_tv_only_after_real_model_reply(self):
  from pathlib import Path
  from unittest.mock import patch
  from backend import easy_start
  child=Mock();child.poll.return_value=None
  with patch.object(easy_start.easy_setup,'preflight',return_value='arm64'),patch.object(easy_start.easy_setup,'read_installation',return_value=(Path('/fixture/server'),Path('/fixture/model'))),patch.object(easy_start,'_free_port'),patch.object(easy_start.subprocess,'Popen',return_value=child),patch.object(easy_start,'request_local',side_effect=[{'status':'ok'},{'choices':[{'message':{'content':'Bereit'}}]}]),patch.object(easy_start,'Store'),patch('backend.server.main')as main:
   easy_start.run(tv=True)
  main.assert_called_once_with(['--open-tv','--local-only']);child.terminate.assert_called_once()
