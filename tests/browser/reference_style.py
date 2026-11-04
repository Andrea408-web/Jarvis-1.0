"""Reference-inspired islands and actual procedural low-poly video export."""
import sys,tempfile,threading,json,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from playwright.sync_api import sync_playwright
with tempfile.TemporaryDirectory() as folder:
 app=Application(folder);app.store.update_settings({'ai_provider':'llamacpp','voice_enabled':False});server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page(viewport={'width':1500,'height':1100},accept_downloads=True);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.goto('http://127.0.0.1:'+str(server.server_port));page.get_by_text('LOKALE VERBINDUNG AKTIV',exact=True).wait_for();page.get_by_role('button',name='Agenten',exact=True).click();page.locator('.island-seat').first.wait_for();assert page.locator('.island-seat').count()==30
   page.locator('.island-seat').first.click();page.locator('#agent-inspector').get_by_text('Schläft',exact=True).wait_for();page.screenshot(path='/tmp/jarvis-work-islands.png',full_page=True)
   release=threading.Event()
   def transport(*args,**kwargs):release.wait(10);return {'choices':[{'finish_reason':'stop','message':{'content':'Geprüftes Test-Ergebnis'}}]}
   app.llamacpp.endpoint_transport=transport;app.office.submit({'role':'planner','task':'Prüfe einen Testplan'})
   page.locator('.planner .island-seat[data-state=running]').first.wait_for(timeout=10000);page.locator('.planner .island-seat[data-state=running]').first.click();page.locator('#agent-inspector').get_by_text('Arbeitet',exact=True).wait_for();release.set();page.locator('#agent-inspector').get_by_text('Fertig',exact=True).wait_for(timeout=10000);page.locator('#agent-inspector').get_by_text('Geprüftes Test-Ergebnis',exact=True).wait_for()
   page.evaluate("()=>{const host=document.createElement('div');host.id='reference-film';document.getElementById('office-dialog').prepend(host);JarvisArtifacts.video(host,{id:'reference-test',result:'Entdecke deine Ideen.\\nGestalte die Zukunft.\\nStarte dein Projekt.',task:'Animation'});}")
   film=page.locator('#reference-film');assert film.locator('select').input_value()=='lowpoly';film.locator('input[type=checkbox]').uncheck();film.locator('canvas').scroll_into_view_if_needed();page.screenshot(path='/tmp/jarvis-lowpoly-video.png')
   with page.expect_download(timeout=20000) as download:
    film.get_by_role('button',name='Video exportieren',exact=True).click();film.get_by_role('link',name='Fertiges Video herunterladen',exact=True).click(timeout=18000)
   path=Path(folder)/'lowpoly.webm';download.value.save_as(str(path));info=json.loads(subprocess.check_output(['ffprobe','-v','quiet','-print_format','json','-show_streams',str(path)]));video=next(s for s in info['streams'] if s['codec_type']=='video');assert video['width']==720 and video['height']==720;assert path.stat().st_size>10000
   page.set_viewport_size({'width':390,'height':844});assert page.evaluate('()=>document.documentElement.scrollWidth<=innerWidth+2');assert not errors,errors
   print('PASS: 30 clickable workstations with actual idle inspector; reference-inspired low-poly scene exported as real 720p video:',path.stat().st_size,'bytes; mobile layout; no page errors.')
   browser.close()
 finally:app.office.stop();server.shutdown();server.server_close();thread.join(3)
