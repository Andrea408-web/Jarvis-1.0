"""One user audio unlock followed by multiple automatic spoken responses."""
import sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from playwright.sync_api import sync_playwright
with tempfile.TemporaryDirectory() as folder:
 app=Application(folder);app.store.update_settings({'ai_provider':'llamacpp','voice_enabled':True});app.llamacpp.endpoint_transport=lambda *a,**k:{'choices':[{'finish_reason':'stop','message':{'content':'Das ist eine automatisch vorgelesene Antwort, Master.'}}]}
 server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--autoplay-policy=user-gesture-required']);page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.add_init_script("window.playedSpeech=0;document.addEventListener('playing',event=>{if(event.target.tagName==='AUDIO'&&event.target.duration>.1)window.playedSpeech++;},true);")
   page.goto('http://127.0.0.1:'+str(server.server_port));page.get_by_text('LOKALE VERBINDUNG AKTIV',exact=True).wait_for()
   page.locator('#chat-input').fill('Hallo');page.locator('#send-button').click();page.locator('#messages .message.user').first.wait_for();page.wait_for_function('()=>window.playedSpeech===1',timeout=20000)
   page.wait_for_function("()=>JarvisBridge.interaction().mode!=='speaking'",timeout=15000)
   page.evaluate('()=>JarvisConversation.stop()')
   page.locator('#chat-input').fill('Erzähl mir etwas');page.locator('#send-button').click();page.wait_for_function('()=>window.playedSpeech===2',timeout=20000)
   assert page.locator('#audio-readiness').is_hidden();assert not errors,errors
   print('PASS: two automatic actual speech playbacks under gesture-required autoplay; no per-answer replay click, including after ending conversation.')
   browser.close()
 finally:app.office.stop();server.shutdown();server.server_close();thread.join(3)
