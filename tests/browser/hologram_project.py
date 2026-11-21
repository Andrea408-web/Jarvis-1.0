"""Physical reflector build workflow, no model call and no provider referral."""
import sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory()as folder:
 app=Application(folder);server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 try:
  with sync_playwright()as p:
   b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']);page=b.new_page(viewport={'width':1440,'height':1040},reduced_motion='reduce');errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto('http://127.0.0.1:'+str(server.server_port));page.wait_for_function('()=>!!window.JarvisWorkshopProject');page.evaluate('()=>JarvisWorkshopProject()');assert page.locator('#build-title').inner_text()=='Smartphone-Reflektor · Pepper’s Ghost';assert page.locator('#build-inline-steps li').count()>=5;assert '35.4'in page.locator('#build-inline-steps').inner_text();assert page.locator('#build-test-motif').is_visible();page.screenshot(path=str(root/'artifacts/jarvis-hologramm-bauen.png'));page.locator('#build-reflector-width').fill('80');page.locator('#build-reflector-recalculate').click();page.wait_for_function("()=>document.getElementById('build-inline-steps').textContent.includes('49.5')");page.locator('#build-test-motif').click();assert page.locator('dialog:visible').count()==2;page.get_by_role('button',name='Testmotiv schließen').click();assert not errors,errors;b.close();print('PASS: four real build panels, inline cut instructions, adjustable dimensions and fourfold optical test motif; no AI inference needed.')
 finally:app.office.stop();app.workshop.stop();server.shutdown();server.server_close();thread.join(2)
