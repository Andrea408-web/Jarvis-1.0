import sys,tempfile,threading,base64,json,subprocess
from pathlib import Path
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from playwright.sync_api import sync_playwright
with tempfile.TemporaryDirectory() as folder:
    app=Application(folder);app.store.update_settings({'ai_provider':'llamacpp','voice_enabled':False})
    app.llamacpp.endpoint_transport=lambda *args,**kwargs:{'choices':[{'finish_reason':'stop','message':{'content':'Frische für deinen Tag.\nDein täglicher Begleiter.\nJetzt entdecken.'}}]}
    server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page(viewport={'width':1440,'height':1000});errors=[];external=[];page.on('pageerror',lambda error:errors.append(str(error)));page.route('https://**/*',lambda route:(external.append(route.request.url),route.abort()))
            page.goto('http://127.0.0.1:'+str(server.server_port));page.get_by_text('LOKALE VERBINDUNG AKTIV',exact=True).wait_for();page.get_by_role('button',name='Agenten',exact=True).click()
            photo=page.evaluate("()=>{const canvas=document.createElement('canvas');canvas.width=640;canvas.height=400;const context=canvas.getContext('2d');context.fillStyle='#438b81';context.fillRect(0,0,640,400);context.fillStyle='#eae2ba';context.fillRect(250,100,140,240);context.fillStyle='#b32333';context.fillRect(270,75,100,30);context.fillStyle='#102020';context.font='bold 20px sans-serif';context.fillText('TEST',291,220);return canvas.toDataURL('image/png').split(',')[1];}")
            page.locator('#agent-role').select_option('studio');page.locator('#agent-task').fill('Drei kurze Werbesätze für meine Getränkeflasche. Keine neuen Eigenschaften erfinden.')
            page.locator('#agent-image').set_input_files({'name':'produkt.png','mimeType':'image/png','buffer':base64.b64decode(photo)});page.locator('#agent-image-preview').wait_for();page.evaluate("()=>window.JarvisBridge.sendMessage('Beauftrage Studio: Erstelle eine kurze Werbung für diese Getränkeflasche mit meinem Foto')")
            page.locator('.agent-station.studio[data-state=completed]').wait_for();page.locator('#agent-jobs summary').first.click();page.locator('.artifact canvas[data-photo=true]').wait_for();assert not page.locator('#agent-image-preview').is_visible()
            page.get_by_role('button',name='Video exportieren',exact=True).click();link=page.get_by_role('link',name='Fertiges Video herunterladen',exact=True);link.wait_for(timeout=35000)
            with page.expect_download() as download:link.click()
            output=Path('/tmp/jarvis-product-final.webm');download.value.save_as(output)
            print('Export diagnostics',page.locator('.artifact').inner_text(),page.locator('.artifact canvas').evaluate('(node)=>({connected:node.isConnected,frame:node.dataset.frame,photo:node.dataset.photo})'),errors)
            info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(output)],text=True));types={stream['codec_type'] for stream in info['streams']};assert types=={'audio','video'},info
            video=next(stream for stream in info['streams'] if stream['codec_type']=='video');assert (video['width'],video['height'])==(720,720)
            subprocess.run(['ffmpeg','-v','error','-y','-i',str(output),'-frames:v','1','/tmp/jarvis-product-frame.png'],check=True)
            assert not errors,errors;assert not external,external
            print('PASS: photo attachment -> private stored asset -> local job result -> photo motion clip plus actual bundled German narration -> exported playable 720p video with video+audio tracks;',output.stat().st_size,'bytes. No external requests.')
            browser.close()
    finally:app.office.stop();server.shutdown();server.server_close();thread.join(timeout=3)
