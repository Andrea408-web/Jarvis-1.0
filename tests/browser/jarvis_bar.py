"""Visible original Mac bar, responsive layouts and deterministic voice-message routing."""
import json,sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory() as folder:
 app=Application(folder);app.store.update_settings({'voice_enabled':False});model_calls=[]
 app.llamacpp.transport=lambda *a,**k:model_calls.append(a)
 server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url='http://127.0.0.1:'+str(server.server_port)
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page(viewport={'width':1512,'height':1100});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.goto(url+'/index.html');page.locator('#quick-bar').wait_for();page.wait_for_function('()=>!!window.JarvisExtras&&!!window.JarvisBridge');page.wait_for_timeout(400)
   assert page.locator('#quick-bar button').count()==8
   bounds=page.locator('#quick-bar').bounding_box();assert bounds and bounds['y']<350
   page.locator('#quick-bar [data-quick="focus"]').click();page.get_by_label('Woran arbeitest du gerade?').wait_for(state='visible');page.get_by_role('button',name='Schließen',exact=True).click();page.mouse.move(0,0);page.wait_for_timeout(200);page.screenshot(path=str(root/'artifacts/jarvis-mac-werkzeugleiste.png'))
   for phrase in ['Jarvis, sende eine Sprachnachricht an Lea','Wie sende ich eine Sprachnachricht?','Öffne Sprachnachrichten','Schicke Lea eine Sprachnachricht']:
    parsed=page.evaluate('text=>JarvisContactRequest(text)',phrase);assert parsed and parsed['voice'] is True,phrase
   page.locator('#chat-input').fill('Jarvis, wie sende ich eine Sprachnachricht?');page.locator('#send-button').click();page.locator('#mac-contacts-dialog[open]').wait_for();frame=page.frame_locator('#mac-contacts-frame');frame.locator('.voice-guided').wait_for();assert frame.locator('#desk-voice-kind').input_value()=='own';assert not frame.locator('#send-confirm').is_visible();assert page.url==url+'/index.html';page.screenshot(path=str(root/'artifacts/jarvis-sprachnachricht-hilfe.png'));page.locator('#mac-contacts-dialog button').first.click()
   assert not errors,errors
   for width,height,layout,name in [(390,844,'phone','handy'),(1194,834,'ipad','ipad')]:
    mobile=browser.new_page(viewport={'width':width,'height':height},is_mobile=layout=='phone',has_touch=True)
    mobile.on('pageerror',lambda e:errors.append(str(e)));mobile.goto(url+'/tablet');mobile.wait_for_function('()=>!!window.DeviceStore&&!!window.DeviceDesk')
    mobile.evaluate("async layout=>{const state=await DeviceStore.get('workspace')||{version:1};await DeviceStore.set('workspace',{...state,layout,voice:false});}",layout);mobile.reload();mobile.wait_for_function('layout=>document.body.dataset.layout===layout',arg=layout);mobile.locator('#quick-bar').wait_for();mobile.wait_for_timeout(300)
    assert mobile.evaluate('()=>document.documentElement.scrollWidth<=innerWidth+1')
    assert mobile.locator('#quick-bar button').count()==8
    mobile.mouse.move(0,0);mobile.screenshot(path=str(root/('artifacts/jarvis-'+name+'-neu.png')))
    mobile.locator('#quick-bar [data-quick="voice"]').click();mobile.locator('.voice-guided').wait_for();assert mobile.locator('#desk-voice-kind').input_value()=='own'
    assert not mobile.locator('#contact-picker').is_visible();assert not mobile.locator('#send-confirm').is_visible();assert 'noch nichts aufgenommen' in mobile.locator('#desk-voice-status').inner_text()
    # A unique saved person routes to audio, never to a text-send confirmation.
    mobile.locator('[data-desk="contacts"]').click();mobile.locator('#desk-contact-name').fill('Lea');mobile.locator('#desk-contact-email').fill('lea@example.test');mobile.locator('#desk-contact-form button.primary').click();mobile.wait_for_function("async()=>(await DeviceStore.get('desk-v1')).contacts.length===1")
    mobile.locator('.rail [data-view="chat"]').click();mobile.locator('#device-chat-input').fill('Sende eine Sprachnachricht an Lea mit dem Text: Morgen passt.');mobile.locator('#chat-send').click();mobile.locator('.voice-guided').wait_for();assert mobile.locator('#desk-recipient').input_value();assert not mobile.locator('#send-confirm').is_visible();assert mobile.locator('#desk-message').input_value()=='Morgen passt.'
    saved=mobile.evaluate("async()=>await DeviceStore.get('workspace')");assert 'lea@example.test' not in json.dumps(saved);assert 'Sprachnachricht an Lea' not in json.dumps(saved);mobile.close()
   assert not errors,errors;assert not model_calls;assert app.confirmed_send.pending=={}
   print('PASS: bar visible on original Mac dashboard; direct feature shortcuts; 390px phone and iPad layouts without horizontal overflow; voice commands and visible audio button bypass model, choose recording without starting it, and never auto-send or save contact command in device chat.');browser.close()
 finally:app.office.stop();app.desktop.stop();server.shutdown();server.server_close();thread.join(3)
