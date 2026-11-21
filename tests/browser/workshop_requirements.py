"""LED requirement regression and complex concept UI, with controlled inference data."""
import copy,json,sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from tests.workshop_complex_fixture import ARM
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory()as folder:
 app=Application(folder);app.store.update_settings({'ai_provider':'llamacpp'});calls=[];questions=[]
 def transport(path,payload=None):
  if 'response_format'not in payload:
   questions.append(payload);return {'choices':[{'finish_reason':'stop','message':{'content':'Sir, Steuerung und Versorgung sind in diesem Konzept noch offen. Wir müssen zuerst Antriebe und eine geeignete Abschaltung festlegen.'}}]}
  calls.append(payload)
  schema=payload['response_format']['json_schema']['schema']['anyOf'][0]
  assert 'lighting'in schema['required'];assert 'concept'in schema['required']
  raw=copy.deepcopy(ARM)
  if 'falsch zugeordnet'in payload['messages'][-1]['content']:
   raw['parts'][0]['material']='plastic' # Reproduces the reported mismatch, without inventing geometry.
   raw['parts'][5]['size'][0]=36
  else:raw['lighting']=raw['parts'].pop(0)
  return {'choices':[{'finish_reason':'stop','message':{'content':json.dumps(raw)}}]}
 app.llamacpp.endpoint_transport=transport
 server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url='http://127.0.0.1:'+str(server.server_port)
 try:
  with sync_playwright()as pw:
   browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']);context=browser.new_context(viewport={'width':1440,'height':1040},reduced_motion='reduce');page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.goto(url);page.locator('#offline-ready[data-ready=true]').wait_for(timeout=25000);page.locator('#quick-collapse').click();page.locator('#workshop-open').click();page.get_by_text('Arbeitsbereich bereit.',exact=False).wait_for();page.locator('#build-request').fill('Entwirf ein Konzept für einen Mini-Roboterarm mit zwei Säulen und LED auf meinem Tisch');page.locator('#build-submit').click();page.wait_for_function("()=>document.getElementById('build-canvas').dataset.assembly==='complete'&&!document.getElementById('build-submit').disabled",timeout=90000)
   assert len(calls)==1;assert page.locator('#build-led-toggle').is_enabled();assert '1 LED'in page.locator('#build-led-summary').inner_text();assert page.locator('#build-supplies li').count()==10;assert page.locator('.build-system').count()==4;assert page.locator('#build-concept').is_visible();assert 'Drehmomente'in page.locator('#build-unresolved').inner_text();assert 'keine'not in page.locator('#build-status').inner_text();page.locator('#build-studio').evaluate('e=>e.scrollTop=0');page.locator('#build-studio .build-controls').evaluate('e=>e.scrollTop=545');page.screenshot(path=str(root/'artifacts/jarvis-komplexes-konzept.png'))
   canvas=page.locator('#build-canvas').bounding_box();before=page.locator('#build-part').inner_text();page.mouse.move(canvas['x']+canvas['width']*.44,canvas['y']+canvas['height']*.68);page.mouse.down();page.mouse.move(canvas['x']+canvas['width']*.46,canvas['y']+canvas['height']*.68,steps=8);page.mouse.up();assert page.locator('#build-part').inner_text()==before
   page.locator('.build-system button').last.click();page.locator('#build-chat').get_by_text('Sir, Steuerung und Versorgung sind in diesem Konzept noch offen.',exact=False).wait_for();assert len(questions)==1;assert 'Hier noch kein Controller'in questions[0]['messages'][-1]['content']
   page.locator('#build-request').fill('Das LED-Modul ist falsch zugeordnet, überarbeite dieses komplexe Konzept');page.locator('#build-submit').click();page.wait_for_function("()=>!document.getElementById('build-submit').disabled",timeout=90000);assert len(calls)==2;assert 'bereits modellierte'in page.locator('#build-decisions').inner_text();assert page.locator('#build-supplies li').count()==10;assert page.locator('#build-error-details').is_hidden();assert '1 LED'in page.locator('#build-led-summary').inner_text()
   page.locator('#build-save').click();page.get_by_text('Entwurf auf diesem Gerät gespeichert.',exact=True).wait_for();page.locator('#build-close').click();context.set_offline(True);page.goto(url+'/tablet?layout=ipad',wait_until='domcontentloaded');page.locator('#offline-ready[data-ready=true]').wait_for(timeout=25000)
   if not page.locator('#workshop-open').is_visible():page.locator('#quick-collapse').click()
   page.locator('#workshop-open').click();page.locator('#build-load:enabled').click();page.get_by_text('Gesicherten Entwurf geladen.',exact=False).wait_for();assert page.locator('.build-system').count()==4;assert '1 LED'in page.locator('#build-led-summary').inner_text();page.set_viewport_size({'width':390,'height':844});assert page.locator('#build-studio').evaluate('e=>e.scrollWidth<=e.clientWidth+1');assert not errors,errors
   context.close();browser.close();print('PASS: dedicated mandatory lighting payload becomes actual LED geometry; wrong material classification repaired at same part count; complex concept renders 10 parts, systems/workflow/open checks; saved concept and LEDs load offline and fit phone. Controlled provider; no real inference quality claim.')
 finally:app.workshop.stop();app.office.stop();app.desktop.stop();server.shutdown();server.server_close();thread.join(3)
