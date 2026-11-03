import sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from playwright.sync_api import sync_playwright
with tempfile.TemporaryDirectory() as folder:
    app=Application(folder);server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page(viewport={'width':390,'height':844});errors=[];external=[];page.on('pageerror',lambda error:errors.append(str(error)));page.route('https://**/*',lambda route:(external.append(route.request.url),route.abort()))
            page.add_init_script("window.cameraTracks=[];navigator.mediaDevices.getUserMedia=async opts=>{const canvas=document.createElement('canvas');canvas.width=640;canvas.height=400;const ctx=canvas.getContext('2d');ctx.fillStyle='red';ctx.fillRect(0,0,640,400);const stream=canvas.captureStream(10);setInterval(()=>ctx.fillRect(0,0,640,400),100);window.cameraTracks.push(...stream.getTracks());return stream;};")
            page.goto('http://127.0.0.1:'+str(server.server_port));page.get_by_text('LOKALE VERBINDUNG AKTIV',exact=True).wait_for(state='attached');assert page.evaluate('()=>document.documentElement.scrollWidth<=innerWidth+1')
            page.get_by_role('button',name='Welt & Kameras',exact=True).click();page.locator('#world-map[data-loaded=true]').wait_for();page.get_by_role('button',name='Deutschland',exact=True).click();assert page.locator('.camera-list>div').count()==3
            page.locator('.camera-list>div').filter(has_text='Zugspitze').get_by_role('button',name='Standort ansehen',exact=True).click();assert 'zugspitze.panomax.com' in page.locator('#public-camera-viewer>a').get_attribute('href');assert page.locator('#world-dialog').evaluate('(node)=>node.scrollWidth<=node.clientWidth+1')
            page.locator('#world-dialog').get_by_role('button',name='Schließen',exact=True).click();page.get_by_role('button',name='Fußball & Live',exact=True).click();page.locator('.sports-list article').first.wait_for();assert page.locator('.sports-list article').count()==3;assert 'sportschau.de' in page.locator('.sports-list a').first.get_attribute('href')
            page.locator('#sports-dialog').get_by_role('button',name='Schließen',exact=True).click();page.get_by_role('button',name='Kamera',exact=True).click();page.get_by_role('button',name='Kamera starten',exact=True).click();page.get_by_text('Vorschau aktiv · keine Bildanalyse.',exact=True).wait_for();page.get_by_role('button',name='Bild an Agenten',exact=True).click();page.locator('#agent-image-preview').wait_for();page.wait_for_function('()=>window.cameraTracks.every(track=>track.readyState==="ended")');assert page.locator('#office-dialog').evaluate('(node)=>node.scrollWidth<=node.clientWidth+1')
            assert errors==[],errors;assert external==[],external
            page.screenshot(path='/tmp/jarvis-v4-mobile.png',full_page=True)
            print('PASS: narrow mobile layout; Germany webcam filtering and official links; sports sources; one-click camera permission; explicit capture to agent preview; camera tracks stop after capture. No external requests.')
            browser.close()
    finally:app.office.stop();server.shutdown();server.server_close();thread.join(timeout=3)
