import sys,tempfile,threading
from pathlib import Path
from http.server import ThreadingHTTPServer
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.quest_window import StaticHandler
from playwright.sync_api import sync_playwright
server=ThreadingHTTPServer(('127.0.0.1',0),StaticHandler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page();errors=[];api=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:api.append(r.url) if '/api/' in r.url else None);page.goto('http://127.0.0.1:'+str(server.server_port)+'/aeris');page.locator('.headset-window-note').wait_for();page.wait_for_function('()=>window.AerisScene?.objects.length===3');assert page.locator('#quick-mic').is_hidden();page.get_by_role('button',name='Projekte und Formen öffnen',exact=True).click();page.locator('#part-sphere').click();assert page.evaluate('AerisScene.objects.length')==4;page.get_by_role('button',name='VR-Fenster öffnen',exact=True).click();page.locator('.advanced-vr').evaluate('(d)=>d.open=true');assert page.locator('#xr-enter').is_disabled();page.wait_for_timeout(500);assert not api,api;assert not errors,errors;print('PASS: account-free static studio edits real shapes, never requests app APIs, hides camera/chat, explicitly disables immersive VR on this connection. No physical Quest tested.');browser.close()
finally:server.shutdown();server.server_close();thread.join(3)
