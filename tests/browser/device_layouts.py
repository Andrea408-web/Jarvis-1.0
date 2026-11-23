"""Actual Mac/iPad/phone shells retain reachable input and bounded navigation."""
import sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory()as folder:
 app=Application(folder);app.store.update_settings({'ai_provider':'llamacpp','voice_enabled':False});server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();base='http://127.0.0.1:'+str(server.server_port)
 try:
  with sync_playwright()as pw:
   browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page(viewport={'width':1440,'height':960},reduced_motion='reduce');errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(base+'/index.html');page.wait_for_function('()=>!!window.JarvisExtras');page.locator('#desktop-tools-menu').wait_for();assert not page.locator('#desktop-tools-menu').evaluate('e=>e.open');assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');page.screenshot(path=str(ROOT/'artifacts/jarvis-mac-neu.png'))
   for mode,width,height in [('phone',390,844),('ipad',768,1024)]:
    page.set_viewport_size({'width':width,'height':height});page.goto(base+'/tablet?layout='+mode);page.wait_for_function('()=>!!window.JarvisDeviceShellReady');assert page.locator('#assistant-aeris').inner_text()=='Aeris';assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');page.locator('#device-chat-input').fill('Hallo Jarvis');page.locator('#device-chat-input').scroll_into_view_if_needed();assert page.locator('#device-chat-input').is_visible();assert page.locator('#device-chat-form button').first.is_visible();page.locator('#device-chat-input').fill('');page.locator('.rail [data-view=notes]').click();assert page.locator('#view-notes').is_visible();page.locator('.rail [data-view=chat]').click();page.evaluate('scrollTo(0,0)');page.screenshot(path=str(ROOT/('artifacts/jarvis-handy-neu.png'if mode=='phone'else'artifacts/jarvis-ipad-neu.png')))
   assert not errors,errors;browser.close();print('PASS: real Mac/iPad/phone shells show Aeris, composer remains reachable, menus bounded and no horizontal overflow or page errors. Screenshots use actual app UI, no model-quality claim.')
 finally:app.office.stop();app.workshop.stop();app.desktop.stop();server.shutdown();server.server_close();thread.join(2)
