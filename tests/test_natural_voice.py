import base64
import hashlib
import io
import json
import os
from pathlib import Path
import struct
import tarfile
import tempfile
import unittest
import wave
from unittest.mock import Mock,patch

from backend import natural_voice as natural
from backend.providers import ProviderError


def wav_bytes():
    target=io.BytesIO()
    with wave.open(target,'wb') as audio:
        audio.setnchannels(1);audio.setsampwidth(2);audio.setframerate(22050);audio.writeframes(struct.pack('<h',4000)*2205)
    return target.getvalue()


class NaturalVoiceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)

    def test_runtime_and_macho_never_switch_architecture(self):
        self.assertIn('arm64',natural.runtime_spec('arm64')['name'])
        self.assertIn('x64',natural.runtime_spec('x86_64')['name'])
        with self.assertRaises(ValueError):natural.runtime_spec('unknown')
        executable=self.root/'binary';executable.write_bytes(b'\xcf\xfa\xed\xfe'+struct.pack('<I',0x0100000c)+b'\0'*24)
        natural.check_macho(executable,'arm64')
        with self.assertRaises(ValueError):natural.check_macho(executable,'x86_64')

    def test_download_checksum_and_verified_cache(self):
        data=b'valid fixture';spec={'name':'voice.tar.bz2','url':'https://example.test/voice','sha256':hashlib.sha256(data).hexdigest(),'maximum':1000}
        with patch.object(natural,'fetch',side_effect=lambda url,path,maximum:Path(path).write_bytes(b'wrong')):
            with self.assertRaises(ValueError):natural.verified_download(spec,self.root)
        self.assertEqual(list(self.root.iterdir()),[])
        with patch.object(natural,'fetch',side_effect=lambda url,path,maximum:Path(path).write_bytes(data)):
            result=natural.verified_download(spec,self.root)
        with patch.object(natural,'fetch') as fetch:
            self.assertEqual(natural.verified_download(spec,self.root),result)
        fetch.assert_not_called()

    def test_archive_traversal_and_external_links_rejected(self):
        for name,link in [('../escape',None),('pack/link','../../outside')]:
            archive=self.root/('archive'+str(len(name))+'.tar.bz2')
            with tarfile.open(archive,'w:bz2') as opened:
                info=tarfile.TarInfo(name)
                if link:info.type=tarfile.SYMTYPE;info.linkname=link;opened.addfile(info)
                else:info.size=3;opened.addfile(info,io.BytesIO(b'bad'))
            target=self.root/'expanded'
            with self.assertRaises(ValueError):natural.extract_archive(archive,target)
            self.assertFalse(target.exists())

    def fixture_install(self):
        engine=natural.NaturalVoice(self.root);folder=engine.root/'version'
        for name,data in [('bin/tts',b'engine'),('model.onnx',b'model'),('tokens.txt',b'tokens'),('data/phonemes',b'phonemes')]:
            path=folder/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
        record={'version':1,'architecture':natural.platform.machine(),'executable':'version/bin/tts','model':'version/model.onnx','tokens':'version/tokens.txt','data_dir':'version/data','files':{str(path.relative_to(engine.root)):natural.digest(path) for path in folder.rglob('*') if path.is_file()}}
        (engine.root/'installed.json').write_text(json.dumps(record))
        return engine

    def test_uninstalled_and_tampered_do_not_fall_back(self):
        engine=natural.NaturalVoice(self.root)
        self.assertFalse(engine.status()['installed'])
        with self.assertRaises(ProviderError):engine.synthesize('Hallo')
        engine=self.fixture_install();self.assertTrue(engine.status()['installed'])
        (engine.root/'version/model.onnx').write_bytes(b'changed')
        with patch.object(natural,'generate') as generate:
            with self.assertRaises(ProviderError):engine.synthesize('Hallo')
        generate.assert_not_called()

    def test_generate_uses_own_process_fixed_flags_and_strips_cloud_keys(self):
        output=self.root/'result.wav'
        def run(command,**kwargs):
            self.assertEqual(command[-2:],[ '--','--nicht-als-option'])
            self.assertNotIn('shell',kwargs)
            self.assertNotIn('OPENAI_API_KEY',kwargs['env'])
            self.assertIn('--provider=cpu',command)
            output.write_bytes(wav_bytes());return Mock(returncode=0)
        with patch.object(natural.subprocess,'run',side_effect=run),patch.dict(os.environ,{'OPENAI_API_KEY':'fake-test-only'}):
            result=natural.generate(self.root/'bin/tts',self.root/'model',self.root/'tokens',self.root/'data','--nicht-als-option',output)
        self.assertEqual(result,wav_bytes())

    def test_silent_or_invalid_audio_is_not_a_success(self):
        output=self.root/'silence.wav'
        with wave.open(str(output),'wb') as audio:
            audio.setnchannels(1);audio.setsampwidth(2);audio.setframerate(22050);audio.writeframes(b'\0'*1000)
        with self.assertRaises(ValueError):natural.wave_bytes(output)
        engine=self.fixture_install()
        for value in [None,'','x'*1801]:
            with self.assertRaises(ValueError):engine.synthesize(value)
        with self.assertRaises(ValueError):engine.synthesize('Hallo',[])

    @patch('backend.natural_voice.platform.system',return_value='Linux')
    def test_mac_installer_rejects_before_download(self,_):
        with patch.object(natural,'verified_download') as download:
            with self.assertRaises(ValueError):natural.install(self.root)
        download.assert_not_called()

class NaturalVoiceHTTPTests(unittest.TestCase):
    def test_endpoint_returns_authenticated_wave_and_no_provider_call(self):
        import http.client
        import threading
        from backend.server import Application,JarvisServer
        with tempfile.TemporaryDirectory() as folder:
            app=Application(folder);app.natural_voice.synthesize=Mock(return_value=wav_bytes())
            app.voice.synthesize=Mock(side_effect=AssertionError('no external voice'))
            server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            def request(body,authorized=True):
                client=http.client.HTTPConnection(*server.server_address,timeout=3)
                headers={'Content-Type':'application/json'}
                if authorized:headers['X-Jarvis-Token']=app.token
                try:
                    client.request('POST','/api/natural-voice/speak',json.dumps(body),headers);response=client.getresponse();return response.status,response.getheader('Content-Type'),response.read()
                finally:client.close()
            try:
                self.assertEqual(request({'text':'Hallo'},False)[0],401)
                self.assertEqual(request({'text':'Hallo','url':'https://private.test'})[0],400)
                status,mime,data=request({'text':'Hallo','preset':'jarvis'})
                self.assertEqual(status,200);self.assertEqual(mime,'audio/wav');self.assertEqual(data,wav_bytes())
                app.natural_voice.synthesize.assert_called_once_with('Hallo','jarvis')
                app.voice.synthesize.assert_not_called()
            finally:server.shutdown();server.server_close();thread.join(timeout=3)
