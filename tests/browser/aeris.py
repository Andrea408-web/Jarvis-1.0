import sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from playwright.sync_api import sync_playwright
with tempfile.TemporaryDirectory() as folder:
 app=Application(folder);server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page(accept_downloads=True);errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto('http://127.0.0.1:'+str(server.server_port)+'/aeris');page.get_by_role('button',name='Würfel hinzufügen').click();page.locator('#shoulder').fill('45')
   with page.expect_download() as download:page.get_by_role('button',name='3D-Modell als OBJ speichern').click()
   path=Path(folder)/'scene.obj';download.value.save_as(path);data=path.read_text();assert data.count('\nv ')==8;assert data.count('\nf ')==6
   page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+2');assert not errors,errors;browser.close();print('PASS: Aeris scene, arm controls, actual OBJ geometry export, mobile layout. No headset tested.')
 finally:app.office.stop();server.shutdown();server.server_close();thread.join(3)
