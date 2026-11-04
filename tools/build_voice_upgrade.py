"""Build the small additive .command, never include model/runtime/user files."""
from pathlib import Path
import base64
import hashlib
import io
import json
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parents[1]
BASE='232ba23b1f7fa0df13753775170649aba88c4f2c'
FILES=['backend/agents.py', 'frontend/office.js', 'backend/render_scene.py']+['backend/models.py', 'backend/blender_scene.py', 'backend/persona.py', 'backend/local_ai.py', 'backend/ai.py', 'backend/openai_client.py']+['README.md', 'docs/EINFACH-STARTEN.md', 'docs/PRUEFUNG.md']+['backend/desktop.py', 'backend/astra_panel.js', 'frontend/astra.js', 'frontend/astra-panel.html', 'frontend/astra-panel.js', 'frontend/astra.css', 'frontend/world-news.js', 'docs/ASTRA.md']+['backend/natural_voice.py','backend/server.py','backend/storage.py','frontend/app.js','frontend/jarvis-voice.js','docs/NATUERLICHE-STIMME.md','frontend/artifacts.js','backend/hub.py','frontend/mini-hub.js','frontend/index.html','frontend/extras.js','frontend/extras.css','frontend/conversation.js']
subprocess.run(['git','rev-parse','--verify',BASE+'^{commit}'],cwd=ROOT,capture_output=True,check=True)
manifest={}
buffer=io.BytesIO()
with zipfile.ZipFile(buffer,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
    for name in FILES:
        data=(ROOT/name).read_bytes()
        previous=subprocess.run(['git','show',BASE+':'+name],cwd=ROOT,capture_output=True)
        accepted=[]
        for ref in ['bd17dfd','9bf0a4e','539bd30','4490b8e']:
            old=subprocess.run(['git','show',ref+':'+name],cwd=ROOT,capture_output=True)
            if old.returncode==0:accepted.append(hashlib.sha256(old.stdout).hexdigest())
        manifest[name]={'accepted_before':accepted,'before':hashlib.sha256(previous.stdout).hexdigest() if previous.returncode==0 else None,'after':hashlib.sha256(data).hexdigest()}
        info=zipfile.ZipInfo(name,date_time=(2026,11,3,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;archive.writestr(info,data)
    info=zipfile.ZipInfo('manifest.json',date_time=(2026,11,3,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;archive.writestr(info,json.dumps(manifest,sort_keys=True))
raw=buffer.getvalue();bootstrap=(ROOT/'tools/voice_upgrade_bootstrap.py').read_text().replace('__PAYLOAD_B64__',base64.b64encode(raw).decode()).replace('__PAYLOAD_SHA__',hashlib.sha256(raw).hexdigest())
header='''#!/bin/bash
# Additive, checksum-verified voice update. No full Jarvis/text-model download.
set -u
if ! command -v python3 >/dev/null 2>&1; then
  echo 'Python 3 fehlt. Bitte den Python-Interpreter deiner vorhandenen Jarvis-Installation verwenden.'
  read -r -p 'Zum Schließen Enter drücken.'
  exit 1
fi
JARVIS_VOICE_HELPER_DIR="$(cd -- "$(dirname -- "$0")" && pwd)" python3 - <<'JARVIS_VOICE_PYTHON'
'''
footer="\nJARVIS_VOICE_PYTHON\nvoice_update_status=$?\nread -r -p 'Zum Schließen Enter drücken.'\nexit \"$voice_update_status\"\n"
output=ROOT/'JARVIS-Stimme-nachruesten.command';output.write_text(header+bootstrap+footer);output.chmod(0o755)
print('Additive voice helper:',output.name,output.stat().st_size,'bytes')

archive_path=ROOT/'updates/JARVIS-Stimme-Nachruestung.zip';archive_path.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(archive_path,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
    info=zipfile.ZipInfo(output.name,date_time=(2026,11,3,0,0,0));info.external_attr=0o100755<<16;info.compress_type=zipfile.ZIP_DEFLATED;archive.writestr(info,output.read_bytes())
    archive.writestr('BITTE-LESEN.txt','Mini-Hub und natürliche Stimme nachrüsten, nicht Jarvis komplett neu laden.\nDie .command-Datei öffnen, gegebenenfalls deinen bestehenden Jarvis-Ordner wählen.\nDer Helfer lädt und prüft etwa 100–104 MB Sprachdaten. Danach Jarvis mit Control+C beenden und wie gewohnt neu starten.\nDeine Text-KI und Einstellungen bleiben erhalten.\n')
print('Small update ZIP:',archive_path.name,archive_path.stat().st_size,'bytes')

# Same reviewed source patch, without a voice/model download for an Astra update.
astra=ROOT/'JARVIS-Astra-aktualisieren.command'
astra.write_text(output.read_text().replace('JARVIS_VOICE_HELPER_DIR=', 'JARVIS_ASTRA_ONLY=1 JARVIS_VOICE_HELPER_DIR=',1));astra.chmod(0o755)
with zipfile.ZipFile(ROOT/'updates/JARVIS-Astra-Update.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
    info=zipfile.ZipInfo(astra.name,date_time=(2026,11,4,0,0,0));info.external_attr=0o100755<<16;info.compress_type=zipfile.ZIP_DEFLATED;archive.writestr(info,astra.read_bytes())
    archive.writestr('BITTE-LESEN.txt','Astra-Update: ZIP entpacken und JARVIS-Astra-aktualisieren.command öffnen.\nVorhandenen Jarvis-Ordner wählen. Danach Jarvis mit Control+C beenden und im Ordner mit python3 -m backend --easy-local neu starten.\nKeine neuen KI-Modelle und kein Stimmen-Download. Mini-Hub entfernt; Welt/Nachrichten und Astra ergänzt.\nEinfache 3D-Modelle über Blender; kein verlässlicher Fotobild-Nachbau. Desktop-Schritte vor dem Start prüfen.\n')
print('Astra update:',(ROOT/'updates/JARVIS-Astra-Update.zip').stat().st_size,'bytes; no model download')
