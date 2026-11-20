"""Real HTTP jobs: time beyond old 120s deadline, stop, malformed replies and restart help.
Provider transport is controlled; this does not measure real small-model quality.
"""
import copy,json,sys,tempfile,threading,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from tests.test_workshop_contours import RAW
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory()as folder:
 app=Application(folder);app.store.update_settings({'ai_provider':'llamacpp'});started=threading.Event();release=threading.Event();calls=[]
 def transport(path,payload=None):
  text=payload['messages'][-1]['content'];calls.append(payload)
  assert payload['response_format']['type']=='json_schema'
  if text.startswith('Entwirf einen geschwungenen Ständer mit LED')or 'stopptest'in text:started.set();release.wait(15)
  data=copy.deepcopy(RAW)
  if 'fehlerfall'in text:return {'choices':[{'finish_reason':'stop','message':{'content':json.dumps({'title':'Unvollständig'})}}]}
  if 'LED'in text:
   data['parts'].append({'name':'LED-Lichtmodul','shape':'cylinder','size':[70,5,50],'position':[0,180,12],'material':'light'});data['explanation']='Die eigene Seitenkontur hält die Ablage. Das weiße LED-Modul zeigt dir die vorgesehene Lichtposition im grauen Modell.'
  return {'choices':[{'finish_reason':'stop','message':{'content':json.dumps(data)}}]}
 app.llamacpp.endpoint_transport=transport
 server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url='http://127.0.0.1:'+str(server.server_port)
 try:
  with sync_playwright()as pw:
   browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']);context=browser.new_context(viewport={'width':1440,'height':1040},reduced_motion='reduce',permissions=['clipboard-read','clipboard-write']);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.goto(url);page.locator('#offline-ready[data-ready=true]').wait_for(timeout=25000);page.locator('#quick-collapse').click();page.locator('#workshop-open').click();page.get_by_text('Arbeitsbereich bereit.',exact=False).wait_for();page.locator('#build-read').evaluate('e=>e.checked=false')
   page.clock.install()
   page.locator('#build-request').fill('Entwirf einen geschwungenen Ständer mit LED aus schwarzem Holz');page.locator('#build-submit').click();assert started.wait(5);page.locator('#build-status[data-phase=generating]').wait_for();page.clock.fast_forward(130000);assert page.locator('#build-submit').is_disabled();assert app.workshop.running is not None;release.set()
   page.wait_for_function("()=>document.getElementById('build-canvas').dataset.assembly==='complete'&&!document.getElementById('build-submit').disabled",timeout=30000);assert page.locator('#build-led-toggle').is_enabled();assert 'LED-Modul'in page.locator('#build-explanation').inner_text();title=page.locator('#build-title').inner_text();page.locator('#build-face-motion').evaluate('e=>e.click()');page.locator('#build-studio').evaluate('e=>e.scrollTop=0');page.screenshot(path=str(root/'artifacts/jarvis-werkstatt-repariert.png'))
   started.clear();release.clear();page.locator('#build-request').fill('stopptest: neue Kontur');page.locator('#build-submit').click();assert started.wait(5);key=app.workshop.running;page.locator('#build-stop').evaluate('e=>e.click()');page.wait_for_function("()=>!document.getElementById('build-submit').disabled");release.set()
   for _ in range(100):
    if app.workshop.running is None:break
    time.sleep(.01)
   assert app.workshop.jobs[key]['state']=='cancelled';assert 'result'not in app.workshop.jobs[key];assert page.locator('#build-title').inner_text()==title
   page.locator('#build-request').fill('Entwirf einen neuen Entwurf fehlerfall');page.locator('#build-submit').click();page.locator('#build-chat').get_by_text('Pflichtfelder fehlen',exact=False).wait_for();page.wait_for_function("()=>!document.getElementById('build-submit').disabled");assert page.locator('#build-title').inner_text()==title;assert page.locator('#build-error-details').is_visible();page.locator('#build-error-details summary').click();page.locator('#build-error-copy').click();diagnostic=page.evaluate('()=>navigator.clipboard.readText()');assert 'Pflichtfelder fehlen'in diagnostic;assert 'fehlerfall'not in diagnostic;assert 'workshop-2026-11-20'in diagnostic
   page.route('**/api/workshop/jobs',lambda route:route.fulfill(status=404,content_type='application/json',body='{"error":"unknown route"}'));page.locator('#build-request').fill('Ein neuer Entwurf');page.locator('#build-submit').click();page.locator('#build-chat').get_by_text('Der Mac-Server läuft noch mit einer alten Jarvis-Version',exact=False).wait_for();assert not errors,errors
   context.close();browser.close();print('PASS: actual HTTP job survives 130s of browser time; structured provider payload; LED result rendered; stop discards late output; invalid output preserves model; private error details copy; stale server gives restart instructions. Controlled provider, not real inference.')
 finally:release.set();app.workshop.stop();app.office.stop();app.desktop.stop();server.shutdown();server.server_close();thread.join(3)
