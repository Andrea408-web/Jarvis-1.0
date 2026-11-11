"""Independent mobile UI, live real website artifact, desktop board and boot fallback."""
import json,sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from playwright.sync_api import sync_playwright
with tempfile.TemporaryDirectory() as folder:
 app=Application(folder);app.store.update_settings({'ai_provider':'llamacpp','voice_enabled':False})
 app.llamacpp.chat=lambda text,**kwargs:{'reply':json.dumps({'title':'Unser Radladen','intro':'Willkommen auf unserer Website.','sections':[{'title':'Werkstatt','text':'Reparaturen nach Absprache.'},{'title':'Besuch','text':'Kontaktdaten ergänzen.'}]}) if 'JSON' in text else 'Hallo, Master. Die mobile Ansicht funktioniert.'}
 server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url='http://127.0.0.1:'+str(server.server_port)
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
   mobile=browser.new_context(user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 Version/15.0 Mobile/15E148 Safari/604.1',viewport={'width':390,'height':844},is_mobile=True,has_touch=True);page=mobile.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.goto(url);page.get_by_text('Mit Jarvis auf deinem Mac verbunden.',exact=True).wait_for();assert page.locator('#office-3d').count()==0;page.locator('#voice').uncheck()
   page.locator('#chat-input').fill('Hallo');page.get_by_role('button',name='Senden',exact=True).click();page.get_by_text('Hallo, Master. Die mobile Ansicht funktioniert.',exact=True).wait_for()
   page.locator('#chat-input').fill('Erstelle eine Website für unseren Radladen');page.get_by_role('button',name='Senden',exact=True).click();page.locator('#jobs iframe').wait_for(timeout=10000);page.frame_locator('#jobs iframe').get_by_role('heading',name='Unser Radladen',exact=True).wait_for();assert page.get_by_role('link',name='HTML-Datei herunterladen').count()==1
   assert page.evaluate('()=>getComputedStyle(document.documentElement).backgroundColor')=='rgb(11, 13, 9)';assert not errors,errors
   desktop=browser.new_page(viewport={'width':1400,'height':1000});desktop.goto(url+'/index.html');desktop.get_by_text('LOKALE VERBINDUNG AKTIV',exact=True).wait_for();desktop.get_by_role('button',name='Auftragstafel',exact=True).click();desktop.locator('#task-board iframe').wait_for();desktop.frame_locator('#task-board iframe').get_by_role('heading',name='Unser Radladen',exact=True).wait_for()
   response=desktop.request.get(url+'/site/'+app.office.snapshot()['jobs'][0]['id']);assert 'sandbox' in response.headers['content-security-policy'];assert 'frame-ancestors' in response.headers['content-security-policy']
   # A failure of the main bundle must leave a visible, working mobile escape route.
   broken=browser.new_page();broken.route('**/app.js',lambda r:r.abort());broken.goto(url+'/index.html');broken.get_by_role('link',name='Einfache Jarvis-Ansicht öffnen',exact=True).wait_for(timeout=10000);broken.get_by_role('link',name='Einfache Jarvis-Ansicht öffnen',exact=True).click();broken.get_by_text('Mit Jarvis auf deinem Mac verbunden.',exact=True).wait_for()
   print('PASS: lightweight iPhone UI, actual chat, plain website request -> private real HTML artifact, mobile preview/download, live desktop board, CSP sandbox and visible fallback after a broken main bundle. No physical iOS device tested.')
   browser.close()
 finally:app.desktop.stop();app.office.stop();server.shutdown();server.server_close();thread.join(3)
