"""Real Tk widgets against the local server; requires a test DISPLAY, no Mac frameworks."""
import json,sys,tempfile,threading,time
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.server import Application,JarvisServer
from backend.companion_tk import Buddy,Client
with tempfile.TemporaryDirectory() as folder:
 app=Application(folder);app.store.update_settings({'ai_provider':'llamacpp'});app.llamacpp.transport=lambda *a,**k:{'done':True,'message':{'content':'Sir, das native Python-Fenster antwortet.'}}
 server=JarvisServer(('127.0.0.1',0),app);worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start();path=Path(folder)/'test-window.json';ready=Path(folder)/'ready';path.write_text(json.dumps({'url':'http://127.0.0.1:'+str(server.server_port)+'/companion','mode':'helper','sequence':1,'wandering':False}));buddy=Buddy(path,ready);buddy.voice.set(False)
 def wait(fn,timeout=5):
  end=time.monotonic()+timeout
  while time.monotonic()<end:
   buddy.root.update()
   if fn():return
   time.sleep(.03)
  raise AssertionError(buddy.status.get())
 try:
  wait(lambda:buddy.client.token);assert ready.read_text()=='visible';assert buddy.root.winfo_ismapped();buddy.input.set('Hallo');buddy.send();wait(lambda:'antwortet' in buddy.status.get());assert 'Sir, das native' in buddy.transcript.get('1.0','end');assert app.store.history()==[]
  x,y=buddy.root.winfo_x(),buddy.root.winfo_y();buddy.drag_start(SimpleNamespace(widget=buddy.canvas,x_root=200,y_root=200));buddy.drag_move(SimpleNamespace(x_root=240,y_root=230));buddy.root.update();assert buddy.root.winfo_x()==x+40 and buddy.root.winfo_y()==y+30
  state=json.loads(path.read_text());state.update(mode='island',sequence=2,wandering=True);path.write_text(json.dumps(state));wait(lambda:buddy.mode=='island');buddy.root.focus_force();buddy.last_input=time.monotonic()-20;x=buddy.root.winfo_x();wait(lambda:buddy.root.winfo_x()!=x,timeout=4)
  state.update(wandering=False);path.write_text(json.dumps(state));wait(lambda:not buddy.config['wandering']);x=buddy.root.winfo_x();end=time.monotonic()+.5
  while time.monotonic()<end:buddy.root.update();time.sleep(.02)
  assert buddy.root.winfo_x()==x;assert not buddy.screen
  try:
   from PIL import ImageGrab
   ImageGrab.grab(xdisplay=__import__('os').environ['DISPLAY']).save('/tmp/jarvis-native-tk.png')
  except ImportError:pass
  from unittest.mock import patch
  buddy.close()
  with patch('backend.companion_window.platform.system',return_value='Darwin'):
   result=app.companion_window.open('http://127.0.0.1:'+str(server.server_port)+'/companion','helper');assert result['visible'];process=app.companion_window.process;assert 'backend.companion_tk' in process.args;app.companion_window.close();process.wait(timeout=5);assert process.returncode==0
  print('PASS: actual Tk native window, private chat response, no DB call history, drag, mode resize, idle motion and motion stop. Linux display; macOS appearance/audio not physically tested.')
 finally:buddy.close();app.office.stop();server.shutdown();server.server_close();worker.join(3)
