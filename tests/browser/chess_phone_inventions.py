"""Visible layouts, continuous chess voice, varied replies, interactive concept diagram."""
import sys,tempfile,threading,io,wave,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from tests.test_inventions import SPEC
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory()as folder:
 app=Application(folder);app.store.update_settings({'voice_enabled':False,'ai_provider':'llamacpp'});voices=[];calls=[];bad=False;hold=False;ready=threading.Event();release=threading.Event()
 def model(path,payload=None):
  if path=='/health':return {'status':'ok'}
  calls.append(payload)
  if hold:ready.set();release.wait(5)
  return {'choices':[{'finish_reason':'stop','message':{'content':'not JSON' if bad else json.dumps(SPEC)}}]}
 app.llamacpp.endpoint_transport=model;app.llamacpp.transport=lambda *a:{'done':True,'message':{'content':'Sir, gemeinsam finden wir einen guten Gedanken.'}};app.local_ai.transport=lambda *a:{'models':[]}
 audio=io.BytesIO()
 with wave.open(audio,'wb')as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000);w.writeframes(b'\0\0'*1600)
 app.natural_voice.synthesize=lambda text,preset:(voices.append((text,preset)),audio.getvalue())[1]
 server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url='http://127.0.0.1:'+str(server.server_port)
 try:
  with sync_playwright()as pw:
   browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page(viewport={'width':1440,'height':1100},accept_downloads=True);errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.add_init_script("window.micStarts=0;window.micAborts=0;window.SpeechRecognition=class{constructor(){window.fakeMic=this;}start(){window.micStarts++;}abort(){window.micAborts++;}};window.systemSaid=0;if(window.speechSynthesis)window.speechSynthesis.speak=()=>window.systemSaid++;")
   page.goto(url+'/index.html');page.locator('#device-layout-select').select_option('phone');page.wait_for_url('**/tablet');page.wait_for_function("()=>document.body.dataset.layout==='phone'");assert page.locator('#device-layout-select').input_value()=='phone';assert page.locator('#code-open').is_hidden();assert 'layout=' not in page.url;page.reload();page.wait_for_function("()=>document.body.dataset.layout==='phone'");page.locator('#device-layout-select').select_option('ipad');page.wait_for_function("()=>document.body.dataset.layout==='ipad'");page.locator('#code-open').wait_for();page.locator('#device-layout-select').select_option('normal');page.wait_for_url('**/index.html');assert page.locator('#device-layout-select').input_value()=='normal'
   page.locator('#play-open').click();seen=[]
   for i in range(7):
    page.locator('#chess-chat-input').fill('haha');page.locator('#chess-chat-send').click();seen.append(page.locator('#chess-chat-reply').inner_text())
   assert len(set(seen))==7,seen
   page.locator('#chess-chat-input').fill('Was denkst du über Weltraumreisen?');page.locator('#chess-chat-send').click();page.get_by_text('Sir, gemeinsam finden wir einen guten Gedanken.',exact=True).wait_for();page.locator('#chess-chat-input').fill('Und über Sterne?');page.locator('#chess-chat-send').click();page.wait_for_function("()=>document.getElementById('chess-chat-reply').textContent!=='Sir, gemeinsam finden wir einen guten Gedanken.'&&!document.getElementById('chess-chat-send').disabled");assert page.locator('#chess-chat-reply').inner_text()!='Sir, gemeinsam finden wir einen guten Gedanken.'
   assert page.evaluate('window.micStarts')==0;page.locator('#chess-mic-consent').check();page.locator('#chess-mic').click();page.wait_for_function('()=>window.micStarts===1');assert page.locator('#chess-voice-on').is_checked();page.evaluate("window.fakeMic.onresult({results:[Object.assign([{transcript:'haha'}],{isFinal:true})]})");page.wait_for_function('()=>window.micStarts>=2');assert voices and all(p=='jarvis'for _,p in voices);assert page.evaluate('window.systemSaid')==0
   page.evaluate("window.fakeMic.onresult({results:[Object.assign([{transcript:'von e zwei nach e vier'}],{isFinal:true})]})");page.wait_for_function("()=>document.getElementById('chess-moves').textContent.includes('e4')");page.wait_for_function('()=>window.micStarts>=3');before=page.evaluate('window.micAborts');page.locator('#play-close').click();assert page.evaluate('window.micAborts')>before
   page.locator('#invention-open').click();page.locator('#invent-idea').fill('Ein Blumentopf, der mir zeigt, wann meine Pflanze Wasser braucht.');page.locator('#invent-generate').click();page.get_by_text('Durstsignal',exact=True).wait_for();assert page.locator('#invent-diagram svg g').count()==2;page.locator('[data-component=light]').click();assert 'Hinweis zeigen' in page.locator('#invent-component-detail').inner_text();page.screenshot(path=str(root/'artifacts/jarvis-erfinder-labor.png'))
   with page.expect_download()as event:page.locator('#invent-svg').click()
   assert 'Durstsignal' in Path(event.value.path()).read_text();page.locator('#invent-revision').fill('Ohne Akku');page.locator('#invent-refine').click();page.get_by_text('KI-Konzept mit schematischer Funktionsskizze. Nicht technisch geprüft.',exact=True).wait_for();assert 'Ohne Akku' in calls[-1]['messages'][-1]['content'];bad=True;page.locator('#invent-generate').click();page.wait_for_function("()=>document.getElementById('invent-status').textContent.includes('bisherige Skizze')");assert page.locator('#invent-title').inner_text()=='Durstsignal';bad=False
   hold=True;page.locator('#invent-generate').click();assert ready.wait(2);page.locator('#invent-idea').fill('Eine neue Idee');release.set();page.wait_for_timeout(150);assert 'Idee geändert' in page.locator('#invent-status').inner_text();page.locator('#invent-close').click()
   page.set_viewport_size({'width':390,'height':844});page.locator('#device-layout-select').select_option('phone');page.wait_for_function("()=>document.body.dataset.layout==='phone'");assert page.locator('#device-layout-select').is_visible();assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');page.screenshot(path=str(root/'artifacts/jarvis-handy-modus.png'));page.locator('#invention-open').click();assert page.locator('#invention-dialog').evaluate('e=>e.scrollWidth<=e.clientWidth+1');page.locator('#invent-close').click();assert 'Ein Blumentopf' not in json.dumps(app.store.history());assert not errors,errors;browser.close();print('PASS: visible Mac/iPad/phone selector, persisted phone layout with no typed route, Code hidden on phone, 7 unique jokes, repeated model reply handled, continuous auto-submitted speech and Thorsten-only answers, spoken legal move, close cleanup; real concept request/refinement, clickable SVG, export, stale output cancellation, honest errors and phone fit.')
 finally:release.set();app.studio_bridge.stop();app.office.stop();app.desktop.stop();server.shutdown();server.server_close();thread.join(3)
