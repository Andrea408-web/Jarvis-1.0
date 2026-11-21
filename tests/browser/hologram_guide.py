"""Physical build guide is readable without generating a model; actual HTTP and DOM."""
import io,sys,tempfile,threading,wave
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory()as folder:
 app=Application(folder);voices=[];app.web.reader=lambda url:('<a class="result__a" href="https://example.com/optics">Optik-Testquelle</a><span class="result__snippet">Reflektor mit Display</span>',url)
 app.code_room._generate=lambda *a,**kw:(_ for _ in ()).throw(AssertionError('A readable guide must not generate a 3D model'))
 audio=io.BytesIO()
 with wave.open(audio,'wb')as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000);w.writeframes(b'\0\0'*16000)
 app.natural_voice.synthesize=lambda text,preset:(voices.append((text,preset)),audio.getvalue())[1]
 server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 try:
  with sync_playwright()as pw:
   browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']);page=browser.new_page(viewport={'width':1440,'height':1040},reduced_motion='reduce');errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto('http://127.0.0.1:'+str(server.server_port))
   page.evaluate("async()=>{const studio=await import('/workshop.js');await studio.openHologramGuide({budget:40,inventory:'Display und USB-Kamera vorhanden'});}")
   assert page.locator('#hologram-build-guide').is_visible();assert page.locator('#build-studio').count()==0
   assert page.locator('#hologram-guide-content section').count()>=4
   assert page.locator('#hologram-guide-content li').count()>=12
   assert page.locator('#hologram-guide-budget').input_value()=='40'
   assert 'USB-Kamera' in page.locator('#hologram-guide-inventory').input_value()
   assert page.locator('#hologram-guide-shopping li').count()>=3
   page.screenshot(path=str(root/'artifacts/jarvis-hologramm-anleitung.png'))
   page.get_by_role('button',name='Mit Thorsten vorlesen').first.click();page.get_by_text('Thorsten liest den Schritt vor.',exact=True).wait_for();assert voices and voices[0][1]=='jarvis'
   page.locator('#hologram-guide-mute').click();assert page.locator('#hologram-guide-status').inner_text()=='Vorlesen gestoppt.'
   page.locator('#hologram-guide-budget').fill('55');page.locator('#hologram-guide-refresh').click();page.get_by_text('Anleitung bereit.',exact=False).wait_for();assert page.locator('#hologram-guide-budget').input_value()=='55'
   page.set_viewport_size({'width':390,'height':844});assert page.locator('#hologram-build-guide').evaluate('e=>e.scrollWidth<=e.clientWidth+1')
   page.keyboard.press('Escape');assert not page.locator('#hologram-build-guide').is_visible()
   page.set_viewport_size({'width':1440,'height':1040});page.evaluate("async()=>{const studio=await import('/workshop.js');await studio.open();}");page.locator('#build-special-projects').evaluate('e=>e.open=true');page.locator('#build-hologram-guide').click();assert page.locator('#hologram-build-guide').is_visible();page.locator('#hologram-guide-close').click();page.locator('#build-request').fill('Erkläre die Hologramm-Bauanleitung für 60 Euro');page.locator('#build-submit').click();page.locator('#hologram-build-guide').wait_for();assert page.locator('#hologram-guide-budget').input_value()=='60';page.locator('#hologram-guide-close').click();page.locator('#build-request').fill('Suche im Internet nach einer Hologramm-Bauanleitung');page.locator('#build-submit').click();page.locator('#build-chat').get_by_text('Optik-Testquelle',exact=False).wait_for();assert not page.locator('#hologram-build-guide').is_visible();assert not errors,errors;browser.close();print('PASS: independent readable physical build guide, budget/inventory, real sections and material list, Thorsten step audio/mute, refresh, phone fit, Escape and visible studio entry; no geometry/model required.')
 finally:app.office.stop();app.workshop.stop();app.desktop.stop();server.shutdown();server.server_close();thread.join(2)
