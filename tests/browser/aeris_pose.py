"""Opt-in camera frames, virtual pose updates and stopping, with controlled camera/pose data."""
import json,sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from playwright.sync_api import sync_playwright
with tempfile.TemporaryDirectory() as folder:
 app=Application(folder);server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page();requests=[];errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.add_init_script("navigator.mediaDevices.getUserMedia=async()=>{const c=document.createElement('canvas');c.width=640;c.height=480;const ctx=c.getContext('2d');ctx.fillStyle='blue';ctx.fillRect(0,0,640,480);const stream=c.captureStream(2);setInterval(()=>{ctx.fillRect(0,0,640,480)},250);window.cameraStream=stream;return stream;};")
   def pose(route):
    requests.append(route.request.post_data_json);route.fulfill(content_type='application/json',body=json.dumps({'arms':{'right':{'shoulder':{'x':.5,'y':.3,'confidence':.9},'elbow':{'x':.65,'y':.5,'confidence':.9},'wrist':{'x':.6,'y':.7,'confidence':.9}}},'message':'2D-Armtracking aktiv.'}))
   page.route('**/api/aeris/pose',pose);page.goto('http://127.0.0.1:'+str(server.server_port)+'/aeris');page.get_by_role('button',name='Kamera einschalten',exact=True).click();page.wait_for_function('()=>document.getElementById("camera").videoWidth>0');page.wait_for_timeout(600);assert not requests
   before=page.locator('#scene').evaluate('(c)=>c.toDataURL()');page.get_by_role('button',name='Armtracking starten',exact=True).click();page.get_by_text('2D-Armtracking aktiv.',exact=False).wait_for();assert page.locator('#scene').evaluate('(c)=>c.toDataURL()')!=before;assert requests[0]['image'].startswith('/9j/')
   page.get_by_role('button',name='Armtracking stoppen',exact=True).click();count=len(requests);page.wait_for_timeout(800);assert len(requests)==count
   page.get_by_role('button',name='Kamera ausschalten',exact=True).click();assert page.evaluate('()=>cameraStream.getTracks().every(t=>t.readyState==="ended")');assert not errors,errors
   print('PASS: camera preview sends no frames until explicit tracking, pose drives virtual scene, stop prevents further frames, camera tracks close. Controlled camera/landmarks; Apple Vision not run on hardware.')
   browser.close()
 finally:app.office.stop();server.shutdown();server.server_close();thread.join(3)
