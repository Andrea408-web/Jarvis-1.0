"""Opt-in private-WLAN static studio. Never expose the app API, keys or files.
This is the normal browser-window editor, not immersive WebXR or an AI server.
"""
import mimetypes,threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from .mobile import private_ip
FRONTEND=Path(__file__).resolve().parents[1]/'frontend'
FILES={'/aeris':'aeris.html','/vr-guide':'vr-guide.html',**{('/'+name):name for name in ['aeris-shell.css','aeris-shell.js','aeris-icon.svg','aeris.js','aeris-model.js','aeris-projects.js','aeris-xr.js','aeris-assistant.js','aeris-gestures.js','aeris-tracking.js','aeris-pose.js','headset-window.js']}}
class StaticHandler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  path=urlsplit(self.path).path
  if path=='/':path='/aeris'
  name=FILES.get(path)
  if not name:
   self.send_error(403 if path.startswith('/api/') else 404,'Only the public 3D studio is available.');return
  source=(FRONTEND/name).read_bytes()
  if name=='aeris.html':source=source.replace(b'<body ',b'<body data-headset-window="true" ',1).replace(b'<script src="/mobile-app.js"></script>',b'<script src="/headset-window.js"></script>')
  self.send_response(200);self.send_header('Content-Type',mimetypes.guess_type(name)[0] or 'application/octet-stream');self.send_header('Content-Length',str(len(source)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Referrer-Policy','no-referrer');self.end_headers();self.wfile.write(source)
 def do_POST(self):self.send_error(403,'No app API on this static studio.')
 do_PUT=do_PATCH=do_DELETE=do_POST
class QuestWindow:
 def __init__(self):self.server=None;self.lock=threading.Lock()
 def start(self):
  with self.lock:
   if not self.server:
    address=private_ip();self.server=ThreadingHTTPServer((address,8767),StaticHandler);self.server.daemon_threads=True;threading.Thread(target=self.server.serve_forever,daemon=True).start()
   return {'url':'http://'+self.server.server_address[0]+':8767/aeris','mode':'browser-window','message':'Mac und Quest ins gleiche private WLAN. Diesen Link im Quest Browser öffnen. Kein Entwicklerkonto und keine Android-Werkzeuge nötig. 3D-Editor im Browserfenster; keine KI, Kamerastreams oder immersives Handtracking über diesen einfachen Zugang.'}
 def stop(self):
  with self.lock:
   if self.server:self.server.shutdown();self.server.server_close();self.server=None

def main():
 import json,sys,urllib.request,webbrowser
 try:
  opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
  with opener.open('http://127.0.0.1:8765/api/session',timeout=5) as response:token=json.loads(response.read(8192))['token']
  stop='--stop' in sys.argv
  request=urllib.request.Request('http://127.0.0.1:8765/api/quest-window/'+('stop' if stop else 'start'),data=b'{}',headers={'Content-Type':'application/json','X-Jarvis-Token':token})
  with opener.open(request,timeout=10) as response:data=json.loads(response.read(16384))
  if stop:print('Einfacher WLAN-Zugang beendet.')
  else:
   print('Diesen Link im Quest Browser öffnen:\n'+data['url']+'\n\n'+data['message']);webbrowser.open(data['url'])
  return 0
 except Exception:print('Bitte zuerst 2-JARVIS-starten.command öffnen und Jarvis laufen lassen. Danach diesen Brillen-Helfer erneut öffnen. Alternativ in Aeris unter VR / MR den einfachen Brillen-Link anzeigen.');return 1
if __name__=='__main__':raise SystemExit(main())
