"""Standalone USB document works without a server or network request. Cloud file: navigation is policy-blocked."""
import base64,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[2]
with sync_playwright()as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page(viewport={'width':1280,'height':900});requests=[];errors=[];page.on('request',lambda r:requests.append(r.url));page.on('pageerror',lambda e:errors.append(str(e)))
 page.evaluate('window.revoked=[];const revoke=URL.revokeObjectURL;URL.revokeObjectURL=function(url){window.revoked.push(url);return revoke.call(this,url);};')
 page.set_content((root/'USB-Jarvis/START-HIER.html').read_text(),wait_until='load');assert 'keine eigenständige KI'in page.locator('.note').inner_text();assert page.locator('#clock').inner_text();assert not page.locator('#video').is_visible();assert not page.locator('#image').is_visible()
 page.locator('#jarvis-link').fill('javascript:alert(1)');page.locator('#connect-form').evaluate('e=>e.requestSubmit()');assert 'HTTP-/HTTPS-Link'in page.locator('#status').inner_text()
 data=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO7+XuoAAAAASUVORK5CYII=')
 page.locator('#media-files').set_input_files({'name':'eigenes-bild.png','mimeType':'image/png','buffer':data});assert page.locator('#image').is_visible();assert page.locator('#media-list').input_value()=='0';assert 'nur lokal'in page.locator('#media-status').inner_text();page.locator('#clear-media').click();assert not page.locator('#image').is_visible();assert page.evaluate('revoked.length')>=1
 page.get_by_role('button',name='Jarvis verbinden',exact=True).focus();page.keyboard.press('ArrowRight');assert page.evaluate('document.activeElement.textContent')=='Eigenes HDMI-Gerät'
 page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');assert not errors,errors;assert not any(url.startswith(('http:','https:'))for url in requests),requests
 browser.close();print('PASS: standalone HTML document helper, no network requests, unsafe link refused, local image preview/release, keyboard navigation and phone fit; no TV hardware tested.')
