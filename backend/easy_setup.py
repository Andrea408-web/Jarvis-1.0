"""Explicit, app-local setup: verified public artifacts, no API keys or sudo."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import os
import platform
import re
import shutil
import stat
import subprocess
import tarfile
import tempfile
import time
import uuid
import zipfile

ROOT = Path(__file__).resolve().parent.parent
RELEASE_API = 'https://api.github.com/repos/ggml-org/llama.cpp/releases/latest'
MODEL_API = 'https://huggingface.co/api/models/Qwen/Qwen2.5-0.5B-Instruct-GGUF?blobs=true'
MODEL_NAME = 'qwen2.5-0.5b-instruct-q4_k_m.gguf'
MODEL_REPO = 'https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF'
MAX_MODEL = 450_000_000
MAX_RUNTIME = 150_000_000


class NoCompatibleRuntime(ValueError):
    """A release contains no usable binary for this exact architecture."""


def digest(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()


def _sha(value):
    return isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value) is not None


def _github_url(url):
    return isinstance(url, str) and url.startswith('https://github.com/ggml-org/llama.cpp/releases/download/') and not any(x in url for x in ['\n', '\r', '@', '#'])


def fetch(url, destination, maximum):
    """Native Mac curl keeps TLS verification; stdout is bounded binary data.

    No .curlrc, insecure flag, credentials, automatic retry or HTTP downgrade.
    Inherited proxy and CA configuration stay in force. Raw curl errors can
    contain signed redirect URLs, so only a safe error reaches the console.
    """
    if not isinstance(url, str) or not url.startswith('https://'):
        raise ValueError('Nur verifizierte HTTPS-Downloads sind erlaubt.')
    destination = Path(destination)
    command = ['/usr/bin/curl', '--disable', '--fail', '--silent', '--show-error', '--location',
               '--proto', '=https', '--proto-redir', '=https', '--connect-timeout', '15',
               '--max-time', '900' if maximum > 2_000_000 else '60', url]
    process = None
    try:
        with tempfile.TemporaryFile() as errors, destination.open('xb') as target:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=errors)
            size = 0
            next_report = time.monotonic() + 5
            while True:
                chunk = process.stdout.read(65536)
                if not chunk:
                    break
                size += len(chunk)
                if size > maximum:
                    raise ValueError('Der Download überschreitet die erlaubte Größe. Es wurde nichts gestartet.')
                target.write(chunk)
                if maximum > 2_000_000 and time.monotonic() >= next_report:
                    print(f'Download: {size/1_000_000:.1f} von {maximum/1_000_000:.1f} MB …', flush=True)
                    next_report = time.monotonic() + 5
            process.stdout.close()
            code = process.wait(timeout=10)
            if code:
                reasons = {6:'Die Internetadresse wurde nicht gefunden (DNS). Bitte die Verbindung prüfen.', 22:'Die offizielle Downloadquelle hat die Anfrage abgelehnt. Möglicherweise ist ein Zugriffslimit erreicht.', 28:'Der Download dauerte zu lange. Bitte die Internetverbindung prüfen.', 60:'macOS-curl kann das HTTPS-Zertifikat nicht prüfen. Bitte Datum, Uhrzeit und System-Vertrauensspeicher prüfen.'}
                raise ValueError(reasons.get(code, 'Download fehlgeschlagen. Bitte die Internetverbindung prüfen.') + ' Es wurde nichts gestartet; die TLS-Prüfung bleibt aktiv.')
        return size
    except (OSError, subprocess.SubprocessError):
        raise ValueError('Der sichere Download konnte nicht abgeschlossen werden. Es wurde nichts gestartet.') from None
    finally:
        if process is not None:
            if process.poll() is None:
                process.kill()
                process.wait()
            if process.stdout is not None:
                process.stdout.close()


def metadata(url):
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / 'metadata.json'
        fetch(url, path, 2_000_000)
        try:
            value = json.loads(path.read_bytes())
        except (ValueError, UnicodeError):
            raise ValueError('Die offizielle Downloadquelle lieferte keine gültigen Metadaten.') from None
    if not isinstance(value, dict):
        raise ValueError('Ungültige Download-Metadaten.')
    return value


def preflight(check_space=True):
    if platform.system() != 'Darwin':
        raise ValueError('Die einfache Einrichtung ist für den Mac. Hier wird nichts installiert.')
    version = platform.mac_ver()[0].split('.')
    if not version or not version[0].isdigit() or int(version[0]) < 14:
        raise ValueError('Diese Einrichtung benötigt macOS 14 oder neuer. Bitte den tatsächlichen Mac prüfen.')
    machine = platform.machine().lower()
    # A Python process may run under Rosetta while the Mac itself is ARM64.
    try:
        probe = subprocess.run(['/usr/sbin/sysctl', '-n', 'hw.optional.arm64'], capture_output=True, text=True, timeout=5)
        if probe.returncode == 0 and probe.stdout.strip() == '1':
            machine = 'arm64'
    except (OSError, subprocess.SubprocessError):
        pass
    architecture = {'arm64': 'arm64', 'aarch64': 'arm64', 'x86_64': 'x64', 'amd64': 'x64'}.get(machine)
    if architecture is None:
        raise ValueError('Für diese Mac-Architektur ist kein sicher ausgewähltes Paket vorgesehen.')
    if check_space and shutil.disk_usage(ROOT).free < 1_500_000_000:
        raise ValueError('Bitte mindestens 1,5 GB freien Speicher für Download, Modell und Entpacken bereitstellen.')
    return architecture


def select_runtime(release, architecture):
    assets = release.get('assets')
    if not isinstance(assets, list):
        raise ValueError('Keine offiziellen llama.cpp-Pakete gefunden.')
    matches = []
    arch_pattern = r'(?:arm64|aarch64)' if architecture == 'arm64' else r'(?:x64|x86_64|amd64)'
    for asset in assets:
        if not isinstance(asset, dict):
            continue
        name = asset.get('name', '')
        if (isinstance(name, str) and re.search(r'(?:macos|darwin|mac)[-_.]' + arch_pattern + r'(?:[-_.]|$)', name, re.I)
                and name.lower().endswith(('.zip', '.tar.gz', '.tgz'))
                and type(asset.get('size')) is int and 0 < asset['size'] <= MAX_RUNTIME
                and _github_url(asset.get('browser_download_url'))):
            matches.append(asset)
    if not matches:
        raise NoCompatibleRuntime('Die offizielle Version bietet kein passendes fertiges Mac-Paket. Es wird keine andere Architektur installiert.')
    matches.sort(key=lambda a: (not _sha((a.get('digest') or '').removeprefix('sha256:')), not a['name'].endswith('.zip'), a['name']))
    asset = matches[0]
    size = asset.get('size')
    if type(size) is not int or not 0 < size <= MAX_RUNTIME or not _github_url(asset.get('browser_download_url')):
        raise ValueError('Das Startpaket ist zu groß oder stammt nicht von der erwarteten offiziellen Quelle.')
    checksum = asset.get('digest', '') or ''
    if checksum.startswith('sha256:'):
        checksum = checksum[7:]
    if not _sha(checksum):
        # Older GitHub assets may publish checksums as a separate release file.
        checksum = ''
        for item in assets:
            if not isinstance(item, dict) or not re.fullmatch(r'(?:sha256sums(?:\.txt)?|checksums(?:\.txt)?|sha256\.txt)', item.get('name', ''), re.I):
                continue
            if not _github_url(item.get('browser_download_url')):
                continue
            with tempfile.TemporaryDirectory() as temp:
                path = Path(temp) / 'checksums'
                fetch(item['browser_download_url'], path, 1_000_000)
                for line in path.read_text(errors='replace').splitlines():
                    found = re.fullmatch(r'([0-9a-fA-F]{64})\s+\*?' + re.escape(asset['name']), line.strip())
                    if found:
                        checksum = found.group(1).lower()
                        break
            if checksum:
                break
    if not _sha(checksum):
        raise ValueError('Das offizielle Startpaket hat keine prüfbare SHA256-Prüfsumme. Die Einrichtung stoppt, bevor es geladen oder ausgeführt wird.')
    return {'url': asset['browser_download_url'], 'size': size, 'sha256': checksum, 'name': asset['name']}


def resolve_runtime(architecture):
    """Follow the checksum-verified stable release's official build pointer.

    Current stable llama.cpp releases publish nightly-tag.txt instead of the
    binaries themselves. Follow that pinned build, not an arbitrary newer build
    and never a binary for another architecture.
    """
    release = metadata(RELEASE_API)
    try:
        return select_runtime(release, architecture)
    except NoCompatibleRuntime:
        pass
    pointers = [item for item in release.get('assets', [])
                if isinstance(item, dict) and item.get('name') == 'nightly-tag.txt']
    if len(pointers) != 1:
        raise NoCompatibleRuntime(f'Kein passendes Mac-Paket für {architecture} und kein eindeutiger offizieller Build-Verweis gefunden.')
    pointer = pointers[0]
    size = pointer.get('size')
    raw_checksum = pointer.get('digest')
    checksum = raw_checksum.removeprefix('sha256:') if isinstance(raw_checksum, str) else ''
    if (type(size) is not int or not 1 <= size <= 64 or not _sha(checksum)
            or not _github_url(pointer.get('browser_download_url'))):
        raise ValueError('Der offizielle Build-Verweis konnte nicht sicher geprüft werden. Es wird kein Programm geladen.')
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary) / 'nightly-tag.txt'
        fetch(pointer['browser_download_url'], path, size)
        if path.stat().st_size != size or digest(path) != checksum:
            raise ValueError('Die Prüfsumme des offiziellen Build-Verweises stimmt nicht.')
        try:
            tag = path.read_text(encoding='ascii').strip()
        except UnicodeError:
            raise ValueError('Der offizielle Build-Verweis ist ungültig.') from None
    if not re.fullmatch(r'b[0-9]{1,12}', tag):
        raise ValueError('Der offizielle Build-Verweis enthält keine erlaubte Build-Kennung.')
    build = metadata(RELEASE_API.removesuffix('/latest') + '/tags/' + tag)
    if build.get('tag_name') != tag:
        raise ValueError('Die offiziellen Build-Metadaten passen nicht zum geprüften Verweis.')
    result = select_runtime(build, architecture)
    print(f'Passendes offizielles Mac-Paket gefunden: {result["name"]}', flush=True)
    return result


def select_model(info, repo=MODEL_REPO, names=None):
    revision=info.get('sha')
    if not isinstance(revision,str) or not re.fullmatch(r'[0-9a-f]{40,64}',revision):
        raise ValueError('Modellversion nicht sicher bestimmbar.')
    names=names or [MODEL_NAME,'qwen2.5-0.5b-instruct-q4_k_s.gguf','qwen2.5-0.5b-instruct-q4_0.gguf']
    files={item.get('rfilename'):item for item in info.get('siblings',[]) if isinstance(item,dict)}
    problems=[]
    for name in names:
        item=files.get(name)
        if not item:continue
        lfs=item.get('lfs') or {}
        if not isinstance(lfs,dict):continue
        values=[lfs[k].removeprefix('sha256:') if isinstance(lfs.get(k),str) else '' for k in ('sha256','oid') if k in lfs]
        size=lfs.get('size',item.get('size'))
        if not values or any(not _sha(v) for v in values) or len(set(values))!=1:
            problems.append(name+': SHA256 fehlt oder ist widersprüchlich');continue
        if type(size) is not int or size<1000000:
            problems.append(name+': Dateigröße fehlt');continue
        if size>MAX_MODEL:
            problems.append(f'{name}: {size/1000000:.1f} MB, über450MB');continue
        return {'url':repo+'/resolve/'+revision+'/'+name,'size':size,'sha256':values[0],'name':name,'source':repo}
    raise ValueError('Keine gültige kleine Modellvariante. '+'; '.join(problems or ['Dateien fehlen.']))


def resolve_model():
    sources=[(MODEL_REPO,MODEL_API,None),('https://huggingface.co/bartowski/Qwen2.5-0.5B-Instruct-GGUF',
        'https://huggingface.co/api/models/bartowski/Qwen2.5-0.5B-Instruct-GGUF?blobs=true',
        ['Qwen2.5-0.5B-Instruct-Q4_K_M.gguf','Qwen2.5-0.5B-Instruct-Q4_K_S.gguf','Qwen2.5-0.5B-Instruct-Q4_0.gguf'])]
    errors=[]
    for repo,url,names in sources:
        try:
            spec=select_model(metadata(url),repo,names)
            print(f'Kleine Modellvariante: {spec["name"]}, {spec["size"]/1000000:.1f} MB, Quelle: {repo}',flush=True)
            return spec
        except ValueError as error:errors.append(str(error))
    raise ValueError('Kein prüfbares Modell unter450MB gefunden; nichts Größeres geladen. '+' | '.join(errors))


def verified_download(spec):
    cache = ROOT / '.jarvis' / 'downloads'
    cache.mkdir(parents=True, exist_ok=True)
    final = cache / spec['sha256']
    if final.is_file() and final.stat().st_size == spec['size'] and digest(final) == spec['sha256']:
        return final
    # Do not overwrite a pre-existing invalid cache file or user data.
    temporary = cache / (spec['sha256'] + '.' + uuid.uuid4().hex + '.part')
    try:
        fetch(spec['url'], temporary, spec['size'])
        if temporary.stat().st_size != spec['size'] or digest(temporary) != spec['sha256']:
            raise ValueError('Die Download-Prüfsumme stimmt nicht. Die Datei wird nicht verwendet.')
        if final.exists():
            final = cache / (spec['sha256'] + '.' + uuid.uuid4().hex)
        temporary.rename(final)
        return final
    finally:
        temporary.unlink(missing_ok=True)


def _member_path(root, name):
    if not isinstance(name, str) or '\\' in name or '\x00' in name:
        raise ValueError('Unsicherer Archivpfad.')
    relative = PurePosixPath(name)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Das Archiv enthält einen unzulässigen Pfad.')
    return root.joinpath(*relative.parts)


def extract_runtime(archive, name):
    parent = ROOT / 'runtime'
    parent.mkdir(exist_ok=True)
    target = Path(tempfile.mkdtemp(prefix='verified-', dir=parent))
    links, entries, total = [], [], 0
    try:
        if name.endswith('.zip'):
            opened = zipfile.ZipFile(archive)
            for entry in opened.infolist():
                mode = entry.external_attr >> 16
                kind = 'dir' if entry.is_dir() else 'link' if stat.S_ISLNK(mode) else 'file'
                entries.append((entry.filename, kind, entry.file_size, mode, entry))
            stream = lambda item: opened.open(item)
        else:
            opened = tarfile.open(archive, 'r:gz')
            for entry in opened:
                if len(entries) >= 3000:
                    raise ValueError('Das Startpaket enthält zu viele Dateien.')
                if not (entry.isdir() or entry.isfile() or entry.issym()):
                    raise ValueError('Das Archiv enthält nicht unterstützte Spezialdateien.')
                entries.append((entry.name, 'dir' if entry.isdir() else 'link' if entry.issym() else 'file', entry.size, entry.mode, entry))
            stream = lambda item: opened.extractfile(item)
        with opened:
            if len(entries) > 3000:
                raise ValueError('Das Startpaket enthält zu viele Dateien.')
            for filename, kind, size, mode, entry in entries:
                path = _member_path(target, filename)
                if kind == 'dir':
                    path.mkdir(parents=True, exist_ok=True)
                    continue
                path.parent.mkdir(parents=True, exist_ok=True)
                if kind == 'link':
                    if isinstance(entry, zipfile.ZipInfo):
                        if size > 4096:
                            raise ValueError('Ungültiger Archivlink.')
                        link = opened.read(entry).decode('utf-8')
                    else:
                        link = entry.linkname
                    links.append((path, link))
                    continue
                total += size
                if size < 0 or total > 512 * 1024 * 1024:
                    raise ValueError('Das entpackte Startprogramm überschreitet die Speichergrenze.')
                written = 0
                with stream(entry) as source, path.open('xb') as output:
                    while True:
                        chunk = source.read(65536)
                        if not chunk:
                            break
                        written += len(chunk)
                        if written > size:
                            raise ValueError('Ungültige Archiv-Dateigröße.')
                        output.write(chunk)
                if written != size:
                    raise ValueError('Unvollständiges Startpaket.')
                path.chmod((mode & 0o755) or 0o644)
            for path, link in links:
                if not link or Path(link).is_absolute() or '\\' in link:
                    raise ValueError('Unsicherer Archivlink.')
                resolved = (path.parent / link).resolve()
                if not resolved.is_relative_to(target.resolve()):
                    raise ValueError('Ein Archivlink verlässt den vorgesehenen Ordner.')
                path.symlink_to(link)
            for path in target.rglob('*'):
                if not path.resolve().is_relative_to(target.resolve()):
                    raise ValueError('Unsichere Archivstruktur.')
        binaries = [p for p in target.rglob('llama-server') if p.is_file() and not p.is_symlink()]
        if len(binaries) != 1:
            raise ValueError('Kein eindeutiges llama-server-Startprogramm im Paket gefunden.')
        binary = binaries[0]
        binary.chmod(binary.stat().st_mode | stat.S_IXUSR)
        return target, binary
    except (zipfile.BadZipFile, tarfile.TarError, UnicodeError, EOFError):
        shutil.rmtree(target)
        raise ValueError('Das geprüfte Startpaket konnte nicht sicher entpackt werden.') from None
    except Exception:
        shutil.rmtree(target)
        raise


def _inside(relative):
    if not isinstance(relative, str):
        raise ValueError('Ungültiger lokaler Installationspfad.')
    result = (ROOT / relative).resolve()
    if Path(relative).is_absolute() or not result.is_relative_to(ROOT.resolve()):
        raise ValueError('Installationspfad liegt außerhalb des Projektordners.')
    return result


def read_installation(architecture=None):
    try:
        path = ROOT / '.jarvis' / 'installed.json'
        if path.stat().st_size > 2_000_000:
            raise ValueError()
        record = json.loads(path.read_text())
        if not isinstance(record, dict):
            raise ValueError()
        if record.get('version') != 1 or not isinstance(record.get('files'), dict) or not record['files']:
            raise ValueError()
        if architecture is not None and record.get('architecture') != architecture:
            raise ValueError()
        for relative, checksum in record['files'].items():
            path = _inside(relative)
            if not _sha(checksum) or not path.is_file() or digest(path) != checksum:
                raise ValueError()
        executable, model = _inside(record['executable']), _inside(record['model'])
        if record['executable'] not in record['files'] or record['model'] not in record['files']:
            raise ValueError()
        return executable, model
    except (OSError, ValueError, TypeError, KeyError, RuntimeError):
        raise ValueError('Bitte einmal „1-JARVIS-einrichten.command“ starten. Die lokale KI ist noch nicht vollständig eingerichtet oder eine Datei wurde verändert.') from None


def _prepare(architecture):
    try:
        existing = read_installation(architecture)
        print('Die geprüfte lokale KI ist bereits vorhanden. Kein neuer Download.', flush=True)
        return existing
    except ValueError:
        pass
    if shutil.disk_usage(ROOT).free < 1_500_000_000:
        raise ValueError('Bitte mindestens 1,5 GB freien Speicher für die Einrichtung bereitstellen.')
    runtime = resolve_runtime(architecture)
    model = resolve_model()
    print(f"Einmaliger Download: Startprogramm {runtime['size']/1_000_000:.1f} MB, kleines KI-Modell {model['size']/1_000_000:.1f} MB. Kein API-Schlüssel oder Anbieter-Guthaben.", flush=True)
    archive = verified_download(runtime)
    print('Startpaket geprüft. Lade und prüfe das kleine Modell …', flush=True)
    model_cache = verified_download(model)
    with model_cache.open('rb') as source:
        if source.read(4) != b'GGUF':
            raise ValueError('Die geprüfte Modelldatei ist kein GGUF.')
    target, executable = extract_runtime(archive, runtime['name'])
    try:
        files = {str(p.relative_to(ROOT)): digest(p) for p in target.rglob('*') if p.is_file()}
        files[str(model_cache.relative_to(ROOT))] = model['sha256']
        record = {'version': 1, 'architecture': architecture, 'executable': str(executable.relative_to(ROOT)),
                  'model': str(model_cache.relative_to(ROOT)), 'files': files}
        path = ROOT / '.jarvis' / 'installed.json'
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps(record))
        temporary.replace(path)
        return read_installation(architecture)
    except Exception:
        shutil.rmtree(target)
        raise


def prepare():
    architecture = preflight(check_space=False)
    import fcntl
    work = ROOT / '.jarvis'
    if work.is_symlink():
        raise ValueError('Der Einrichtungsordner darf kein symbolischer Link sein.')
    work.mkdir(exist_ok=True)
    descriptor = os.open(work / 'setup.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError('Die Einrichtung läuft bereits. Bitte das andere Einrichtungsfenster verwenden.') from None
        for directory in ['runtime', 'models', '.jarvis/downloads']:
            if (ROOT / directory).is_symlink():
                raise ValueError('Ein Einrichtungsordner ist umgeleitet. Vorhandene Dateien werden nicht überschrieben.')
        return _prepare(architecture)
    finally:
        os.close(descriptor)
