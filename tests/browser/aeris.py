import sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from playwright.sync_api import sync_playwright
with tempfile.TemporaryDirectory() as folder:
 app=Application(folder);server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page(accept_downloads=True);errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto('http://127.0.0.1:'+str(server.server_port)+'/aeris');page.get_by_role('button',name='Chat öffnen',exact=True).click();page.get_by_text('Mit Jarvis auf deinem Mac verbunden.',exact=True).wait_for();page.locator('#voice').uncheck();page.locator('#chat-input').fill('Aeris, wer bist du?');page.get_by_role('button',name='Senden',exact=True).click();page.locator('#messages').get_by_text('Ich bin AERIS, Sir.',exact=True).wait_for();assert app.store.settings()['assistant_identity']=='jarvis';page.locator('#chat-input').fill('Erstelle einen Würfel');page.get_by_role('button',name='Senden',exact=True).click();page.locator('#messages').get_by_text('Ein Würfel wurde in die virtuelle Szene eingefügt, Master.',exact=True).wait_for();page.get_by_role('button',name='Armregler öffnen',exact=True).click();page.locator('#shoulder').fill('45');page.get_by_role('button',name='Fenster schließen').click()
   with page.expect_download() as download:page.get_by_role('button',name='3D-Modell als OBJ speichern').click()
   path=Path(folder)/'scene.obj';download.value.save_as(path);data=path.read_text();assert data.count('\nv ')==8;assert data.count('\nf ')==6
   page.screenshot(path='/tmp/aeris-studio.png');page.get_by_role('button',name='Energiekern',exact=True).click();page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+2');assert page.evaluate('document.documentElement.scrollHeight<=innerHeight+2');page.wait_for_timeout(750);page.screenshot(path='/tmp/aeris-mobile.png');assert not errors,errors;browser.close();print('PASS: Aeris scene, arm controls, actual OBJ geometry export, mobile layout. No headset tested.')
 finally:app.office.stop();server.shutdown();server.server_close();thread.join(3)
