"""Cold starts with the actual Mac server stopped; no navigator.offline shortcut.
Checks optional cache failure, failed update rollback, notes, query routes and phone rails.
"""
import sys,tempfile,threading,json,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer,Handler,FRONTEND
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[2];fail_core=False;new_worker=False;server_stopped=False;slow_docs=False
class TestHandler(Handler):
 def _dispatch(self):
  global fail_core,new_worker,slow_docs
  path=self.path.split('?')[0]
  if slow_docs and path=='/':time.sleep(4)
  if path=='/vendor/three/RoomEnvironment.js':self._json({'error':'Optional test asset unavailable'},404);return
  if fail_core and path=='/device-style.css':self._json({'error':'Core test asset unavailable'},503);return
  if new_worker and path=='/aeris-sw.js':
   body=(FRONTEND/'aeris-sw.js').read_text().replace('aeris-workspace-v43','aeris-workspace-v44-test').encode();self._headers(200,'text/javascript',len(body));self.wfile.write(body);return
  return super()._dispatch()
with tempfile.TemporaryDirectory()as folder:
 app=Application(Path(folder)/'data');server=JarvisServer(('127.0.0.1',0),app);server.RequestHandlerClass=TestHandler;thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url='http://127.0.0.1:'+str(server.server_port);profile=str(Path(folder)/'browser');errors=[]
 try:
  with sync_playwright()as pw:
   opts={'executable_path':'/usr/bin/chromium','args':['--no-sandbox'],'viewport':{'width':320,'height':740},'user_agent':'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Version/17.0 Mobile/15E148 Safari/604.1','is_mobile':True,'has_touch':True}
   context=pw.chromium.launch_persistent_context(profile,**opts);page=context.pages[0];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(url+'/');page.locator('[data-device-app]').wait_for();page.locator('#offline-ready[data-ready=true]').wait_for(timeout=25000);page.wait_for_function('()=>!!navigator.serviceWorker.controller');assert page.locator('#device-layout-select').input_value()=='phone';assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');rail=page.locator('.rail').bounding_box();assert rail['height']<115 and rail['width']<=321,rail
   page.locator('.rail [data-view=notes]').click();page.locator('#note-title').fill('Ohne Mac behalten');page.locator('#note-body').fill('Meine Notiz bleibt auf dem Handy.');page.locator('#note-form button').click();page.wait_for_function("async()=>(await DeviceStore.get('workspace'))?.notes.some(n=>n.title==='Ohne Mac behalten')");page.evaluate("async()=>{await DeviceStore.chunk('offline-sentinel',new Blob(['keep']));const c=await caches.open('jarvis-device-runtime-3.13.0');await c.put('/device-runtime/3.13.0/test-sentinel',new Response('keep'));}")
   # A broken optional 3D asset must not prevent the actual phone shell installing.
   cache=page.evaluate('async()=>await caches.keys()');assert 'aeris-workspace-v43'in cache
   slow_docs=True;start=time.monotonic();page.goto(url+'/',wait_until='domcontentloaded');page.locator('[data-device-app]').wait_for();assert time.monotonic()-start<3.8;slow_docs=False
   new_worker=True;fail_core=True
   result=page.evaluate("""async()=>{const r=await navigator.serviceWorker.getRegistration();await r.update();const w=r.installing;if(w&&w.state!=='redundant'&&w.state!=='activated')await new Promise(resolve=>{w.addEventListener('statechange',()=>{if(['redundant','activated'].includes(w.state))resolve()});setTimeout(resolve,12000)});return {state:w?.state,keys:await caches.keys()};}""")
   assert result['state']=='redundant',result;assert 'aeris-workspace-v43'in result['keys'];assert 'aeris-workspace-v44-test'not in result['keys'];assert 'jarvis-device-runtime-3.13.0'in result['keys'];assert page.evaluate("async()=>(await DeviceStore.chunk('offline-sentinel')).text()")=='keep'
   server.shutdown();server.server_close();thread.join(3);server_stopped=True
   for path in ['/tablet?layout=phone','/','/mobile','/index.html','/brands#business']:
    page.goto(url+path,wait_until='domcontentloaded',timeout=12000);page.locator('[data-device-app]').wait_for();page.locator('#offline-ready[data-ready=true]').wait_for(timeout=12000);page.locator('#connection-badge').filter(has_text='OHNE MAC').wait_for(timeout=12000);assert page.evaluate('window.JarvisDeviceShellReady===true');assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
   page.locator('.rail [data-view=notes]').click();page.get_by_text('Ohne Mac behalten',exact=True).wait_for();page.locator('#device-layout-select').select_option('ipad');page.locator('#device-layout-select').select_option('normal');assert page.locator('[data-device-app]').count()==1;page.locator('#device-layout-select').select_option('phone');page.locator('.rail [data-view=chat]').click();page.locator('#device-chat-input').scroll_into_view_if_needed();page.locator('#device-chat-input').fill('Offline schreiben');assert page.locator('#quick-bar').evaluate("e=>getComputedStyle(e).position==='static'");page.screenshot(path=str(root/'artifacts/jarvis-handy-ohne-mac.png'));assert page.evaluate('navigator.onLine')is True;page.locator('#device-chat-input').focus();page.evaluate("()=>{Object.defineProperty(visualViewport,'height',{configurable:true,get:()=>innerHeight-250});visualViewport.dispatchEvent(new Event('resize'));}");assert page.locator('.rail').is_hidden();page.locator('#device-chat-input').blur();page.evaluate("()=>{delete visualViewport.height;visualViewport.dispatchEvent(new Event('resize'));}");page.locator('.rail').wait_for();page.locator('#device-toast').wait_for(state='hidden',timeout=7000);page.evaluate('window.scrollTo(0,0)');page.screenshot(path=str(root/'artifacts/jarvis-handy-ohne-mac.png'))
   # Reopen a new browser process/profile while the server remains completely off.
   context.close();context=pw.chromium.launch_persistent_context(profile,**opts);page=context.pages[0];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(url+'/tablet',wait_until='domcontentloaded',timeout=12000);page.locator('#offline-ready[data-ready=true]').wait_for(timeout=12000);page.locator('.rail [data-view=notes]').click();page.get_by_text('Ohne Mac behalten',exact=True).wait_for();assert page.evaluate("async()=>(await DeviceStore.chunk('offline-sentinel')).text()")=='keep';page.locator('#device-layout-select').select_option('phone');page.set_viewport_size({'width':1440,'height':900});rail=page.locator('.rail').bounding_box();assert rail['height']<115 and rail['width']<=601,rail;assert not errors,errors;context.close();print('PASS: phone root uses offline shell, optional asset failure does not block cache, failed core update keeps old working cache and model storage, real server-off navigation/root/mobile/query/brands and cold browser restart work, notes persist, no white document, no horizontal overflow or full-height phone rail, local view switching and nonsticky tools.')
 finally:
  app.studio_bridge.stop();app.office.stop();app.desktop.stop()
  if not server_stopped:server.shutdown();server.server_close();thread.join(3)
