"""Optional German neural voice. Separate install, fixed public artifacts, offline inference."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import os
import platform
import shutil
import struct
import subprocess
import tarfile
import tempfile
import threading
import time
import uuid
import wave

from .providers import ProviderError
from .storage import default_data_dir
from .easy_setup import fetch

VERSION='1.12.34'
MODEL={
    'name':'vits-piper-de_DE-thorsten-medium.tar.bz2',
    'url':'https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-de_DE-thorsten-medium.tar.bz2',
    'sha256':'50487d9c95fdf2191f31d2588569381063ba1591dcd4c7d4bdd30f12b2191714',
    'maximum':70000000,
}
RUNTIMES={
    'arm64':{'name':'sherpa-onnx-v1.12.34-osx-arm64-shared.tar.bz2','sha256':'65ed4f3784406163e505694c39acb507f5d4bd1b2b9e6cef23f00d3c4a81b40f'},
    'x86_64':{'name':'sherpa-onnx-v1.12.34-osx-x64-shared.tar.bz2','sha256':'6627b7a3682005eea43f72944cf03c1faa15ed6959ef3451180cac357adbfccc'},
}


def digest(path):
    value=hashlib.sha256()
    with Path(path).open('rb') as source:
        for chunk in iter(lambda:source.read(1024*1024),b''):value.update(chunk)
    return value.hexdigest()


def runtime_spec(architecture):
    if architecture not in RUNTIMES:raise ValueError('Für diese Mac-Architektur ist kein geprüftes Sprachpaket hinterlegt.')
    spec=dict(RUNTIMES[architecture]);spec['url']='https://github.com/k2-fsa/sherpa-onnx/releases/download/v'+VERSION+'/'+spec['name'];spec['maximum']=40000000
    return spec


def verified_download(spec,folder):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True,mode=0o700)
    path=folder/spec['name']
    if path.is_file() and not path.is_symlink() and digest(path)==spec['sha256']:return path
    temporary=folder/(uuid.uuid4().hex+'.part')
    try:
        fetch(spec['url'],temporary,spec['maximum'])
        if digest(temporary)!=spec['sha256']:raise ValueError('Die Sprachpaket-Prüfsumme stimmt nicht. Es wird nichts gestartet.')
        if path.exists():path=folder/(uuid.uuid4().hex+'-'+spec['name'])
        temporary.replace(path);return path
    finally:temporary.unlink(missing_ok=True)


def extract_archive(archive,target):
    """No traversal, devices, hardlinks, shell commands or preexisting targets."""
    target=Path(target);target.mkdir(mode=0o700)
    links=[];total=0
    try:
        with tarfile.open(archive,'r:bz2') as opened:
            members=opened.getmembers()
            if len(members)>3000:raise ValueError('Das Sprachpaket enthält zu viele Dateien.')
            for item in members:
                name=PurePosixPath(item.name)
                if name.is_absolute() or '..' in name.parts or '\\' in item.name or not name.parts:raise ValueError('Unsicherer Pfad im Sprachpaket.')
                path=target.joinpath(*name.parts)
                if item.isdir():path.mkdir(parents=True,exist_ok=True);continue
                path.parent.mkdir(parents=True,exist_ok=True)
                if item.issym():
                    if not item.linkname or Path(item.linkname).is_absolute() or '\\' in item.linkname:raise ValueError('Unsicherer Link im Sprachpaket.')
                    if not (path.parent/item.linkname).resolve().is_relative_to(target.resolve()):raise ValueError('Archivlink verlässt das Sprachpaket.')
                    links.append((path,item.linkname));continue
                if not item.isfile() or item.size<0:raise ValueError('Nicht unterstützte Spezialdatei im Sprachpaket.')
                total+=item.size
                if total>400000000:raise ValueError('Das Sprachpaket ist entpackt zu groß.')
                with opened.extractfile(item) as source,path.open('xb') as output:
                    remaining=item.size
                    while remaining:
                        chunk=source.read(min(65536,remaining))
                        if not chunk:raise ValueError('Unvollständige Sprachdatei.')
                        output.write(chunk);remaining-=len(chunk)
                path.chmod((item.mode&0o755) or 0o644)
            for path,link in links:path.symlink_to(link)
        for path in target.rglob('*'):
            if not path.resolve().is_relative_to(target.resolve()):raise ValueError('Ein Link verlässt das Sprachpaket.')
        roots=[path for path in target.iterdir() if path.is_dir() and not path.is_symlink()]
        if len(roots)!=1:raise ValueError('Kein eindeutiger Sprachpaket-Ordner.')
        return roots[0]
    except Exception:
        shutil.rmtree(target);raise


def check_macho(path,architecture):
    with Path(path).open('rb') as source:header=source.read(4096)
    expected={'arm64':0x0100000c,'x86_64':0x01000007}[architecture]
    if header[:4] in {b'\xcf\xfa\xed\xfe',b'\xce\xfa\xed\xfe'}:
        valid=len(header)>=8 and struct.unpack('<I',header[4:8])[0]==expected
    elif header[:4]==b'\xca\xfe\xba\xbe':
        count=struct.unpack('>I',header[4:8])[0] if len(header)>=8 else 0
        valid=count<=16 and any(len(header)>=12+index*20 and struct.unpack('>I',header[8+index*20:12+index*20])[0]==expected for index in range(count))
    else:valid=False
    if not valid:raise ValueError('Das Sprachprogramm passt nicht zur erkannten Mac-Architektur. Es wird keine andere Architektur installiert.')


def wave_bytes(path):
    if Path(path).stat().st_size>16000000:raise ValueError('Die Sprachdatei überschreitet das Größenlimit.')
    with wave.open(str(path),'rb') as audio:
        if audio.getnchannels() not in {1,2} or audio.getsampwidth()!=2 or not 8000<=audio.getframerate()<=96000 or audio.getnframes()<10:raise ValueError('Die Sprachengine hat keine gültige PCM-Sprachdatei erzeugt.')
        if not any(audio.readframes(min(audio.getnframes(),200000))):raise ValueError('Die Sprachdatei enthält kein Sprachsignal.')
    return Path(path).read_bytes()


def generate(executable,model,tokens,data_dir,text,output,preset='jarvis',cancel_event=None):
    if not isinstance(text,str) or not text.strip() or len(text)>1800:raise ValueError('Bitte 1 bis 1.800 Zeichen zum Sprechen senden.')
    if preset not in {'jarvis','clear','system'}:raise ValueError('Unbekanntes Stimmprofil.')
    env=dict(os.environ)
    for key in ['GEMINI_API_KEY','OPENAI_API_KEY','ELEVENLABS_API_KEY']:env.pop(key,None)
    lib=Path(executable).parent.parent/'lib'
    # Child-local loader path for the official standalone package; no global changes.
    env['DYLD_LIBRARY_PATH' if platform.system()=='Darwin' else 'LD_LIBRARY_PATH']=str(lib)
    command=[str(executable),'--vits-model='+str(model),'--vits-tokens='+str(tokens),'--vits-data-dir='+str(data_dir),'--provider=cpu','--num-threads=2','--vits-length-scale='+({'jarvis':'1.0','clear':'.94','system':'1.06'}[preset]),'--output-filename='+str(output),'--',text.strip()]
    try:
        if cancel_event is None:
            result=subprocess.run(command,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=90,env=env,cwd=str(Path(executable).parent))
        else:
            process=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,env=env,cwd=str(Path(executable).parent))
            try:
                deadline=time.monotonic()+90
                while process.poll() is None:
                    if cancel_event.wait(.1):raise ValueError('Sprachausgabe gestoppt.')
                    if time.monotonic()>deadline:raise ValueError('Die Sprachengine hat nicht rechtzeitig geantwortet.')
                result=process
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:process.wait(timeout=2)
                    except subprocess.TimeoutExpired:process.kill();process.wait()

        if result.returncode:raise ValueError('Die neuronale Stimme konnte nicht sprechen. Bitte das Sprachpaket und eventuelle macOS-Sicherheitsmeldungen prüfen. Es wird keine Roboter- oder Systemstimme eingeschaltet.')
        return wave_bytes(output)
    except (OSError,subprocess.SubprocessError):raise ValueError('Die neuronale Sprachengine konnte nicht gestartet werden. Es wird keine andere Stimme verwendet.') from None


class NaturalVoice:
    def __init__(self,data_dir=None):
        self.root=(Path(data_dir) if data_dir is not None else default_data_dir())/'natural-voice'
        self.lock=threading.Lock();self.record=None;self.signatures=None;self.waiters=threading.BoundedSemaphore(4);self.events={};self.event_lock=threading.Lock()
    def _inside(self,relative):
        if not isinstance(relative,str) or Path(relative).is_absolute():raise ValueError('Ungültiger Sprachpfad.')
        path=(self.root/relative).resolve()
        if not path.is_relative_to(self.root.resolve()):raise ValueError('Sprachpfad verlässt den privaten Ordner.')
        return path
    def verify(self):
        path=self.root/'installed.json'
        if not path.is_file() or path.stat().st_size>1000000:raise ValueError('Die natürliche Stimme ist noch nicht eingerichtet. Bitte den separaten Stimmen-Nachrüsthelfer verwenden.')
        record=json.loads(path.read_text())
        if record.get('version')!=1 or record.get('architecture')!=platform.machine() or not isinstance(record.get('files'),dict) or not 1<=len(record['files'])<=3000:raise ValueError('Die natürliche Stimme ist für diesen Mac nicht gültig eingerichtet.')
        signatures={}
        for relative,checksum in record['files'].items():
            file=self._inside(relative)
            if not isinstance(checksum,str) or len(checksum)!=64 or not file.is_file() or digest(file)!=checksum:raise ValueError('Eine Sprachdatei fehlt oder wurde verändert. Bitte den Nachrüsthelfer erneut starten.')
            stat=file.stat();signatures[relative]=(stat.st_size,stat.st_mtime_ns)
        for key in ['executable','model','tokens']:
            if record.get(key) not in record['files']:raise ValueError('Unvollständige Sprachinstallation.')
        if not self._inside(record.get('data_dir','')).is_dir():raise ValueError('Sprachdaten fehlen.')
        self.record=record;self.signatures=signatures
        return record
    def status(self):
        try:
            if self.record is None:self.verify()
            return {'installed':True,'name':'Thorsten · natürliche deutsche Offline-Stimme','message':'Neuronale Stimme eingerichtet. Kein Konto und kein externer Sprachdienst.'}
        except (OSError,ValueError,TypeError,KeyError,RuntimeError):return {'installed':False,'name':'Thorsten','message':'Natürliche Stimme noch nicht eingerichtet oder beschädigt. Separaten Nachrüsthelfer verwenden.'}
    def cancel(self,request_id):
        if not isinstance(request_id,str) or not 1<=len(request_id)<=80:raise ValueError('Ungültige Sprachkennung.')
        with self.event_lock:
            event=self.events.get(request_id)
            if event:event.set()
        return {'ok':True}
    def synthesize(self,text,preset='jarvis',request_id=None,background=False):
        if not isinstance(text,str) or not text.strip() or len(text)>1800:raise ValueError('Bitte 1 bis 1.800 Zeichen zum Sprechen senden.')
        if not isinstance(preset,str) or preset not in {'jarvis','clear','system'}:raise ValueError('Unbekanntes Stimmprofil.')
        if type(background) is not bool or (request_id is not None and (not isinstance(request_id,str) or not 1<=len(request_id)<=80)):raise ValueError('Ungültige Sprachoptionen.')
        if not self.waiters.acquire(blocking=False):raise ProviderError('Die Sprachwarteschlange ist voll. Bitte die Antwort erneut anhören.',429)
        event=threading.Event();acquired=False
        if request_id and not background:
            with self.event_lock:self.events[request_id]=event
        try:
            deadline=time.monotonic()+90
            while not acquired:
                if event.is_set():raise ValueError('Sprachausgabe gestoppt.')
                acquired=self.lock.acquire(timeout=.1)
                if time.monotonic()>deadline:raise ValueError('Sprachwarteschlange wartet zu lange. Bitte erneut anhören.')

            if self.record is None:self.verify()
            for relative,signature in self.signatures.items():
                stat=self._inside(relative).stat()
                if (stat.st_size,stat.st_mtime_ns)!=signature:self.verify();break
            record=self.record
            with tempfile.TemporaryDirectory(prefix='speech-',dir=self.root) as folder:
                return generate(self._inside(record['executable']),self._inside(record['model']),self._inside(record['tokens']),self._inside(record['data_dir']),text,Path(folder)/'speech.wav',preset,cancel_event=event)
        except (OSError,ValueError,TypeError,KeyError,RuntimeError) as error:raise ProviderError(str(error) if isinstance(error,ValueError) else 'Die natürliche Stimme ist nicht verfügbar. Bitte den Nachrüsthelfer prüfen.',503) from None
        finally:
            if acquired:self.lock.release()
            with self.event_lock:
                if request_id:self.events.pop(request_id,None)
            self.waiters.release()


def install(data_dir=None):
    if platform.system()!='Darwin':raise ValueError('Dieser Nachrüsthelfer ist für deinen Mac. Es wurde nichts installiert.')
    architecture=platform.machine();runtime=runtime_spec(architecture)
    voice=NaturalVoice(data_dir);root=voice.root
    if root.is_symlink():raise ValueError('Der private Sprachordner darf nicht umgeleitet sein.')
    root.mkdir(parents=True,exist_ok=True,mode=0o700)
    import fcntl
    descriptor=os.open(root/'install.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    try:
        try:fcntl.flock(descriptor,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise ValueError('Die Stimme wird bereits eingerichtet. Bitte dieses Fenster schließen.') from None
        if voice.status()['installed']:print('Die natürliche Stimme ist bereits geprüft eingerichtet. Kein neuer Download.',flush=True);return voice
        if shutil.disk_usage(root).free<500000000:raise ValueError('Bitte für die Einrichtung etwa 500 MB freien Speicher bereitstellen; dauerhaft wird weniger benötigt.')
        print('Lade nur die neue Stimme und Sprachengine, ungefähr 100–104 MB. Deine Text-KI bleibt erhalten.',flush=True)
        cache=root/'downloads';runtime_archive=verified_download(runtime,cache);model_archive=verified_download(MODEL,cache)
        stage=root/('build-'+uuid.uuid4().hex);stage.mkdir(mode=0o700);installed=None
        previous_manifest=(root/'installed.json').read_bytes() if (root/'installed.json').is_file() else None
        activated=False
        try:
            runtime_root=extract_archive(runtime_archive,stage/'engine');model_root=extract_archive(model_archive,stage/'voice')
            executable=runtime_root/'bin/sherpa-onnx-offline-tts';model=model_root/'de_DE-thorsten-medium.onnx';tokens=model_root/'tokens.txt';data=model_root/'espeak-ng-data'
            check_macho(executable,architecture)
            if not all(path.is_file() for path in [model,tokens]) or not data.is_dir():raise ValueError('Das deutsche Stimmenmodell ist unvollständig.')
            # Keep only the needed TTS executable and shared libraries, not ASR/demo tools.
            for path in (runtime_root/'bin').iterdir():
                if path!=executable:path.unlink()
            sample=stage/'voice-test.wav'
            print('Prüfe eine echte deutsche Sprachdatei …',flush=True)
            generate(executable,model,tokens,data,'Guten Tag, Sir. Die natürliche Stimme ist bereit.',sample);sample.unlink()
            installed=root/('voice-'+uuid.uuid4().hex);stage.rename(installed)
            def moved(path):return installed/path.relative_to(stage)
            executable,model,tokens,data=map(moved,[executable,model,tokens,data])
            files={str(path.relative_to(root)):digest(path) for path in installed.rglob('*') if path.is_file()}
            record={'version':1,'architecture':architecture,'executable':str(executable.relative_to(root)),'model':str(model.relative_to(root)),'tokens':str(tokens.relative_to(root)),'data_dir':str(data.relative_to(root)),'files':files}
            temporary=root/'installed.tmp';temporary.write_text(json.dumps(record));temporary.replace(root/'installed.json');activated=True;voice.verify()
            for path in [runtime_archive,model_archive]:path.unlink(missing_ok=True)
            size=sum(path.stat().st_size for path in installed.rglob('*') if path.is_file() and not path.is_symlink())
            print(f'Natürliche Stimme geprüft und installiert: {size/1000000:.1f} MB. Keine Text-KI neu geladen.',flush=True)
            return voice
        except BaseException:
            if stage.exists():shutil.rmtree(stage)
            if installed is not None and installed.exists():shutil.rmtree(installed)
            if activated:
                if previous_manifest is None:(root/'installed.json').unlink(missing_ok=True)
                else:(root/'installed.json').write_bytes(previous_manifest)
            raise
    finally:os.close(descriptor)
