"""Audio guidance must stay clickable inside modal dialogs and dismiss reliably."""
import sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from playwright.sync_api import sync_playwright
with tempfile.TemporaryDirectory() as folder:
 app=Application(folder);app.store.update_settings({'voice_enabled':True});server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.add_init_script("window.blockAudio=true;const realPlay=HTMLMediaElement.prototype.play;HTMLMediaElement.prototype.play=function(){return window.blockAudio?Promise.reject(new DOMException('Blocked fixture','NotAllowedError')):realPlay.call(this);};")
   url='http://127.0.0.1:'+str(server.server_port)
   page.goto(url);page.get_by_text('LOKALE VERBINDUNG AKTIV',exact=True).wait_for();page.get_by_role('button',name='Stimme',exact=True).click();page.locator('#voice-dialog #audio-readiness').wait_for();page.get_by_role('button',name='Audiohinweis schließen',exact=True).click();assert page.locator('#audio-readiness').is_hidden()
   page.get_by_role('button',name='Thorsten · Standard',exact=False).click();page.wait_for_timeout(500);assert page.locator('#audio-readiness').is_hidden()
   page.locator('#voice-dialog').get_by_role('button',name='Schließen',exact=True).click()
   page.reload();page.get_by_text('LOKALE VERBINDUNG AKTIV',exact=True).wait_for();page.get_by_role('button',name='Stimme',exact=True).click();page.locator('#voice-dialog #audio-readiness').wait_for();page.evaluate('()=>window.blockAudio=false');page.get_by_role('button',name='Automatisches Vorlesen aktivieren',exact=True).click();page.wait_for_function("()=>document.getElementById('audio-readiness').hidden");assert app.store.settings()['voice_enabled'];assert not errors,errors
   print('PASS: audio banner appears in modal top layer, dismisses without reopening on failed speech, and activation is clickable and succeeds.')
   browser.close()
 finally:app.office.stop();server.shutdown();server.server_close();thread.join(3)
