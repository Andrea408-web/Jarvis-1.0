"""Guided real projects: explicit progress, current-step dialogue and opt-in voice.

Model, ASR and WAV fixtures test the real browser/server path, not hardware quality.
"""
import io,sys,tempfile,threading,wave
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory()as folder:
 app=Application(folder);app.store.update_settings({'ai_provider':'llamacpp'});chats=[];voices=[];designs=[]
 def chat(path,payload):
  chats.append(payload);return {'done':True,'message':{'content':'Sir, wir prüfen zuerst die Standfläche und deine Pappe. Die Markierung im Labor ist nur deine eigene Fortschrittsangabe.'}}
 def no_design(*args,**kwargs):
  designs.append(args);raise AssertionError('Guided projects must not generate a 3D model')
 app.llamacpp.transport=chat;app.code_room._generate=no_design
 wav=io.BytesIO()
 with wave.open(wav,'wb')as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000);w.writeframes(b'\0\0'*16000)
 app.natural_voice.synthesize=lambda text,preset:(voices.append((text,preset)),wav.getvalue())[1]
 server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 try:
  with sync_playwright()as p:
   browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page(viewport={'width':1440,'height':1040},reduced_motion='reduce');errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.add_init_script("""window.SpeechRecognition=class{start(){window.techRecognition=this;this.onstart?.();}abort(){this.aborted=true;this.onend?.();}};window.techPlaybacks=0;const original=AudioContext.prototype.createBufferSource;AudioContext.prototype.createBufferSource=function(){const source=original.call(this),start=source.start.bind(source);source.start=(...args)=>{window.techPlaybacks++;return start(...args);};return source;};""")
   page.goto('http://127.0.0.1:'+str(server.server_port));page.evaluate("async()=>{const lab=await import('/technik-lab.js');await lab.open();}")
   page.locator('#technik-lab').wait_for();assert page.locator('#tl-chooser').is_visible();assert page.locator('[data-project]').count()==3;assert page.locator('#tl-workspace').is_hidden();assert not designs
   page.locator('[data-project=stand]').click();page.locator('#tl-workspace').wait_for();project=page.locator('#tl-project-title').inner_text();first=page.locator('#tl-step-title').inner_text();assert project and first
   page.locator('#tl-preparation summary').click();assert page.locator('#tl-materials').is_visible();assert page.locator('#tl-materials li').count()>=2;assert page.locator('#tl-tools li').count()>=1
   assert page.locator('#tl-done').get_attribute('aria-pressed')=='false';page.locator('#tl-done').click();assert page.locator('#tl-done').get_attribute('aria-pressed')=='true';assert page.locator('#tl-step-title').inner_text()==first
   page.locator('#tl-next').click();page.wait_for_function('(first)=>document.getElementById("tl-step-title").textContent!==first',arg=first);assert page.locator('#tl-done').get_attribute('aria-pressed')=='false';page.locator('#tl-prev').click();assert page.locator('#tl-step-title').inner_text()==first;assert page.locator('#tl-done').get_attribute('aria-pressed')=='true'
   page.locator('#tl-input').fill('Warum hält mein Halter noch nicht?');page.locator('#tl-send').click();page.locator('#tl-chat').get_by_text('Standfläche',exact=False).wait_for();page.wait_for_function('()=>window.techPlaybacks>=1');assert len(chats)==1;prompt=chats[0]['messages'][-1]['content'];assert project in prompt;assert first in prompt;assert not designs;assert voices and all(preset=='jarvis'for _,preset in voices)
   page.locator('#tl-mute').click();page.locator('#tl-talk').click();assert page.evaluate('()=>!window.techRecognition');page.locator('#tl-consent').check();page.locator('#tl-talk').click();page.wait_for_function('()=>!!window.techRecognition');page.evaluate("()=>techRecognition.onresult({results:[[{transcript:'Was kann ich mit dünner Pappe machen?'}]]})");page.wait_for_function('()=>window.techPlaybacks>=2');assert len(chats)==2;assert not designs
   page.locator('#tl-mute').click();page.locator('#tl-talk').click();page.locator('#tl-preparation').evaluate('e=>e.open=false');page.locator('#technik-lab').evaluate('e=>e.scrollTop=0');page.screenshot(path=str(ROOT/'artifacts/jarvis-technik-labor.png'))
   page.set_viewport_size({'width':390,'height':844});assert page.locator('#technik-lab').evaluate('e=>e.scrollWidth<=e.clientWidth+1');page.locator('#tl-project-change').click();assert page.locator('#tl-chooser').is_visible();page.locator('#tl-input').fill('Ich möchte eine eigene Kugelbahn entwickeln');page.locator('#tl-send').click();page.wait_for_function('()=>window.techPlaybacks>=3');assert len(chats)==3;assert project not in str(chats[-1]['messages']);assert 'Noch kein bereitgestelltes Projekt' in chats[-1]['messages'][-1]['content'];page.locator('#tl-mute').click();page.locator('[data-project=light]').click();page.locator('#tl-workspace').wait_for();assert page.locator('#tl-done').get_attribute('aria-pressed')=='false';assert not designs;page.evaluate("async()=>{const lab=await import('/technik-lab.js');await lab.open('Ich möchte ein Windspiel entwickeln');}");assert page.locator('#tl-workspace').is_hidden();assert page.locator('#tl-input').input_value()=='Ich möchte ein Windspiel entwickeln';page.locator('#tl-send').click();page.wait_for_function('()=>window.techPlaybacks>=4');assert len(chats)==4;assert 'Noch kein bereitgestelltes Projekt' in chats[-1]['messages'][-1]['content'];assert 'USB-LED' not in str(chats[-1]['messages']);assert not designs
   page.locator('#tl-close').click();assert not page.locator('#technik-lab').is_visible();assert not errors,errors;browser.close();print('PASS: provided real guides, visible preparation, explicit manual progress survives navigation, current-project/current-step local dialogue, automatic Thorsten, opt-in speech auto-submit, no 3D calls, project switch resets progress, mobile fit and close. Controlled model/ASR/audio; hardware not tested.')
 finally:app.office.stop();app.workshop.stop();app.desktop.stop();server.shutdown();server.server_close();thread.join(2)
