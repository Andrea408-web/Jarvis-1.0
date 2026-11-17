"""Business workflow: real UI calculations, saved drafts, prompts and offline reload."""
import json,sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[2];shots=root/'artifacts';shots.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory() as folder:
 app=Application(folder);app.store.update_settings({'ai_provider':'llamacpp','voice_enabled':False});calls=[]
 def local_transport(path,payload):
  calls.append((path,payload));return {'done':True,'message':{'content':'Sir, teste zuerst dein Angebot mit einem kleinen Muster.'}}
 app.llamacpp.transport=local_transport
 server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url='http://127.0.0.1:'+str(server.server_port)
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);context=browser.new_context(timezone_id='Europe/Berlin',viewport={'width':1440,'height':1100},accept_downloads=True);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(url+'/brands');page.wait_for_function("()=>document.getElementById('brand-select').options.length>0")
   for key,value in {'name':'LUMEN STUDIO','product':'Handgemachte Notizbücher mit personalisiertem Einband.','audience':'Menschen, die ihre eigenen Projekte planen','goal':'Erste bezahlte Musterbestellung finden'}.items():page.locator('#brand-'+key).fill(value)
   page.get_by_role('button',name='Business & Prompts ↗',exact=True).click();page.get_by_text('Business-Werkzeuge bereit – auch ohne Mac.',exact=True).wait_for();page.locator('#business-brand').click();page.wait_for_function("()=>document.getElementById('business-name').value==='LUMEN STUDIO'");page.locator('#business-form button.primary').click();page.get_by_text('Bearbeitbarer Angebotsentwurf und Testplan erstellt.',exact=True).wait_for();assert 'Handgemachte Notizbücher' in page.locator('#business-plan').input_value();assert 'Tag 7:' in page.locator('#business-plan').input_value();page.mouse.move(0,0);page.screenshot(path=str(shots/'business-angebot.png'))
   for key,value in {'price':'0.30','cost':'0.20','fixed':'0.30','quantity':'3'}.items():page.locator('#business-'+key).fill(value)
   assert page.locator('#business-results strong').nth(1).inner_text()=='3 Verkäufe';assert page.locator('#business-results strong').nth(2).inner_text().startswith('0,00')
   page.locator('#business-cost').fill('0.30');assert page.locator('#business-results').get_by_text('Keine positive Stückmarge',exact=True).count()==1
   for key,value in {'price':'24','cost':'10','fixed':'120','quantity':'30'}.items():page.locator('#business-'+key).fill(value)
   assert page.locator('#business-results strong').nth(1).inner_text()=='9 Verkäufe';assert page.locator('#business-results strong').nth(2).inner_text().startswith('300,00')
   page.locator('#business-promptType').select_option('website');page.locator('#business-custom').fill('Schreibe eine klare Startseite mit einem Kontaktbereich.');page.locator('#business-prompt-create').click();page.wait_for_function("()=>document.getElementById('business-prompt').value.includes('Entwirf die Struktur')");assert 'LUMEN STUDIO' in page.locator('#business-prompt').input_value();page.locator('#business-results').scroll_into_view_if_needed();page.mouse.move(0,0);page.screenshot(path=str(shots/'business-zahlen-prompts.png'))
   # This is a test transport, not a claim about real model answer quality.
   page.locator('#device-voice').evaluate('(el)=>{el.checked=false;el.dispatchEvent(new Event("change"));}');page.locator('#business-prompt-ai').click();page.get_by_text('Sir, teste zuerst dein Angebot mit einem kleinen Muster.',exact=True).wait_for();assert len(calls)==1;assert calls[0][0]=='/api/chat';assert 'Entwirf die Struktur' in calls[0][1]['messages'][-1]['content']
   page.locator('#device-chat-input').fill('Gib mir einen Prompt für Instagram-Inhalte');page.locator('#chat-send').click();page.locator('#view-business').wait_for(state='visible');page.wait_for_function("()=>document.getElementById('business-prompt').value.includes('fünf konkrete Content-Ideen')");assert len(calls)==1
   with page.expect_download() as event:page.locator('#business-backup').click()
   saved=json.loads(Path(event.value.path()).read_text());assert saved['format']=='jarvis-business-v1';assert saved['data']['price']==24;assert saved['data']['quantity']==30
   bad=json.loads(json.dumps(saved));bad['data']['price']=-1;page.locator('#business-import').set_input_files({'name':'bad.json','mimeType':'application/json','buffer':json.dumps(bad).encode()});page.get_by_text('Ungültiger Betrag oder Stückzahl.',exact=True).wait_for();assert page.locator('#business-price').input_value()=='24'
   page.locator('.rail [data-view="setup"]').click()
   with page.expect_download() as event:page.locator('#workspace-export').click()
   full=json.loads(Path(event.value.path()).read_text());assert full['business']['name']=='LUMEN STUDIO'
   page.wait_for_function("()=>document.getElementById('cache-status').textContent.startsWith('Offline-Oberfläche bereit')");page.wait_for_function('()=>navigator.serviceWorker.controller!==null');context.set_offline(True);page.goto(url+'/brands#business',wait_until='domcontentloaded');page.reload(wait_until='domcontentloaded');page.locator('#view-business').wait_for(state='visible');page.get_by_text('Business-Werkzeuge bereit – auch ohne Mac.',exact=True).wait_for();assert page.locator('#business-plan').input_value()==saved['data']['plan'];assert page.locator('#business-price').input_value()=='24';assert 'Instagram-Inhalte' in page.locator('#business-prompt').input_value();page.locator('#business-plan').fill('Mein eigener bearbeiteter Angebotsentwurf.');page.wait_for_function("async()=>(await DeviceStore.get('business-v1')).plan==='Mein eigener bearbeiteter Angebotsentwurf.'")
   page.set_viewport_size({'width':390,'height':844});page.evaluate('()=>window.scrollTo(0,0)');assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');page.screenshot(path=str(shots/'business-handy.png'));assert not errors,errors
   print('PASS: active brand to offer/test plan, exact cent-based break-even calculation, no-margin case, editable prompt generation, actual local-only API handoff with test transport, prompt request from chat, invalid import preserves data, complete backup, offline persistence and mobile layout. No messages sent.')
   browser.close()
 finally:app.office.stop();app.desktop.stop();server.shutdown();server.server_close();thread.join(3)
