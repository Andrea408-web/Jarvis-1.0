"""Local opt-in floating Jarvis panel. No automatic screen capture or startup registration."""
import json,os,platform,subprocess,threading,time
from pathlib import Path
class CompanionWindow:
 def __init__(self,directory):
  self.directory=Path(directory);self.process=None;self.lock=threading.Lock();self.mode='island';self.wandering=True;self.url='';self.sequence=0
  from .screen_view import ScreenView
  self.screen=ScreenView()
 def _write(self):
  self.directory.mkdir(parents=True,exist_ok=True);path=self.directory/'jarvis-companion.json';temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps({'url':self.url,'mode':self.mode,'sequence':self.sequence,'wandering':self.wandering}));temporary.chmod(0o600);temporary.replace(path);return path
 def open(self,url,mode='island'):
  if mode not in {'island','helper','expanded'}:raise ValueError('Unbekannte Helferansicht.')
  if platform.system()!='Darwin':raise ValueError('Das schwebende Mac-Fenster benötigt macOS. Der Browser-Helfer bleibt verfügbar.')
  with self.lock:
   self.url=url+('&' if '?' in url else '?')+'mode='+mode;self.mode=mode;self.sequence+=1;config=self._write()
   if self.process and self.process.poll() is None:return {'ok':True,'mode':mode}
   self.screen.stop()
   ready=self.directory/'jarvis-companion.ready';ready.unlink(missing_ok=True)
   log=self.directory/'jarvis-companion.log'
   with log.open('w') as output:self.process=subprocess.Popen(['/usr/bin/osascript','-l','JavaScript',str(Path(__file__).with_name('companion_window.js')),str(config),str(ready)],stdout=output,stderr=subprocess.STDOUT)
   log.chmod(0o600)
   deadline=time.monotonic()+6;visible_since=None
   while time.monotonic()<deadline:
    if self.process.poll() is not None:
     self.process=None
     try:detail=log.read_text(errors='replace').strip().splitlines()[-1][:350]
     except (OSError,IndexError):detail='Keine weitere Diagnose verfügbar.'
     raise ValueError('Das Mac-Helferfenster konnte nicht starten. '+detail+' · Der Browser-Helfer bleibt nutzbar.')
    if ready.is_file():
     if visible_since is None:visible_since=time.monotonic()
     elif time.monotonic()-visible_since>=.3:return {'ok':True,'mode':mode,'visible':True}
    time.sleep(.05)
   self.process.terminate();self.process=None
   raise ValueError('macOS hat kein sichtbares Helferfenster bestätigt. Bitte den Browser-Helfer verwenden; kein Fenster wurde als geöffnet gemeldet.')
 def change(self,mode):
  if mode not in {'island','helper','expanded'}:raise ValueError('Unbekannte Helferansicht.')
  with self.lock:
   if not self.process or self.process.poll() is not None:raise ValueError('Das Mac-Fenster ist nicht geöffnet.')
   self.mode=mode;self.sequence+=1;self._write();return {'ok':True,'mode':mode}
 def motion(self,enabled):
  if not isinstance(enabled,bool):raise ValueError('Bewegung ein- oder ausschalten.')
  with self.lock:self.wandering=enabled;self.sequence+=1;self._write();return {'ok':True,'wandering':enabled}
 def start_screen(self):
  if not self.process or self.process.poll() is not None:raise ValueError('Bitte zuerst das Mac-Helferfenster öffnen.')
  return self.screen.start()
 def capture(self):
  if not self.process or self.process.poll() is not None:self.screen.stop();raise ValueError('Das Mac-Helferfenster ist geschlossen. Keine Bildschirmaufnahme.')
  return self.screen.capture()
 def close(self):
  with self.lock:
   if self.process and self.process.poll() is None:self.process.terminate()
   self.process=None
   self.screen.stop()

def main():
 import urllib.request,urllib.error
 try:
  opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
  with opener.open('http://127.0.0.1:8765/api/session',timeout=3) as response:token=json.loads(response.read(8192))['token']
  request=urllib.request.Request('http://127.0.0.1:8765/api/companion/open',data=b'{"mode":"island"}',headers={'Content-Type':'application/json','X-Jarvis-Token':token})
  with opener.open(request,timeout=10) as response:json.loads(response.read(8192))
  print('Jarvis-Helfer angefordert. Den großen Browser-Tab kannst du schließen. Das Server-Terminal muss geöffnet bleiben.');return 0
 except urllib.error.HTTPError as error:
  if error.code==404:print('Bitte Jarvis nach dem Update im gleichen Ordner neu starten. Der Helfer braucht die aktuelle Serverversion.')
  else:
   try:print(json.loads(error.read(8192)).get('error','Das Mac-Fenster konnte nicht gestartet werden.'))
   except (ValueError,OSError):print('Das Mac-Fenster konnte nicht gestartet werden.')
   import webbrowser
   webbrowser.open('http://localhost:8765/companion?mode=helper')
   print('Browser-Helfer geöffnet: http://localhost:8765/companion')
  return 1
 except urllib.error.URLError:
  from .easy_start import run
  try:run(companion=True);return 0
  except KeyboardInterrupt:return 0
  except (OSError,ValueError) as error:print(str(error));return 1
 except (ValueError,KeyError,OSError):print('Jarvis-Server konnte nicht geprüft werden. Bitte das laufende Server-Terminal prüfen.');return 1
if __name__=='__main__':raise SystemExit(main())
