"""Call and VR entry points remain visible even if the full dashboard JS fails."""
import sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from playwright.sync_api import sync_playwright
with tempfile.TemporaryDirectory() as folder:
 app=Application(folder);server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url='http://127.0.0.1:'+str(server.server_port)
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);context=browser.new_context(java_script_enabled=False);page=context.new_page();page.goto(url+'/index.html');tile=page.get_by_role('link',name='Videoanruf mit Jarvis',exact=False);assert tile.is_visible();assert tile.bounding_box()['y']<600
   page.set_viewport_size({'width':390,'height':844});page.goto(url+'/mobile');tile=page.get_by_role('link',name='Videoanruf mit Jarvis Hier tippen',exact=False);assert tile.is_visible();assert tile.bounding_box()['y']<150;page.screenshot(path='/tmp/jarvis-call-entry.png');page.goto(url+'/vr-guide');assert page.get_by_text('Verlässlicher lokaler Verbindungsweg: USB',exact=True).is_visible()
   print('PASS: large call entry above fold on desktop/mobile with JavaScript disabled, direct /call link, local VR guide reachable.')
   browser.close()
 finally:app.office.stop();server.shutdown();server.server_close();thread.join(3)
