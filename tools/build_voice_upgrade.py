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
FILES=['frontend/focus-mode.js','frontend/focus-mode.css','frontend/aeris-holo.js','frontend/discord-helper.js','backend/system_check.py','docs/KERN-SYSTEM.md','backend/system_info.py','frontend/core-entry.js','frontend/core-entry.css','backend/media.py','frontend/media-player.js','frontend/media-player.css','docs/MUSIK-VIDEO.md','frontend/jarvis-hud.js','frontend/jarvis-hud.css','frontend/call-intro.js','frontend/conversation-room.js','frontend/conversation-room.css','frontend/app-menu.js','frontend/app-menu.css','frontend/style.css','docs/ANRUFE.md','backend/phone_calls.py','frontend/phone-calls.js','frontend/phone-calls.css','frontend/web-call.html','frontend/web-call.js','frontend/web-call.css','docs/TECHNIKLABOR-IRIS.md','backend/technik_lab.py','frontend/technik-lab.js','frontend/technik-lab-layout.js','frontend/technik-lab.css','frontend/technik-lab-icons.svg','frontend/iris.html','frontend/iris.js','frontend/iris.css','frontend/iris-core.js','frontend/iris-icon.svg','frontend/tv.html', 'frontend/tv.js', 'frontend/tv.css', 'frontend/pair.js', 'USB-Jarvis/START-HIER.html', 'USB-Jarvis/LIES-MICH.txt', 'docs/FERNSEHER.md', 'Jarvis-TV-starten.command', 'backend/hologram_project.py', 'backend/workshop_requirements.py', 'backend/workshop_jobs.py', 'backend/workshop_schema.py', 'backend/llamacpp.py', 'backend/workshop_feedback.py', 'backend/workshop_contours.py', 'backend/workshop_free.py', 'backend/workshop.py', 'frontend/workshop-conversation.js', 'frontend/workshop.js', 'frontend/workshop.css', 'frontend/personal-brain.js', 'frontend/vendor/brain/fsaverage5.bin', 'frontend/vendor/brain/LICENSE.txt', 'frontend/vendor/brain/NOTICE.txt', 'backend/personal_profile.py', 'frontend/personal-store.js', 'frontend/personal-memory.js', 'frontend/personal-memory.css', 'frontend/offline-ready.js', 'frontend/offline-ready.css', 'backend/roblox_plan.py', 'frontend/roblox-hero-client.lua', 'frontend/roblox-hero-server.lua', 'backend/inventions.py', 'frontend/invention-lab.js', 'frontend/invention-lab.css', 'frontend/layout-switch.js', 'frontend/layout-switch.css', 'backend/studio_bridge.py', 'frontend/roblox-plugin.lua', 'frontend/code-companion.js', 'backend/code_room.py', 'frontend/code-room.js', 'frontend/code-room.css', 'frontend/studio-tools.js', 'frontend/studio-tools.css', 'frontend/chess-pieces.js', 'frontend/play-chess.js', 'frontend/chess-ai.js', 'frontend/chess-worker.js', 'frontend/vendor/chess/chess.js', 'frontend/vendor/chess/LICENSE', 'frontend/vendor/chess/NOTICE.txt', 'frontend/play.js', 'frontend/play.css', 'backend/object_models.py', 'frontend/object-viewer.js', 'frontend/object-viewer.css', 'frontend/vendor/three/three.module.min.js', 'frontend/vendor/three/GLTFLoader.js', 'frontend/vendor/three/OrbitControls.js', 'frontend/vendor/three/BufferGeometryUtils.js', 'frontend/vendor/three/RoomEnvironment.js', 'frontend/vendor/three/LICENSE', 'frontend/vendor/three/NOTICE.txt', 'frontend/device-polish.css', 'frontend/quick-help.js', 'backend/audio_send.py', 'backend/confirmed_send.py', 'frontend/contacts-panel.html', 'frontend/contacts-panel.js', 'backend/apple_contacts.py', 'frontend/contact-request.js', 'frontend/device-business.js', 'frontend/hud-core.js', 'frontend/device-desk.js', 'backend/device_ai.py', 'backend/brands.py', 'frontend/device.html', 'frontend/device-app.js', 'frontend/device-ai.js', 'frontend/device-store.js', 'frontend/device-style.css', 'docs/IPAD-UNTERWEGS.md', 'backend/companion_tk.py', 'backend/video_style.py', 'frontend/video-renderer.js', 'frontend/quest-hands.js', 'frontend/quest-assistant.js', 'backend/video_metadata.py', 'VR-Quest-verbinden.command', 'Jarvis-Helfer-starten.command', 'backend/easy_start.py', 'backend/video_editor.py', 'backend/video_native.js', 'frontend/video-editor.html', 'frontend/video-editor.js', 'frontend/companion-actions.js', 'backend/screen_view.py', 'backend/companion_window.py', 'backend/companion_window.js', 'frontend/jarvis-orb.js', 'frontend/companion.js', 'frontend/companion.css', 'backend/quest_window.py', 'frontend/headset-window.js', 'backend/quest_link.py', 'frontend/vr-guide.html', 'frontend/call.html', 'frontend/call-bridge.js', 'frontend/aeris-model.js', 'frontend/aeris-projects.js', 'backend/video_call.py', 'backend/native_vision.py', 'frontend/video-call.js', 'frontend/video-call.css', 'frontend/aeris-tracking.js', 'frontend/aeris-gestures.js', 'frontend/aeris-shell.css', 'frontend/aeris-shell.js', 'frontend/aeris-icon.svg', 'frontend/aeris-sw.js', 'backend/arm_pose.py', 'frontend/aeris-pose.js', 'frontend/aeris-xr.js', 'frontend/aeris-assistant.js', 'frontend/aeris.html', 'frontend/aeris.js', 'backend/everyday.py', 'frontend/discover.js', 'backend/task_router.py', 'backend/input_access.py', 'backend/website.py', 'frontend/mobile.html', 'frontend/mobile-app.js', 'frontend/boot.js', 'frontend/task-board.js', 'backend/web_assistant.py', 'backend/mobile.py', 'frontend/pair.html', 'frontend/manifest.webmanifest', 'frontend/app-icon.png', 'backend/dialogue.py', 'backend/notes.py', 'frontend/office-3d.js', 'frontend/lowpoly-stage.js', 'backend/agents.py', 'frontend/office.js', 'backend/render_scene.py', 'backend/models.py', 'backend/blender_scene.py', 'backend/persona.py', 'backend/local_ai.py', 'backend/ai.py', 'backend/openai_client.py', 'README.md', 'docs/EINFACH-STARTEN.md', 'docs/PRUEFUNG.md', 'backend/desktop.py', 'backend/astra_panel.js', 'frontend/astra.js', 'frontend/astra-panel.html', 'frontend/astra-panel.js', 'frontend/astra.css', 'frontend/world-news.js', 'docs/ASTRA.md', 'backend/natural_voice.py', 'backend/server.py', 'backend/storage.py', 'frontend/app.js', 'frontend/jarvis-voice.js', 'docs/NATUERLICHE-STIMME.md', 'frontend/artifacts.js', 'backend/hub.py', 'frontend/mini-hub.js', 'frontend/index.html', 'frontend/extras.js', 'frontend/extras.css', 'frontend/conversation.js']
subprocess.run(['git','rev-parse','--verify',BASE+'^{commit}'],cwd=ROOT,capture_output=True,check=True)
manifest={}
buffer=io.BytesIO()
with zipfile.ZipFile(buffer,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
    for name in FILES:
        data=(ROOT/name).read_bytes()
        previous=subprocess.run(['git','show',BASE+':'+name],cwd=ROOT,capture_output=True)
        accepted=[]
        for ref in ['31602bf','e4bcef0','b635c4e','c8a755f','683e271','966e26c','64067d2','de0678b','472560d','092f6eb','7d7a34e','7c045d5','d26ac7d','3e4d3e4','34f959f','256f8c1','4510dc2','62f1fba','a26e40c','d253c5a','b2513da','16a33db','d67d496','73dad6a','e9edd81','c6eb24b','57a5af3','89c5df1','694bafc','a3f3b3c','1b239bc','96cac06','bd17dfd','9bf0a4e','539bd30','4490b8e','9b30d32','ef0726f','2c234cb','43d6239','edbc0a0','a4f53df','6d16c7b','4129eb0','be6f74a','11c02f4','28d00a8','fd37579','c9eb5d3','108dc26','cf70d99','b57c755','fbe15c9','f683031','eb91d58','61babf6','a3b2dd8','24d8f0d','3dd8c69','04dce3c','38a72d6','504a8bb','f9111cb','64ced83','df58d55','c8a532e','18c327a','a17e5a3','6bcc307','507298a','ccef6c5','72e1781','3b9b5eb','9934a38','adbe59a','3030d57','9328319','c49b981','fa5c9f1','cfd2049','487db2a','6571cee','56f4107','7c8713f','7d5d94d','b69216f','b0b6239','0a1957c','d508f52','d3a5f6f','a524a1e','1761545','fd4c1a1']:
            old=subprocess.run(['git','show',ref+':'+name],cwd=ROOT,capture_output=True)
            if old.returncode==0:
                checksum=hashlib.sha256(old.stdout).hexdigest()
                if checksum not in accepted:accepted.append(checksum)
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
    for name in ['USB-Jarvis/START-HIER.html','USB-Jarvis/LIES-MICH.txt','docs/FERNSEHER.md']:
        archive.write(ROOT/name,name)
    archive.writestr('BITTE-LESEN.txt','ZIP entpacken und JARVIS-Astra-aktualisieren.command öffnen.\nJarvis Apps mit eigenen Symbolen, Techniklabor, Aeris und das Telefonmenü sowie die bisherigen Funktionen sind gemeinsam enthalten. USB-Jarvis ist eine optionale Browser-Starthilfe, keine Fire-TV-App oder eigenständige KI.\nDeinen vorhandenen Jarvis-Ordner wählen. Danach Jarvis im Terminal mit Control+C beenden und im selben Ordner mit python3 -m backend --easy-local neu starten. Browserseite neu laden.\nKeine neuen KI-Modelle und kein automatischer Stimmen-Download. Thorsten bleibt fest ausgewählt.\nDie Text-KI, Einstellungen und persönlichen Daten bleiben erhalten. Die neue Anleitung liegt danach unter docs/TECHNIKLABOR-IRIS.md. Sicherung ersetzter Programmdateien wird angelegt.\n')
print('Astra update:',(ROOT/'updates/JARVIS-Astra-Update.zip').stat().st_size,'bytes; no model download')
