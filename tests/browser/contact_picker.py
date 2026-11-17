"""Contact correction and real local audio previews; never place a call or send."""
import io,math,struct,sys,tempfile,threading,wave
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[2];shots=root/'artifacts';shots.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory() as folder:
 app=Application(folder);app.store.update_settings({'voice_enabled':False});voice_calls=[];audio=io.BytesIO()
 with wave.open(audio,'wb') as out:out.setnchannels(1);out.setsampwidth(2);out.setframerate(16000);out.writeframes(b''.join(struct.pack('<h',int(1800*math.sin(i*.15))) for i in range(8000)))
 def voice(text,preset):voice_calls.append(text);return audio.getvalue()
 app.natural_voice.synthesize=voice
 server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url='http://127.0.0.1:'+str(server.server_port)
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--use-fake-device-for-media-stream','--use-fake-ui-for-media-stream']);page=browser.new_page(viewport={'width':1194,'height':900},accept_downloads=True);errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(url+'/tablet');page.locator('#device-voice').uncheck();page.locator('.rail [data-view="desk"]').click();page.get_by_text('Offline-Ablage bereit. Kein Mac benötigt.',exact=True).wait_for();page.locator('[data-desk="contacts"]').click()
   for name,email,phone in [('Lea · Beispiel','lea@example.com','+49 000 111'),('Leon · Beispiel','leon@example.com','+49 000 222')]:
    page.locator('#desk-contact-new').click();page.locator('#desk-contact-name').fill(name);page.locator('#desk-contact-email').fill(email);page.locator('#desk-contact-phone').fill(phone);page.locator('#desk-contact-form button.primary').click();page.wait_for_function('async name=>(await DeviceStore.get("desk-v1")).contacts.some(c=>c.name===name)',arg=name)
   page.locator('.rail [data-view="chat"]').click();page.locator('#device-chat-input').fill('Jarvis, rufe Liana an');page.locator('#chat-send').click();page.locator('#contact-picker[open]').wait_for();assert page.locator('#picker-list button').count()==2;assert 'Liana' in page.locator('#picker-heard').inner_text();page.screenshot(path=str(shots/'kontakte-auswahl.png'));page.locator('#picker-list').get_by_role('button',name='Lea · Beispiel',exact=False).click();assert page.locator('#desk-channel').input_value()=='call';assert page.get_by_role('link',name='Telefon-App öffnen').get_attribute('href')=='tel:+49000111';assert page.get_by_role('link',name='Mail-Entwurf öffnen').count()==0
   page.locator('.rail [data-view="chat"]').click();page.locator('#device-chat-input').fill('Schreibe eine E-Mail an Lena');page.locator('#chat-send').click();page.locator('#contact-picker[open]').wait_for();page.locator('#picker-list').get_by_role('button',name='Leon · Beispiel',exact=False).click();assert page.locator('#desk-channel').input_value()=='mail';page.locator('#desk-message').fill('Hallo Leon, wir sprechen morgen über die neue Idee.');assert 'leon%40example.com' in page.get_by_role('link',name='Mail-Entwurf öffnen').get_attribute('href')
   page.locator('#desk-voice-start').click();page.get_by_text('Sprachnachricht bereit. Du kannst sie anhören, als Datei speichern oder ausdrücklich teilen.',exact=True).wait_for();assert voice_calls==['Hallo Leon, wir sprechen morgen über die neue Idee.']
   with page.expect_download() as event:page.locator('#desk-voice-save').click()
   assert event.value.suggested_filename.endswith('.wav');assert Path(event.value.path()).read_bytes().startswith(b'RIFF');page.locator('#desk-voice-audio').scroll_into_view_if_needed();page.screenshot(path=str(shots/'sprachnachricht-vorschau.png'))
   page.locator('#desk-voice-kind').select_option('own');page.locator('#desk-voice-start').click();page.get_by_text('Aufnahme läuft. Sprich jetzt und tippe danach auf Stoppen.',exact=True).wait_for();page.wait_for_timeout(400);page.locator('#desk-voice-stop').click();page.get_by_text('Sprachnachricht bereit. Du kannst sie anhören, als Datei speichern oder ausdrücklich teilen.',exact=True).wait_for()
   with page.expect_download() as event:page.locator('#desk-voice-save').click()
   assert Path(event.value.path()).stat().st_size>100;assert len(voice_calls)==1
   page.goto(url+'/index.html');page.wait_for_function('()=>!!window.JarvisExtras');page.locator('#chat-input').fill('Schicke eine SMS an Lia');page.locator('#send-button').click();page.wait_for_url('**/tablet*');page.locator('#contact-picker[open]').wait_for();assert 'SMS' in page.locator('#picker-title').inner_text();assert page.locator('#picker-list button').count()==2;assert not errors,errors
   print('PASS: misheard names open all saved contacts; user chooses exact recipient/channel; no native links activated; actual WAV preview via test voice transport and real browser microphone recording export; classic Mac chat routes to the same picker. No call or message sent.');browser.close()
 finally:app.office.stop();app.desktop.stop();server.shutdown();server.server_close();thread.join(3)
