"""WebXR capability fallback, virtual grip ownership and session lifecycle with a controlled runtime."""
import sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from playwright.sync_api import sync_playwright
with tempfile.TemporaryDirectory() as folder:
 app=Application(folder);server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url='http://127.0.0.1:'+str(server.server_port)+'/aeris'
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']);page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.add_init_script("Object.defineProperty(navigator,'xr',{value:{isSessionSupported:async()=>false}})");page.goto(url);page.locator('#xr-enter').click();page.get_by_text('Dieser Browser bietet keinen immersiven VR-Modus.',exact=False).wait_for();assert page.locator('#xr-enter').is_enabled()
   page.evaluate("()=>{const s=window.AerisXRSimulation,a={},b={};const point=[...s.boxes[0].p];s.gripStep(a,point,true);if(s.boxes[0].owner!==a)throw Error('not grabbed');s.gripStep(b,point,true);if(s.boxes[0].owner!==a)throw Error('ownership stolen');s.gripStep(a,[.1,1.2,-.7],true);if(s.boxes[0].p[0]!==.1)throw Error('not moved');s.gripStep(a,null,false);if(s.boxes[0].owner!==null)throw Error('tracking loss did not release');}")
   obj=page.evaluate('()=>AerisXRSimulation.obj()');assert obj.count('\nv ')==24;assert obj.count('\nf ')==18
   session=browser.new_page();session.on('pageerror',lambda e:errors.append(str(e)));session.add_init_script("""(()=>{WebGLRenderingContext.prototype.makeXRCompatible=async()=>{};window.XRWebGLLayer=class{constructor(){this.framebuffer=null}getViewport(){return{x:0,y:0,width:1000,height:650}}};const eye={projectionMatrix:new Float32Array([1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]),transform:{inverse:{matrix:new Float32Array([1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1])}}};const runtime=new EventTarget();runtime.inputSources=[];runtime.renderState={};runtime.updateRenderState=x=>runtime.renderState=x;runtime.requestReferenceSpace=async()=>({});runtime.requestAnimationFrame=cb=>requestAnimationFrame(t=>cb(t,{getViewerPose:()=>({views:[eye]})}));runtime.end=async()=>runtime.dispatchEvent(new Event('end'));Object.defineProperty(navigator,'xr',{value:{isSessionSupported:async()=>true,requestSession:async()=>runtime}});})();""")
   session.goto(url);session.locator('#xr-enter').click();session.get_by_text('VR aktiv:',exact=False).wait_for();session.locator('#xr-exit').click();session.get_by_text('VR beendet.',exact=False).wait_for();assert session.locator('#xr-enter').is_enabled();assert not errors,errors
   print('PASS: unsupported-device fallback, pinch/controller grip simulation ownership/move/release, immersive GL session start/render/end with controlled XR runtime. No physical headset or real robot tested.')
   browser.close()
 finally:app.office.stop();server.shutdown();server.server_close();thread.join(3)
