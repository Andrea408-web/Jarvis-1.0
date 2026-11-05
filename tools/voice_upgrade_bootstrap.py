"""Self-contained, hash-checked, rollback-capable patch installer embedded in .command."""
import base64
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import platform
import shutil
import subprocess
import sys
import tempfile
import uuid
import zipfile

PAYLOAD_B64='__PAYLOAD_B64__'
PAYLOAD_SHA='__PAYLOAD_SHA__'
ALLOWED={
    'backend/notes.py',
    'frontend/office-3d.js',
    'frontend/lowpoly-stage.js',
    'backend/agents.py','frontend/office.js','backend/render_scene.py',
    'backend/models.py','backend/blender_scene.py','backend/persona.py','backend/local_ai.py','backend/ai.py','backend/openai_client.py',
    'README.md','docs/EINFACH-STARTEN.md','docs/PRUEFUNG.md',
    'backend/desktop.py','backend/astra_panel.js','frontend/astra.js','frontend/astra-panel.html','frontend/astra-panel.js','frontend/astra.css','frontend/world-news.js','docs/ASTRA.md',
    'backend/natural_voice.py','backend/server.py','backend/storage.py',
    'frontend/app.js','frontend/jarvis-voice.js','docs/NATUERLICHE-STIMME.md',
    'frontend/artifacts.js','backend/hub.py','frontend/mini-hub.js','frontend/index.html','frontend/extras.js','frontend/extras.css','frontend/conversation.js',
}


def payload_files(encoded=PAYLOAD_B64,checksum=PAYLOAD_SHA):
    raw=base64.b64decode(encoded,validate=True)
    if len(raw)>2000000 or hashlib.sha256(raw).hexdigest()!=checksum:raise ValueError('Der Nachrüsthelfer ist beschädigt. Es wurde nichts geändert.')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        if set(archive.namelist())!=ALLOWED|{'manifest.json'}:raise ValueError('Unbekannte Dateien im Stimmenupdate.')
        if any(info.file_size>1000000 for info in archive.infolist()):raise ValueError('Das Stimmenupdate ist zu groß.')
        manifest=json.loads(archive.read('manifest.json'))
        files={name:archive.read(name) for name in ALLOWED}
    for name,data in files.items():
        if hashlib.sha256(data).hexdigest()!=manifest[name]['after']:raise ValueError('Das Stimmenupdate hat eine ungültige Prüfsumme.')
    return files,manifest


def compatible(root,files,manifest):
    root=Path(root)
    if not (root/'backend/server.py').is_file() or not (root/'frontend/app.js').is_file():return False
    for name in files:
        path=root/name
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):return False
        if path.exists():
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() not in ({manifest[name]['before'],manifest[name]['after']}|set(manifest[name].get('accepted_before',[]))):return False
        elif manifest[name]['before'] is not None:return False
    return True


def choose_root(files,manifest):
    helper=Path(os.environ.get('JARVIS_VOICE_HELPER_DIR',str(Path.cwd())))
    if compatible(helper,files,manifest):return helper
    candidates=[]
    try:
        candidates=[path for path in helper.iterdir() if path.is_dir() and not path.is_symlink() and path.name.casefold().startswith('jarvis') and compatible(path,files,manifest)]
    except OSError:pass
    if len(candidates)==1:return candidates[0]
    try:
        result=subprocess.run(['/usr/bin/osascript','-e','POSIX path of (choose folder with prompt "Wähle deinen vorhandenen JARVIS-Ordner. Die Text-KI bleibt erhalten.")'],capture_output=True,text=True,timeout=180,check=True)
    except (OSError,subprocess.SubprocessError):raise ValueError('Ordnerauswahl abgebrochen. Es wurde nichts geändert.') from None
    root=Path(result.stdout.strip())
    if not compatible(root,files,manifest):raise ValueError('Dieser Ordner passt nicht zum geprüften Stimmenupdate oder Programmdateien wurden verändert. Es wurde nichts überschrieben. Unterstützt sind die bereitgestellten Versionen 232ba23, bd17dfd, 9bf0a4e und 539bd30; weder Jarvis noch die Text-KI werden automatisch neu geladen.')
    return root


