"""WebXR fallbacks, real render paths and VR/MR lifecycle with a controlled runtime."""
import sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from playwright.sync_api import sync_playwright
RUNTIME="""(()=>{
 WebGLRenderingContext.prototype.makeXRCompatible=async()=>{};
 window.XRWebGLLayer=class{constructor(){this.framebuffer=null}getViewport(){return{x:0,y:0,width:1000,height:650}}};
 const eye={projectionMatrix:new Float32Array([1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]),transform:{inverse:{matrix:new Float32Array([1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1])}}};
 const runtime=new EventTarget();window.mockPosePoint=[-.18,1.1,-.55];window.mockSource={gripSpace:{},gamepad:{buttons:[{pressed:true}]},handedness:'right'};
 runtime.inputSources=[mockSource];runtime.environmentBlendMode='alpha-blend';runtime.renderState={};runtime.updateRenderState=x=>runtime.renderState=x;runtime.requestReferenceSpace=async()=>({});
 runtime.requestAnimationFrame=cb=>requestAnimationFrame(t=>cb(t,{getViewerPose:()=>({views:[eye]}),getPose:space=>space===mockSource.targetRaySpace&&window.mockRayPoint?{transform:{position:{x:mockRayPoint[0],y:mockRayPoint[1],z:mockRayPoint[2]},matrix:new Float32Array([1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1])}}:mockPosePoint?{transform:{position:{x:mockPosePoint[0],y:mockPosePoint[1],z:mockPosePoint[2]}}}:null}));
 runtime.end=async()=>runtime.dispatchEvent(new Event('end'));
 Object.defineProperty(navigator,'xr',{value:{isSessionSupported:async()=>true,requestSession:async mode=>{window.requestedXRMode=mode;return runtime;}}});
})();"""
with tempfile.TemporaryDirectory() as folder:
 app=Application(folder);server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url='http://127.0.0.1:'+str(server.server_port)+'/aeris'
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']);page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.add_init_script("Object.defineProperty(navigator,'xr',{value:{isSessionSupported:async()=>false}})");page.goto(url);page.get_by_role('button',name='VR-Fenster öffnen').click();page.locator('.advanced-vr').evaluate('(d)=>d.open=true');page.locator('#xr-enter').click();page.get_by_text('Dieser Browser bietet keinen immersiven VR-Modus.',exact=False).wait_for();assert page.locator('#xr-enter').is_enabled()
   page.evaluate("()=>{const s=AerisXRSimulation,a={},b={};const point=[...s.boxes[0].p];s.gripStep(a,point,true);if(s.boxes[0].owner!==a)throw Error('not grabbed');s.gripStep(b,point,true);if(s.boxes[0].owner!==a)throw Error('ownership stolen');s.gripStep(a,[.1,1.2,-.7],true);if(s.boxes[0].p[0]!==.1)throw Error('not moved');s.gripStep(a,null,false);if(s.boxes[0].owner!==null)throw Error('tracking loss did not release');}")
   obj=page.evaluate('()=>AerisXRSimulation.obj()');assert obj.count('\nv ')==24;assert obj.count('\nf ')==18
   for mixed in [False,True]:
    session=browser.new_page();session.on('pageerror',lambda e:errors.append(str(e)));session.add_init_script(RUNTIME);session.goto(url);
    if mixed:
     session.wait_for_function('()=>document.getElementById("offline-status").textContent.includes("automatisch gespeichert")');session.context.set_offline(True);session.reload();
    session.get_by_role('button',name='VR-Fenster öffnen').click();session.locator('.advanced-vr').evaluate('(d)=>d.open=true');session.locator('#xr-passthrough').set_checked(mixed);session.locator('#xr-enter').click();session.get_by_text('Mixed Reality aktiv:' if mixed else 'VR aktiv:',exact=False).wait_for();assert session.evaluate('requestedXRMode')==('immersive-ar' if mixed else 'immersive-vr')
    session.wait_for_function('()=>AerisXRSimulation.boxes[0].owner===mockSource');session.evaluate('mockPosePoint=[.1,1.25,-.6]');session.wait_for_function('()=>AerisXRSimulation.boxes[0].p[0]===.1');session.evaluate('mockPosePoint=null');session.wait_for_function('()=>AerisXRSimulation.boxes[0].owner===null')
    session.evaluate('()=>{mockSource.gamepad.buttons[0].pressed=false;mockSource.targetRaySpace={};window.mockRayPoint=[-.420325,1.67185,-.3];}');session.wait_for_function('()=>AerisXRSimulation.hover==="box"');session.evaluate('mockSource.gamepad.buttons[0].pressed=true');session.wait_for_function('()=>AerisXRSimulation.boxes.length===4',timeout=6000);session.evaluate('mockSource.gamepad.buttons[0].pressed=false');session.wait_for_timeout(100);
    session.evaluate('''()=>{const s=AerisXRSimulation;s.action('undo');if(s.boxes.length!==3)throw Error('undo failed');const a={},b={},box=s.boxes[0],p=[...box.p];s.gripStep(a,p,true);s.twoHands([{source:a,point:p,closed:true},{source:b,point:[p[0]+.1,p[1],p[2]],closed:true}]);s.twoHands([{source:a,point:p,closed:true},{source:b,point:[p[0]+.2,p[1],p[2]+.1],closed:true}]);if(box.s[0]<=.1||Math.abs(box.yaw)<.1)throw Error('two hand scale/rotate failed');s.release(a);s.action('save');if(AerisScene.objects.length!==3)throw Error('VR project not saved');}''');session.locator('#xr-exit').click();session.get_by_text('VR beendet.',exact=False).wait_for();assert session.locator('#xr-enter').is_enabled();session.close()
   assert not errors,errors
   print('PASS: unavailable XR fallback, exclusive grip ownership, glass/arm GL render paths, controller move/loss/release, immersive-vr and immersive-ar start/render/end. Controlled runtime; no physical headset or real robot tested.')
   browser.close()
 finally:app.office.stop();server.shutdown();server.server_close();thread.join(3)
