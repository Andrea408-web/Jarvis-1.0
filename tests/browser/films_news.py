import sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from tests.test_natural_voice import wav_bytes
from playwright.sync_api import sync_playwright
with tempfile.TemporaryDirectory() as folder:
 app=Application(folder);app.store.update_settings({'voice_enabled':False});spoken=[]
 def voice(text,preset,**kw):spoken.append(text);return wav_bytes()
 app.natural_voice.synthesize=voice
 feed={'items':[{'title':'Testmeldung Deutschland','summary':'Eine Meldung aus Deutschland.','countries':['DE'],'url':'https://www.tagesschau.de/test','image':None},{'title':'Testmeldung USA','summary':'Nicht für Deutschland.','countries':['US'],'url':'https://www.tagesschau.de/test2','image':None}],'updated_at':'2026-11-11T12:00:00+00:00','stale':False}
 app.hub.news=lambda:feed
 server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto('http://127.0.0.1:'+str(server.server_port));page.get_by_text('LOKALE VERBINDUNG AKTIV',exact=True).wait_for()
   def send(text):page.locator('#chat-input').fill(text);page.locator('#send-button').click();page.wait_for_function("()=>!document.getElementById('send-button').disabled")
   send('Was kann ich für einen Film angucken?');page.locator('#discover-dialog').wait_for();assert page.locator('.discover-card').count()==3;assert page.locator('#discover-dialog a').count()==0;page.locator('#discover-dialog').get_by_role('button',name='Schließen',exact=True).click()
   send('Lies mir die Nachrichten aus Deutschland vor');page.locator('#world-dialog').wait_for();assert page.locator('#world-country').input_value()=='DE';assert page.locator('#world-articles article').count()==1;page.wait_for_function('()=>document.querySelector("audio")?.src.startsWith("blob:")');assert any('Testmeldung Deutschland' in s for s in spoken);assert not any('Testmeldung USA' in s for s in spoken)
   page.get_by_role('button',name='Ausgewählte Nachrichten vorlesen',exact=True).click();page.wait_for_timeout(250);assert len(spoken)>=2
   assert not errors,errors
   print('PASS: internal film cards without arbitrary links, country-filtered internal news and explicit Thorsten reading with global automatic voice disabled. Controlled feed/WAV.')
   browser.close()
 finally:app.office.stop();server.shutdown();server.server_close();thread.join(3)
