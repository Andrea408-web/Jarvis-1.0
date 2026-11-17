"""Mobile layouts keep their HUD; MacBook routes to the original control centre."""
import sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[2];shots=root/'artifacts';shots.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory() as folder:
 app=Application(folder);server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url='http://127.0.0.1:'+str(server.server_port)
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page(viewport={'width':1440,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.goto(url+'/tablet');page.wait_for_function("()=>document.getElementById('layout-toggle').textContent==='iPad-Modus'");page.locator('#layout-toggle').click();page.wait_for_function("()=>document.body.dataset.layout==='ipad'");assert page.locator('#layout-toggle').inner_text()=='MacBook-Modus';page.locator('#layout-toggle').click();page.wait_for_url('**/index.html');page.locator('.app-shell').wait_for();assert page.locator('.core-svg').count()==1;assert page.locator('[data-device-app]').count()==0;page.wait_for_timeout(1200);page.screenshot(path=str(shots/'macbook-klassisch.png'))
   page.goto(url+'/tablet');page.locator('.rail [data-view="setup"]').click();page.locator('#layout-normal').click();page.wait_for_url('**/index.html');page.locator('.app-shell').wait_for()
   page.goto(url+'/aeris');page.locator('#aeris-transition').wait_for(state='detached');page.wait_for_timeout(250);page.mouse.move(0,0);page.screenshot(path=str(shots/'aether-kern.png'));assert page.locator('#aeris-core').is_visible()
   page.goto(url+'/tablet');page.locator('.rail [data-view="setup"]').click();page.locator('#layout-phone').click();page.set_viewport_size({'width':390,'height':844});page.locator('.rail [data-view="chat"]').click();assert page.locator('#device-orb').is_visible();assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');assert not errors,errors;browser.close();print('PASS: both MacBook buttons restore original control centre; mobile HUD remains; new amber Aeris core renders; no JS errors.')
 finally:app.office.stop();app.desktop.stop();server.shutdown();server.server_close();thread.join(3)
