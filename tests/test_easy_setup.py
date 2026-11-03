import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock,patch
import zipfile

from backend import easy_setup as setup
from backend import easy_start


def sha(data):return hashlib.sha256(data).hexdigest()


class SetupTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.root_patch=patch.object(setup,'ROOT',self.root);self.root_patch.start();self.addCleanup(self.root_patch.stop)

    def release(self,checksum='a'*64,arch='arm64',size=500):
        return {'assets':[{'name':f'llama-bin-macos-{arch}.zip','size':size,'digest':'sha256:'+checksum,
                          'browser_download_url':f'https://github.com/ggml-org/llama.cpp/releases/download/test/llama-bin-macos-{arch}.zip'}]}

    def model(self,checksum='b'*64,size=1_000_000):
        return {'sha':'c'*40,'siblings':[{'rfilename':setup.MODEL_NAME,'lfs':{'sha256':checksum,'size':size}}]}

    def test_correct_architecture_only_and_no_unsigned_or_larger_fallback(self):
        self.assertEqual(setup.select_runtime(self.release(),'arm64')['size'],500)
        for release in [self.release(arch='x64'),self.release(size=setup.MAX_RUNTIME+1),self.release(checksum='bad')]:
            with self.assertRaises(ValueError):setup.select_runtime(release,'arm64')
        for model in [self.model(checksum='bad'),self.model(size=setup.MAX_MODEL+1),{'sha':'bad','siblings':[]}]:
            with self.assertRaises(ValueError):setup.select_model(model)
        selected=setup.select_model(self.model())
        self.assertIn('/resolve/'+'c'*40+'/',selected['url'])

    @patch('backend.easy_setup.platform.system',return_value='Linux')
    def test_platform_rejects_before_download_or_install(self,_):
        with patch.object(setup,'metadata') as metadata,patch.object(setup,'fetch') as fetch:
            with self.assertRaises(ValueError):setup.prepare()
        metadata.assert_not_called();fetch.assert_not_called();self.assertEqual(list(self.root.iterdir()),[])

    def test_mismatch_is_not_used_and_valid_cache_needs_no_redownload(self):
        data=b'verified fixture';spec={'sha256':sha(data),'size':len(data),'url':'https://example.invalid/fixture'}
        def wrong(url,path,maximum):Path(path).write_bytes(b'wrong')
        with patch.object(setup,'fetch',side_effect=wrong),self.assertRaises(ValueError):setup.verified_download(spec)
        self.assertFalse((self.root/'.jarvis/downloads'/spec['sha256']).exists())
        def correct(url,path,maximum):Path(path).write_bytes(data)
        with patch.object(setup,'fetch',side_effect=correct):path=setup.verified_download(spec)
        with patch.object(setup,'fetch') as fetch:self.assertEqual(setup.verified_download(spec),path)
        fetch.assert_not_called()

    def archive(self,entries):
        path=self.root/'fixture.zip'
        with zipfile.ZipFile(path,'w') as z:
            for name,data in entries:z.writestr(name,data)
        return path

    def test_archive_preserves_libraries_and_rejects_traversal_and_external_links(self):
        path=self.archive([('bin/llama-server',b'runtime'),('bin/libggml.dylib',b'library')])
        target,binary=setup.extract_runtime(path,'fixture.zip')
        self.assertEqual(binary.read_bytes(),b'runtime');self.assertTrue((binary.parent/'libggml.dylib').exists())
        self.assertTrue(binary.stat().st_mode&0o100)
        path.unlink();path=self.archive([('../escape',b'bad')])
        with self.assertRaises(ValueError):setup.extract_runtime(path,'fixture.zip')
        self.assertFalse((self.root/'escape').exists())
        path.unlink()
        with zipfile.ZipFile(path,'w') as z:
            entry=zipfile.ZipInfo('external');entry.create_system=3;entry.external_attr=0o120777<<16
            z.writestr(entry,'/outside')
        with self.assertRaises(ValueError):setup.extract_runtime(path,'fixture.zip')

    def test_complete_fixture_install_is_repeatable_offline_and_checks_tampering(self):
        runtime=self.archive([('bin/llama-server',b'fixture-not-executed'),('bin/libggml.dylib',b'library')]).read_bytes()
        model=b'GGUF'+b'0'*999996
        release=self.release(sha(runtime),size=len(runtime));info=self.model(sha(model),len(model))
        def metadata(url):return release if url==setup.RELEASE_API else info
        def download(url,path,maximum):Path(path).write_bytes(runtime if url.startswith('https://github.com/') else model)
        with patch.object(setup,'preflight',return_value='arm64'),patch.object(setup,'metadata',side_effect=metadata),patch.object(setup,'fetch',side_effect=download):
            executable,model_path=setup.prepare()
        self.assertEqual(executable.read_bytes(),b'fixture-not-executed')
        self.assertEqual(setup.digest(model_path),sha(model))
        with patch.object(setup,'preflight',return_value='arm64'),patch.object(setup,'metadata') as metadata,patch.object(setup,'fetch') as fetch:
            self.assertEqual(setup.prepare(),(executable,model_path))
        metadata.assert_not_called();fetch.assert_not_called()
        with self.assertRaises(ValueError):setup.read_installation('x64')
        executable.write_bytes(b'modified')
        with self.assertRaises(ValueError):setup.read_installation('arm64')

    def test_native_curl_keeps_tls_no_curlrc_or_keys_and_bounds_bytes(self):
        process=Mock();process.stdout=io.BytesIO(b'payload');process.wait.return_value=0;process.poll.return_value=0
        with patch('backend.easy_setup.subprocess.Popen',return_value=process) as popen:
            setup.fetch('https://example.invalid/file',self.root/'file',7)
        args=popen.call_args.args[0]
        self.assertEqual(args[:2],['/usr/bin/curl','--disable']);self.assertNotIn('--insecure',args);self.assertNotIn('-k',args)
        self.assertIn('=https',args);self.assertNotIn('Authorization',repr(args))
        process=Mock();process.stdout=io.BytesIO(b'too much');process.poll.return_value=None
        with patch('backend.easy_setup.subprocess.Popen',return_value=process),self.assertRaises(ValueError):
            setup.fetch('https://example.invalid/file',self.root/'oversize',2)
        process.kill.assert_called_once()


