"""Play real rounds, early-click/timer cancellation, offline mode and touch layout."""
import sys,tempfile,threading,re
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory()as folder:
 app=Application(folder);app.store.update_settings({'voice_enabled':False});server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url='http://127.0.0.1:'+str(server.server_port)
 try:
  with sync_playwright()as pw:
   browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page(viewport={'width':1300,'height':1050});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(url+'/index.html');page.clock.install();page.evaluate('()=>{Math.random=()=>.5;}');page.locator('#play-open').click();page.locator('#play-dialog[open]').wait_for();assert page.locator('.memory-card').count()==12
   page.locator('[data-card="0"]').click();page.locator('[data-card="0"]').click();assert page.locator('#memory-moves').inner_text()=='0 Züge';page.locator('#memory-new').click()
   seen={}
   for i in range(0,12,2):
    for index in [i,i+1]:
     card=page.locator('[data-card="'+str(index)+'"]');card.click();seen.setdefault(card.inner_text(),[]).append(index)
    page.clock.fast_forward(900)
   assert len(seen)==6
   for indexes in seen.values():
    if page.locator('[data-card="'+str(indexes[0])+'"]').is_disabled():continue
    for i in indexes:page.locator('[data-card="'+str(i)+'"]').click()
   assert page.locator('#memory-pairs').inner_text()=='6 / 6 Paare';assert 'Alle sechs Paare gefunden' in page.locator('#memory-status').inner_text()
   page.mouse.move(0,0);page.screenshot(path=str(root/'artifacts/spielpause-memory.png'))
   page.locator('[data-game-tab="reaction"]').click();page.locator('#reaction-pad').click();assert page.locator('#reaction-pad').get_attribute('data-state')=='waiting';page.locator('#reaction-pad').click();assert page.locator('#reaction-pad').get_attribute('data-state')=='early';page.clock.fast_forward(5000);assert page.locator('#reaction-pad').get_attribute('data-state')=='early';page.locator('#reaction-pad').click();page.clock.fast_forward(3000);assert page.locator('#reaction-pad').get_attribute('data-state')=='ready';page.clock.fast_forward(150);page.locator('#reaction-pad').click();assert page.locator('#reaction-pad').get_attribute('data-state')=='result';assert re.search(r'\d+ ms',page.locator('#reaction-best').inner_text())
   page.locator('#reaction-pad').click();page.evaluate("()=>{Object.defineProperty(document,'hidden',{configurable:true,value:true});document.dispatchEvent(new Event('visibilitychange'));delete document.hidden;}");page.clock.fast_forward(5000);assert page.locator('#reaction-pad').get_attribute('data-state')=='idle'
   page.context.set_offline(True);page.locator('[data-game-tab="number"]').click()
   def guess(value):page.locator('#number-guess').fill(str(value));page.locator('#number-submit').click()
   guess(0);assert page.locator('#number-count').inner_text()=='0 / 7 Versuche'
   guess(32);assert 'größer' in page.locator('#number-status').inner_text();guess(32);assert page.locator('#number-count').inner_text()=='1 / 7 Versuche';guess(70);assert 'kleiner' in page.locator('#number-status').inner_text();guess(51);assert 'Richtig, Sir!' in page.locator('#number-status').inner_text();assert page.locator('#number-submit').is_disabled()
   page.locator('#number-new').click()
   for i in range(1,8):guess(i)
   assert 'Die gesuchte Zahl war 51' in page.locator('#number-status').inner_text();assert page.locator('#number-guess').is_disabled()
   page.locator('[data-game-tab="reaction"]').click();page.locator('#reaction-pad').click();page.locator('#play-close').click();page.clock.fast_forward(5000);assert not page.locator('#play-dialog').is_visible();page.locator('#play-open').click();page.locator('[data-game-tab="reaction"]').click();assert page.locator('#reaction-best').inner_text()=='Noch kein Bestwert.';page.locator('#play-close').click();page.context.set_offline(False)
   page.locator('#chat-input').fill('Jarvis, mir ist langweilig');page.locator('#send-button').click();page.locator('#play-dialog[open]').wait_for();page.locator('#play-close').click();page.goto(url+'/tablet');page.set_viewport_size({'width':390,'height':844});page.locator('#play-open').click();page.locator('.memory-card').first.wait_for();assert page.locator('#play-dialog').evaluate('(e)=>e.scrollWidth<=e.clientWidth+1');assert page.locator('#play-dialog').bounding_box()['height']<=844*.93;page.mouse.move(0,0);page.screenshot(path=str(root/'artifacts/spielpause-handy.png'));page.locator('[data-game-tab="number"]').click();assert page.locator('#number-guess').bounding_box()['width']>100;page.locator('[data-game-tab="memory"]').click();page.evaluate("()=>window.dispatchEvent(new Event('pagehide'))");page.wait_for_function("()=>!document.getElementById('play-dialog').open");page.locator('#play-open').click();assert page.locator('#memory-pairs').inner_text()=='0 / 6 Paare';page.locator('#play-close').click();assert page.evaluate('()=>document.documentElement.scrollWidth<=innerWidth+1');page.locator('#device-voice').uncheck();page.locator('#device-chat-input').fill('Öffne Spielpause');page.locator('#chat-send').click();page.locator('#play-dialog[open]').wait_for();page.locator('#play-close').click();assert not errors,errors;browser.close();print('PASS: full memory round, same-card guard, reaction false start and timing, hidden-tab cancellation, number validation/duplicates/win/attempt limit, offline play, close clears timers and best score, phone layout and original Mac bar entry.')
 finally:app.office.stop();app.desktop.stop();server.shutdown();server.server_close();thread.join(3)
