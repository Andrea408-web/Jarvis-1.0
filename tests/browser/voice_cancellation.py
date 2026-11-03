"""Conversational mute must not abort a voice render used by a background export."""
import sys,tempfile,threading,time,struct
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from tests.test_natural_voice import wav_bytes
from playwright.sync_api import sync_playwright
with tempfile.TemporaryDirectory() as folder:
    app=Application(folder);app.store.update_settings({'voice_engine':'natural','voice_enabled':False})
    server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page();routes=[]
            page.route('**/api/natural-voice/speak',lambda route:routes.append(route))
            page.goto('http://127.0.0.1:'+str(server.server_port));page.get_by_text('LOKALE VERBINDUNG AKTIV',exact=True).wait_for()
            page.evaluate("()=>{window.bg='pending';window.fg='pending';window.JarvisVoice.render('background','jarvis',{background:true}).then(wav=>window.bg=wav.byteLength).catch(error=>window.bg=error.name);window.JarvisVoice.render('interactive').then(()=>window.fg='done').catch(error=>window.fg=error.name);}")
            deadline=time.monotonic()+3
            while len(routes)<2 and time.monotonic()<deadline:page.wait_for_timeout(20)
            assert len(routes)==2
            page.evaluate('()=>window.JarvisVoice.cancel()')
            page.wait_for_function("()=>window.fg==='AbortError'")
            assert page.evaluate('()=>window.bg')=='pending'
            route=next(route for route in routes if route.request.post_data_json['text']=='background')
            route.fulfill(status=200,body=wav_bytes(),content_type='audio/wav')
            page.wait_for_function("()=>typeof window.bg==='number'&&window.bg>44")
            for pending in routes:
                if pending.request.post_data_json['text']!='background':pending.abort()
            print('PASS: mute aborts conversational audio while background export rendering completes.')
            browser.close()
    finally:server.shutdown();server.server_close();thread.join(timeout=3)
