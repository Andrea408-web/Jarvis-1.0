"""IRIS integration through the actual HTTP server and Chromium.

Controlled local-model, recognition and WAV fixtures verify orchestration only;
they do not establish model quality, Thorsten's installed voice or audio hardware.
"""
import io
import sys
import tempfile
import threading
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from backend.server import Application, JarvisServer
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory() as folder:
    app = Application(folder)
    app.store.update_settings({'ai_provider': 'llamacpp', 'assistant_identity': 'astra'})
    chats, voices, designs = [], [], []
    delayed, release, completed = threading.Event(), threading.Event(), threading.Event()

    def chat(path, payload):
        chats.append(payload)
        if payload['messages'][-1]['content'] == 'Verspätete Frage':
            delayed.set()
            release.wait(10)
            completed.set()
            return {'done': True, 'message': {'content': 'VERSPAETETE ANTWORT'}}
        return {'done': True, 'message': {'content': 'Ich bin AERIS. Wir sortieren deine Idee.'}}

    def no_design(*args, **kwargs):
        designs.append(args)
        raise AssertionError('Default IRIS must not generate 3D')

    app.llamacpp.transport = chat
    app.code_room._generate = no_design
    wav = io.BytesIO()
    with wave.open(wav, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b'\0\0' * 1600)
    app.natural_voice.synthesize = lambda text, preset: (voices.append((text, preset)), wav.getvalue())[1]
    server = JarvisServer(('127.0.0.1', 0), app)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    origin = 'http://127.0.0.1:' + str(server.server_port)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox', '--autoplay-policy=user-gesture-required'])
            page = browser.new_page(viewport={'width': 1440, 'height': 1040}, reduced_motion='reduce')
            errors, requests = [], []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.on('request', lambda request: requests.append((request.method, request.url)))
            page.add_init_script("""window.irisRecognitions=0;window.irisPlaybacks=0;
              window.SpeechRecognition=class{start(){window.irisRecognition=this;window.irisRecognitions++;this.onstart?.();}abort(){this.onend?.();}};
              const original=AudioContext.prototype.createBufferSource;
              AudioContext.prototype.createBufferSource=function(){const source=original.call(this),start=source.start.bind(source);source.start=(...args)=>{window.irisPlaybacks++;return start(...args);};return source;};""")
            page.goto(origin + '/iris')
            page.locator('#iris-title').wait_for()
            assert page.title().startswith('IRIS')
            assert not page.locator('model-viewer, [id="scene"], [id="aeris-scene"]').count()
            assert not designs and not chats and not voices
            assert page.evaluate('irisRecognitions') == 0
            page.locator('#iris-talk').click()
            assert page.evaluate('irisRecognitions') == 0
            page.locator('#iris-question').fill('Wer bist du?')
            page.locator('#iris-send').click()
            page.locator('#iris-messages').get_by_text('Iris: Ich bin IRIS. Wir sortieren deine Idee.', exact=True).wait_for()
            page.wait_for_function('()=>irisPlaybacks === 1')
            assert 'Du bist IRIS' in chats[0]['messages'][0]['content']
            assert app.store.settings()['assistant_identity'] == 'astra'
            assert app.store.history() == []
            assert page.evaluate("async()=>await DeviceStore.get('iris-notes-v1')") is None
            page.locator('#iris-speech-consent').check()
            page.locator('#iris-talk').click()
            page.wait_for_function('()=>irisRecognitions >= 1')
            page.evaluate("irisRecognition.onresult({results:[[{transcript:'Hilf mir mit meiner Idee'}]]})")
            page.wait_for_function('()=>irisPlaybacks === 2')
            assert len(chats) == 2
            assert chats[1]['messages'][-3]['content'] == 'Wer bist du?'
            page.wait_for_function('()=>irisRecognitions >= 2')
            page.locator('#iris-talk').click()
            assert page.locator('#iris-talk').get_attribute('aria-pressed') == 'false'
            assert voices and all(preset == 'jarvis' for _, preset in voices)
            assert not any('/api/natural-voice/settings' in url for _, url in requests)
            page.locator('.iris-voice-settings summary').click()
            page.locator('#iris-read').uncheck()
            page.locator('#iris-question').fill('Verspätete Frage')
            page.locator('#iris-send').click()
            assert delayed.wait(3)
            page.locator('#iris-clear').click()
            release.set()
            assert completed.wait(3)
            page.wait_for_timeout(200)
            assert page.locator('#iris-messages').inner_text() == ''
            page.locator('#iris-question').fill('Neuer Anfang')
            page.locator('#iris-send').click()
            page.locator('#iris-send').wait_for(state='visible')
            page.locator('#iris-messages .assistant').wait_for()
            assert len(chats[-1]['messages']) == 2
            assert 'VERSPAETETE' not in page.locator('#iris-messages').inner_text()
            page.locator('#iris-notes').click()
            page.locator('#iris-note-text').fill('Explizite private Notiz')
            assert page.evaluate("async()=>await DeviceStore.get('iris-notes-v1')") is None
            count = len(chats)
            page.locator('#iris-note-save').click()
            page.locator('#iris-note-list').get_by_text('Explizite private Notiz', exact=True).wait_for()
            assert len(chats) == count
            page.locator('#iris-notes-close').click()
            page.locator('#iris-clear').click()
            page.reload()
            page.locator('#iris-notes').click()
            page.locator('#iris-note-list').get_by_text('Explizite private Notiz', exact=True).wait_for()
            assert 'Neuer Anfang' not in page.locator('#iris-messages').inner_text()
            page.locator('#iris-note-list button').click()
            page.wait_for_function("async()=> (await DeviceStore.get('iris-notes-v1')).length === 0")
            page.locator('#iris-notes-close').click()
            page.locator('#iris-lab').click()
            page.locator('#technik-lab').wait_for()
            assert page.locator('#tl-chooser').is_visible()
            page.locator('#tl-close').click()
            page.goto(origin + '/aeris')
            page.locator('#iris-title').wait_for()
            assert not designs
            for width, height in [(390, 844), (320, 568), (768, 1024)]:
                page.set_viewport_size({'width': width, 'height': height})
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), (width, height)
                assert page.locator('#iris-question').is_visible()
            page.set_viewport_size({'width': 1440, 'height': 1040})
            (ROOT / 'artifacts').mkdir(exist_ok=True)
            page.screenshot(path=str(ROOT / 'artifacts/jarvis-iris.png'), full_page=True)
            for mode in ['jarvis', 'astra']:
                page.locator('#iris-mode-' + mode).click()
                page.wait_for_url(origin + '/index.html')
                assert app.store.settings()['assistant_identity'] == mode
                page.goto(origin + '/iris')
                page.locator('#iris-title').wait_for()
            assert app.store.history() == []
            assert not errors, errors
            browser.close()
            print('PASS: IRIS/aeris routes, local persona, RAM chat, fixed Thorsten audio, opt-in ASR automatic turns, clear discards late replies and history, explicit device notes, Techniklabor, mode switching, mobile fit; model/ASR/WAV fixtures, no hardware claims.')
    finally:
        release.set()
        app.office.stop()
        app.workshop.stop()
        app.desktop.stop()
        server.shutdown()
        server.server_close()
        thread.join(2)
