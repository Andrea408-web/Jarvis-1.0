"""Real launcher layout and navigation; supplied lab projects, no generated design claim."""
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
   for path,width,height,label in [('/index.html',1440,960,'mac'),('/tablet?layout=phone',390,844,'handy'),('/tablet?layout=ipad',768,1024,'ipad'),('/aeris',1280,900,'aeris')]:
    page.set_viewport_size({'width':width,'height':height});page.goto(base+path);page.wait_for_function('()=>!!window.JarvisApps&&!!window.JarvisCalls');page.locator('#jarvis-app-open').click();menu=page.locator('#jarvis-app-menu');menu.wait_for();assert menu.locator('.jam-grid button').count()==11;assert menu.locator('.jam-symbol svg').count()==11;assert menu.evaluate('e=>e.scrollWidth<=e.clientWidth+1');menu.screenshot(path=str(ROOT/f'artifacts/jarvis-apps-{label}.png'));page.locator('[data-app=lab]').click();page.locator('#technik-lab').wait_for();assert page.locator('#tl-projects').is_visible();page.locator('#tl-close').click();page.locator('#jarvis-app-open').click();page.locator('[data-app=phone]').click();page.locator('#phone-calls').wait_for();assert page.locator('#phone-calls a[href="/web-call"]').is_hidden();page.locator('#phone-close').click()
   page.goto(base+'/tablet?layout=phone');page.wait_for_function('()=>!!window.JarvisDeviceShellReady');page.locator('#jarvis-app-open').click();page.locator('[data-app=notes]').click();assert page.locator('#view-notes').is_visible();page.locator('#jarvis-app-open').click();page.locator('[data-app=planner]').click();assert page.locator('#view-planner').is_visible();page.locator('#jarvis-app-open').click();page.locator('[data-app=aeris]').click();page.wait_for_url(base+'/aeris');page.locator('#iris-title').wait_for();assert not errors,errors;browser.close();print('PASS: Mac/phone/iPad/Aeris original SVG launcher, eleven reachable apps, supplied Techniklabor, telephone without mandatory web-link, notes/planner navigation and Aeris route. Actual UI screenshots; no native call/hardware claim.')
 finally:app.office.stop();app.workshop.stop();app.desktop.stop();server.shutdown();server.server_close();thread.join(2)
