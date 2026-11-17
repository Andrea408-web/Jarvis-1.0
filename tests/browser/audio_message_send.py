"""Real audio UI/API, a test native sender, no real email or SMS."""
import io,json,sys,tempfile,threading,wave
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from backend.confirmed_send import ConfirmedSend
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[2];shots=root/'artifacts';shots.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory() as folder:
 app=Application(folder);app.store.update_settings({'voice_enabled':False});sent=[];app.confirmed_send=ConfirmedSend(sender=lambda p:sent.append(p));buf=io.BytesIO()
 with wave.open(buf,'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000);w.writeframes(b'\0\0'*8000)
 audio=buf.getvalue();app.natural_voice.synthesize=lambda *a,**k:audio
 server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url='http://127.0.0.1:'+str(server.server_port)
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--use-fake-device-for-media-stream','--use-fake-ui-for-media-stream']);page=browser.new_page(viewport={'width':1194,'height':1000},accept_downloads=True);errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(url+'/tablet');page.locator('#device-voice').uncheck();page.locator('.rail [data-view="desk"]').click();page.get_by_text('Offline-Ablage bereit. Kein Mac benötigt.',exact=True).wait_for();page.locator('[data-desk="contacts"]').click();page.locator('#desk-contact-name').fill('Lea');page.locator('#desk-contact-email').fill('lea@example.test');page.locator('#desk-contact-form button.primary').click();page.wait_for_function('async()=>(await DeviceStore.get("desk-v1")).contacts.length===1');page.locator('#desk-message').fill('Hallo Lea, hier ist meine Sprachnachricht.');page.locator('#desk-voice-start').click();page.get_by_text('Sprachnachricht bereit. Du kannst sie anhören, als Datei speichern oder ausdrücklich teilen.',exact=True).wait_for()
   page.locator('#desk-voice-send').click();page.locator('#send-confirm[open]').wait_for();assert sent==[];assert page.locator('#send-audio-preview').is_visible();assert 'Jarvis-Sprachnachricht.wav' in page.locator('#send-audio-info').inner_text();plan=next(iter(app.confirmed_send.pending.values()))['payload'];assert plan['audio']['bytes']==audio;page.screenshot(path=str(shots/'sprachnachricht-senden.png'));page.locator('#send-cancel').click();page.wait_for_function('()=>!document.getElementById("send-confirm").open');assert sent==[]
   page.locator('#desk-voice-send').click();page.locator('#send-confirm[open]').wait_for();page.locator('#send-now').click();page.wait_for_function('()=>document.getElementById("send-confirm").dataset.state==="accepted"');assert len(sent)==1;assert sent[0]['audio']['bytes']==audio;assert sent[0]['address']=='lea@example.test';assert page.locator('#desk-voice-audio').is_hidden();page.locator('#send-cancel').click()
   page.locator('#desk-voice-kind').select_option('own');page.locator('#desk-voice-start').click();page.get_by_text('Aufnahme läuft. Sprich jetzt und tippe danach auf Stoppen.',exact=True).wait_for();page.wait_for_timeout(300);page.locator('#desk-voice-stop').click();page.get_by_text('Sprachnachricht bereit. Du kannst sie anhören, als Datei speichern oder ausdrücklich teilen.',exact=True).wait_for();page.locator('#desk-voice-discard').click();assert page.locator('#desk-voice-audio').is_hidden();page.locator('#desk-voice-send').click();page.get_by_text('Zuerst eine Sprachnachricht aufnehmen oder erstellen.',exact=True).wait_for();assert len(sent)==1
   state=page.evaluate("async()=>({desk:await DeviceStore.get('desk-v1'),workspace:await DeviceStore.get('workspace')})");assert 'RIFF' not in json.dumps(state);assert 'audio' not in json.dumps(state)
   page.locator('[data-desk="storage"]').click()
   with page.expect_download() as event:page.locator('#desk-backup').click()
   backup=Path(event.value.path()).read_text();assert 'audio' not in backup and 'RIFF' not in backup;assert not errors,errors;assert app.confirmed_send.pending=={};print('PASS: recorded/generated clip -> immutable audio preview -> explicit send, cancellation sends nothing, test sender receives exact bytes once, volatile preview cleared after acceptance, discard prevents reuse, no audio in local documents or backups. Native Mac Mail is not executed.');browser.close()
 finally:app.office.stop();app.desktop.stop();server.shutdown();server.server_close();thread.join(3)
