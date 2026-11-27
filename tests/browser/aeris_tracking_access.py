"""Aeris assistant reaches its real tracking UI, with explicit camera consent and cleanup."""
import sys,tempfile,threading,json
from pathlib import Path
from unittest.mock import Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from backend.web_assistant import SEARCH
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory() as folder:
 app=Application(folder);app.store.update_settings({'voice_enabled':False,'ai_provider':'gemini'});app.selected_client=Mock(side_effect=AssertionError('Tools must not use the text model'))
 app.web.reader=lambda url:('<a class="result__a" href="https://example.com/solar">Solar-Ratgeber</a>' if url.startswith(SEARCH) else '<p>Solarmodule benötigen einen passenden Laderegler, damit die Batterie kontrolliert geladen werden kann.</p>',url)
 state={'confidence':.9};server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();base='http://127.0.0.1:'+str(server.server_port)
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page(viewport={'width':1360,'height':950});poses=[];errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.add_init_script("navigator.mediaDevices.getUserMedia=async()=>{const c=document.createElement('canvas');c.width=640;c.height=480;const ctx=c.getContext('2d');ctx.fillStyle='#182619';ctx.fillRect(0,0,640,480);window.mockCamera=c.captureStream(8);setInterval(()=>ctx.fillRect(0,0,640,480),100);return mockCamera;};")
   j={'wrist':{'x':.5,'y':.85},'thumbTip':{'x':.49,'y':.5}}
   for finger in ['index','middle','ring','little']:
    for part,y in [('MCP',.65),('PIP',.53),('DIP',.4),('Tip',.3)]:j[finger+part]={'x':.5,'y':y}
   j['indexTip']={'x':.51,'y':.5}
   def pose(route):poses.append(route.request.post_data_json);route.fulfill(json={'hands':[{'joints':j,'confidence':state['confidence']}],'arms':{}})
   page.route('**/api/aeris/pose',pose);page.goto(base+'/aeris');page.wait_for_function('()=>!!window.JarvisApps');page.locator('#iris-read').evaluate('e=>e.checked=false');page.locator('#iris-question').fill('Recherchiere Solarmodule mit Batterie');page.locator('#iris-send').click();page.locator('.iris-message.assistant .jarvis-source-link').wait_for();assert 'Laderegler' in page.locator('.iris-message.assistant').last.inner_text();page.locator('#iris-question').fill('Prüfe meinen Mac');page.locator('#iris-send').click();page.wait_for_function("()=>document.getElementById('iris-messages').textContent.includes('Momentaufnahme')");page.locator('#iris-question').fill('Mein ungesendeter Entwurf');page.locator('#iris-tracking').click();frame=page.frame_locator('#iris-tracking-dialog iframe');frame.locator('body[data-view=camera]').wait_for();assert not poses;assert frame.locator('#camera').evaluate('e=>!e.srcObject');frame.locator('#pose-on').click();frame.locator('#tracking-badge').get_by_text('PINCH / GREIFEN',exact=True).wait_for();assert poses and poses[0]['image'].startswith('/9j/');assert frame.locator('#aeris-holo-enabled').is_checked();j['thumbTip']={'x':.25,'y':.65};j['indexTip']={'x':.5,'y':.3};page.wait_for_function("()=>document.querySelector('#iris-tracking-dialog iframe').contentWindow.AerisHolo.scale>1.25");assert frame.locator('#aeris-holo-core').is_visible();assert frame.locator('#panel').is_hidden();page.screenshot(path=str(ROOT/'artifacts/aeris-handkern-gross.png'));
   for finger in ['index','middle','ring','little']:j[finger+'Tip']['y']=.76
   page.wait_for_function("()=>document.querySelector('#iris-tracking-dialog iframe').contentWindow.AerisHolo.scale<.95");state['confidence']=.1;frame.locator('#aeris-holo-core').wait_for(state='hidden');state['confidence']=.9
   for finger in ['index','middle','ring','little']:j[finger+'Tip']['y']=.3
   page.wait_for_function("()=>document.querySelector('#iris-tracking-dialog iframe').contentWindow.AerisHolo.scale>1.25");page.evaluate("window.heldCamera=document.querySelector('#iris-tracking-dialog iframe').contentWindow.mockCamera");page.screenshot(path=str(ROOT/'artifacts/aeris-handtracking-zurueck.png'));page.locator('#iris-tracking-close').click();page.wait_for_function("()=>heldCamera.getTracks().every(t=>t.readyState==='ended')");count=len(poses);page.wait_for_timeout(350);assert len(poses)==count;assert page.locator('#iris-question').input_value()=='Mein ungesendeter Entwurf';assert app.store.history()==[];assert not errors,errors;browser.close();print('PASS: Aeris research source links and read-only system tool, tracking dialog reaches camera view, no automatic camera frames, explicit tracked pinch, close stops camera/requests and preserves chat draft. Controlled camera and landmarks; physical Mac recognition not tested.')
 finally:app.office.stop();app.workshop.stop();app.desktop.stop();server.shutdown();server.server_close();thread.join(2)
