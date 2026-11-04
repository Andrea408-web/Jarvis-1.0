import hashlib
from pathlib import Path
import tempfile
import unittest
from tools import voice_upgrade_bootstrap as upgrade

class UpgradeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.files={name:('new '+name).encode() for name in upgrade.ALLOWED}
        self.manifest={}
        for name,data in self.files.items():
            old=None if name in {'backend/natural_voice.py','backend/hub.py','frontend/mini-hub.js','docs/NATUERLICHE-STIMME.md'} else ('old '+name).encode()
            self.manifest[name]={'before':hashlib.sha256(old).hexdigest() if old else None,'after':hashlib.sha256(data).hexdigest()}
            if old:
                path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(old)
        model=self.root/'.jarvis/model.gguf';model.parent.mkdir(exist_ok=True);model.write_bytes(b'unchanged text model')
        (self.root/'.env').write_text('fake-test-secret-not-to-copy')

    def test_only_small_patch_written_text_model_and_settings_not_touched(self):
        called=[]
        backup=upgrade.apply(self.root,self.files,self.manifest,lambda root:called.append(root))
        self.assertEqual(called,[self.root.resolve()])
        self.assertEqual((self.root/'.jarvis/model.gguf').read_bytes(),b'unchanged text model')
        self.assertEqual((self.root/'.env').read_text(),'fake-test-secret-not-to-copy')
        self.assertFalse((backup/'.env').exists())
        for name,data in self.files.items():self.assertEqual((self.root/name).read_bytes(),data)

    def test_failed_install_restores_original_files_and_removes_new_modules(self):
        def fail(root):raise ValueError('test install failed')
        with self.assertRaises(ValueError):upgrade.apply(self.root,self.files,self.manifest,fail)
        for name,metadata in self.manifest.items():
            path=self.root/name
            if metadata['before'] is None:self.assertFalse(path.exists())
            else:self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),metadata['before'])

    def test_custom_files_refused_without_any_download_or_overwrite(self):
        path=self.root/'frontend/app.js';path.write_text('my custom changes')
        self.assertFalse(upgrade.compatible(self.root,self.files,self.manifest))
        with self.assertRaises(ValueError):upgrade.apply(self.root,self.files,self.manifest,lambda root:self.fail('must not install'))
        self.assertEqual(path.read_text(),'my custom changes')

    def test_rollback_keeps_concurrent_user_edits(self):
        def fail(root):
            (root/'frontend/app.js').write_text('concurrent edit')
            raise ValueError('test failure')
        with self.assertRaises(ValueError):upgrade.apply(self.root,self.files,self.manifest,fail)
        self.assertEqual((self.root/'frontend/app.js').read_text(),'concurrent edit')

class GeneratedPackageTests(unittest.TestCase):
    def test_packaged_helper_contains_current_patch_and_no_model_weights(self):
        import ast
        import zipfile
        root=Path(__file__).resolve().parents[1]
        script=(root/'JARVIS-Stimme-nachruesten.command').read_text()
        source=script.split("<<'JARVIS_VOICE_PYTHON'\n",1)[1].split('\nJARVIS_VOICE_PYTHON\n',1)[0]
        values={}
        for node in ast.parse(source).body:
            if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in {'PAYLOAD_B64','PAYLOAD_SHA'}:
                values[node.targets[0].id]=ast.literal_eval(node.value)
        files,manifest=upgrade.payload_files(values['PAYLOAD_B64'],values['PAYLOAD_SHA'])
        for name,data in files.items():self.assertEqual(data,(root/name).read_bytes())
        self.assertLess(len(script),300000)
        with zipfile.ZipFile(root/'updates/JARVIS-Stimme-Nachruestung.zip') as archive:
            self.assertEqual(archive.read('JARVIS-Stimme-nachruesten.command'),script.encode())
            self.assertFalse(any(name.endswith(('.onnx','.gguf')) for name in archive.namelist()))


class AstraPackageTests(unittest.TestCase):
    def test_astra_package_disables_downloads_and_accepts_last_shipped_version(self):
        import ast,zipfile,subprocess
        root=Path(__file__).resolve().parents[1];script=(root/'JARVIS-Astra-aktualisieren.command').read_text()
        self.assertIn('JARVIS_ASTRA_ONLY=1 JARVIS_VOICE_HELPER_DIR=',script)
        source=script.split("<<'JARVIS_VOICE_PYTHON'\n",1)[1].split('\nJARVIS_VOICE_PYTHON\n',1)[0];values={}
        for node in ast.parse(source).body:
            if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in {'PAYLOAD_B64','PAYLOAD_SHA'}:values[node.targets[0].id]=ast.literal_eval(node.value)
        files,manifest=upgrade.payload_files(values['PAYLOAD_B64'],values['PAYLOAD_SHA'])
        with tempfile.TemporaryDirectory() as folder:
            target=Path(folder)
            for name in files:
                old=subprocess.run(['git','show','bd17dfd:'+name],cwd=root,capture_output=True)
                if old.returncode==0:
                    path=target/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(old.stdout)
            self.assertTrue(upgrade.compatible(target,files,manifest))
            upgrade.apply(target,files,manifest,lambda root:None)
            for name,data in files.items():self.assertEqual((target/name).read_bytes(),data)
        with zipfile.ZipFile(root/'updates/JARVIS-Astra-Update.zip') as archive:
            self.assertEqual(archive.read('JARVIS-Astra-aktualisieren.command'),script.encode());self.assertLess(sum(i.file_size for i in archive.infolist()),200000)
