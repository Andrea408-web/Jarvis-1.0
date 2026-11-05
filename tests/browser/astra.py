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
    import backend.desktop as desktop_module
    desktop_module.create_note=lambda title,body:(events.append({'type':'note','title':title,'text':body}) or {'id':'x-coredata://fixture/ICNote/p1','message':'Notiz bestätigt'})
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
            assert [e['type'] for e in events]==['note'];assert app.desktop.snapshot()['muted']
            page.get_by_role('button',name='Wieder reden',exact=True).click();page.wait_for_function("()=>window.JarvisDesktopMuted===false")
            page.locator('#astra-desktop').get_by_role('button',name='Schließen',exact=True).click()
            page.evaluate("()=>JarvisBridge.sendMessage('Wie heißt du?')");page.get_by_text('Ich bin ASTRA, Master.',exact=True).wait_for()
            page.evaluate("()=>JarvisBridge.sendMessage('Astrid, öffne Spotify')");page.locator('#astra-steps').get_by_text('Spotify öffnen',exact=True).wait_for();page.wait_for_function("()=>document.getElementById('astra-desktop-status').textContent.startsWith('done')");assert any(e.get('app')=='Spotify' for e in events)
            with page.expect_popup() as popup_event:page.get_by_role('button',name='Browser-Pop-up',exact=True).click()
            popup=popup_event.value;popup.locator('#status').get_by_text('done',exact=False).wait_for();popup.get_by_role('button',name='Reden stoppen',exact=True).click();popup.wait_for_function("()=>document.getElementById('mute').disabled");assert app.desktop.snapshot()['muted'];popup.close()
            page.get_by_label('Desktop-Auftrag',exact=True).fill('Öffne Notizen und schreibe Testnotiz');page.get_by_role('button',name='Ablauf vorbereiten',exact=True).click();page.wait_for_function("()=>document.getElementById('astra-desktop-status').textContent.startsWith('review')");page.get_by_role('button',name='Geprüften Ablauf starten',exact=True).click();page.evaluate("()=>JarvisBridge.sendMessage('Astda, hör auf')");page.wait_for_function("()=>document.getElementById('astra-desktop-status').textContent.startsWith('stopped')")
            page.locator('#astra-desktop').get_by_role('button',name='Schließen',exact=True).click()
            page.evaluate("()=>JarvisBridge.sendMessage('Astra, öffne example.com/app')");page.locator('#astra-steps').get_by_text('https://example.com/app öffnen',exact=True).wait_for();page.wait_for_function("()=>document.getElementById('astra-desktop-status').textContent.startsWith('done')");page.locator('#astra-desktop').get_by_role('button',name='Schließen',exact=True).click()
            page.evaluate("()=>JarvisBridge.sendMessage('Astra, erstelle ein 3D Auto in Blender')");page.locator('#astra-steps').get_by_text('Karosserie · cube',exact=True).wait_for();assert app.desktop.snapshot()['plan']['kind']=='model';assert page.locator('#astra-steps li').count()==6;page.locator('#astra-desktop').get_by_role('button',name='Schließen',exact=True).click()
            page.evaluate("()=>JarvisBridge.sendMessage('Werde wieder zu Jarvis')");page.wait_for_function("()=>!document.body.classList.contains('astra-mode')")
            page.evaluate("()=>JarvisBridge.sendMessage('Astrid, ich heiße Maxine')");page.get_by_text('Ich merke mir deinen Namen: Maxine.',exact=True).wait_for();assert app.store.settings()['user_name']=='Maxine';assert app.desktop.snapshot()['plan']['kind']=='model'
            page.evaluate("()=>JarvisBridge.sendMessage('Astra, wie heiße ich?')");page.get_by_text('Du heißt Maxine.',exact=True).wait_for()
            page.evaluate("()=>JarvisBridge.sendMessage('Astrid, kannst du Blender öffnen?')");page.locator('#astra-steps').get_by_text('Blender öffnen',exact=True).wait_for();page.wait_for_function("()=>document.getElementById('astra-desktop-status').textContent.startsWith('done')");assert any(e.get('app')=='Blender' for e in events);page.locator('#astra-desktop').get_by_role('button',name='Schließen',exact=True).click()
            page.evaluate("()=>JarvisBridge.sendMessage('Jarvis, werde zu Astra')");page.evaluate("()=>JarvisBridge.sendMessage('Öffne Blender und mach mir einen Lamborghini')");page.locator('#astra-steps').get_by_text('Sportwagen-Karosserie · wedge',exact=True).wait_for();assert app.desktop.snapshot()['plan']['kind']=='model';assert len(app.desktop.snapshot()['plan']['scene']['parts'])==14;assert not app.desktop.snapshot()['plan'].get('artifact');page.locator('#astra-desktop').get_by_role('button',name='Schließen',exact=True).click()
            token=app.token;panel=browser.new_page();panel.goto('http://127.0.0.1:'+str(server.server_port)+'/astra-panel.html#'+token);panel.locator('#status').get_by_text('review',exact=False).wait_for();panel.get_by_role('button',name='Wieder reden',exact=True).click();panel.wait_for_function("()=>!document.getElementById('mute').disabled");panel.get_by_role('button',name='Reden stoppen',exact=True).click();panel.wait_for_function("()=>document.getElementById('mute').disabled");assert app.desktop.snapshot()['muted']
            page.set_viewport_size({'width':390,'height':844});page.evaluate("()=>JarvisAstra.identity(true)");page.wait_for_timeout(100);assert page.evaluate('()=>document.documentElement.scrollWidth<=innerWidth+2')
            assert not errors,errors
            print('PASS: persistent ASTRA identity, Spotify and website requests without model guesses, token-free browser-popup login, spoken stop, real scene plan; no hub/camera catalogue; source news country filter; spoken-text Astra particle switch and return; reviewed input steps; mute preserves work; popup controls; mobile layout. Native Mac events/panel not tested.')
            browser.close()
    finally:app.desktop.stop();app.office.stop();server.shutdown();server.server_close();thread.join(3)
