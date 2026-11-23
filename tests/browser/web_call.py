"""Controlled peer transport with actual microphone/WebAudio streams; cloud policy blocks UDP."""
import sys,tempfile,threading,io,wave,math,struct
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory()as folder:
 app=Application(folder);app.store.update_settings({'ai_provider':'llamacpp'});chats=[];voices=[]
 def chat(path,payload):chats.append(payload);return {'done':True,'message':{'content':'Gerne, ich kann den Termin am Dienstag vorschlagen.'}}
 app.llamacpp.transport=chat;data=io.BytesIO()
 with wave.open(data,'wb')as wav:
  wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(16000);wav.writeframes(b''.join(struct.pack('<h',int(math.sin(i*2*math.pi*440/16000)*9000))for i in range(48000)))
 app.natural_voice.synthesize=lambda text,preset:(voices.append((text,preset)),data.getvalue())[1]
 server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url='http://127.0.0.1:'+str(server.server_port)
 try:
  with sync_playwright()as p:
   browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream','--autoplay-policy=no-user-gesture-required']);context=browser.new_context(permissions=['microphone']);context.add_init_script("window.SpeechRecognition=class{start(){window.callRecognition=this;this.onstart?.();}abort(){this.onend?.();}};")
   context.add_init_script(path=str(root/'tests/browser/rtc_fixture.js'));host=context.new_page();host.goto(url+'/web-call');
   with host.expect_popup()as popup:host.evaluate("url=>window.open(url,'guest')",url+'/web-call')
   guest=popup.value;errors=[]
   for page in [host,guest]:page.on('pageerror',lambda e:errors.append(str(e)));page.goto(url+'/web-call');page.locator('#wc-mic-consent').check()
   host.locator('#wc-create').click();host.wait_for_function("()=>document.getElementById('wc-signal').value.length>100");offer=host.locator('#wc-signal').input_value();guest.locator('#wc-signal').fill(offer);guest.locator('#wc-apply').click();guest.wait_for_function("()=>document.getElementById('wc-signal').value.length>100");answer=guest.locator('#wc-signal').input_value();assert answer!=offer;host.locator('#wc-signal').fill(answer);host.locator('#wc-apply').click()
   for page in [host,guest]:page.wait_for_function("()=>document.getElementById('wc-state').textContent.toLowerCase().includes('verbindung')&&document.getElementById('wc-remote').srcObject?.getAudioTracks()[0]?.readyState==='live'",timeout=30000)
   # Manual messages are actual peer-data messages. They must not trigger AI by default.
   guest.locator('#wc-message').fill('Hallo, wann passt der Termin?');guest.locator('#wc-message-form button').click();host.locator('#wc-log').get_by_text('Gegenüber: Hallo',exact=False).wait_for();assert not chats and not voices
   host.locator('#wc-listen').check();host.locator('#wc-agreed').check();host.locator('#wc-mode').select_option('suggest');guest.locator('#wc-message').fill('Geht Dienstag?');guest.locator('#wc-message-form button').click();host.wait_for_function("()=>document.getElementById('wc-draft').value.includes('Dienstag')");assert len(chats)==1 and not voices
   # Measure actual incoming audio: AI PCM goes into the outgoing WebRTC mix.
   guest.evaluate("async()=>{window.meterCtx=new AudioContext();await meterCtx.resume();window.meter=meterCtx.createAnalyser();meterCtx.createMediaStreamSource(document.getElementById('wc-remote').srcObject).connect(meter);}")
   host.locator('#wc-say').click();guest.locator('#wc-log').get_by_text('KI-Assistent: Hallo, ich bin Jarvis',exact=False).wait_for();guest.wait_for_function("()=>{const a=new Uint8Array(meter.fftSize);meter.getByteTimeDomainData(a);return [...a].some(v=>Math.abs(v-128)>4)}",timeout=10000);assert voices[0][1]=='jarvis';assert voices[0][0].startswith('Hallo, ich bin Jarvis, ein KI-Assistent.')
   host.locator('#wc-ai-stop').click();host.locator('#wc-listen').check();host.locator('#wc-mode').select_option('auto');guest.locator('#wc-caption-consent').check();guest.wait_for_function('()=>!!window.callRecognition');guest.evaluate("()=>callRecognition.onresult({results:[[{transcript:'Und wie spät?'}]]})");host.locator('#wc-log').get_by_text('Gegenüber · erkannt: Und wie spät?',exact=True).wait_for();host.wait_for_function("()=>document.getElementById('wc-ai-state').textContent.includes('Thorsten spricht')");assert len(chats)==2
   host.locator('#wc-ptt').scroll_into_view_if_needed();box=host.locator('#wc-ptt').bounding_box();host.mouse.move(box['x']+box['width']/2,box['y']+box['height']/2);host.mouse.down();assert host.locator('#wc-mode').input_value()=='manual';assert host.locator('#wc-ptt').get_attribute('aria-pressed')=='true';host.mouse.up();assert host.locator('#wc-ptt').get_attribute('aria-pressed')=='false'
   host.locator('#wc-owner').screenshot(path=str(root/'artifacts/jarvis-web-anruf.png'));host.locator('#wc-block').click();assert 'blockiert'in host.locator('#wc-state').inner_text();assert not host.locator('#wc-log p').count();guest.wait_for_function("()=>document.getElementById('wc-state').textContent.includes('geschlossen')");assert not errors,errors;browser.close();print('PASS: controlled peer transport with actual microphone/WebAudio streams, manual and recognized peer messages, AI suggestion/automatic turn, actual Thorsten PCM received over the shared peer audio stream, manual takeover and session block cleanup. Cloud policy prevents real UDP/WebRTC connection tests; network transport, AI and ASR are fixtures. No phone network or physical Safari tested.')
 finally:app.office.stop();app.workshop.stop();app.desktop.stop();server.shutdown();server.server_close();thread.join(2)
