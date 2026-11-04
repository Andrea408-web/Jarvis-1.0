"""Astra identity, world news and input execution with controlled local driver."""
import json,sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from tests.test_hub import RSS
from playwright.sync_api import sync_playwright
with tempfile.TemporaryDirectory() as folder:
    app=Application(folder);app.store.update_settings({'ai_provider':'llamacpp','voice_enabled':False});app.hub.reader=lambda url:RSS
    events=[]
    class Driver:
        def execute(self,step):events.append(step)
    app.desktop.driver=Driver
    app.llamacpp.chat=lambda *a,**k:{'reply':json.dumps({'steps':[{'type':'open','app':'Notizen'},{'type':'wait','seconds':.5},{'type':'text','text':'Testnotiz'}]})}
    server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page(viewport={'width':1440,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.route('https://**/*',lambda r:r.abort())
            page.goto('http://127.0.0.1:'+str(server.server_port));page.get_by_text('LOKALE VERBINDUNG AKTIV',exact=True).wait_for()
            assert page.get_by_role('button',name='Mini-Hub',exact=True).count()==0
            assert page.get_by_role('button',name='Welt & Kameras',exact=True).count()==0
            page.evaluate("()=>JarvisBridge.sendMessage('Jarvis, werde zu Astra')")
            page.wait_for_function("()=>document.body.classList.contains('astra-mode')")
            page.locator('#astra-particles').wait_for(state='visible');page.wait_for_timeout(1500)
            page.screenshot(path='/tmp/jarvis-astra.png')
            page.get_by_role('button',name='Welt',exact=True).click();page.locator('#world-articles').get_by_text('Deutschland: Testmeldung',exact=True).wait_for()
            page.locator('#world-country').select_option('DE');assert page.locator('#world-articles article').count()==1
            page.locator('#world-dialog').get_by_role('button',name='Schließen',exact=True).click()
            page.evaluate("()=>JarvisBridge.sendMessage('Astra, öffne Notizen und schreibe eine Testnotiz')")
            page.locator('#astra-steps li').first.wait_for();assert len(events)==0
            page.get_by_role('button',name='Geprüften Ablauf starten',exact=True).click()
            page.get_by_role('button',name='Reden stoppen',exact=True).click()
            page.wait_for_function("()=>window.JarvisDesktopMuted===true")
            page.wait_for_function("()=>document.getElementById('astra-desktop-status').textContent.startsWith('done')",timeout=10000)
            assert [e['type'] for e in events]==['open','text'];assert app.desktop.snapshot()['muted']
            page.get_by_role('button',name='Wieder reden',exact=True).click();page.wait_for_function("()=>window.JarvisDesktopMuted===false")
            page.locator('#astra-desktop').get_by_role('button',name='Schließen',exact=True).click()
            page.evaluate("()=>JarvisBridge.sendMessage('Werde wieder zu Jarvis')");page.wait_for_function("()=>!document.body.classList.contains('astra-mode')")
            token=app.token;panel=browser.new_page();panel.goto('http://127.0.0.1:'+str(server.server_port)+'/astra-panel.html#'+token);panel.locator('#status').get_by_text('done',exact=False).wait_for();panel.get_by_role('button',name='Reden stoppen',exact=True).click();panel.wait_for_function("()=>document.getElementById('mute').disabled");assert app.desktop.snapshot()['muted']
            page.set_viewport_size({'width':390,'height':844});page.evaluate("()=>JarvisAstra.identity(true)");page.wait_for_timeout(100);assert page.evaluate('()=>document.documentElement.scrollWidth<=innerWidth+2')
            assert not errors,errors
            print('PASS: no hub/camera catalogue; source news country filter; spoken-text Astra particle switch and return; reviewed input steps; mute preserves work; popup controls; mobile layout. Native Mac events/panel not tested.')
            browser.close()
    finally:app.desktop.stop();app.office.stop();server.shutdown();server.server_close();thread.join(3)
