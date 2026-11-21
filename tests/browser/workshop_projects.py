"""General project planning does not build a prefab or hide user requirements."""
import sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory()as folder:
 app=Application(folder);app.store.update_settings({'ai_provider':'llamacpp'});chats=[]
 def chat(path,payload):
  chats.append(payload);return {'done':True,'message':{'content':'Sir, wir planen die Kugelbahn mit wechselbaren Strecken. Zuerst klären wir die Maße; ich habe noch kein Modell gebaut.'}}
 app.llamacpp.transport=chat;app.code_room._generate=lambda *a,**k:(_ for _ in ()).throw(AssertionError('Planning must not generate a model'))
 server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 try:
  with sync_playwright()as p:
   b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']);page=b.new_page(viewport={'width':1440,'height':1040},reduced_motion='reduce');errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto('http://127.0.0.1:'+str(server.server_port));page.wait_for_function('()=>!!window.JarvisWorkshopOpen');page.evaluate('()=>JarvisWorkshopOpen()')
   assert not page.locator('#build-special-projects').evaluate('e=>e.open');assert not page.locator('#build-hologram-guide').is_visible();assert page.locator('#build-result').is_hidden()
   page.locator('#build-starts summary').click();page.get_by_role('button',name='Kugelbahn',exact=True).click();assert 'Kugelbahn'in page.locator('#build-request').input_value();assert page.locator('#build-result').is_hidden();assert not chats
   page.locator('#build-project-plan summary').click();page.locator('#build-project-purpose').fill('Die Strecke soll austauschbar sein');page.locator('#build-project-resources').fill('Holz und Schraubendreher');page.locator('#build-project-budget').fill('60');page.locator('#build-project-days').fill('4');page.locator('#build-project-transfer').click();first=page.locator('#build-request').input_value();page.locator('#build-project-transfer').click();assert first==page.locator('#build-request').input_value()
   page.locator('#build-read').evaluate('e=>e.checked=false');page.locator('#build-project-discuss').click();page.locator('#build-chat').get_by_text('wir planen die Kugelbahn',exact=False).wait_for();assert len(chats)==1;prompt=chats[0]['messages'][-1]['content'];assert all(t in prompt for t in ['Kugelbahn','austauschbar','Holz','60','4']);assert page.locator('#build-result').is_hidden()
   page.locator('#build-project-plan').evaluate('e=>e.open=false');page.locator('#build-starts').evaluate('e=>e.open=true');page.locator('#build-studio').evaluate('e=>e.scrollTop=0');page.screenshot(path=str(root/'artifacts/jarvis-eigene-projekte.png'));page.locator('#build-request').fill('x'*1401);page.locator('#build-project-plan').evaluate('e=>e.open=true');page.locator('#build-project-discuss').click();assert '1400'in page.locator('#build-project-note').inner_text();assert len(chats)==1;assert page.locator('#build-request').input_value()=='x'*1401;page.set_viewport_size({'width':390,'height':844});assert page.locator('#build-studio').evaluate('e=>e.scrollWidth<=e.clientWidth+1');assert not errors,errors;b.close();print('PASS: broad project ideas, collapsed optics, no prefab generation, complete planning requirements reach local chat, repeated transfer stable and mobile fit.')
 finally:app.office.stop();app.workshop.stop();app.desktop.stop();server.shutdown();server.server_close();thread.join(2)
