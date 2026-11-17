"""Actual WebGL + real public reference geometry; camera/native landmarks are test doubles."""
import sys,tempfile,threading,time
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
root=Path(__file__).resolve().parents[2]
from playwright.sync_api import sync_playwright
from tests.glb_fixture import make_glb
reference=Path(sys.argv[1]) if len(sys.argv)>1 else None
raw=reference.read_bytes() if reference else make_glb();mode=['closed'];frames=[];loads=[]
def hand_detect(image):
 assert image.startswith(b'\xff\xd8\xff') and len(image)<=300000;frames.append(len(image))
 if mode[0]=='lost':return {'hands':[]}
 spread=.025 if mode[0]=='closed' else .22
 return {'hands':[{'confidence':.95,'joints':{key:{'x':x,'y':y,'confidence':.95}for key,x,y in [('wrist',.5,.8),('middleMCP',.5,.55),('thumbTip',.4,.3),('indexTip',.4+spread,.3)]}}]}
with tempfile.TemporaryDirectory()as folder,patch('backend.arm_pose.detect',side_effect=hand_detect),patch('backend.object_models.load_model',side_effect=lambda url:(loads.append(url),raw)[1]):
 app=Application(folder);app.store.update_settings({'voice_enabled':False});server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url='http://127.0.0.1:'+str(server.server_port)
 try:
  with sync_playwright()as pw:
   browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--use-fake-device-for-media-stream','--use-fake-ui-for-media-stream']);page=browser.new_page(viewport={'width':1450,'height':1020});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.route('**/api/objects/info',lambda route:route.fulfill(json={'camera_tracking':True}));page.goto(url+'/index.html');page.locator('#object-open').click();page.locator('#object-viewer[open]').wait_for();page.locator('#object-query').fill('Getriebe');page.locator('#object-search button').click();page.wait_for_function("()=>window.JarvisObjects?.inspect().parts>=2",timeout=30000)
   print('MODEL',page.locator('#object-quality').inner_text());assert loads and loads[0].endswith('/GearboxAssy.glb');assert errors==[],errors
   page.mouse.move(0,0);page.wait_for_timeout(500);page.screenshot(path=str(root/('artifacts/objekt-zusammen.png' if reference else 'artifacts/objekt-test-zusammen.png')))
   page.locator('#object-spread').fill('100');page.locator('#object-spread').dispatch_event('input');page.wait_for_timeout(400)
   assert page.evaluate("async()=>(await import('/object-viewer.js')).inspect().positions.some(p=>p.some(n=>Math.abs(n)>.01))")
   assert page.evaluate('()=>JarvisObjects.inspect().inFrame');page.screenshot(path=str(root/('artifacts/objekt-einzelteile.png' if reference else 'artifacts/objekt-test-einzelteile.png')))
   # Embedded model data cannot sneak an external texture or a graph cycle into the loader.
   checks=page.evaluate('''async()=>{const session=await(await fetch('/api/session')).json();const r=await fetch('/api/objects/load',{method:'POST',headers:{'Content-Type':'application/json','X-Jarvis-Token':session.token},body:JSON.stringify({url:'https://threejs.org/test.glb'})});const buffer=await r.arrayBuffer(),v=new DataView(buffer),n=v.getUint32(12,true),doc=JarvisObjects.validateGLB(buffer),rest=new Uint8Array(buffer,20+n);function pack(d){let j=new TextEncoder().encode(JSON.stringify(d));const len=(j.length+3)&~3,result=new ArrayBuffer(20+len+rest.length),out=new Uint8Array(result),head=new DataView(result);head.setUint32(0,0x46546c67,true);head.setUint32(4,2,true);head.setUint32(8,result.byteLength,true);head.setUint32(12,len,true);head.setUint32(16,0x4e4f534a,true);out.fill(32,20,20+len);out.set(j,20);out.set(rest,20+len);return result;}const result=[];const external=structuredClone(doc);external.images=[{uri:'https://example.invalid/private.png'}];try{JarvisObjects.validateGLB(pack(external));result.push(false);}catch(e){result.push(true);}const cycle=structuredClone(doc);cycle.nodes[0].children=[0];try{JarvisObjects.validateGLB(pack(cycle));result.push(false);}catch(e){result.push(true);}return result;}''');assert checks==[True,True]
   # An arbitrary picture cannot pass the GLB quality gate.
   page.locator('#object-file').set_input_files({'name':'fake.glb','mimeType':'model/gltf-binary','buffer':b'not a glb'});page.get_by_text('Bitte ein GLB-2.0-Modell bis 20 MB auswählen.',exact=True).wait_for();assert page.evaluate("async()=>(await import('/object-viewer.js')).inspect().parts>=2")
   bottle=Path('/tmp/jarvis-bottle.glb')
   if bottle.is_file():
    page.locator('#object-file').set_input_files(str(bottle));page.get_by_text('Qualitätsfilter: Das Modell enthält keine getrennten Bauteile. Fehlende Innenteile werden nicht erfunden.',exact=True).wait_for()
   page.locator('#object-camera-on').click();page.wait_for_function("()=>window.JarvisObjects.inspect().armed",timeout=15000);mode[0]='open';page.wait_for_function("()=>Number(document.getElementById('object-spread').value)>35",timeout=15000)
   mode[0]='closed';page.wait_for_function("()=>Number(document.getElementById('object-spread').value)<4",timeout=15000)
   mode[0]='lost';page.wait_for_function("()=>!window.JarvisObjects.inspect().armed",timeout=15000);page.locator('#object-spread').fill('70');page.locator('#object-spread').dispatch_event('input');before=page.evaluate("async()=>(await import('/object-viewer.js')).inspect().positions");page.wait_for_timeout(800);assert page.evaluate("async()=>(await import('/object-viewer.js')).inspect().positions")==before
   page.evaluate("()=>{window.testObjectTracks=document.getElementById('object-camera').srcObject.getTracks();}");page.locator('#object-close').click();page.wait_for_function("()=>window.testObjectTracks.every(t=>t.readyState==='ended')");page.wait_for_function("()=>window.JarvisObjects.inspect().parts===0");count=len(frames);page.wait_for_timeout(500);assert len(frames)==count
   page.set_viewport_size({'width':390,'height':844});page.locator('#object-open').click();assert page.locator('#object-viewer').evaluate('(e)=>e.scrollWidth<=e.clientWidth+1');page.locator('#object-close').click();assert not errors,errors;assert frames
   browser.close();print('PASS: actual WebGL reference model and separated real nodes, Internet-name route with test download, malformed file rejected without replacing model, calibrated camera gesture opens/closes parts, lost landmarks freeze pose, close stops camera and clears geometry, mobile fit. Camera feed and native macOS landmarks are simulated; no physical Mac camera is tested.')
 finally:app.office.stop();app.desktop.stop();server.shutdown();server.server_close();thread.join(3)
