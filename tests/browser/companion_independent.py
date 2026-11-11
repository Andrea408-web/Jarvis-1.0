"""The small window handles its own chat, Thorsten playback and recognition after main closes."""
import sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from tests.test_natural_voice import wav_bytes
from playwright.sync_api import sync_playwright
with tempfile.TemporaryDirectory() as folder:
 app=Application(folder);app.store.update_settings({'voice_enabled':True});spoken=[]
 def voice(text,preset,**kwargs):spoken.append(text);return wav_bytes()
 app.natural_voice.synthesize=voice
 server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url='http://127.0.0.1:'+str(server.server_port)
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);main=browser.new_page();main.goto(url);main.get_by_text('LOKALE VERBINDUNG AKTIV',exact=True).wait_for()
   panel=browser.new_page();errors=[];panel.on('pageerror',lambda e:errors.append(str(e)))
   panel.add_init_script("window.recognitions=[];window.SpeechRecognition=class{constructor(){window.recognitions.push(this)}start(){this.onstart?.()}abort(){}};window.playbacks=0;document.addEventListener('playing',e=>{if(e.target.tagName==='AUDIO')window.playbacks++;},true);")
   panel.goto(url+'/astra-panel.html');panel.get_by_text('Eigenständiges Gespräch bereit.',exact=False).wait_for();main.close()
   panel.locator('#companion-input').fill('Was ist eins plus eins?');panel.get_by_role('button',name='Senden',exact=True).click();panel.locator('#companion-reply').get_by_text('1 + 1 = 2, Sir.',exact=True).wait_for();panel.wait_for_function('()=>window.playbacks>=1');assert spoken==['1 + 1 = 2, Sir.']
   panel.get_by_role('button',name='Gespräch starten',exact=True).click();panel.wait_for_function('()=>window.recognitions.length>0')
   panel.evaluate("()=>{const r=window.recognitions.at(-1);const result=[{transcript:'zwei plus zwei'}];result.isFinal=true;r.onresult({results:[result]});r.onend();}")
   panel.locator('#companion-reply').get_by_text('2 + 2 = 4, Sir.',exact=True).wait_for();panel.wait_for_function('()=>window.playbacks>=2');panel.wait_for_function('()=>window.recognitions.length>=2')
   panel.get_by_role('button',name='Gespräch beenden',exact=True).click();assert app.desktop.commands==[] or all(c['command']=='end' for c in app.desktop.commands)
   app.desktop.prepare({'goal':'Öffne Finder'});panel.locator('#companion-input').fill('Jarvis, stopp');panel.get_by_role('button',name='Senden',exact=True).click();panel.locator('#companion-reply').get_by_text('Der Desktop-Auftrag ist gestoppt, Sir.',exact=True).wait_for();assert app.desktop.plan['state']=='stopped'
   assert not errors,errors
   print('PASS: main tab closed, independent typed chat, own Thorsten audio path, own recognition/follow-up loop and stop. Controlled recognition/WAV; native macOS WebKit microphone availability not tested.')
   browser.close()
 finally:app.desktop.stop();app.office.stop();server.shutdown();server.server_close();thread.join(3)
