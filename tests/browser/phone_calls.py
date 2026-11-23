"""Number dialing stays on the device; fixtures never ring a real number."""
import sys,tempfile,threading,json
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
   browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);errors=[];posts=[];drafts=[]
   for device,path in [('Macintosh; Intel Mac OS X 13_6','/index.html'),('iPhone; CPU iPhone OS 17_0 like Mac OS X','/tablet')]:
    context=browser.new_context(user_agent='Mozilla/5.0 ('+device+') AppleWebKit/537.36 Chrome/130.0 Safari/537.36',viewport={'width':390,'height':844}if'iPhone'in device else{'width':1280,'height':900},is_mobile='iPhone'in device,has_touch='iPhone'in device);page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
    page.route('**/api/phone-calls/start',lambda route:(posts.append(route.request.post_data_json),route.abort()))
    page.route('**/api/device-ai/chat',lambda route:(drafts.append(route.request.post_data_json),route.fulfill(json={'reply':'Guten Tag, können wir am Dienstag einen Termin vereinbaren?'}))[1])
    page.goto(base+path);page.wait_for_function('()=>!!window.DeviceStore&&!!window.JarvisCalls&&!!window.JarvisApps');page.evaluate("contacts=>{window.realPhoneStore=window.DeviceStore;window.phoneStoreWrites=[];window.DeviceStore={get:async key=>key==='desk-v1'?contacts:null,set:async(...args)=>phoneStoreWrites.push(args)};}",CONTACTS)
    page.locator('#jarvis-app-open').click();page.locator('[data-app=phone]').click();page.locator('#phone-calls').wait_for();assert page.locator('#phone-review').is_hidden();assert page.locator('#phone-calls a[href="/web-call"]').is_hidden()
    page.locator('#phone-contacts').get_by_role('button',name='Amelie QA',exact=False).click();page.locator('#phone-prepare').click();page.locator('#phone-review').wait_for();assert not posts;assert '170' in page.locator('#phone-review-number').inner_text();page.locator('#phone-cancel').click();assert not posts
    page.locator('#phone-number').fill('abc');page.locator('#phone-prepare').click();assert page.locator('#phone-review').is_hidden();assert not posts
    page.locator('#phone-script').fill('Bitte einen Termin am Dienstag klären.');page.locator('#phone-ai-draft').click();page.wait_for_function("()=>document.getElementById('phone-script').value.startsWith('Guten Tag')");payload=json.dumps(drafts[-1]);assert 'Amelie'not in payload and '170'not in payload and 'number'not in payload;assert drafts[-1]['history']==[]
    page.locator('#phone-number').fill('+49 170 1234567');page.locator('#phone-prepare').click();native=page.locator('#phone-native');native.wait_for();assert native.get_attribute('href')=='tel:+491701234567';assert page.locator('#phone-confirm').is_hidden();page.evaluate("()=>{window.nativeCallClicks=0;document.getElementById('phone-native').addEventListener('click',e=>{e.preventDefault();window.nativeCallClicks++;});}");native.click();assert page.evaluate('nativeCallClicks')==1;assert not posts;assert page.evaluate("()=>phoneStoreWrites.every(([key,value])=>key!=='desk-v1'&&!JSON.stringify(value).includes('Amelie')&&!JSON.stringify(value).includes('1701234567'))")
    assert page.locator('#phone-calls').evaluate('e=>e.scrollWidth<=e.clientWidth+1');page.locator('#phone-close').click();page.wait_for_function("()=>!document.getElementById('phone-number').value&&!document.getElementById('phone-script').value");assert not page.locator('#phone-number').input_value();assert not page.locator('#phone-script').input_value();assert page.locator('#phone-review-number').inner_text()=='';assert page.locator('#phone-contacts').count()==1 and not page.locator('#phone-contacts button').count();
    if 'iPhone'in device:
     page.evaluate("async()=>{await DeviceWorkspace.ask('Rufe +49 170 1234567 an');}");page.locator('#phone-calls').wait_for();assert page.locator('#phone-number').input_value()=='+491701234567';assert page.evaluate("async()=>!(/170.?1234567/.test(JSON.stringify((await realPhoneStore.get('workspace'))?.chat||{})))");page.locator('#phone-close').click()
    context.close()
   assert len(drafts)==2 and not errors,errors;assert app.store.history()==[];browser.close();print('PASS: Mac and phone select contacts, reject invalid numbers, require confirmation, dial via local tel link without server-number POST, AI drafting excludes recipient/number, close clears fields and contact DOM, no new contact writes. AI/native dial fixtures; no real phone call tested.')
 finally:app.office.stop();app.workshop.stop();app.desktop.stop();server.shutdown();server.server_close();thread.join(2)
