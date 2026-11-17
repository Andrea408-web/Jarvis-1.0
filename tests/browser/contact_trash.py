"""Real drag-and-drop and touch deletion, cancellation, storage failure and draft preservation."""
import sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory() as folder:
 app=Application(folder);app.store.update_settings({'voice_enabled':False})
 server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url='http://127.0.0.1:'+str(server.server_port)
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page(viewport={'width':1300,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.goto(url+'/tablet');page.locator('.rail [data-view="desk"]').click();page.get_by_text('Offline-Ablage bereit. Kein Mac benötigt.',exact=True).wait_for()
   seed={'version':1,'documents':[],'events':[],'updated':'','backup':'','contacts':[{'id':'lea','name':'Lea','email':'lea@example.test','phone':'+49000111'},{'id':'ben','name':'Ben','email':'ben@example.test','phone':'+49000222'}],'drafts':[{'id':'draft-lea','contact':'lea','subject':'Termin','text':'Der Entwurf bleibt erhalten.'},{'id':'draft-ben','contact':'ben','subject':'Idee','text':'Ein zweiter Entwurf.'}]}
   page.evaluate('async data=>await DeviceDesk.import(data)',seed);page.locator('[data-desk="contacts"]').click()
   page.locator('#desk-contact-trash').scroll_into_view_if_needed()
   source=page.locator('.contact-row[data-contact-id="lea"] .desk-list-item').bounding_box();target=page.locator('#desk-contact-trash').bounding_box()
   page.mouse.move(source['x']+30,source['y']+20);page.mouse.down();page.mouse.move(source['x']+45,source['y']+25,steps=5);page.mouse.move(target['x']+target['width']/2,target['y']+target['height']/2,steps=15);page.mouse.move(target['x']+target['width']/2+3,target['y']+target['height']/2+3);page.mouse.up()
   page.locator('#contact-delete-confirm[open]').wait_for(timeout=3000);assert page.locator('#contact-delete-name').inner_text()=='Lea'
   assert len(page.evaluate("async()=>(await DeviceStore.get('desk-v1')).contacts"))==2
   page.locator('#contact-delete-no').click();assert page.locator('#desk-contact-list .contact-row').count()==2
   page.get_by_role('button',name='Lea',exact=False).filter(has=page.locator('small')).first.click()
   page.locator('#desk-contact-trash').click();page.locator('#contact-delete-confirm[open]').wait_for()
   page.evaluate("()=>{window.realDeskSet=DeviceStore.set;DeviceStore.set=async()=>{throw Error('Test: Speicher nicht verfügbar');};}")
   page.locator('#contact-delete-yes').click();page.get_by_text('Kontakt nicht gelöscht: Test: Speicher nicht verfügbar',exact=True).wait_for()
   assert page.locator('#desk-contact-list .contact-row').count()==2
   page.evaluate('()=>{DeviceStore.set=window.realDeskSet;delete window.realDeskSet;}')
   page.locator('#contact-delete-yes').click();page.wait_for_function("async()=>(await DeviceStore.get('desk-v1')).contacts.length===1")
   page.wait_for_function("()=>!document.getElementById('contact-delete-confirm').open")
   saved=page.evaluate("async()=>await DeviceStore.get('desk-v1')")
   assert saved['contacts']==[seed['contacts'][1]] and saved['drafts'][0]['contact']==''
   assert saved['drafts'][0]['text']==seed['drafts'][0]['text'] and saved['drafts'][1]['contact']=='ben'
   assert page.locator('#desk-recipient').input_value()=='' and page.locator('#desk-contact-name').input_value()==''
   assert not page.locator('#desk-contact-links').inner_text()
   page.reload();page.locator('.rail [data-view="desk"]').click();page.locator('[data-desk="contacts"]').click()
   page.locator('.contact-row[data-contact-id="ben"]').wait_for();assert page.locator('.contact-row').count()==1
   # Same stored contact and touch-size delete control in the original Mac iframe.
   page.goto(url+'/index.html');page.wait_for_function('()=>!!window.JarvisExtras');page.locator('#chat-input').fill('Schreibe eine E-Mail an Ben');page.locator('#send-button').click();frame=page.frame_locator('#mac-contacts-frame');frame.locator('#contact-picker[open]').wait_for();frame.locator('#picker-new').click();frame.locator('#desk-contact-trash').scroll_into_view_if_needed();page.screenshot(path=str(root/'artifacts/kontakt-papierkorb.png'));frame.get_by_role('button',name='Kontakt Ben löschen',exact=True).click();frame.locator('#contact-delete-confirm[open]').wait_for();page.screenshot(path=str(root/'artifacts/kontakt-papierkorb-mac.png'));assert page.url==url+'/index.html';frame.locator('#contact-delete-no').click();page.locator('#mac-contacts-dialog button').first.click()
   # Phone alternative requires no dragging.
   page.set_viewport_size({'width':390,'height':844});page.goto(url+'/tablet');page.locator('.rail [data-view="desk"]').click();page.locator('[data-desk="contacts"]').click();page.get_by_role('button',name='Kontakt Ben löschen',exact=True).click();page.locator('#contact-delete-confirm[open]').wait_for();page.screenshot(path=str(root/'artifacts/kontakt-papierkorb-handy.png'));page.locator('#contact-delete-yes').click();page.wait_for_function("async()=>(await DeviceStore.get('desk-v1')).contacts.length===0");assert (page.evaluate("async()=>await DeviceStore.get('desk-v1')"))['drafts'][1]['text']=='Ein zweiter Entwurf.';assert not errors,errors
   browser.close();print('PASS: real drag to trash -> named confirmation; cancel preserves contacts; failed storage leaves data and form intact; successful deletion survives reload and detaches only matching drafts; Mac iframe and touch delete work; no native Apple contact action.')
 finally:app.office.stop();app.desktop.stop();server.shutdown();server.server_close();thread.join(3)
