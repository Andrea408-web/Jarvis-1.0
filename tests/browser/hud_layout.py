"""Functional HUD navigation at six desktop, tablet and phone sizes."""
import sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory()as folder:
 app=Application(folder);app.store.update_settings({'voice_enabled':False,'ai_provider':'llamacpp'});server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();base='http://127.0.0.1:'+str(server.server_port)
 try:
  with sync_playwright()as p:
   browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page(reduced_motion='reduce');errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   for path,width,height,label in [('/index.html',1280,800,'mac-compact'),('/index.html',1440,960,'mac'),('/tablet?layout=phone',320,740,'phone-small'),('/tablet?layout=phone',390,844,'phone'),('/tablet?layout=ipad',768,1024,'ipad'),('/tablet?layout=ipad',1024,768,'ipad-landscape')]:
    page.set_viewport_size({'width':width,'height':height});page.goto(base+path);page.wait_for_function('()=>!!window.JarvisApps');page.locator('#jarvis-app-open').wait_for();assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');assert not page.locator('#hud-settings').evaluate('e=>e.open');assert page.locator('#device-layout-select').is_hidden();assert page.locator('#quick-bar').is_hidden();device='/tablet'in path
    compose=page.locator('#device-chat-form'if device else'#chat-form');box=compose.bounding_box();assert box['y']+box['height']<=height-(62 if device and width<=700 else 0)+2,(label,box)
    page.locator('#hud-settings>summary').click();page.locator('#device-layout-select').wait_for();assert page.locator('#device-layout-select').is_visible();assert page.locator('#offline-ready').is_visible();assert page.locator('#device-voice-retry'if device else'#clap-enabled').is_visible();page.locator('#hud-settings').evaluate('e=>e.open=false')
    page.locator('#jarvis-app-open').click();page.locator('#jarvis-app-menu').wait_for();page.locator('[data-app=lab]').click();page.locator('#technik-lab').wait_for();page.locator('#tl-close').click();
    if device:
     page.locator('#device-more-menu>summary').click();page.locator('.rail [data-view=setup]').click();assert page.locator('#view-setup').is_visible();page.locator('.rail [data-view=chat]').click()
    page.evaluate('scrollTo(0,0)');page.screenshot(path=str(ROOT/f'artifacts/jarvis-hud-{label}.png'))
   assert not errors,errors;browser.close();print('PASS: six desktop/tablet/phone sizes show usable core and composer without initial scrolling, no horizontal overflow, settings and Apps/Techniklabor navigation work. Actual UI screenshots; no model or audio-hardware claim.')
 finally:app.office.stop();app.workshop.stop();app.desktop.stop();server.shutdown();server.server_close();thread.join(2)
