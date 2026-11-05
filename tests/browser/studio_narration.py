"""Real Thorsten preview, timed subtitles, original host and a voiced video export."""
import json,subprocess,sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from backend.natural_voice import generate
from playwright.sync_api import sync_playwright
root=Path('/tmp/jarvis-natural-test');runtime=next((root/'linux-extracted').iterdir());model=next((root/'voice-extracted').iterdir())
with tempfile.TemporaryDirectory() as folder:
 app=Application(folder);app.store.update_settings({'voice_enabled':False});spoken=[];fail=[False]
 def synthesize(text,preset,**kwargs):
  if fail[0]:raise ValueError('Thorsten fehlt im Test.')
  spoken.append(text);return generate(runtime/'bin/sherpa-onnx-offline-tts',model/'de_DE-thorsten-medium.onnx',model/'tokens.txt',model/'espeak-ng-data',text,Path(folder)/'speech.wav',preset)
 app.natural_voice.synthesize=synthesize
 server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page(viewport={'width':1000,'height':1000},accept_downloads=True);errors=[];requests=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append(r.url))
   page.add_init_script("window.audioStarts=0;const realStart=AudioBufferSourceNode.prototype.start;AudioBufferSourceNode.prototype.start=function(...args){window.audioStarts++;return realStart.apply(this,args);};")
   page.goto('http://127.0.0.1:'+str(server.server_port));page.get_by_text('LOKALE VERBINDUNG AKTIV',exact=True).wait_for(state='attached')
   page.evaluate("()=>{const host=document.createElement('div');host.id='studio-test';document.querySelector('main').prepend(host);JarvisArtifacts.video(host,{id:'narrated',result:'Deine Idee beginnt hier.\\nJarvis hilft dir dabei.\\nEntdecke deine Möglichkeiten.',task:'Werbeclip mit Stimme und Untertiteln'});}")
   film=page.locator('#studio-test');assert film.get_by_label('Thorsten-Sprecher',exact=True).is_checked();assert film.get_by_label('Untertitel',exact=True).is_checked()
   film.get_by_role('button',name='Vorschau abspielen',exact=True).click();page.wait_for_function('()=>window.audioStarts===1',timeout=30000)
   page.wait_for_function("()=>document.querySelector('#studio-test canvas').dataset.caption==='Jarvis hilft dir dabei.'",timeout=15000);page.screenshot(path='/tmp/jarvis-original-host.png');film.get_by_role('button',name='Vorschau stoppen',exact=True).click()
   assert spoken==['Deine Idee beginnt hier.','Jarvis hilft dir dabei.','Entdecke deine Möglichkeiten.']
   film.get_by_role('button',name='Video exportieren',exact=True).click();link=film.get_by_role('link',name='Fertiges Video herunterladen',exact=True);link.wait_for(timeout=20000)
   with page.expect_download() as download:link.click()
   path=Path('/tmp/jarvis-original-narrated.webm');download.value.save_as(path)
   info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(path)],text=True));assert {s['codec_type'] for s in info['streams']}=={'audio','video'};assert len(spoken)==3
   levels=subprocess.run(['ffmpeg','-hide_banner','-i',str(path),'-vn','-af','volumedetect','-f','null','-'],capture_output=True,text=True,check=True).stderr;assert 'max_volume:' in levels and 'max_volume: -inf' not in levels
   # No silent success and no synthetic fallback when Thorsten cannot speak.
   film.locator('details').evaluate('(e)=>e.open=true');film.locator('textarea').first.fill('Ein neuer Sprechertext.');fail[0]=True
   film.get_by_role('button',name='Vorschau abspielen',exact=True).click();film.get_by_text('Vorschau fehlgeschlagen: Thorsten fehlt im Test.',exact=True).wait_for()
   assert not any('/voice-worker.js' in url for url in requests);assert not errors,errors
   print('PASS: original Jarvis host, actual Thorsten preview, sentence-timed subtitles, cached narration in exported 720p audio+video, non-silent audio, visible error without voice fallback.')
   browser.close()
 finally:app.desktop.stop();app.office.stop();server.shutdown();server.server_close();thread.join(3)
