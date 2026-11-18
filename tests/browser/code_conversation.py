"""Actual browser conversation controls and real local bridge protocol; no Studio installed."""
import sys,tempfile,threading,json,io,wave,urllib.request,xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory()as folder:
 app=Application(folder);voices=[];calls=[];ready=threading.Event();release=threading.Event();hold=False
 def transport(path,payload=None):
  if path=='/health':return {'status':'ok'}
  calls.append(payload)
  if payload.get('response_format'):
   if hold:ready.set();release.wait(8)
   reply=json.dumps({'summary':'Ein heller Entwurf.','files':[{'path':'index.html','content':'<!doctype html><h1>Hallo Sir</h1>'}]})
  else:reply='Sir, lass uns eine übersichtliche Website mit klarer Überschrift planen.'
  return {'choices':[{'finish_reason':'stop','message':{'content':reply}}]}
 app.llamacpp.endpoint_transport=transport;app.local_ai.transport=lambda *args:{'models':[]}
 audio=io.BytesIO()
 with wave.open(audio,'wb')as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000);w.writeframes(b'\0\0'*1600)
 app.natural_voice.synthesize=lambda text,preset:(voices.append((text,preset)),audio.getvalue())[1]
 server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url='http://127.0.0.1:'+str(server.server_port)
 try:
  with sync_playwright()as pw:
   browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page(viewport={'width':1500,'height':1150},accept_downloads=True);errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.add_init_script("window.micStarts=0;window.micAborts=0;window.SpeechRecognition=class{constructor(){window.fakeMic=this;}start(){window.micStarts++;}stop(){}abort(){window.micAborts++;}};window.systemSaid=0;if(window.speechSynthesis)window.speechSynthesis.speak=()=>{window.systemSaid++;};")
   page.goto(url+'/index.html');page.locator('#code-open').click();page.get_by_text('Lokale KI verbunden. Es wird kein Modell heruntergeladen.',exact=True).wait_for();page.locator('#code-tab-talk').click();page.locator('#code-talk-input').fill('Wie könnte meine Website aussehen?');page.locator('#code-talk-send').click();page.locator('#code-talk-history').get_by_text('Sir, lass uns eine übersichtliche Website mit klarer Überschrift planen.',exact=True).wait_for();page.wait_for_function('()=>document.getElementById("code-talk-send").disabled===false');assert voices and voices[-1][1]=='jarvis';assert page.evaluate('window.systemSaid')==0;assert page.evaluate('window.micStarts')==0
   page.locator('#code-task').fill('Erstelle eine Website');hold=True;page.locator('#code-start').click();assert ready.wait(2);page.locator('#code-tab-talk').click();page.locator('#code-talk-consent').check();page.locator('#code-talk-mic').click();page.wait_for_function('()=>window.micStarts===1');page.evaluate("window.fakeMic.onresult({results:[Object.assign([{transcript:'Wie weit bist du?'}],{isFinal:true})]})");page.locator('#code-talk-history').get_by_text('Wie weit bist du?',exact=True).wait_for();page.wait_for_function('()=>window.micStarts>=2');assert len(calls)==2
   page.locator('#code-talk-kind').select_option('steer');page.evaluate("window.fakeMic.onresult({results:[Object.assign([{transcript:'Bitte heller gestalten'}],{isFinal:true})]})");page.get_by_text('Zusatzwunsch empfangen. Im Ablauf siehst du, ob er eingearbeitet wurde.',exact=True).wait_for();release.set();page.locator('#code-run-label').filter(has_text='Deine Freigabe fehlt').wait_for();assert list(app.code_room.jobs.values())[0]['instructions'][0]['applied'];assert any('Bitte heller gestalten' in p['messages'][-1]['content'] for p in calls);page.locator('#code-talk-mic').click();page.mouse.move(0,0);page.screenshot(path=str(root/'artifacts/jarvis-code-gespraech.png'))
   page.locator('#code-tab-studio').click();assert page.locator('#code-studio-build').is_disabled()
   with page.expect_download()as event:page.locator('#code-studio-plugin').click()
   data=Path(event.value.path()).read_text();assert ET.fromstring(data).find('.//ProtectedString')is not None;assert 'loadstring(' not in data
   key=app.studio_bridge.sessions['127.0.0.1|']['key'];bridge_url='http://127.0.0.1:'+str(app.studio_bridge.server.server_port)
   def request(path,body=None):
    req=urllib.request.Request(bridge_url+path,data=None if body is None else json.dumps(body).encode(),headers={'X-Jarvis-Studio':key,'Content-Type':'application/json'})
    with urllib.request.urlopen(req)as r:return json.load(r)
   request('/poll');page.locator('#code-studio-refresh').click();page.wait_for_function('()=>!document.getElementById("code-studio-build").disabled');page.locator('#code-studio-platforms').select_option('6');page.locator('#code-studio-build').click();page.wait_for_function("()=>document.getElementById('code-studio-state').textContent.includes('An Studio übergeben')");j=request('/poll')['job'];assert len(j['scene']['parts'])==14;request('/result',{'id':j['id'],'status':'progress','count':4,'message':'Test-Plugin bestätigt 4 Teile'});page.locator('#code-studio-refresh').click();page.wait_for_function("()=>document.getElementById('code-studio-state').textContent.includes('4/14')");page.mouse.move(0,0);page.screenshot(path=str(root/'artifacts/jarvis-roblox-bruecke.png'));request('/result',{'id':j['id'],'status':'done','count':14,'message':'Test-Plugin meldet Bau abgeschlossen; Spieltest offen.'});page.locator('#code-studio-refresh').click();page.wait_for_function("()=>document.getElementById('code-studio-state').textContent.includes('14/14')");page.locator('#code-studio-disconnect').click();page.wait_for_function('()=>document.getElementById("code-studio-build").disabled')
   page.locator('#code-tab-talk').click();page.locator('#code-talk-kind').select_option('talk');starts=page.evaluate('window.micStarts');page.locator('#code-talk-mic').click();page.wait_for_function('(n)=>window.micStarts>n',arg=starts);before=page.evaluate('window.micAborts');page.locator('#code-close').click();assert page.evaluate('window.micAborts')>before;assert 'Bitte heller gestalten' not in json.dumps(app.store.history());assert not errors,errors;browser.close();print('PASS: local pre-task conversation, automatic mic submission and restart, Thorsten WAV only, grounded busy status without parallel model call, real steering revision, lifecycle cleanup and no chat archive; plugin XML export and actual loopback HTTP pairing/progress/completion/disconnect. Studio execution itself not available here.')
 finally:release.set();app.studio_bridge.stop();app.office.stop();app.desktop.stop();server.shutdown();server.server_close();thread.join(3)
