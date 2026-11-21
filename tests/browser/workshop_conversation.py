"""Discuss a real user's idea before opening; reuse local AI and all device layouts."""
import json,sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from playwright.sync_api import sync_playwright
with tempfile.TemporaryDirectory()as folder:
 app=Application(folder);app.store.update_settings({'ai_provider':'llamacpp','voice_enabled':False});calls=[]
 def transport(path,payload=None):
  calls.append(payload);return {'choices':[{'finish_reason':'stop','message':{'content':'Sir, dein Roboterarm könnte kleine Teile sortieren, ein Werkstück halten oder eine Kamera positionieren. Welche dieser Aufgaben wäre dir am wichtigsten?'}}]}
 app.llamacpp.endpoint_transport=transport;app.code_room._generate=lambda *a,**kw:(_ for _ in ()).throw(AssertionError('Opening an offered draft must not silently build it'))
 server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url='http://127.0.0.1:'+str(server.server_port)
 try:
  with sync_playwright()as pw:
   browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']);page=browser.new_page(viewport={'width':1440,'height':1040},reduced_motion='reduce');errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.goto(url);page.locator('#offline-ready[data-ready=true]').wait_for(timeout=25000)
   assert page.evaluate("()=>JarvisWorkshopRequest('Baue mir einen Roboterarm')")
   reply=page.evaluate("()=>JarvisExtras.command('Ich will einen Roboterarm bauen. Was könnte der machen?')");assert 'kleine Teile sortieren'in reply['reply'];assert 'Soll ich dazu das Baustudio öffnen'in reply['reply'];assert not page.locator('#build-studio').count();assert len(calls)==1
   reply=page.evaluate("()=>JarvisExtras.command('Was könnte er noch greifen?')");assert len(calls)==2;assert any('Roboterarm'in m['content']for m in calls[-1]['messages'][:-1]);assert not page.locator('#build-studio').count()
   reply=page.evaluate("()=>JarvisExtras.command('Ja, bitte.')");assert page.locator('#build-studio').is_visible();assert 'Roboterarm'in page.locator('#build-request').input_value();assert 'kleine Teile sortieren'in page.locator('#build-request').input_value();assert page.locator('#build-result').is_hidden();page.locator('#build-close').click()
   page.evaluate("()=>JarvisExtras.command('Welche Bauideen hätte ein Roboterarm?')");page.evaluate("()=>JarvisExtras.command('Nein, danke.')");assert not page.locator('#build-studio').is_visible()
   intro=page.evaluate("()=>JarvisExtras.command('Ich will einen Roboterarm bauen')");assert 'Soll ich dazu das Baustudio öffnen'in intro['reply'];page.evaluate("()=>JarvisExtras.command('Was kann er machen?')");assert any('Ich will einen Roboterarm bauen'in m['content']for m in calls[-1]['messages'][:-1]);assert not page.locator('#build-studio').is_visible()
   # Clear must erase the pending offer, without keeping a late reply alive.
   page.evaluate("()=>JarvisExtras.command('Was könnte ich für ein Bauprojekt machen?')");page.locator('#clear-chat').click();page.wait_for_function("()=>document.getElementById('messages').textContent.includes('Chatverläufe')");assert page.evaluate("()=>JarvisWorkshopConversation.command('Ja')")is None
   # Shared integration is used by the actual iPad/phone chat form.
   page.goto(url+'/tablet?layout=ipad');page.locator('#offline-ready[data-ready=true]').wait_for(timeout=25000);page.locator('#device-chat-input').fill('Was könnte ein Roboterarm bauen?');page.locator('#device-chat-form').evaluate('e=>e.requestSubmit()');page.get_by_text('Soll ich dazu das Baustudio öffnen',exact=False).wait_for();assert not page.locator('#build-studio').count();page.locator('#device-chat-input').fill('Ja');page.locator('#device-chat-form').evaluate('e=>e.requestSubmit()');page.locator('#build-studio').wait_for();assert 'Roboterarm'in page.locator('#build-request').input_value();assert page.locator('#build-result').is_hidden();assert not errors,errors
   page.close();browser.close();print('PASS: local-AI build discussion precedes studio; follow-up retains goal; yes opens transferred draft without generating; no stays in chat; clear removes offer; actual tablet chat uses the same offer flow. Controlled text model.')
 finally:app.workshop.stop();app.office.stop();app.desktop.stop();server.shutdown();server.server_close();thread.join(3)
