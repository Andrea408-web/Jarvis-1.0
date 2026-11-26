"""Real UI and camera pipeline with controlled landmark responses; no physical Mac claim."""
import json,sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from playwright.sync_api import sync_playwright

def joints(kind='pinch',x=.5):
 out={'wrist':{'x':x,'y':.85},'thumbTip':{'x':x-.01,'y':.5}}
 for i,f in enumerate(['index','middle','ring','little']):
  fx=x+(i-1)*.04
  for part,y in [('MCP',.65),('PIP',.53),('DIP',.4),('Tip',.3)]:out[f+part]={'x':fx,'y':y}
 if kind=='pinch':out['indexTip']={'x':x+.01,'y':.5}
 else:
  out['thumbTip']={'x':x-.2,'y':.65}
  if kind=='fist':
   for f in ['index','middle','ring','little']:out[f+'Tip']['y']=.76
  if kind=='victory':
   for f in ['ring','little']:out[f+'Tip']['y']=.76
 return out

with tempfile.TemporaryDirectory() as folder:
 app=Application(folder);server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page();requests=[];errors=[];state={'kind':'pinch','x':.5,'hands':True};page.on('pageerror',lambda e:errors.append(str(e)))
   page.add_init_script("navigator.mediaDevices.getUserMedia=async()=>{const c=document.createElement('canvas');c.width=640;c.height=480;const ctx=c.getContext('2d');ctx.fillStyle='#152531';ctx.fillRect(0,0,640,480);const stream=c.captureStream(8);setInterval(()=>{ctx.fillRect(0,0,640,480)},100);window.cameraStream=stream;return stream;};")
   def pose(route):
    requests.append(route.request.post_data_json);route.fulfill(content_type='application/json',body=json.dumps({'arms':{},'hands':[{'joints':joints(state['kind'],state['x']),'confidence':.9}] if state['hands'] else [],'message':'Keine sichere Hand erkannt.'}))
   page.route('**/api/aeris/pose',pose);page.goto('http://127.0.0.1:'+str(server.server_port)+'/quest');page.get_by_role('button',name='Kamera und Handtracking',exact=True).click();page.get_by_role('button',name='Kamera einschalten',exact=True).click();page.wait_for_function('()=>document.getElementById("camera").videoWidth>0');page.wait_for_timeout(400);assert not requests
   page.get_by_role('button',name='Handtracking einschalten',exact=True).click();page.get_by_text('PINCH / GREIFEN',exact=True).wait_for();assert requests[0]['image'].startswith('/9j/');assert page.locator('#pose-overlay').is_visible()
   state['x']=.35;page.wait_for_function('()=>AerisScene.objects[0].x>.8');assert page.evaluate('AerisScene.objects.length')==1;page.get_by_role('button',name='Zieltraining starten',exact=True).click();state['x']=.2833;page.wait_for_function('()=>AerisScene.objects[0].x>1.15');state['kind']='palm';page.get_by_text('Zieltraining · 1 Treffer.',exact=True).wait_for()
   assert page.locator('#shoulder').input_value()!='32';state['hands']=False;page.get_by_text('HAND SUCHEN …',exact=True).wait_for();old=page.evaluate('AerisScene.objects[0].x');page.wait_for_timeout(350);assert page.evaluate('AerisScene.objects[0].x')==old
   state.update(hands=True,kind='palm');page.wait_for_function('()=>!document.getElementById("panel").hidden && !document.querySelector("[data-content=chat]").hidden');page.get_by_role('button',name='Fenster schließen').click();page.wait_for_timeout(1800);assert page.locator('#panel').is_hidden(),'Held gesture must not repeatedly reopen a panel'
   state['kind']='fist';page.wait_for_function('()=>AerisEffects.snow');page.wait_for_timeout(1900);assert page.evaluate('AerisEffects.snow'),'Held fist must toggle only once'
   page.get_by_role('button',name='Tracking stoppen',exact=True).click();count=len(requests);page.wait_for_timeout(450);assert len(requests)==count
   page.get_by_role('button',name='Kamera ausschalten',exact=True).click();assert page.evaluate('()=>cameraStream.getTracks().every(t=>t.readyState==="ended")')
   page.get_by_role('button',name='Gesten einstellen',exact=True).click();page.locator('#gesture-palm').select_option('snow');page.reload();page.get_by_role('button',name='Gesten einstellen',exact=True).click();assert page.locator('#gesture-palm').input_value()=='snow'
   page.get_by_role('button',name='Fenster schließen').click();page.get_by_role('button',name='Handtracking starten',exact=True).click();page.wait_for_function('()=>document.body.classList.contains("tracking")');page.get_by_role('button',name='Tracking stoppen',exact=True).click();page.get_by_role('button',name='Kamera ausschalten',exact=True).click();page.evaluate('''()=>{AerisTracking.reset();const arm=x=>({shoulder:{x,y:.2},elbow:{x,y:.45},wrist:{x,y:.7}});const hand={wrist:{x:.75,y:.7},middleMCP:{x:.75,y:.5},indexTip:{x:.74,y:.4},thumbTip:{x:.73,y:.4}};let f=AerisTracking.frame({arms:{left:arm(.75),right:arm(.2)},hands:[{joints:hand}]},{side:'auto',mirror:false,alpha:1});if(f.side!=='left')throw Error('wrong arm association');AerisTracking.calibrate(f.body);const a=AerisTracking.rig(f.body);const moved=arm(.75);moved.wrist.x=.95;const b=AerisTracking.rig(moved);if(Math.abs(a.elbow-b.elbow)<5)throw Error('rig does not move after calibration');}''');assert not errors,errors
   print('PASS: opt-in frames, finger pinch moves an actual virtual object, tracking loss releases, palm opens chat, fist toggles snow once, settings persist, stop cancels uploads and camera. Controlled landmarks; Apple Vision requires a real Mac test.')
   browser.close()
 finally:app.office.stop();server.shutdown();server.server_close();thread.join(3)
