"""TLS pairing and a separate home-screen-like browser storage context."""
import json,ssl,sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.mobile import DeviceAuth,certificates
from backend.server import Application,JarvisServer
from playwright.sync_api import sync_playwright
with tempfile.TemporaryDirectory() as folder:
 app=Application(Path(folder)/'data');app.store.update_settings({'voice_enabled':False,'ai_provider':'llamacpp'})
 app.llamacpp.chat=lambda *a,**k:{'reply':'Verbindung zum Mac funktioniert.','proposals':[]}
 cert,key,_,_=certificates(Path(folder)/'cert','127.0.0.1')
 server=JarvisServer(('127.0.0.1',0),app,secure=True);server.device_auth=DeviceAuth(Path(folder)/'devices.json')
 context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);context.load_cert_chain(cert,key);server.socket=context.wrap_socket(server.socket,server_side=True,do_handshake_on_connect=False)
 thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url='https://127.0.0.1:'+str(server.server_port)
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
   safari=browser.new_context(ignore_https_errors=True,viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
   page=safari.new_page();ticket=server.device_auth.issue();page.goto(url+'/#pair='+ticket);page.get_by_text('Mit Jarvis auf deinem Mac verbunden.',exact=True).wait_for();assert page.url==url+'/'
   manifest=page.evaluate("async()=>await (await fetch(document.querySelector('link[rel=manifest]').href)).json()")
   assert manifest['start_url']=='/' and '#' not in manifest['start_url'];assert manifest['display']=='standalone'
   assert page.locator('link[rel=apple-touch-icon]').count()==1
   # Home-screen Safari may have independent cookie storage. Pair there without scanning back into Safari.
   home=browser.new_context(ignore_https_errors=True,viewport={'width':390,'height':844},is_mobile=True,has_touch=True);icon=home.new_page();errors=[];icon.on('pageerror',lambda e:errors.append(str(e)))
   icon.goto(url+'/');icon.locator('#pair-form').wait_for();ticket=server.device_auth.issue();icon.locator('#pair-link').fill(url+'/#pair='+ticket);icon.get_by_role('button',name='Mit Mac verbinden',exact=True).click();icon.get_by_text('Mit Jarvis auf deinem Mac verbunden.',exact=True).wait_for()
   icon.locator('#voice').uncheck();icon.get_by_text('Auf dem Home-Bildschirm',exact=True).click();icon.get_by_text('In Safari: Teilen',exact=False).wait_for()
   icon.locator('#chat-input').fill('Hallo');icon.locator('#send').click();icon.get_by_text('Verbindung zum Mac funktioniert.',exact=True).wait_for()
   icon.locator('#chat-input').fill('Öffne Spotify');icon.locator('#send').click();icon.locator('#messages').get_by_text('Desktop-Aufträge bitte in Jarvis direkt auf dem Mac starten.',exact=False).wait_for();assert app.desktop.plan is None
   assert not errors,errors
   print('PASS: HTTPS QR pairing, separate-context manual pairing, manifest and icon, install guide, mobile chat, clear Mac-control limitation. No physical iPhone installation tested.')
   browser.close()
 finally:app.desktop.stop();app.office.stop();server.shutdown();server.server_close();thread.join(3)