def atomic_write(path,data,mode=0o644):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    descriptor,name=tempfile.mkstemp(prefix='.voice-update-',dir=path.parent)
    temporary=Path(name)
    try:
        with os.fdopen(descriptor,'wb') as output:output.write(data)
        temporary.chmod(mode);temporary.replace(path)
    finally:temporary.unlink(missing_ok=True)


def apply(root,files,manifest,install_callback):
    root=Path(root).resolve()
    if not compatible(root,files,manifest):raise ValueError('Eine Programmdatei wurde verändert. Das Update wird nicht darübergeschrieben.')
    private=root/'.jarvis'
    if private.is_symlink():raise ValueError('Der JARVIS-Einrichtungsordner darf nicht umgeleitet sein.')
    backup=private/'voice-update-backups'/uuid.uuid4().hex
    if not backup.resolve().is_relative_to(root):raise ValueError('Der Sicherungsordner darf den Projektordner nicht verlassen.')
    backup.mkdir(parents=True,mode=0o700)
    originals={};written=[]
    for name in files:
        target=root/name
        originals[name]=(target.read_bytes(),target.stat().st_mode&0o777) if target.exists() else None
        if originals[name]:
            destination=backup/name;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(target,destination)
    try:
        for name,data in files.items():
            target=root/name;written.append(name);atomic_write(target,data,originals[name][1] if originals[name] else 0o644)
        install_callback(root)
    except BaseException:
        for name in reversed(written):
            previous=originals[name]
            if (root/name).is_file() and hashlib.sha256((root/name).read_bytes()).hexdigest() not in {manifest[name]['after'],manifest[name]['before']}:continue
            if previous:atomic_write(root/name,*previous)
            else:(root/name).unlink(missing_ok=True)
        raise
    return backup


def main():
    if platform.system()!='Darwin':raise ValueError('Dieser Nachrüsthelfer ist für den Mac. Es wurde nichts geändert.')
    if sys.version_info<(3,10):raise ValueError('Bitte denselben Python-3.10+-Interpreter wie für dein vorhandenes Jarvis verwenden.')
    files,manifest=payload_files();root=choose_root(files,manifest)
    print('Gefundenes Jarvis:',root,flush=True)
    print('Es werden Astra, Weltansicht und Desktop-Abläufe aktualisiert. Deine Text-KI, Gespräche und Schlüssel bleiben erhalten.',flush=True)
    def install_voice(project):
        sys.path.insert(0,str(project));os.chdir(project)
        if os.environ.get('JARVIS_ASTRA_ONLY')=='1':return
        from backend.natural_voice import install
        from backend.storage import Store
        voice=install()
        if not voice.status()['installed']:raise ValueError('Die Sprachprobe war nicht erfolgreich. Die bisherige Einrichtung bleibt erhalten.')
        store=Store();store.update_settings({'voice_engine':'natural','voice_preset':'jarvis','voice_enabled':True,'elevenlabs_enabled':False})
    backup=apply(root,files,manifest,install_voice)
    print('\nFertig. Das JARVIS-Update ist eingerichtet. Bitte dein bisheriges JARVIS im Terminal mit Control+C beenden und normal mit 2-JARVIS-starten.command neu starten. Im Browser bei Bedarf Seite neu laden.',flush=True)
    print('Die Text-KI muss nicht neu eingerichtet werden. Sicherung der ersetzten Programmdateien:',backup,flush=True)


if __name__=='__main__':
    try:main()
    except KeyboardInterrupt:print('\nAbgebrochen. Bereits ersetzte Programmdateien wurden zurückgesetzt.');sys.exit(1)
    except Exception as error:print('\nStimmen-Nachrüstung nicht abgeschlossen:',str(error));print('Die bisherigen Programmdateien wurden beibehalten oder wiederhergestellt.');sys.exit(1)
