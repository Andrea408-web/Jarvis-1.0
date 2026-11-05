"""One click prepares missing/changed plans; failures stay visible and retryable."""
import sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from playwright.sync_api import sync_playwright

with tempfile.TemporaryDirectory() as folder:
 app=Application(folder);app.store.update_settings({'voice_enabled':False});events=[]
 class Driver:
  def execute(self,step):events.append(step)
 app.desktop.driver=Driver
 server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page();page.goto('http://127.0.0.1:'+str(server.server_port));page.get_by_text('LOKALE VERBINDUNG AKTIV',exact=True).wait_for()
   page.evaluate('()=>JarvisAstra.open()');start=page.locator('#astra-start');goal=page.get_by_label('Desktop-Auftrag',exact=True)
   assert start.is_enabled();start.click();page.get_by_text('Schreibe zuerst deinen Auftrag in das Textfeld.',exact=True).wait_for();assert not events
   goal.fill('Öffne Spotify');start.click();page.wait_for_function("()=>document.getElementById('astra-desktop-status').textContent.startsWith('done')");assert events==[{'type':'open','app':'Spotify'}];assert start.is_disabled()
   # Editing after completion must re-enable the same button and prepare the NEW goal.
   goal.fill('Öffne youtube.com');assert start.is_enabled();start.click();page.wait_for_function("()=>document.getElementById('astra-desktop-status').textContent.startsWith('done')");assert events[-1]=={'type':'website','url':'https://youtube.com'}
   # Failed start must show an error and remain usable (without a refresh or a new prepare click).
   class Failing:
    def __init__(self):raise ValueError('Test: macOS-Berechtigung fehlt')
   app.desktop.driver=Failing;goal.fill('Öffne Finder');start.click();page.get_by_text('Test: macOS-Berechtigung fehlt',exact=True).wait_for();assert start.is_enabled();page.wait_for_timeout(1200);assert page.locator('#astra-desktop-status').inner_text()=='Test: macOS-Berechtigung fehlt'
   app.desktop.driver=Driver;start.click();page.wait_for_function("()=>document.getElementById('astra-desktop-status').textContent.startsWith('done')");assert events[-1]=={'type':'open','app':'Finder'}
   # Expired reviews are rebuilt by the same click, rather than failing forever.
   app.desktop.prepare({'goal':'Öffne Rechner'});app.desktop.plan['expires']=0
   page.evaluate('()=>JarvisAstra.open()');start.click();page.wait_for_function("()=>document.getElementById('astra-desktop-status').textContent.startsWith('done')");assert events[-1]=={'type':'open','app':'Rechner'}
   assert len(events)==4
   print('PASS: start without a plan, empty input guidance, edited completed goal, visible failure and retry; controlled driver, no native Mac actions.')
   browser.close()
 finally:app.desktop.stop();app.office.stop();server.shutdown();server.server_close();thread.join(3)
