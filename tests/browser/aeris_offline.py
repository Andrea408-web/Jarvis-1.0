import sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from playwright.sync_api import sync_playwright
with tempfile.TemporaryDirectory() as folder:
 app=Application(folder);server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url='http://127.0.0.1:'+str(server.server_port)
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);context=browser.new_context();page=context.new_page();page.goto(url+'/aeris');page.locator('#aeris-core').wait_for();page.locator('#aeris-transition').wait_for(state='detached');page.screenshot(path='/tmp/aeris-core.png',full_page=False)
   page.wait_for_function('()=>document.getElementById("offline-status").textContent.includes("automatisch gespeichert")');awaiting=page.evaluate('()=>navigator.serviceWorker.controller!==null');assert awaiting
   context.set_offline(True);page.reload(wait_until='domcontentloaded');page.get_by_role('button',name='3D-Werkstatt',exact=True).click();page.get_by_role('button',name='Würfel hinzufügen',exact=True).click();page.get_by_role('button',name='3D-Modell als OBJ speichern',exact=True).click();page.get_by_text('OBJ-Datei mit 1 Objekten erstellt.',exact=False).wait_for();assert page.locator('#aeris-core').count()==1
   context.set_offline(False);page.locator('#aeris-transition').wait_for(state='detached');page.get_by_role('button',name='Astra',exact=True).click();page.wait_for_url('**/index.html');assert app.store.settings()['assistant_identity']=='astra'
   print('PASS: own core/icon, cached offline 3D workspace and OBJ export, real Astra mode switch. Offline AI/Thorsten not provided.')
   browser.close()
 finally:app.office.stop();server.shutdown();server.server_close();thread.join(3)
