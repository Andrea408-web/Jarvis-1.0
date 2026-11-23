"""Device speech turns with controlled ASR/model/WAV; no physical Safari claim."""
import io,sys,tempfile,threading,wave
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from playwright.sync_api import sync_playwright
with tempfile.TemporaryDirectory() as folder:
 app=Application(folder);app.store.update_settings({'ai_provider':'llamacpp'});chats=[];voices=[]
 app.llamacpp.transport=lambda path,payload:(chats.append(payload),{'done':True,'message':{'content':'Sir, ich höre dir zu.'}})[1]
 data=io.BytesIO()
 with wave.open(data,'wb')as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000);w.writeframes(b'\0\0'*3200)
 app.natural_voice.synthesize=lambda text,preset:(voices.append(preset),data.getvalue())[1]
 server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 try:
  with sync_playwright()as p:
   browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--autoplay-policy=user-gesture-required']);page=browser.new_page(viewport={'width':390,'height':844});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.add_init_script("window.recStarts=0;window.SpeechRecognition=class{start(){window.deviceRec=this;window.recStarts++;this.onstart?.();}abort(){this.onend?.();}};")
   page.goto('http://127.0.0.1:'+str(server.server_port)+'/tablet?layout=phone');page.wait_for_function('()=>window.JarvisDeviceShellReady&&window.JarvisMacConnected');page.locator('#device-mic').click();assert page.evaluate('recStarts')==0
   page.locator('#device-mic-consent').check();page.locator('#device-mic').click();page.wait_for_function('()=>recStarts===1');page.evaluate("deviceRec.onresult({results:[[{transcript:'Wie geht es dir?'}]]})");page.locator('#device-messages').get_by_text('Sir, ich höre dir zu.',exact=True).wait_for();page.wait_for_function('()=>recStarts>=2');assert chats and voices==['jarvis']
   page.evaluate("deviceRec.onresult({results:[[{transcript:'Und jetzt?'}]]})");page.wait_for_function('()=>recStarts>=3');assert len(chats)==2 and voices==['jarvis','jarvis'];page.locator('#device-mic-consent').uncheck();assert page.locator('#device-mic').get_attribute('aria-pressed')=='false';assert not errors,errors;browser.close();print('PASS: phone speech consent, two automatically submitted voice turns, fixed Thorsten requests, browser audio playback and continuous recognition resumption. ASR/model/WAV fixtures; physical Safari and installed voice not tested.')
 finally:app.office.stop();app.workshop.stop();app.desktop.stop();server.shutdown();server.server_close();thread.join(2)
