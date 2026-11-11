"""Web clarifications, factual movie answer and a direct open-site link in the UI."""
import sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from tests.test_web_assistant import NOW,CINEMA,SEARCH,event,html
from playwright.sync_api import sync_playwright
with tempfile.TemporaryDirectory() as folder:
 app=Application(folder);app.store.update_settings({'voice_enabled':False});app.web.clock=lambda:NOW
 app.web.reader=lambda url:('',url) if url.startswith(SEARCH) else (html([event('Sternenreise',6),event('Nur für Erwachsene',18)]),url)
 server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.goto('http://127.0.0.1:'+str(server.server_port));page.get_by_text('LOKALE VERBINDUNG AKTIV',exact=True).wait_for()
   def send(text):page.locator('#chat-input').fill(text);page.locator('#send-button').click();page.wait_for_function("()=>!document.getElementById('send-button').disabled")
   send('Jarvis, welche Filme kann ich jetzt im Cineplex Neufahrn ansehen?');page.get_by_text('Wie alt ist die jüngste Person, Master? Dann berücksichtige ich die FSK.',exact=True).wait_for()
   send('zwölf');message=page.locator('#messages .message.assistant').last;assert 'Sternenreise' in message.inner_text();assert 'Nur für Erwachsene' not in message.inner_text();link=message.get_by_role('link',name='Website öffnen',exact=True);assert link.get_attribute('href')==CINEMA;assert link.get_attribute('target')=='_blank';assert 'noopener' in link.get_attribute('rel')
   # No/yes is handled as the previous source question, rather than sent to the model.
   send('nein danke');assert app.dialogue.get() is None;assert app.desktop.plan is None
   send('Wo kann ich jetzt billig Pizza essen?');send('München');send('zwei');send('20 Euro insgesamt');assert app.dialogue.get()['kind']=='web_open'
   page.get_by_role('button',name='Chat löschen',exact=True).click();page.get_by_text('Chatverläufe, gemerkter Name und offene Rückfragen gelöscht.',exact=True).wait_for();assert app.dialogue.get() is None
   page.get_by_role('button',name='Einstellungen öffnen',exact=True).click();web=page.locator('input[name=web_enabled]');assert web.is_checked();web.uncheck();page.get_by_role('button',name='Einstellungen speichern',exact=False).click();page.wait_for_function("()=>!document.getElementById('settings-dialog').open");assert not app.store.settings()['web_enabled']
   assert not errors,errors
   print('PASS: cinema age follow-up, FSK-filtered sourced answer, explicit direct website link, decline, food follow-ups, chat reset and persisted web opt-out. Controlled public pages; live external sites blocked here.')
   browser.close()
 finally:app.office.stop();server.shutdown();server.server_close();thread.join(3)
