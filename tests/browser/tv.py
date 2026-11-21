"""TV client with real local server: D-pad, local chat/audio, local media and display modes."""
import base64,io,sys,tempfile,threading,wave
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory() as folder:
 app=Application(folder);app.store.update_settings({'ai_provider':'llamacpp'});chats=[];voices=[]
 def chat(path,payload):
  chats.append(payload);return {'done':True,'message':{'content':'Sir, wir können deine Projektidee gemeinsam besprechen. Die KI läuft auf dem verbundenen Rechner.'}}
 app.llamacpp.transport=chat;audio=io.BytesIO()
 with wave.open(audio,'wb')as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000);w.writeframes(b'\0\0'*16000)
 app.natural_voice.synthesize=lambda text,preset:(voices.append(preset),audio.getvalue())[1]
 server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url='http://127.0.0.1:'+str(server.server_port)
 try:
  with sync_playwright()as pw:
   browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']);page=browser.new_page(viewport={'width':1920,'height':1080},reduced_motion='reduce');errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(url+'/tv');page.get_by_text('Mit Jarvis verbunden',exact=False).wait_for()
   page.locator('[data-panel=chat]').focus();page.keyboard.press('ArrowRight');assert page.evaluate('document.activeElement.id')=='tv-workshop'
   page.locator('#tv-question').fill('Hallo Jarvis');page.locator('#tv-question').focus();page.keyboard.press('ArrowLeft');page.keyboard.press('ArrowUp');assert page.evaluate('document.activeElement.id')=='tv-question';page.keyboard.press('End');page.keyboard.press('Backspace');assert page.locator('#tv-question').input_value()!='Hallo Jarvis'
   page.locator('#tv-question').fill('Plane mit mir eine Werkzeugstation');page.locator('#tv-send').click();page.locator('#tv-messages').get_by_text('gemeinsam besprechen',exact=False).wait_for();page.wait_for_function("()=>document.getElementById('tv-core').dataset.speaking==='true'");assert chats and voices==['jarvis'];page.locator('#tv-voice-stop').click();assert page.locator('#tv-read').is_checked()
   page.locator('#tv-ambient').click();assert page.locator('#tv-ambient-exit').is_visible();page.keyboard.press('Escape');assert not page.locator('#tv-ambient-exit').is_visible()
   page.locator('[data-panel=media]').click();png=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/f1sAAAAASUVORK5CYII=');page.locator('#tv-media-file').set_input_files([{'name':'eins.png','mimeType':'image/png','buffer':png},{'name':'zwei.png','mimeType':'image/png','buffer':png}]);page.wait_for_function("()=>document.getElementById('tv-media-status').textContent.includes('1 / 2')");page.locator('#tv-image').wait_for(state='visible');assert page.locator('#tv-image').is_visible();page.locator('#tv-media-next').click();assert '2 / 2'in page.locator('#tv-media-status').inner_text();page.locator('#tv-media-prev').click();assert '1 / 2'in page.locator('#tv-media-status').inner_text();assert len(chats)==1
   page.locator('#tv-media-clear').focus();page.keyboard.press('Escape');assert page.locator('#tv-chat-panel').is_visible();assert page.locator('#tv-image').is_hidden()
   page.locator('#tv-workshop').click();page.locator('#build-studio').wait_for();page.locator('#build-close').focus();page.keyboard.press('ArrowDown');assert page.evaluate("()=>!!document.activeElement.closest('#build-studio')");page.locator('#build-close').click()
   page.locator('#tv-chat-clear').click();assert not page.locator('#tv-messages p').count();page.screenshot(path=str(root/'artifacts/jarvis-tv.png'));page.set_viewport_size({'width':960,'height':540});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');assert not errors,errors;browser.close();print('PASS: TV D-pad focus/modal scope and native text editing, local chat/Thorsten, stop/clear, ambientexit, multiimagepreview and Back cleanup, no media uploads. Browser/server/audio use controlled fixtures; physical Fire TV not tested.')
 finally:app.office.stop();app.workshop.stop();app.desktop.stop();server.shutdown();server.server_close();thread.join(2)
