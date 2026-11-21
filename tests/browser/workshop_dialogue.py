"""Real workshop HTTP/dialogue/audio lifecycle with controlled model, WAV and ASR fixtures."""
import io,json,sys,tempfile,threading,wave
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory() as folder:
 app=Application(folder);app.store.update_settings({'ai_provider':'llamacpp'});chats=[];voices=[];designs=[];fail_voice=[False]
 def chat(path,payload):
  chats.append(payload);return {'done':True,'message':{'content':'Sir, wir besprechen zuerst deine Idee. Eine runde Kameraöffnung ist möglich; ein Bauentwurf wurde noch nicht erstellt.'}}
 app.llamacpp.transport=chat
 def unexpected_design(*args,**kwargs):
  designs.append(args);raise AssertionError('A conversation must not generate geometry')
 app.code_room._generate=unexpected_design
 audio=io.BytesIO()
 with wave.open(audio,'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000);w.writeframes(b'\0\0'*16000)
 def speak(text,preset):
  voices.append((text,preset))
  if fail_voice[0]:raise ValueError('Thorsten-Testfehler: bitte erneut versuchen.')
  return audio.getvalue()
 app.natural_voice.synthesize=speak
 server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url='http://127.0.0.1:'+str(server.server_port)
 try:
  with sync_playwright() as pw:
   b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']);page=b.new_page(viewport={'width':1440,'height':1040},reduced_motion='reduce');errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.add_init_script("""window.SpeechRecognition=class{start(){window.studioRecognition=this;this.onstart?.();}abort(){this.aborted=true;this.onend?.();}};window.playbacks=0;const source=AudioContext.prototype.createBufferSource;AudioContext.prototype.createBufferSource=function(){const node=source.call(this),start=node.start.bind(node);node.start=(...args)=>{window.playbacks++;return start(...args);};return node;};""")
   page.goto(url);page.wait_for_function('()=>!!window.JarvisWorkshopOpen');page.evaluate('()=>JarvisWorkshopOpen()');page.locator('#build-talk').wait_for(state='visible');assert page.locator('#build-speech-consent').is_visible()
   # Fresh typed question automatically renders Thorsten without mic or guide clicks.
   page.locator('#build-request').fill('Hallo, wie kann ich meine Idee besprechen?');page.locator('#build-submit').click();page.wait_for_function('()=>window.playbacks===1');assert len(chats)==1;assert len(voices)==1;assert not designs;assert page.locator('#build-result').is_hidden();assert page.locator('#build-input-mode').input_value()=='auto'
   page.locator('#build-face-mute').evaluate('e=>e.click()');assert page.locator('#build-read').is_checked()
   # Consent required before ASR starts; spoken result submits discussion automatically.
   page.locator('#build-talk').click();assert page.evaluate('()=>!window.studioRecognition');page.locator('#build-speech-consent').check();page.locator('#build-talk').click();page.wait_for_function('()=>!!window.studioRecognition');page.evaluate("()=>studioRecognition.onresult({results:[[{transcript:'Kann ich das mit einer Kamera steuern?'}]]})");page.wait_for_function('()=>window.playbacks===2');assert len(chats)==2;assert not designs;assert all(preset=='jarvis' for _,preset in voices)
   page.locator('#build-talk').click();assert page.locator('#build-talk').get_attribute('aria-pressed')=='false'
   # Explicit discussion mode keeps declarative messages out of geometry too.
   page.locator('#build-input-mode').select_option('talk');page.locator('#build-request').fill('Ich finde die Idee noch nicht gut');page.locator('#build-submit').click();page.wait_for_function('()=>window.playbacks===3');assert len(chats)==3;assert not designs
   # Visible audio errors; retry only retries audio and never sends a phantom design.
   page.locator('#build-face-mute').evaluate('e=>e.click()');fail_voice[0]=True;page.locator('#build-speech-settings summary').click();page.locator('#build-voice-test').click();page.locator('#build-voice-status').get_by_text('Thorsten-Testfehler',exact=False).wait_for();assert not designs;fail_voice[0]=False;page.locator('#build-voice-test').click();page.wait_for_function('()=>window.playbacks===4');assert not designs
   page.locator('#build-studio').evaluate('e=>e.scrollTop=0');page.screenshot(path=str(root/'artifacts/jarvis-baustudio-gespraech.png'));page.locator('#build-close').click();assert not errors,errors;b.close();print('PASS: visible consent/mic, pre-model questions route to dialogue, fresh typed answer plays Thorsten automatically, speech auto-submits question, mute preserves next auto-play, explicit discussion prevents redesign, failed audio is visible/retryable and never creates geometry. Model/ASR/WAV use fixtures; real microphone hardware not tested.')
 finally:app.office.stop();app.workshop.stop();app.desktop.stop();server.shutdown();server.server_close();thread.join(2)
