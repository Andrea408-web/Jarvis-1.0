"""Real UI and loopback RPC of direct Studio work; mock plugin reports are labelled."""
import sys,tempfile,threading,json,urllib.request,urllib.error
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory()as folder:
 app=Application(folder)
 app.llamacpp.endpoint_transport=lambda *a:{'status':'not-running'}
 app.local_ai.transport=lambda *a:{'models':[]}
 server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url='http://127.0.0.1:'+str(server.server_port)
 try:
  with sync_playwright()as pw:
   browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page(viewport={'width':1500,'height':1180},accept_downloads=True);errors=[];downloads=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('download',lambda d:downloads.append(d.suggested_filename));page.goto(url+'/index.html');page.locator('#code-open').click();page.get_by_text('Keine lokale KI erreichbar. Starte die vorhandene KI am Mac. Es wird nichts heruntergeladen.',exact=True).wait_for();page.locator('#code-tab-studio').click()
   with page.expect_download()as event:page.locator('#code-studio-plugin').click()
   plugin=Path(event.value.path()).read_text();assert 'JarvisHeroHUD' in plugin and 'Plugin-Version' in plugin;owner='127.0.0.1|';key=app.studio_bridge.sessions[owner]['key'];bridge_url='http://127.0.0.1:'+str(app.studio_bridge.server.server_port)
   def rpc(path,body=None,version='2'):
    req=urllib.request.Request(bridge_url+path,data=None if body is None else json.dumps(body).encode(),headers={'Content-Type':'application/json','X-Jarvis-Studio':key,'X-Jarvis-Plugin-Version':version,'X-Jarvis-Place':'Browser-Testprojekt'})
    with urllib.request.urlopen(req)as r:return json.load(r)
   rpc('/poll');page.locator('#code-studio-refresh').click();page.wait_for_function('()=>!document.getElementById("code-studio-build").disabled');page.locator('#code-tab-files').click();page.locator('#code-task').fill('Baue direkt in Roblox Studio einen eigenen Superhelden-Prototyp wie Miles Morales mit Schwingen, Stadt und Dach-Zeitrennen.');page.locator('#code-access').select_option('ask');assert page.locator('#code-start').is_enabled();assert page.locator('#code-model').is_disabled();page.locator('#code-start').click();page.locator('#code-run-label').filter(has_text='Deine Freigabe fehlt').wait_for();assert page.locator('#code-studio-result').is_visible();assert page.locator('#code-download').is_hidden();assert page.locator('#code-source').is_hidden();assert not (Path(folder)/'code-projects').exists();assert rpc('/poll')['job']is None;page.locator('#code-save').filter(has_text='In Studio bauen').click();page.locator('#code-run-label').filter(has_text='Studio baut').wait_for();j=rpc('/poll')['job'];assert j['scene']['kind']=='hero-city';total=len(j['scene']['parts']);rpc('/result',{'id':j['id'],'status':'progress','count':12,'message':'Test-Plugin bestätigt 12 gebaute Stadtteile'});page.wait_for_function('()=>document.getElementById("code-events").textContent.includes("12/")');page.screenshot(path=str(root/'artifacts/jarvis-studio-direkt.png'))
   incomplete={'id':j['id'],'status':'done','count':total,'message':'unvollständig'}
   try:rpc('/result',incomplete);raise AssertionError('accepted missing gameplay')
   except urllib.error.HTTPError as e:assert e.code==403
   assert page.locator('#code-run-label').inner_text()=='Studio baut';rpc('/result',{**incomplete,'gameplay_ready':True,'message':'Test-Plugin bestätigt Stadt und Spielskripte. Play-Test bleibt offen.'});page.locator('#code-run-label').filter(has_text='Im Studio aufgebaut').wait_for();assert not (Path(folder)/'code-projects').exists()
   page.locator('#code-tab-studio').click();page.locator('#code-studio-disconnect').click();page.wait_for_function('()=>document.getElementById("code-studio-build").disabled')
   with page.expect_response('**/api/code-room/studio/reconnect')as response:page.locator('#code-studio-reconnect').click()
   assert response.value.ok;rpc('/poll');page.locator('#code-studio-refresh').click();page.wait_for_function('()=>!document.getElementById("code-studio-build").disabled');assert len(downloads)==1;assert app.studio_bridge.sessions[owner]['key']==key;page.locator('#code-studio-kind').select_option('hero-city');assert page.locator('#code-studio-buildings').is_visible();assert page.locator('#code-studio-platforms').is_hidden()
   page.locator('#code-tab-files').click();page.locator('#code-task').fill('Baue einen Roblox Parcours mit 6 Plattformen');page.locator('#code-access').select_option('project');page.locator('#code-start').click();page.locator('#code-run-label').filter(has_text='Studio baut').wait_for();other=rpc('/poll')['job'];page.locator('#code-stop').click();page.locator('#code-run-label').filter(has_text='Gestoppt').wait_for();assert rpc('/result',{'id':other['id'],'status':'progress','count':1,'message':'late'})['cancelled'];assert not errors,errors;assert len(downloads)==1;assert not (Path(folder)/'code-projects').exists();page.locator('#code-close').click();browser.close();print('PASS: automatic Roblox destination, no file fallback, Studio review gate, no model required for reviewed builders, real loopback progress, gameplay confirmation required, built label only after report, persistent reconnect without download, city settings, automatic project permission and cancellation. Actual Roblox rendering not available here.')
 finally:app.studio_bridge.stop();app.office.stop();app.desktop.stop();server.shutdown();server.server_close();thread.join(3)
