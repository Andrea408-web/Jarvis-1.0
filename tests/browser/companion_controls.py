"""Explicit Mac commands route to reviewed execution; widget motion is separate."""
import sys,tempfile,threading
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from playwright.sync_api import sync_playwright
with tempfile.TemporaryDirectory() as folder:
 app=Application(folder);server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url='http://127.0.0.1:'+str(server.server_port)
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page();errors=[];model=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:model.append(r.url) if r.url.endswith('/api/video-call') else None);page.add_init_script("window.SpeechRecognition=class{start(){this.onstart?.()}stop(){}};")
   page.goto(url+'/companion?mode=helper');page.locator('#call-start').click();page.locator('#decline-mic').click();page.route('**/api/natural-voice/speak',lambda r:r.abort())
   def send(text):page.locator('#call-input').fill(text);page.locator('#call-form button').click();page.wait_for_function('()=>!JarvisBridge.interaction().busy')
   one={'supported':True,'plan':{'id':'a'*32,'steps':[{'type':'open','app':'Safari'}],'state':'review','message':'Safari öffnen'}}
   with patch.object(app.desktop,'prepare',return_value=one) as prepare,patch.object(app.desktop,'start',return_value={'ok':True}) as start:
    send('Öffne Safari');prepare.assert_called_once_with({'goal':'Öffne Safari'});start.assert_called_once_with('a'*32);assert not model
   two={'supported':True,'plan':{'id':'b'*32,'steps':[{'type':'open','app':'Notizen'},{'type':'text','text':'Hallo'}],'state':'review','message':'Zwei konkrete Schritte'}}
   with patch.object(app.desktop,'prepare',return_value=two),patch.object(app.desktop,'start',return_value={'ok':True}) as start:
    send('Tippe Hallo in Notizen');start.assert_not_called();page.locator('#buddy-action-start').click();page.locator('#buddy-action-start').wait_for(state='hidden');start.assert_called_once_with('b'*32)
   with patch.object(app.desktop,'stop',return_value={'ok':True}) as stop:
    send('Stopp');stop.assert_called_once()
   send('Beweg dich nicht');assert page.locator('#companion-motion').get_attribute('aria-pressed')=='false';send('Bewege dich');assert page.locator('#companion-motion').get_attribute('aria-pressed')=='true'
   with page.expect_popup() as opened:send('Schneide ein Video, du hast fünf Minuten')
   editor=opened.value;editor.wait_for_url('**/video-editor?budget=5');editor.get_by_text('Videoschnitt bereit.',exact=False).wait_for();assert editor.locator('#budget').input_value()=='5';assert not model;assert not errors,errors
   print('PASS: explicit open starts reviewed Mac executor, longer steps require actual start button, stop reaches executor, negative movement command disables only widget motion, spoken budget opens editor with 5 minutes. No physical Mac input performed.');browser.close()
 finally:app.office.stop();app.video_editor.close();app.companion_window.close();server.shutdown();server.server_close();thread.join(3)