class EasyStartTests(unittest.TestCase):
    def test_real_reply_required_before_app_and_only_owned_process_stopped(self):
        child=Mock();child.poll.return_value=None
        fake_store=Mock()
        responses=[{'status':'ok'},{'choices':[{'message':{'content':'Bereit.'}}]}]
        with patch.object(easy_start.easy_setup,'preflight',return_value='arm64'), \
             patch.object(easy_start.easy_setup,'read_installation',return_value=(Path('/fixture/server'),Path('/fixture/model'))), \
             patch.object(easy_start,'_free_port'),patch.object(easy_start.subprocess,'Popen',return_value=child) as popen, \
             patch.object(easy_start,'request_local',side_effect=responses) as request, \
             patch.object(easy_start,'Store',return_value=fake_store),patch('backend.server.main') as main, \
             patch.dict('os.environ',{'OPENAI_API_KEY':'never-pass-test-key'}):
            easy_start.run()
        self.assertNotIn('OPENAI_API_KEY',popen.call_args.kwargs['env'])
        self.assertEqual(request.call_args_list[1].args[0],'/v1/chat/completions')
        main.assert_called_once_with(['--open-browser','--local-only'])
        self.assertFalse(fake_store.update_settings.call_args.args[0]['cloud_enabled'])
        child.terminate.assert_called_once();child.kill.assert_not_called()

    def test_invalid_model_reply_does_not_launch_app_and_cleans_up(self):
        child=Mock();child.poll.return_value=None
        with patch.object(easy_start.easy_setup,'preflight',return_value='arm64'), \
             patch.object(easy_start.easy_setup,'prepare',return_value=(Path('/fixture/server'),Path('/fixture/model'))), \
             patch.object(easy_start,'_free_port'),patch.object(easy_start.subprocess,'Popen',return_value=child), \
             patch.object(easy_start,'request_local',side_effect=[{'status':'ok'},{}]), \
             patch('backend.server.main') as main,patch.object(easy_start,'Store') as store:
            with self.assertRaises(ValueError):easy_start.run(setup=True)
        main.assert_not_called();store.assert_not_called();child.terminate.assert_called_once()

    def test_existing_port_never_kills_an_unrelated_process(self):
        with patch.object(easy_start.easy_setup,'preflight',return_value='arm64'), \
             patch.object(easy_start.easy_setup,'read_installation',return_value=(Path('/fixture/server'),Path('/fixture/model'))), \
             patch.object(easy_start,'_free_port',side_effect=ValueError('occupied')), \
             patch.object(easy_start.subprocess,'Popen') as popen:
            with self.assertRaises(ValueError):easy_start.run()
        popen.assert_not_called()

class EntryPointTests(unittest.TestCase):
    def test_setup_cli_routes_once_without_starting_another_app(self):
        from backend.server import main
        with patch('backend.easy_start.run') as run,patch('backend.server.Application') as app,patch('backend.server.load_saved_keys') as keys:
            main(['--setup-small-ai'])
        run.assert_called_once_with(setup=True);app.assert_not_called();keys.assert_not_called()

    def test_local_only_start_skips_keys_and_disables_paid_modes(self):
        from backend.server import main
        server=Mock();server.serve_forever.side_effect=KeyboardInterrupt
        app=Mock()
        with patch('backend.server.Application',return_value=app),patch('backend.server.JarvisServer',return_value=server),patch('backend.server.load_saved_keys') as keys,patch('backend.server.getpass.getpass') as prompt:
            main(['--local-only','--ask-keys'])
        keys.assert_not_called();prompt.assert_not_called()
        app.store.update_settings.assert_called_once_with({'ai_provider':'llamacpp','cloud_enabled':False,'elevenlabs_enabled':False,'voice_enabled':True})
        server.server_close.assert_called_once()

if __name__=='__main__':unittest.main()
