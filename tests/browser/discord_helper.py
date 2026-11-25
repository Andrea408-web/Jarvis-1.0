"""Local-only draft and channel handoff: no outbound Discord message or credential flow."""
import sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory() as folder:
 app=Application(folder);app.store.update_settings({'voice_enabled':False});server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();base='http://127.0.0.1:'+str(server.server_port)
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page(viewport={'width':1280,'height':900});requests=[];page.on('request',lambda r:requests.append(r.url) if 'discord.com' in r.url else None)
   for path in ['/index.html','/tablet?layout=phone']:
    page.goto(base+path);page.wait_for_function('()=>!!window.JarvisDiscord');page.locator('#jarvis-app-open').click();page.locator('[data-app=discord]').click();page.locator('#jarvis-discord').wait_for();page.locator('#discord-channel').fill('https://discord.com.evil.example/channels/123456/123456');page.locator('#discord-save').click();assert 'Bitte' in page.locator('#discord-status').inner_text();assert page.evaluate("localStorage.getItem('jarvis.discord.channel.v1')") is None
    page.locator('#discord-channel').fill('https://discord.com/channels/123456789/987654321');page.locator('#discord-save').click();assert page.locator('#discord-open').get_attribute('href').endswith('/123456789/987654321');page.locator('#discord-draft').fill('Morgen um 18 Uhr gemeinsam spielen?');page.locator('#jarvis-discord').screenshot(path=str(ROOT/'artifacts/jarvis-discord.png'));page.locator('#discord-close').click();page.evaluate('JarvisDiscord.open()');assert page.locator('#discord-draft').input_value()=='';assert page.locator('#discord-channel').input_value().endswith('987654321');page.locator('#discord-draft').fill('Morgen um 18 Uhr gemeinsam spielen?');page.locator('#discord-formulate').click();target='#device-chat-input' if '/tablet' in path else '#chat-input';assert 'Morgen um 18' in page.locator(target).input_value();page.evaluate('JarvisDiscord.open()');page.locator('#discord-forget').click();assert page.evaluate("localStorage.getItem('jarvis.discord.channel.v1')") is None;page.locator('#discord-close').click()
   assert not requests,requests;assert app.store.history()==[];browser.close();print('PASS: desktop/phone Discord launcher, strict channel URL validation, explicit local save/delete, draft cleanup, chat handoff without automatic submission, no Discord requests or messages.')
 finally:app.office.stop();app.workshop.stop();app.desktop.stop();server.shutdown();server.server_close();thread.join(2)
