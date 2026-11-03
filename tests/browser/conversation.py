import sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from playwright.sync_api import sync_playwright
with tempfile.TemporaryDirectory() as folder:
    app=Application(folder);app.store.update_settings({'ai_provider':'llamacpp','voice_enabled':False})
    app.llamacpp.endpoint_transport=lambda *args,**kwargs:{'choices':[{'finish_reason':'stop','message':{'content':'Sir, hier ist dein Entwurf.'}}]}
    server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page(viewport={'width':1440,'height':1000});errors=[];external=[];page.on('pageerror',lambda error:errors.append(str(error)));page.route('https://**/*',lambda route:(external.append(route.request.url),route.abort()))
            page.add_init_script('''window.systemVoiceCalls=0;if(window.speechSynthesis)speechSynthesis.speak=()=>{window.systemVoiceCalls++;throw Error('Forbidden system voice');};
            window.recognitions=[];window.SpeechRecognition=class{constructor(){window.recognitions.push(this)}start(){this.onstart?.()}stop(){}};
            const originalSource=AudioContext.prototype.createBufferSource;AudioContext.prototype.createBufferSource=function(){const source=originalSource.call(this);source.playbackRate.value=8;return source;};
            window.testStreams=[];window.microphones=[];navigator.mediaDevices.getUserMedia=async()=>{const context=new AudioContext();await context.resume();const source=context.createBufferSource();const buffer=context.createBuffer(1,context.sampleRate,context.sampleRate);const samples=buffer.getChannelData(0);for(let i=0;i<samples.length;i++)samples[i]=Math.random()*2-1;source.buffer=buffer;source.loop=true;const gain=context.createGain();gain.gain.value=0;const destination=context.createMediaStreamDestination();source.connect(gain);gain.connect(destination);source.start();window.microphones.push({context,gain});window.testStreams.push(destination.stream);return destination.stream;};''')
            page.goto('http://127.0.0.1:'+str(server.server_port));page.get_by_text('LOKALE VERBINDUNG AKTIV',exact=True).wait_for()
            page.locator('#reactor').click();page.locator('#allow-mic').click();page.wait_for_function('()=>window.recognitions.length===1')
            page.evaluate("()=>{const recognition=window.recognitions.at(-1);const result=[{transcript:'Zeig meine Agenten bei der Arbeit'}];result.isFinal=true;recognition.onresult({results:[result]});recognition.onend();}")
            page.locator('#office-dialog').wait_for();page.wait_for_function('()=>window.recognitions.length>=2',timeout=20000)
            page.evaluate("()=>{const recognition=window.recognitions.at(-1);const result=[{transcript:'Beauftrage einen Agenten, der einen Lernplan erstellt'}];result.isFinal=true;recognition.onresult({results:[result]});recognition.onend();}")
            page.locator('.agent-station.planner[data-state=completed]').wait_for(timeout=10000);page.wait_for_function('()=>window.recognitions.length>=3',timeout=20000)
            page.locator('#office-dialog').get_by_role('button',name='Gespräch beenden',exact=True).click();assert page.evaluate('()=>window.JarvisConversation.active()') is False
            page.locator('#office-dialog').get_by_role('button',name='Schließen',exact=True).click()
            page.locator('#clap-enabled').check();page.get_by_text('Mikrofon an: zweimal kurz klatschen startet oder beendet das Gespräch. Auswertung erfolgt lokal.',exact=True).wait_for()
            page.evaluate('''()=>{const {context,gain}=window.microphones.at(-1);const now=context.currentTime;for(const delay of [.2,.5]){gain.gain.setValueAtTime(.9,now+delay);gain.gain.setValueAtTime(0,now+delay+.06);}}''')
            page.wait_for_function('()=>window.JarvisConversation.active()',timeout=6000)
            page.locator('#stop-speech').click();assert page.evaluate('()=>window.JarvisConversation.active()') is False;assert not page.locator('#clap-enabled').is_checked()
            assert page.evaluate('()=>window.testStreams.every(stream=>stream.getTracks().every(track=>track.readyState==="ended"))')
            assert page.evaluate('()=>window.systemVoiceCalls')==0;assert not errors,errors;assert not external,external
            print('PASS: core starts consented continuous conversation; actual bundled voice plays; recognition resumes in agent view; spoken task creates real result; local double-clap starts conversation; Stop closes all mic streams; no system voices or external requests.')
            browser.close()
    finally:app.office.stop();server.shutdown();server.server_close();thread.join(timeout=3)
