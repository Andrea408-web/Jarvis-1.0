"""Explicit device-AI preparation: verified browser runtime and an existing local GGUF.
No model is downloaded. Paired devices can copy only the configured small model.
"""
import base64,hashlib,io,json,mimetypes,os,secrets,subprocess,tarfile,threading
from pathlib import Path
VERSION='3.13.0';CHUNK=8*1024*1024;MAX_MODEL=450_000_000
PACKAGES=[
 {'url':'https://registry.npmjs.org/@wllama/wllama/-/wllama-3.13.0.tgz','integrity':'ZvoRdQAn+E+18EvQ9qS036gudiI9rbZRBJgG/qNICPPwrA0Y6SMMdbziz/j7K/0WxcbJlhaRraVIYsnEy732NA==','files':{'wllama.js':'package/esm/index.min.js','wllama.wasm':'package/esm/wasm/wllama.wasm','LICENSE':'package/LICENCE'}},
 {'url':'https://registry.npmjs.org/@wllama/wllama-compat/-/wllama-compat-3.13.0.tgz','integrity':'MSWwyzVXpwkstvIGzOsQ9jlRm8kY5S5J0Gdw4E6M9mXqhgO/5tj+YNfxSoqN1GvsAOwui95JPtwX3hO6VZkbzg==','files':{'compat.js':'package/wasm/wllama.js','compat.wasm':'package/wasm/wllama.wasm'}}]
# File hashes are pinned to these npm releases; archives are verified independently.
FILES={'wllama.js': {'size': 219295, 'sha256': 'e7f3745ee508c111c22d178d23c52cc74016dd8cec39e4600d87e28d287d7981', 'url': '/device-runtime/3.13.0/wllama.js'}, 'wllama.wasm': {'size': 10244628, 'sha256': '79ac5be917b71d50571a4f584436a9f6baf6b6e57719d094ed8bd950e9a65780', 'url': '/device-runtime/3.13.0/wllama.wasm'}, 'LICENSE': {'size': 1071, 'sha256': '5866e3bd7e3cbd3f7c8bea6efd8a1e7fa7cc8de68c30f428aff7c6584a0fb720', 'url': '/device-runtime/3.13.0/LICENSE'}, 'compat.js': {'size': 173601, 'sha256': '942062a7495790a317061b27a6bcd2bd3b247e2ddef53a069baf5abb07284758', 'url': '/device-runtime/3.13.0/compat.js'}, 'compat.wasm': {'size': 18755784, 'sha256': '35df8c1e2f7dbd74b8e8b01054fb9f1fbe86cf566945fbf4cef3965855a8b92e', 'url': '/device-runtime/3.13.0/compat.wasm'}}

class DeviceAI:
 def __init__(self,directory,locator=None):
  self.root=Path(directory)/'device-ai'/VERSION;self.lock=threading.RLock();self.locator=locator;self.known=None
 def model(self):
  if self.locator:path=Path(self.locator()).resolve()
  else:
   from .small_model import locate
   _,path=locate()
  stat=path.stat()
  if not 1<=stat.st_size<=MAX_MODEL:raise ValueError('Für das Gerät ist nur die vorhandene kleine KI bis 450 MB vorgesehen.')
  signature=(str(path),stat.st_size,stat.st_mtime_ns)
  with self.lock:
   if self.known and self.known[0]==signature:return self.known[1],self.known[2]
   full=hashlib.sha256();chunks=[]
   with path.open('rb') as stream:
    head=stream.read(4)
    if head!=b'GGUF':raise ValueError('Die vorhandene Modelldatei ist kein GGUF.')
    stream.seek(0)
    for chunk in iter(lambda:stream.read(CHUNK),b''):full.update(chunk);chunks.append(hashlib.sha256(chunk).hexdigest())
   data={'name':path.name,'size':stat.st_size,'sha256':full.hexdigest(),'chunk_size':CHUNK,'chunks':chunks};self.known=(signature,path,data);return path,data
 def runtime_ready(self):
  return all((self.root/name).is_file() and (self.root/name).stat().st_size==spec['size'] and hashlib.sha256((self.root/name).read_bytes()).hexdigest()==spec['sha256'] for name,spec in FILES.items())
 def status(self):
  try:_,model=self.model();error=None
  except (OSError,ValueError) as e:model=None;error=str(e)
  return {'model':model,'runtime_ready':self.runtime_ready(),'version':VERSION,'assets':[{'name':name,**spec} for name,spec in FILES.items()],'runtime_size':sum(v['size'] for v in FILES.values()),'message':error or 'Vorhandenes Modell kann auf ein gekoppeltes Gerät übertragen werden. Kein neuer Modelldownload vom Internet.'}
 def prepare(self,download=None):
  self.model() # Fail before any runtime download if there is no existing small model.
  with self.lock:
   if self.runtime_ready():return self.status()
   self.root.mkdir(parents=True,exist_ok=True,mode=0o700)
   for package in PACKAGES:
    if download:raw=download(package)
    else:
     process=subprocess.Popen(['/usr/bin/curl','--disable','--fail','--silent','--show-error','--location','--proto','=https','--proto-redir','=https','--connect-timeout','15','--max-time','90',package['url']],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
     try:
      parts=[];total=0
      while True:
       data=process.stdout.read(65536)
       if not data:break
       total+=len(data)
       if total>16*1024*1024:raise ValueError('Browser-Laufzeit überschreitet das Größenlimit.')
       parts.append(data)
      if process.wait(timeout=10):raise ValueError('Die Browser-Laufzeit konnte nicht sicher geladen werden. Internet und macOS-Zertifikatsspeicher prüfen. Keine TLS-Prüfung wurde abgeschaltet.')
      raw=b''.join(parts)
     finally:
      if process.poll() is None:process.terminate()
      process.stdout.close()
    if base64.b64encode(hashlib.sha512(raw).digest()).decode()!=package['integrity']:raise ValueError('Prüfsumme der Browser-Laufzeit stimmt nicht. Nichts wird gestartet.')
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as archive:
     for name,member in package['files'].items():
      info=archive.getmember(member);spec=FILES[name]
      if not info.isfile() or info.size!=spec['size']:raise ValueError('Ungültige Laufzeitdatei.')
      data=archive.extractfile(info).read()
      if hashlib.sha256(data).hexdigest()!=spec['sha256']:raise ValueError('Ungültige Laufzeit-Prüfsumme.')
      path=self.root/name;temp=path.with_name(name+'.'+secrets.token_hex(4)+'.tmp');temp.write_bytes(data);temp.chmod(0o600);temp.replace(path)
   return self.status()
 def asset(self,name):
  if name not in FILES:raise ValueError('Unbekannte Browser-Laufzeitdatei.')
  path=self.root/name
  if not path.is_file() or path.stat().st_size!=FILES[name]['size']:raise ValueError('Browser-Laufzeit zuerst ausdrücklich vorbereiten.')
  return path,('application/wasm' if name.endswith('.wasm') else 'text/javascript' if name.endswith('.js') else 'text/plain')
