"""Transient Apple contact never enters documents, backup, history or a model call.
Native macOS selection is mocked here; real browser/UI/API guards are exercised.
"""
import json,sys,tempfile,threading
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from backend import apple_contacts
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory() as folder:
 app=Application(folder);server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url='http://127.0.0.1:'+str(server.server_port)
 try:
  with patch.object(apple_contacts,'open_contacts',return_value={'message':'Eine Person in Apple Kontakte auswählen.'}),patch.object(apple_contacts,'selected',return_value={'name':'Apple Beispielkontakt','phones':['+49 000 123','+49 000 456'],'emails':['privat@example.com'],'temporary':True}),sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page(viewport={'width':1194,'height':1000},accept_downloads=True);errors=[];sent=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:sent.append((r.url,r.post_data)) if r.method=='POST' else None)
   page.goto(url+'/tablet');page.locator('.rail [data-view="desk"]').click();page.get_by_text('Offline-Ablage bereit. Kein Mac benötigt.',exact=True).wait_for();page.locator('[data-desk="contacts"]').click();page.locator('#apple-open').click();page.get_by_text('Eine Person in Apple Kontakte auswählen.',exact=True).wait_for();page.locator('#apple-selected').click();page.locator('#apple-current').wait_for(state='visible');assert page.locator('#apple-name').inner_text()=='Apple Beispielkontakt';assert page.get_by_role('link',name='Telefon-App öffnen').count()==0;page.locator('#apple-phone').select_option('+49 000 456');assert page.get_by_role('link',name='Telefon-App öffnen').get_attribute('href')=='tel:+49000456';assert page.locator('#desk-draft-form button.primary').is_disabled();assert page.locator('#desk-contact-name').input_value()==''
   page.locator('#apple-current').scroll_into_view_if_needed();page.screenshot(path=str(root/'artifacts/apple-kontakte-voruebergehend.png'))
   state=page.evaluate("async()=>({desk:await DeviceStore.get('desk-v1'),workspace:await DeviceStore.get('workspace'),local:{...localStorage}})");assert 'Apple Beispielkontakt' not in json.dumps(state);assert '+49 000' not in json.dumps(state)
   page.locator('[data-desk="storage"]').click()
   with page.expect_download() as event:page.locator('#desk-backup').click()
   backup=Path(event.value.path()).read_text();assert 'Apple Beispielkontakt' not in backup and 'privat@example.com' not in backup
   page.locator('.rail [data-view="setup"]').click()
   with page.expect_download() as event:page.locator('#workspace-export').click()
   backup=Path(event.value.path()).read_text();assert 'Apple Beispielkontakt' not in backup and 'privat@example.com' not in backup
   assert not any('/api/chat' in u or '/api/device-ai/chat' in u for u,_ in sent);assert all(body=='{}' for u,body in sent if '/api/apple-contacts/' in u)
   page.reload();page.locator('.rail [data-view="desk"]').click();page.locator('[data-desk="contacts"]').click();page.get_by_text('Offline-Ablage bereit. Kein Mac benötigt.',exact=True).wait_for();assert page.locator('#apple-current').is_hidden();assert page.locator('#desk-recipient option').count()==1
   # The server does not write selected fields to its data files.
   for file in Path(folder).rglob('*'):
    if file.is_file():assert b'Apple Beispielkontakt' not in file.read_bytes()
   assert not errors,errors;print('PASS: real guarded Apple endpoints with mocked native selection, explicit phone choice, temporary RAM-only recipient, no draft save, no data in documents/backups/localStorage/server files, no model requests, disappears on reload. Actual macOS Contacts not available in this test environment.');browser.close()
 finally:app.office.stop();app.desktop.stop();server.shutdown();server.server_close();thread.join(3)
