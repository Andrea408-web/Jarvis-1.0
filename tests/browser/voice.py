import sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from playwright.sync_api import sync_playwright
with tempfile.TemporaryDirectory() as folder:
    app=Application(folder);app.store.update_settings({'ai_provider':'llamacpp','voice_enabled':False});server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page();errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
            page.add_init_script("window.systemVoiceCalls=0;if(window.speechSynthesis){speechSynthesis.speak=()=>{window.systemVoiceCalls++;throw Error('System voice must never run');};}")
            page.goto('http://127.0.0.1:'+str(server.server_port));page.get_by_text('LOKALE VERBINDUNG AKTIV',exact=True).wait_for()
            result=page.evaluate("async()=>{const wav=await window.JarvisVoice.render('Guten Tag, Sir. Die Systeme sind bereit.');const context=new AudioContext();const audio=await context.decodeAudioData(wav);let energy=0;for(const sample of audio.getChannelData(0))energy+=sample*sample;await context.close();return {duration:audio.duration,rate:audio.sampleRate,energy};}")
            assert result['duration']>1 and result['energy']>0,result
            page.get_by_role('button',name='Stimme',exact=True).click();page.locator('[data-preset=jarvis]').click();page.get_by_text('JARVIS · EIGENE OFFLINE-ENGINE',exact=True).wait_for(timeout=10000)
            assert page.evaluate('()=>window.systemVoiceCalls')==0;assert not errors,errors
            print('PASS: actual German speech generated, decoded and playing without any system voice:',result)
            browser.close()
    finally:app.office.stop();server.shutdown();server.server_close();thread.join(timeout=3)
