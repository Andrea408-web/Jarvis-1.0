"""Real browser editing, native-picker boundary, range preview and background export."""
import json,subprocess,sys,tempfile,threading
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from playwright.sync_api import sync_playwright
with tempfile.TemporaryDirectory() as folder:
 root=Path(folder);source=root/'clip.mp4';subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i','color=blue:s=320x180:r=30:d=2','-c:v','libx264','-threads','1',str(source)],check=True,capture_output=True)
 app=Application(root/'data');asset=app.video_editor.import_paths([str(source)])[0];server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url='http://127.0.0.1:'+str(server.server_port)
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);context=browser.new_context(accept_downloads=True);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   with patch.object(app.video_editor,'choose',side_effect=lambda:app.video_editor.import_paths([str(source)])) as choose:
    page.goto(url+'/video-editor?budget=3');page.get_by_text('Videoschnitt bereit.',exact=False).wait_for();assert page.locator('#budget').input_value()=='3';page.evaluate("Object.defineProperty(document,'hidden',{get:()=>true,configurable:true})");page.locator('#choose').click();page.get_by_text('Clips ausgewählt.',exact=False).wait_for();choose.assert_called_once();assert page.locator('#cuts .cut').count()==1;page.evaluate('delete document.hidden')
    denied=context.request.post(url+'/api/video-editor/choose',headers={'X-Jarvis-Token':app.token},data={'path':'/etc/passwd'});assert denied.status==400;assert choose.call_count==1
   partial=context.request.get(url+'/edit-media/'+asset['id'],headers={'Range':'bytes=0-15'});assert partial.status==206 and len(partial.body())==16;assert partial.headers['content-range'].startswith('bytes 0-15/')
   page.get_by_role('textbox',name='Start Schnitt 1',exact=True).fill('0.5');page.get_by_role('textbox',name='Start Schnitt 1',exact=True).press('Tab');page.get_by_role('textbox',name='Ende Schnitt 1',exact=True).fill('1.5');page.get_by_role('textbox',name='Ende Schnitt 1',exact=True).press('Tab');page.locator('#start').click();page.get_by_text('Schnittauftrag gestartet.',exact=False).wait_for();assert len(app.video_editor.jobs)==1;page.close();app.video_editor.worker.join(40);assert not app.video_editor.worker.is_alive();job=list(app.video_editor.jobs.values())[0];assert job['state']=='completed',job
   page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.goto(url+'/video-editor');page.get_by_role('heading',name='Fertig',exact=True).wait_for();assert page.get_by_role('link',name='MP4 herunterladen',exact=True).count()==2
   with page.expect_download() as download:page.get_by_role('link',name='MP4 herunterladen',exact=True).first.click()
   path=root/'download.mp4';download.value.save_as(path);assert path.stat().st_size>1000;assert app.video_editor.probe(path)['width']==1920;assert source.exists();page.screenshot(path='/tmp/astra-video-editor.png');assert not errors,errors
   # Real browser multi-file selection, sequential bounded uploads, direct cut list.
   with page.expect_file_chooser() as chooser:page.locator('#files').click()
   chooser.value.set_files([str(source),str(path)])
   page.get_by_text('2 von 2 Clips geladen.',exact=False).wait_for();assert page.locator('#cuts .cut').count()==2
   assert page.locator('#asset-list').inner_text().count('Zur Schnittliste')>=3
   assert page.locator('#preview').get_attribute('src').startswith('/edit-media/')
   page.locator('#shorts').uncheck();page.locator('#assist').click();page.get_by_text('Automatischer technischer Schnitt:',exact=False).wait_for();app.video_editor.worker.join(40)
   assert list(app.video_editor.jobs.values())[-1]['state']=='completed'
   invalid=context.request.post(url+'/api/video-editor/upload',headers={'X-Jarvis-Token':app.token,'Content-Type':'application/octet-stream','X-Video-Name':'no.py'},data=b'bad');assert invalid.status==400
   page.route('**/api/video-editor/upload',lambda route:route.fulfill(status=404,content_type='application/json',body='{}'))
   page.locator('#files').set_input_files(str(source));page.get_by_text('Kein Clip importiert.',exact=False).wait_for()
   assert 'Strg+C' in page.locator('#imports').inner_text()
   assert page.locator('#files').is_enabled();assert not errors,errors
   print('PASS: actual clip/time UI, both formats exported, original remains, no raw paths accepted, partial HTTP preview, job completes after editor closes, playable MP4 download. AVFoundation fallback not tested on physical Mac.');browser.close()
 finally:app.video_editor.close();app.office.stop();server.shutdown();server.server_close();thread.join(3)
