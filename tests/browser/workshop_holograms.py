"""Generic non-arm model: hologram picking, info, AI explanation, saved offline model."""
import json,sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from tests.test_workshop_free import RAW
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory()as folder:
 app=Application(folder);app.store.update_settings({'ai_provider':'llamacpp','voice_enabled':False});calls=[];questions=[]
 def planner(*a,**kw):calls.append(a);return json.dumps(RAW)
 def transport(path,payload=None):questions.append(payload);return {'choices':[{'finish_reason':'stop','message':{'content':'Sir, dieses Bauteil gehört zur Ablage. Maße und Material siehst du direkt im Modell.'}}]}
 app.code_room._generate=planner;app.llamacpp.endpoint_transport=transport;server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url='http://127.0.0.1:'+str(server.server_port)
 try:
  with sync_playwright()as pw:
   browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']);context=browser.new_context(viewport={'width':1440,'height':1040},reduced_motion='reduce');page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.goto(url);page.locator('#offline-ready[data-ready=true]').wait_for(timeout=25000);result=page.evaluate("()=>JarvisExtras.command('Öffne die Hologramme')");page.locator('#build-studio[data-surface=hologram]').wait_for();assert not calls;page.locator('#build-starts summary').click();page.get_by_role('button',name='Organizer',exact=True).click();assert 'Organizer'in page.locator('#build-request').input_value();assert not calls
   page.locator('#build-request').fill('Ein runder Beistelltisch mit Ablage und stabilem Fuß');page.locator('#build-submit').click();page.wait_for_function("()=>document.getElementById('build-canvas').dataset.assembly==='complete'&&!document.getElementById('build-submit').disabled",timeout=90000);assert len(calls)==1;assert page.locator('#build-title').inner_text()=='Runder Beistelltisch'
   holo=page.locator('#build-canvas').screenshot();page.locator('#build-style').select_option('solid');solid=page.locator('#build-canvas').screenshot();assert holo!=solid;page.locator('#build-style').select_option('hologram');canvas=page.locator('#build-canvas').bounding_box();page.locator('#build-canvas').click(position={'x':canvas['width']*.5,'y':canvas['height']*.68});assert page.locator('#build-part-info').is_visible();assert 'mm'in page.locator('#build-part-info').inner_text();page.locator('#build-ask-part').click();page.locator('#build-chat').get_by_text('Sir, dieses Bauteil gehört zur Ablage.',exact=False).wait_for();assert '"part"'in questions[-1]['messages'][-1]['content'];page.locator('#build-studio').evaluate('e=>e.scrollTop=0');page.screenshot(path=str(root/'artifacts/jarvis-hologramme.png'))
   page.locator('#build-save').click();page.get_by_text('Entwurf auf diesem Gerät gespeichert.',exact=True).wait_for();page.locator('#build-close').click();page.goto(url+'/tablet?layout=ipad');page.locator('#offline-ready[data-ready=true]').wait_for(timeout=25000);context.set_offline(True);page.reload(wait_until='domcontentloaded');page.evaluate("()=>JarvisWorkshopOpen('Öffne die Hologramme')");page.locator('#build-load:enabled').click();page.get_by_text('Gesicherten Entwurf geladen.',exact=False).wait_for();assert page.locator('#build-studio').get_attribute('data-surface')=='hologram';assert page.locator('#build-title').inner_text()=='Runder Beistelltisch';page.set_viewport_size({'width':390,'height':844});assert page.locator('#build-studio').evaluate('e=>e.scrollWidth<=e.clientWidth+1');assert not errors,errors
   context.close();browser.close();print('PASS: spoken hologram opening, no stock model, different prompt categories, generic table renders in hologram/solid views, real part picking and local-AI explanation, offline saved hologram and phone fit. Controlled model geometry.')
 finally:app.workshop.stop();app.office.stop();app.desktop.stop();server.shutdown();server.server_close();thread.join(3)
