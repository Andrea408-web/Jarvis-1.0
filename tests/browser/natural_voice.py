"""Optional real neural inference check; model/runtime stay outside the repository."""
import os,sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from backend.natural_voice import generate
from playwright.sync_api import sync_playwright
root=Path(os.environ.get('JARVIS_NEURAL_TEST_FILES','/tmp/jarvis-natural-test'))
runtime=next((root/'linux-extracted').iterdir());model=next((root/'voice-extracted').iterdir())
with tempfile.TemporaryDirectory() as folder:
    app=Application(folder);app.store.update_settings({'ai_provider':'llamacpp','voice_engine':'natural','voice_enabled':False})
    app.natural_voice.status=lambda:{'installed':True,'name':'Thorsten'}
    def synthesize(text,preset,**kwargs):
        return generate(runtime/'bin/sherpa-onnx-offline-tts',model/'de_DE-thorsten-medium.onnx',model/'tokens.txt',model/'espeak-ng-data',text,Path(folder)/'speech.wav',preset)
    app.natural_voice.synthesize=synthesize
    server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page();errors=[];requests=[]
            page.on('pageerror',lambda error:errors.append(str(error)));page.on('request',lambda request:requests.append(request.url))
            page.add_init_script("window.systemCalls=0;if(window.speechSynthesis)speechSynthesis.speak=()=>{window.systemCalls++;throw Error('System voice forbidden');};")
            page.goto('http://127.0.0.1:'+str(server.server_port));page.get_by_text('LOKALE VERBINDUNG AKTIV',exact=True).wait_for()
            page.get_by_role('button',name='Stimme',exact=True).click();page.get_by_role('button',name='Natürliche Stimme verwenden',exact=True).click()
            page.get_by_text('THORSTEN · NEURONALE OFFLINE-STIMME',exact=True).wait_for(timeout=15000)
            assert page.evaluate('()=>window.systemCalls')==0;assert not any('voice-worker.js' in url for url in requests)
            assert any('/api/natural-voice/speak' in url for url in requests);assert not errors,errors
            print('PASS: actual neural German model -> authenticated backend WAV -> browser playback; no system speech, formant worker or external voice service.')
            browser.close()
    finally:app.office.stop();server.shutdown();server.server_close();thread.join(timeout=3)
