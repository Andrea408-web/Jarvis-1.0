"""Native-call preparation and confirmation; fixtures never ring a real number."""
import sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
CONTACTS={'version':1,'contacts':[{'id':'qa-contact','name':'Amelie QA','phone':'+49 170 1234567','email':''}]}
with tempfile.TemporaryDirectory()as folder:
 app=Application(folder);app.store.update_settings({'ai_provider':'llamacpp'});server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();base='http://127.0.0.1:'+str(server.server_port)
 try:
  with sync_playwright()as pw:
   browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);errors=[];posts=[]
   mac=browser.new_context(user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/537.36 Chrome/130.0 Safari/537.36');page=mac.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
   page.route('**/api/phone-calls/start',lambda route:(posts.append(route.request.post_data_json),route.fulfill(json={'state':'handoff','message':'Telefon-App wurde geöffnet. Prüfe dort den Anruf.','method':'phone'}))[1])
   page.goto(base+'/index.html');page.wait_for_function('()=>!!window.DeviceStore');page.evaluate("contacts=>{window.phoneStoreWrites=[];window.DeviceStore={get:async key=>key==='desk-v1'?contacts:null,set:async(...args)=>phoneStoreWrites.push(args)};}",CONTACTS)
   page.evaluate("async()=>{const calls=await import('/phone-calls.js');await calls.open({heard:'Rufe Amelie QA an',recipient:'Amelie QA'});}")
   page.locator('#phone-calls').wait_for();assert not posts;assert page.locator('#phone-review').is_hidden()
   page.locator('#phone-contacts').get_by_role('button',name='Amelie QA',exact=False).first.click();page.locator('#phone-prepare').click();page.locator('#phone-review').wait_for();assert not posts;assert '170' in page.locator('#phone-review-number').inner_text()
   page.locator('#phone-cancel').click();assert not posts
   if not page.locator('#phone-calls').is_visible():page.evaluate("async()=>{await(await import('/phone-calls.js')).open({number:'+49 170 1234567',recipient:'Amelie QA'});}")
   page.locator('#phone-number').fill('abc');page.locator('#phone-prepare').click();assert not posts;assert page.locator('#phone-review').is_hidden()
   page.locator('#phone-number').fill('+49 170 1234567');page.locator('#phone-prepare').click();page.locator('#phone-confirm').click();page.wait_for_function("()=>document.getElementById('phone-status').textContent.length>0");assert len(posts)==1;assert posts[0]['number'].replace(' ','')=='+491701234567';assert posts[0]['method']=='phone';assert 'verbunden' not in page.locator('#phone-status').inner_text().lower();assert page.evaluate('phoneStoreWrites.length')==0
   page.locator('#phone-close').click();mac.close()
   # On an iPhone the native link remains usable even with no Mac/session.
   mobile=browser.new_context(user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Version/17.0 Mobile/15E148 Safari/604.1',viewport={'width':390,'height':844},is_mobile=True,has_touch=True);phone=mobile.new_page();phone.on('pageerror',lambda e:errors.append(str(e)))
   phone.goto(base+'/tablet');phone.wait_for_function('()=>!!window.DeviceStore');phone.route('**/api/session',lambda route:route.abort());phone.evaluate("contacts=>{window.phoneStoreWrites=[];window.DeviceStore={get:async key=>key==='desk-v1'?contacts:null,set:async(...args)=>phoneStoreWrites.push(args)};}",CONTACTS)
   phone.evaluate("async()=>{await(await import('/phone-calls.js')).open({number:'+49 170 1234567',recipient:'Amelie QA'});}");phone.locator('#phone-prepare').click();native=phone.locator('#phone-native');native.wait_for();assert native.get_attribute('href').startswith('tel:');assert len(posts)==1
   phone.evaluate("()=>{window.nativeCallClicks=0;document.getElementById('phone-native').addEventListener('click',e=>{e.preventDefault();window.nativeCallClicks++;});}");native.click();assert phone.evaluate('nativeCallClicks')==1;assert len(posts)==1;assert phone.evaluate('phoneStoreWrites.length')==0;assert phone.locator('#phone-calls').evaluate('e=>e.scrollWidth<=e.clientWidth+1')
   phone.locator('#phone-close').click();assert not errors,errors;mobile.close();browser.close();print('PASS: readonly contact choice, invalid number, prepare/cancel cannot dial, explicit Mac native handoff only, mobile tel link without Mac/session, no call-history writes and phone fit. Native APIs are controlled fixtures; no real phone call tested.')
 finally:app.office.stop();app.workshop.stop();app.desktop.stop();server.shutdown();server.server_close();thread.join(2)
