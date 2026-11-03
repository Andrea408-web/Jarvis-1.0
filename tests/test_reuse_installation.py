"""Last-download update: verified sibling cache reuse without network or overwrite."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from backend import easy_setup as setup

class ReuseTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.parent=Path(self.temp.name);self.old=self.parent/'Jarvis-old';self.new=self.parent/'Jarvis-new';self.new.mkdir()
        self.patch=patch.object(setup,'ROOT',self.new);self.patch.start();self.addCleanup(self.patch.stop)
        executable='.jarvis/runtime/build/llama-server';model='.jarvis/downloads/model'
        for relative,data in [(executable,b'verified binary fixture'),(model,b'GGUFverified model fixture')]:
            target=self.old/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        (self.old/executable).chmod(0o755)
        self.record={'version':1,'architecture':'arm64','executable':executable,'model':model,'files':{relative:setup.digest(self.old/relative) for relative in [executable,model]}}
        (self.old/'.jarvis/installed.json').write_text(json.dumps(self.record))
    def test_reuses_verified_files_without_download_and_survives_old_folder_removal(self):
        (self.old/'.env').write_text('private example not copied')
        with patch.object(setup,'metadata') as metadata,patch.object(setup,'fetch') as fetch:
            result=setup.reuse_previous('arm64')
        self.assertIsNotNone(result);metadata.assert_not_called();fetch.assert_not_called()
        self.assertFalse((self.new/'.env').exists());self.assertEqual(result[1].read_bytes(),b'GGUFverified model fixture')
        shutil.rmtree(self.old)
        self.assertEqual(setup.read_installation('arm64')[1].read_bytes(),b'GGUFverified model fixture')
    def test_tampering_and_wrong_architecture_never_reused(self):
        self.assertIsNone(setup.reuse_previous('x64'))
        (self.old/self.record['model']).write_bytes(b'changed')
        self.assertIsNone(setup.reuse_previous('arm64'));self.assertFalse((self.new/'.jarvis/installed.json').exists())
    def test_conflicting_existing_file_is_preserved_and_created_files_rolled_back(self):
        target=self.new/self.record['model'];target.parent.mkdir(parents=True);target.write_bytes(b'user-owned file')
        self.assertIsNone(setup.reuse_previous('arm64'));self.assertEqual(target.read_bytes(),b'user-owned file')
        self.assertFalse((self.new/self.record['executable']).exists());self.assertFalse((self.new/'.jarvis/installed.json').exists())
    def test_manifest_cannot_copy_other_source_files(self):
        (self.old/'README.md').write_text('not a cache file');self.record['files']['README.md']=setup.digest(self.old/'README.md')
        (self.old/'.jarvis/installed.json').write_text(json.dumps(self.record))
        self.assertIsNone(setup.reuse_previous('arm64'));self.assertFalse((self.new/'README.md').exists())
