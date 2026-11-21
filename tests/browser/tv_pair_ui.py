"""The Mac connection UI exposes the short TV URL and existing six-digit code."""
import sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from playwright.sync_api import sync_playwright
with tempfile.TemporaryDirectory()as folder:
 app=Application(folder);server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 try:
  with sync_playwright()as p:
   b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=b.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.route('**/api/mobile/start',lambda route:route.fulfill(json={'tv_entry_url':'https://192.168.1.20:8766/tv','tv_code':'123456','fingerprint':'fixture fingerprint'}));page.goto('http://127.0.0.1:'+str(server.server_port));page.wait_for_function('()=>!!window.JarvisExtras');reply=page.evaluate("()=>JarvisExtras.command('Öffne die Fernseher-Verbindung')");assert 'geöffnet'in reply['reply'];page.locator('#tv-connect-dialog').get_by_role('button',name='TV-Verbindung vorbereiten').click();page.get_by_text('Kopplungscode 123456',exact=False).wait_for();assert page.locator('#tv-connection-link').get_attribute('href')=='https://192.168.1.20:8766/tv';assert not errors,errors;b.close();print('PASS: spoken TV connection command opens actual Mac dialog, short IP URL + six-digit code are shown, no long ticket needed. Pairing result uses fixture.')
 finally:app.office.stop();app.workshop.stop();app.desktop.stop();server.shutdown();server.server_close();thread.join(2)
