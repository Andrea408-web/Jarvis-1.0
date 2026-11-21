"""Web references remain visible, selectable data beside an existing own 3D model."""
import sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from backend.workshop_free import result
from backend.workshop import DEFAULT
from tests.test_workshop_contours import RAW
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory()as folder:
 app=Application(folder);calls=[]
 def reader(url):
  calls.append(url);return '<a class="result__a" href="https://example.com/reactor">Arc-Reaktor Referenzquelle</a><span class="result__snippet">Rundes Gehäuse mit konzentrischen Ringen und LED-Diffusor. Ungeprüfter Bauhinweis.</span>',url
 app.web.reader=reader;app.code_room._generate=lambda *a,**kw:(_ for _ in ()).throw(AssertionError('Selecting a source must not start a design'))
 server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 try:
  with sync_playwright()as pw:
   browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']);page=browser.new_page(viewport={'width':1440,'height':1040},reduced_motion='reduce');errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto('http://127.0.0.1:'+str(server.server_port));page.wait_for_function('()=>!!window.DeviceStore')
   page.evaluate("data=>DeviceStore.set('jarvis-workshop-v1',data)",result(RAW,DEFAULT));page.evaluate("async()=>{const studio=await import('/workshop.js');await studio.open();}");page.locator('#build-load:enabled').click();page.wait_for_function("()=>document.getElementById('build-canvas').dataset.assembly==='complete'");title=page.locator('#build-title').inner_text()
   page.locator('#build-references summary').click();page.locator('#build-request').fill('Entwirf ein rundes Gehäuse mit Ringen und sichtbaren LEDs');page.locator('#build-reference-query').fill('Arc Reaktor Gehäuse Aufbau');page.locator('#build-reference-run').click();page.locator('#build-reference-results a').first.wait_for();assert calls
   link=page.locator('#build-reference-results a').first;assert link.get_attribute('href')=='https://example.com/reactor';assert link.get_attribute('rel')=='noopener noreferrer'
   page.get_by_role('button',name='Als Referenz für Entwurf übernehmen').first.click();text=page.locator('#build-request').input_value();assert text.startswith('[WEBREFERENZ]');assert '[/WEBREFERENZ]'in text;assert 'https://example.com/reactor'in text;assert 'Entwirf ein rundes Gehäuse'in text;assert len(text)<=1800
   assert page.locator('#build-title').inner_text()==title;assert page.locator('#build-canvas').get_attribute('data-assembly')=='complete';assert 'keine Bilder'in page.locator('#build-references').inner_text()
   page.locator('#build-studio').evaluate('e=>e.scrollTop=250');page.screenshot(path=str(root/'artifacts/jarvis-vorlagen-recherche.png'))
   page.set_viewport_size({'width':390,'height':844});assert page.locator('#build-studio').evaluate('e=>e.scrollWidth<=e.clientWidth+1');assert not errors,errors;browser.close();print('PASS: real research results visible with safe source links; selected untrusted source and user wish transfer to input; existing actual own model unchanged; no AI generation on source selection; phone fit. Web reader uses controlled fixture.')
 finally:app.office.stop();app.workshop.stop();app.desktop.stop();server.shutdown();server.server_close();thread.join(2)
