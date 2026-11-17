"""Editor controls, real transformed geometry, device-local persistence and file transfer."""
import json,sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from playwright.sync_api import sync_playwright
with tempfile.TemporaryDirectory() as folder:
 app=Application(folder);server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url='http://127.0.0.1:'+str(server.server_port)
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.goto(url+'/aeris');page.get_by_role('button',name='Projekte und Formen öffnen',exact=True).click();page.locator('#template-room').click();assert page.evaluate('AerisScene.objects.length')==9;assert not page.locator('#show-arm').is_checked()
   page.get_by_role('button',name='Projekte und Formen öffnen',exact=True).click();sphere=page.evaluate('AerisScene.objects.find(o=>o.type==="sphere").id');page.locator('#part-list').select_option(sphere);page.locator('#part-sx').fill('1.4');page.locator('#part-sx').press('Tab');page.locator('#part-rotation').fill('45');page.locator('#part-rotation').press('Tab');page.locator('#part-duplicate').click();assert page.evaluate('AerisScene.objects.length')==10
   page.locator('#project-name').fill('VR-Raum');page.locator('#project-save').click();page.get_by_text('„VR-Raum“ auf diesem Gerät gespeichert.',exact=True).wait_for()
   with page.expect_download() as download:page.locator('#project-download').click()
   path=Path(folder)/'room.json';download.value.save_as(path);project=json.loads(path.read_text());assert project['name']=='VR-Raum';assert len(project['objects'])==10;assert project['objects'][-1]['sx']==1.4
   page.get_by_role('button',name='Fenster schließen').click()
   with page.expect_download() as download:page.get_by_role('button',name='3D-Modell als OBJ speichern').click()
   obj=Path(folder)/'room.obj';download.value.save_as(obj);text=obj.read_text();assert 'o sphere_' in text and 'o cylinder_' in text;assert text.count('\nv ')>200
   page.reload();page.wait_for_function('()=>window.AerisScene?.objects.length===10');assert page.evaluate('AerisScene.objects.at(-1).rotation')==45
   other=browser.new_page();other.goto(url+'/aeris');other.get_by_role('button',name='Projekte und Formen öffnen').click();other.locator('#project-import').set_input_files(path);other.wait_for_function('()=>AerisScene.objects.length===10');assert other.evaluate('AerisScene.objects.at(-1).sx')==1.4
   # Invalid input must leave the previously edited scene intact.
   other.get_by_role('button',name='Projekte und Formen öffnen').click();other.locator('#project-import').set_input_files({'name':'bad.json','mimeType':'application/json','buffer':json.dumps({'version':1,'objects':[{'type':'script','x':0}]}).encode()});other.get_by_text('Unbekannte Form.',exact=True).wait_for();assert other.evaluate('AerisScene.objects.length')==10
   page.get_by_role('button',name='3D-Werkstatt',exact=True).click();page.wait_for_timeout(800);page.screenshot(path='/tmp/aeris-project-studio.png');page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+2');assert page.evaluate('document.documentElement.scrollHeight<=innerHeight+2');page.evaluate('''()=>{for(const type of AerisModel.TYPES){const m=AerisModel.mesh({type,sx:1.4,sy:2,sz:.8,rotation:35});for(const f of m.faces){const a=m.vertices[f[0]],b=m.vertices[f[1]],c=m.vertices[f[2]],u=b.map((v,i)=>v-a[i]),v=c.map((n,i)=>n-a[i]),normal=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]],mid=f.reduce((s,i)=>s.map((n,k)=>n+m.vertices[i][k]/f.length),[0,0,0]);mid[1]-=.4;if(normal.reduce((s,n,i)=>s+n*mid[i],0)<-1e-9)throw Error('Inward export surface: '+type);}}}''');assert not errors,errors
   print('PASS: real room geometry, select/resize/rotate/duplicate via UI, named save and reload, JSON transfer to independent browser, OBJ primitives, invalid import is atomic, no arm by default, mobile layout.')
   browser.close()
 finally:app.office.stop();server.shutdown();server.server_close();thread.join(3)
