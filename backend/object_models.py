"""Bounded, on-demand public GLB retrieval. No file cache or arbitrary web proxy."""
import platform,struct
from urllib.parse import urlsplit,urlunsplit
from urllib.request import Request,build_opener,HTTPRedirectHandler
from urllib.error import URLError,HTTPError
MAX_MODEL=20*1024*1024
HOSTS={'raw.githubusercontent.com','modelviewer.dev','threejs.org'}
class NoRedirect(HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs):raise ValueError('Der Modell-Link darf nicht weiterleiten. Bitte den direkten GLB-Link verwenden.')
def model_url(raw):
 if not isinstance(raw,str) or len(raw)>2000:raise ValueError('Bitte einen direkten HTTPS-Link zu einer GLB-Datei eingeben.')
 try:u=urlsplit(raw.strip());port=u.port
 except ValueError:raise ValueError('Ungültiger Modell-Link.') from None
 if u.scheme=='https' and u.hostname=='github.com' and not u.username and not u.password and not u.query and not u.fragment:
  parts=u.path.split('/')
  if len(parts)>=6 and parts[3]=='blob':u=urlsplit('https://raw.githubusercontent.com/'+ '/'.join(parts[1:3]+parts[4:]))
 if u.scheme!='https' or u.hostname not in HOSTS or port not in {None,443} or u.username is not None or u.password is not None or u.query or u.fragment or not u.path.lower().endswith('.glb') or '..' in u.path.split('/') or any(ord(c)<33 for c in raw):raise ValueError('Unterstützt werden direkte GLB-Links von raw.githubusercontent.com, modelviewer.dev und threejs.org. Andere Modelle als GLB-Datei herunterladen und hier auswählen.')
 return urlunsplit(('https',u.hostname,u.path,'',''))
def load_model(raw,transport=None):
 url=model_url(raw)
 try:
  if transport:data=transport(url,MAX_MODEL)
  else:
   with build_opener(NoRedirect()).open(Request(url,headers={'User-Agent':'Jarvis-ObjectViewer/1.0','Accept':'model/gltf-binary','Accept-Encoding':'identity'}),timeout=20) as response:
    length=response.headers.get('Content-Length')
    if length and (not length.isdigit() or int(length)>MAX_MODEL):raise ValueError('Das 3D-Modell überschreitet 20 MB.')
    data=response.read(MAX_MODEL+1)
 except (HTTPError,URLError,TimeoutError,OSError):raise ValueError('Das Modell konnte nicht geladen werden. Prüfe den direkten GLB-Link und die Internetverbindung.') from None
 if not isinstance(data,bytes) or not 20<=len(data)<=MAX_MODEL:raise ValueError('Bitte eine GLB-Datei bis 20 MB verwenden.')
 magic,version,size=struct.unpack_from('<III',data)
 if magic!=0x46546c67 or version!=2 or size!=len(data):raise ValueError('Der Link liefert kein gültiges GLB-2.0-Modell.')
 return data
def capabilities():return {'camera_tracking':platform.system()=='Darwin','max_bytes':MAX_MODEL,'hosts':sorted(HOSTS)}
