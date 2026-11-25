"""Readiness reflects endpoint results, not an animation timer; replay has no side effects."""
import sys,tempfile,threading,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory() as folder:
 app=Application(folder);app.store.update_settings({'voice_enabled':False,'ai_provider':'llamacpp'});server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();base='http://127.0.0.1:'+str(server.server_port)
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page(viewport={'width':1440,'height':960},reduced_motion='reduce');ai=[];voice=[];unexpected=[]
   page.on('request',lambda r:unexpected.append(r.url) if any(v in r.url for v in ['/api/chat','/api/device-ai/chat','/api/natural-voice/install','/api/natural-voice/speak']) else None)
   page.route('**/api/llamacpp/status',lambda r:(ai.append(r.request.method),r.fulfill(json={'ok':True,'message':'Fixture health is ready'}))[-1]);page.route('**/api/natural-voice/status',lambda r:(voice.append(r.request.method),r.fulfill(json={'installed':False}))[-1])
   page.goto(base+'/index.html');page.wait_for_function('()=>!!window.JarvisCore&&!!window.JarvisBridge');page.locator('#reactor').click();page.wait_for_function("()=>document.getElementById('entry-check-ai').dataset.result==='ok'&&document.getElementById('entry-check-voice').dataset.result==='problem'");assert ai==['POST'];assert voice==['GET'];assert 'nicht Antwortqualität' in page.locator('.entry-check-note').inner_text();page.locator('#core-entry').screenshot(path=str(ROOT/'artifacts/jarvis-kern-startcheck.png'));page.locator('#entry-replay').click();assert ai==['POST'];page.locator('#entry-recheck').click();page.wait_for_function("()=>document.getElementById('entry-check-ai').dataset.result==='ok'");assert len(ai)==2
   page.route('**/api/llamacpp/status',lambda r:r.fulfill(json={'ok':False}));page.locator('#entry-recheck').click();page.wait_for_function("()=>document.getElementById('entry-check-ai').dataset.result==='problem'");assert 'nicht bereit' in page.locator('#entry-check-ai').inner_text();page.locator('#entry-voice-help').click();assert page.locator('#core-entry').is_hidden();page.locator('#voice-dialog').wait_for();assert not unexpected,unexpected;page.locator('#voice-dialog').evaluate('e=>e.close()')
   # A server failure does not leave previously green health checks visible.
   page.route('**/api/status',lambda r:r.fulfill(status=503,json={'error':'controlled outage'}));page.evaluate('JarvisCore.open()');page.wait_for_function("()=>document.getElementById('entry-check-server').dataset.result==='problem'");assert page.locator('#entry-check-ai').inner_text()=='Nicht geprüft';page.locator('#entry-continue').click();assert page.locator('#core-entry').is_hidden();assert app.store.history()==[];browser.close();print('PASS: actual endpoint-driven readiness, local health only, negative states, no timer-generated success, replay without repeat checks, explicit recheck, existing voice settings shortcut, offline failure clears old green states; fixture readiness, no hardware/audio-quality claim.')
 finally:app.office.stop();app.workshop.stop();app.desktop.stop();server.shutdown();server.server_close();thread.join(2)
