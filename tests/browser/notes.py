"""A new notes task must execute the note adapter, despite unrelated old context."""
import sys,tempfile,threading
from pathlib import Path
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from playwright.sync_api import sync_playwright
with tempfile.TemporaryDirectory() as folder:
 app=Application(folder);app.store.update_settings({'ai_provider':'llamacpp','voice_enabled':False});app.store.append('user','Baue ein 3D-Spiel');app.store.append('assistant','Ich biete dir ein Videospiel an')
 app.llamacpp.chat=Mock(side_effect=AssertionError('Notes must not use the text model'))
 events=[]
 def create(title,body):events.append({'title':title,'body':body});return {'id':'x-coredata://fixture/ICNote/p1','message':'Notiz von der App bestätigt'}
 server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 try:
  with patch('backend.desktop.create_note',side_effect=create),sync_playwright() as p:
   browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page();page.goto('http://127.0.0.1:'+str(server.server_port));page.get_by_text('LOKALE VERBINDUNG AKTIV',exact=True).wait_for()
   page.locator('#chat-input').fill('Erstelle eine Notiz: Morgen Milch kaufen');page.locator('#send-button').click();page.locator('#astra-steps').get_by_text('Milch kaufen',exact=False).wait_for();assert app.desktop.snapshot()['plan']['kind']=='note';assert not events
   page.get_by_role('button',name='Geprüften Ablauf starten',exact=True).click();page.wait_for_function("()=>document.getElementById('astra-desktop-status').textContent.startsWith('done')");assert events==[{'title':'Morgen Milch kaufen','body':'Morgen Milch kaufen'}];assert app.desktop.snapshot()['plan']['note_id'].startswith('x-coredata://');app.llamacpp.chat.assert_not_called()
   print('PASS: stale 3D/game history does not affect note task; actual note adapter called; done only after note acknowledgement. Native Mac Notes not tested.')
   browser.close()
 finally:app.desktop.stop();app.office.stop();server.shutdown();server.server_close();thread.join(3)
