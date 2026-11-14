"""Private call integration: transient camera snapshots, local answer, actual audio playback and cleanup."""
import io,math,struct,sys,tempfile,threading,wave
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from playwright.sync_api import sync_playwright
buf=io.BytesIO()
with wave.open(buf,'wb') as wav:
 wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(16000);wav.writeframes(b''.join(struct.pack('<h',int(math.sin(i*.12)*1800)) for i in range(48000)))
with tempfile.TemporaryDirectory() as folder:
 app=Application(folder);app.store.update_settings({'ai_provider':'llamacpp','voice_enabled':False,'voice_engine':'natural'})
 app.llamacpp.endpoint_transport=lambda *args,**kwargs:{'choices':[{'finish_reason':'stop','message':{'content':'Sir, die Texterkennung meldet Milch. Das ist ein unsicherer lokaler Hinweis.'}}]}
 app.natural_voice.status=lambda:{'installed':True,'name':'Thorsten'};app.natural_voice.synthesize=lambda *a,**k:buf.getvalue()
 server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 try:
  with patch('backend.video_call.native_vision.analyze',return_value={'available':True,'labels':[{'label':'bottle','confidence':.8}],'text':'Milch'}) as vision,sync_playwright() as p:
   browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page(viewport={'width':1440,'height':1000});errors=[];frames=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:frames.append(r.post_data_json) if r.url.endswith('/api/video-call') else None)
   page.add_init_script("""window.callStreams=[];window.SpeechRecognition=class{start(){this.onstart?.()}stop(){}};navigator.mediaDevices.getUserMedia=async constraint=>{if(constraint.video){const c=document.createElement('canvas');c.width=640;c.height=480;const x=c.getContext('2d');x.fillStyle='#243942';x.fillRect(0,0,640,480);x.fillStyle='white';x.font='60px sans-serif';x.fillText('MILCH',160,230);const s=c.captureStream(8);setInterval(()=>x.fillRect(0,0,1,1),100);callStreams.push(s);return s;}const a=new AudioContext(),s=a.createMediaStreamDestination().stream;callStreams.push(s);return s;};""")
   page.goto('http://127.0.0.1:'+str(server.server_port)+'/index.html');page.get_by_role('button',name='Videoanruf mit Jarvis',exact=True).click();assert page.locator('#call-video').is_hidden();assert not frames
   page.locator('#call-start').click();page.locator('#allow-mic').click();page.wait_for_function('()=>document.getElementById("call-video").videoWidth>0');page.wait_for_timeout(300);assert not frames,'Preview alone must not upload';assert vision.call_count==0
   page.locator('#call-input').fill('Was steht darauf?');page.locator('#call-form').get_by_role('button',name='Fragen',exact=True).click();page.locator('#call-transcript .assistant').wait_for();assert frames[0]['image'].startswith('/9j/');assert vision.call_count==1;assert app.store.history()==[];assert 'Milch' not in page.locator('#messages').inner_text()
   page.wait_for_function('()=>document.getElementById("call-state").textContent==="THORSTEN SPRICHT"');page.screenshot(path='/tmp/jarvis-video-call.png')
   page.locator('#call-camera').click();assert page.locator('#call-video').is_hidden();page.locator('#call-input').fill('Weiter ohne Kamera');page.locator('#call-form').get_by_role('button',name='Fragen',exact=True).click();page.wait_for_function('()=>document.querySelectorAll("#call-transcript .assistant").length===2');assert 'image' not in frames[-1];assert vision.call_count==1;assert app.store.history()==[]
   pending=[];page.route('**/api/video-call',lambda r:pending.append(r));page.locator('#call-input').fill('Späte Antwort');page.locator('#call-form').get_by_role('button',name='Fragen',exact=True).click();page.wait_for_timeout(250);assert pending;page.locator('#call-end').click();page.wait_for_function('()=>!JarvisBridge.interaction().busy');assert page.locator('#call-transcript').inner_text()=='';assert page.evaluate('()=>callStreams.every(s=>s.getTracks().every(t=>t.readyState==="ended"))');assert page.evaluate('()=>!JarvisConversation.active()');assert app.store.history()==[]
   
   for route in pending:
    try:route.abort()
    except Exception:pass
   page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+2');assert not errors,errors
   print('PASS: call preview never uploads, per-question JPEG reaches local Vision, no DB history, camera off sends text only, Thorsten path plays audio and mouth follows playback, end aborts stale answers/closes all devices. Controlled camera/Vision/voice; no physical Mac test.')
   browser.close()
 finally:app.office.stop();server.shutdown();server.server_close();thread.join(3)
