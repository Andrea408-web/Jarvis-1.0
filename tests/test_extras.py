"""Local pairing and truthful small-model behavior; no external services."""
import http.client
import json
from pathlib import Path
import plistlib
import ssl
import tempfile
import threading
import unittest
from unittest.mock import patch

from backend import easy_setup as setup
from backend.mobile import DeviceAuth, MobileLink, certificates
from backend.server import Application, JarvisServer
from backend.training import plan


class ModelMetadataTests(unittest.TestCase):
    def metadata(self,lfs,name=None):
        return {'sha':'a'*40,'siblings':[{'rfilename':name or setup.MODEL_NAME,'lfs':lfs}]}

    def test_oid_and_conflicts(self):
        spec=setup.select_model(self.metadata({'oid':'sha256:'+'b'*64,'size':400000000}))
        self.assertEqual(spec['sha256'],'b'*64)
        for lfs in [{'size':400000000},{'oid':'b'*64,'sha256':'c'*64,'size':400000000},{'oid':'b'*64,'size':450000001}]:
            with self.assertRaises(ValueError):setup.select_model(self.metadata(lfs))

    def test_pinned_small_community_fallback_only_after_invalid_official(self):
        community=self.metadata({'sha256':'b'*64,'size':400000000},'Qwen2.5-0.5B-Instruct-Q4_K_M.gguf')
        with patch.object(setup,'metadata',side_effect=[self.metadata({'oid':'b'*64,'size':500000000}),community]) as metadata,patch.object(setup,'fetch') as fetch:
            spec=setup.resolve_model()
        self.assertEqual(metadata.call_count,2);fetch.assert_not_called()
        self.assertIn('bartowski/',spec['url']);self.assertIn('/resolve/'+'a'*40+'/',spec['url']);self.assertLessEqual(spec['size'],setup.MAX_MODEL)

    def test_no_unverified_or_larger_fallback(self):
        with patch.object(setup,'metadata',return_value={'sha':'a'*40,'siblings':[]}),patch.object(setup,'fetch') as fetch:
            with self.assertRaises(ValueError):setup.resolve_model()
        fetch.assert_not_called()


class TrainingTests(unittest.TestCase):
    def test_rules_differ_by_edition_and_version_and_never_claim_image_analysis(self):
        modern=plan({'edition':'java','version':'1.21'})
        legacy=plan({'edition':'java','version':'1.8.9'})
        bedrock=plan({'edition':'bedrock','version':'1.21'})
        self.assertIn('ab 1.9',modern['timing']);self.assertIn('bis 1.8',legacy['timing']);self.assertIn('nicht den Java',bedrock['timing'])
        self.assertIn('keine Analyse',modern['basis']);self.assertEqual(len(modern['drills']),3)
        for data in [{'edition':'bad'},{'image':'base64'},{'version':['1.21']},{'goal':'unknown'}]:
            with self.assertRaises(ValueError):plan(data)


class PairingTests(unittest.TestCase):
    def test_tickets_single_use_expiry_and_session_reset(self):
        auth=DeviceAuth();ticket=auth.issue()
        with self.assertRaises(ValueError):auth.pair('wrong')
        session=auth.pair(ticket);self.assertTrue(auth.valid('jarvis_device='+session))
        with self.assertRaises(ValueError):auth.pair(ticket)
        ticket=auth.issue();auth.expires=0
        with self.assertRaises(ValueError):auth.pair(ticket)
        self.assertFalse(auth.valid('jarvis_device=wrong'))

    def test_pairing_persists_as_hashes_and_can_be_revoked(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'devices.json';auth=DeviceAuth(path);session=auth.pair(auth.issue())
            self.assertNotIn(session,path.read_text());self.assertEqual(path.stat().st_mode & 0o777,0o600)
            restored=DeviceAuth(path);self.assertTrue(restored.valid('jarvis_device='+session))
            restored.revoke();self.assertFalse(DeviceAuth(path).valid('jarvis_device='+session))

    def test_normal_shutdown_preserves_pairing_but_explicit_stop_revokes_it(self):
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as folder:
            app=SimpleNamespace(store=SimpleNamespace(data_dir=Path(folder)))
            link=MobileLink(app);session=link.auth.pair(link.auth.issue());link.stop(revoke=False)
            restored=MobileLink(app);self.assertTrue(restored.auth.valid('jarvis_device='+session))
            restored.stop();self.assertFalse(MobileLink(app).auth.valid('jarvis_device='+session))

    def test_real_verified_tls_pairing_guards_and_public_profile(self):
        with tempfile.TemporaryDirectory() as folder:
            cert,key,profile,fingerprint=certificates(Path(folder)/'cert','127.0.0.1')
            config=plistlib.loads(profile.read_bytes());der=config['PayloadContent'][0]['PayloadContent']
            self.assertEqual(config['PayloadContent'][0]['PayloadType'],'com.apple.security.root')
            self.assertNotIn(b'PRIVATE KEY',profile.read_bytes());self.assertEqual(len(fingerprint),64)
            self.assertEqual(ssl.PEM_cert_to_DER_cert((Path(folder)/'cert/ca.pem').read_text()),der)
            app=Application(Path(folder)/'data');server=JarvisServer(('127.0.0.1',0),app,secure=True);server.device_auth=DeviceAuth()
            ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);ctx.load_cert_chain(cert,key)
            server.socket=ctx.wrap_socket(server.socket,server_side=True,do_handshake_on_connect=False)
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            clientctx=ssl.create_default_context(cafile=str(Path(folder)/'cert/ca.pem'))
            def request(path,method='GET',data=None,cookie=None,origin=None):
                client=http.client.HTTPSConnection(*server.server_address,context=clientctx,timeout=5)
                headers={'X-Jarvis-Token':app.token,'Content-Type':'application/json'}
                if cookie:headers['Cookie']=cookie
                if origin:headers['Origin']=origin
                try:
                    client.request(method,path,json.dumps(data) if data is not None else None,headers)
                    response=client.getresponse();return response.status,dict(response.getheaders()),response.read()
                finally:client.close()
            try:
                self.assertEqual(request('/api/session')[0],401)
                self.assertIn(b'pair.js',request('/')[2]);self.assertIn(b'pair-form',request('/')[2])
                self.assertEqual(request('/manifest.webmanifest')[0],200);self.assertEqual(request('/app-icon.png')[0],200)
                ticket=server.device_auth.issue();status,headers,_=request('/api/mobile/pair','POST',{'ticket':ticket})
                self.assertEqual(status,200);cookie=headers['Set-Cookie'];self.assertIn('Secure',cookie);self.assertIn('HttpOnly',cookie);self.assertIn('SameSite=Strict',cookie)
                self.assertEqual(request('/api/session',cookie=cookie)[0],200);self.assertTrue(json.loads(request('/api/session',cookie=cookie)[2])['remote_device'])
                self.assertEqual(request('/api/mobile/pair','POST',{'ticket':ticket})[0],400)
                self.assertEqual(request('/api/mobile/stop','POST',{},cookie)[0],403)
                self.assertEqual(request('/api/settings',cookie=cookie,origin='https://evil.example')[0],403)
                self.assertEqual(request('/api/training/plan','POST',{'edition':'bedrock'},cookie)[0],200)
                for asset in ['/extras.js','/extras.css','/world.geojson','/qr.js']:
                    self.assertEqual(request(asset,cookie=cookie)[0],200)
                self.assertEqual(request('/backend/mobile.py',cookie=cookie)[0],404)
            finally:server.shutdown();server.server_close();thread.join(timeout=3)
