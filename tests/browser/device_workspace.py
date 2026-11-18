"""Real browser offline workspace, exports, storage, and optional real WASM test.
--runtime uses the two verified npm archives in /tmp; no network download in test.
Synthetic weights verify execution only, not production model quality or iOS hardware.
"""
import argparse,json,sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from backend.device_ai import DeviceAI
from tiny_gguf import write_model
from playwright.sync_api import sync_playwright
args=argparse.ArgumentParser();args.add_argument('--runtime',action='store_true');options=args.parse_args()
root=Path(__file__).resolve().parents[2];shots=root/'artifacts';shots.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory() as folder:
 app=Application(folder);app.store.update_settings({'voice_enabled':False,'ai_provider':'llamacpp'})
 app.device_ai=DeviceAI(folder,locator=lambda:write_model(Path(folder)/'test.gguf') if not (Path(folder)/'test.gguf').exists() else Path(folder)/'test.gguf')
 if options.runtime:
  app.device_ai.prepare(lambda p:Path('/tmp/wllama-compat-3.13.0.tgz' if 'compat' in p['url'] else '/tmp/wllama-3.13.0.tgz').read_bytes())
 server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url='http://127.0.0.1:'+str(server.server_port)
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);context=browser.new_context(viewport={'width':1440,'height':1100},accept_downloads=True);page=context.new_page();errors=[];blocked=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda msg:print('BROWSER',msg.text[:1000]) if msg.type=='error' else None)
   page.on('request',lambda r:blocked.append(r.url) if not r.url.startswith((url,'blob:','data:')) else None)
   page.goto(url+'/brands');page.wait_for_function("()=>document.getElementById('brand-select').options.length>0");page.locator('.rail [data-view="chat"]').click();page.locator('#device-voice').uncheck();page.locator('.rail [data-view="brands"]').click()
   for key,value in {'name':'LUMEN STUDIO','tagline':'Kleine Ideen. Klarer Auftritt.','product':'Designvorlagen und handgemachte Notizbücher.','audience':'Kreative Menschen mit eigenen Projekten','tone':'Klar, warm und neugierig','goal':'Die erste eigene Kollektion vorstellen','website':'lumen.example'}.items():page.locator('#brand-'+key).fill(value)
   page.locator('#brand-form button.primary').click();page.locator('#brand-preview-name').get_by_text('LUMEN STUDIO',exact=True).wait_for()
   page.wait_for_timeout(4600);page.screenshot(path=str(shots/'markenstudio-normal.png'),full_page=False)
   for button,name in [('#brand-logo','Logoidee.svg'),('#brand-card','Markenkarte.png'),('#brand-export','Jarvis-Markenprofil.json')]:
    with page.expect_download() as event:page.locator(button).click()
    download=event.value;assert download.suggested_filename==name;assert Path(download.path()).stat().st_size>100
   page.locator('#brand-plan').click();assert page.locator('#content-plan article').count()==7;page.locator('#content-plan article').first.get_by_text('Als Aufgabe planen').click()
   page.locator('details summary').click();page.locator('#brand-push').click();page.wait_for_function("()=>document.getElementById('device-toast').textContent.includes('auf dem Mac gespeichert')");assert app.brands.all()['profiles'][0]['name']=='LUMEN STUDIO'
   page.locator('.rail [data-view="chat"]').click();page.locator('#device-chat-input').fill('Erstelle eine Notiz');page.locator('#chat-send').click();page.get_by_text('Was soll in der Notiz stehen, Sir?',exact=True).wait_for();page.locator('#device-chat-input').fill('Morgen Milch kaufen');page.locator('#chat-send').click();page.get_by_text('Die Notiz ist auf diesem Gerät gespeichert, Sir.',exact=True).wait_for()
   page.locator('#device-layout-select').select_option('ipad');page.set_viewport_size({'width':1194,'height':900});page.locator('.rail [data-view="sketch"]').click()
   board=page.locator('#sketch-canvas').bounding_box();page.mouse.move(board['x']+80,board['y']+100);page.mouse.down();page.mouse.move(board['x']+250,board['y']+200,steps=20);page.mouse.move(board['x']+430,board['y']+90,steps=20);page.mouse.up()
   page.wait_for_timeout(400);assert page.evaluate("async()=>(await DeviceStore.get('workspace')).sketch.length")==1
   page.locator('#sketch-clear').click()
   # A product-box concept drawn through real pointer input, rather than a mockup overlay.
   for line in [[(130,150),(300,60),(500,150),(330,250),(130,150)],[(130,150),(130,320),(330,430),(500,320),(500,150)],[(330,250),(330,430)],[(300,60),(300,200)]]:
    page.mouse.move(board['x']+line[0][0],board['y']+line[0][1]);page.mouse.down()
    for x,y in line[1:]:page.mouse.move(board['x']+x,board['y']+y,steps=12)
    page.mouse.up()
   page.wait_for_timeout(4600);page.screenshot(path=str(shots/'ipad-skizze.png'),full_page=False)
   with page.expect_download() as event:page.locator('#sketch-export').click()
   assert event.value.suggested_filename=='Jarvis-Skizze.png'
   page.locator('.rail [data-view="setup"]').click();page.wait_for_function("()=>document.getElementById('cache-status').textContent.startsWith('Offline-Oberfläche bereit')");page.wait_for_function('()=>navigator.serviceWorker.controller!==null')
   if options.runtime:
    page.locator('#ai-install').click();page.wait_for_function("()=>/erfolgreich gestartet|konnte|fehl|Error|error|starten/.test(document.getElementById('model-status').textContent)",timeout=120000);print('INSTALL:',page.locator('#model-status').inner_text());assert page.evaluate('DeviceAI.loaded')
   context.set_offline(True);page.goto(url+'/tablet',wait_until='domcontentloaded');page.wait_for_function("()=>document.getElementById('connection-badge').textContent.includes('OHNE MAC')")
   page.locator('.rail [data-view="notes"]').click();page.locator('#notes-list').get_by_text('Morgen Milch kaufen',exact=True).first.wait_for();page.locator('.rail [data-view="planner"]').click();assert page.locator('#task-list .task-row').count()==1
   page.locator('.rail [data-view="brands"]').click();assert page.locator('#brand-name').input_value()=='LUMEN STUDIO'
   if options.runtime:
    result=page.evaluate("async()=>{let streamed='';const reply=await DeviceAI.chat([{role:'user',content:'Hello'}],()=>{},text=>streamed=text);return {reply,streamed,loaded:DeviceAI.loaded};}")
    assert result['loaded'] and result['reply'] and result['streamed'];print('PASS: real WASM inference after offline page reload with synthetic weights.')
    # Exercise the actual wasm32 compatibility binary used by Safari, within Chromium.
    result=page.evaluate("""async()=>{await DeviceAI.unload();const {Wllama}=await import('/device-runtime/3.13.0/wllama.js');const e=new Wllama({default:'/device-runtime/3.13.0/wllama.wasm'},{allowOffline:true,suppressNativeLog:true});e.getWorkerResources=()=>({wasmPath:location.origin+'/device-runtime/3.13.0/compat.wasm',jsPath:location.origin+'/device-runtime/3.13.0/compat.js',compat:true,noWebGPU:true});const m=await DeviceAI.record(),parts=[];for(let i=0;i<m.count;i++)parts.push(await DeviceStore.chunk(m.id+':'+i));await e.loadModel([new Blob(parts)],{n_ctx:256,n_batch:32,n_threads:1,n_gpu_layers:0,warmup:false,jinja:true});let count=0;await e.createChatCompletion({messages:[{role:'user',content:'Hi'}],max_tokens:6,stream:true,onData:chunk=>{if(chunk.choices?.[0]?.delta?.content)count++;}});await e.exit();return count;}""")
    assert result>0;print('PASS: actual Safari compatibility binary runs offline (Chromium engine, not physical Safari).')
   page.set_viewport_size({'width':390,'height':844});page.locator('.rail [data-view="setup"]').click();page.locator('#layout-phone').click();page.locator('.rail [data-view="chat"]').click();page.locator('#chat-clear').click();page.wait_for_timeout(4600);page.screenshot(path=str(shots/'handy-unterwegs.png'),full_page=False)
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'), 'Phone horizontal overflow'
   assert not blocked,blocked;assert not errors,errors
   print('PASS: real responsive brand studio, PNG/SVG/profile export, template plan, explicit Mac transfer, note follow-up, drawing, offline reload/storage and phone layout. Screenshots in artifacts/.')
   browser.close()
 finally:app.office.stop();app.desktop.stop();server.shutdown();server.server_close();thread.join(3)
