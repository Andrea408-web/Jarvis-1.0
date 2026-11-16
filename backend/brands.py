"""Private brand profiles and explicit revision-checked device transfer. No publishing."""
import json,re,secrets,threading
from pathlib import Path
class Brands:
 def __init__(self,directory):self.path=Path(directory)/'brands.json';self.lock=threading.RLock()
 def all(self):
  with self.lock:
   if not self.path.exists():return {'profiles':[]}
   try:
    data=json.loads(self.path.read_text());return {'profiles':data['profiles'][:20]}
   except (ValueError,KeyError,TypeError):raise ValueError('Markenspeicher konnte nicht gelesen werden. Die Datei wurde nicht überschrieben.') from None
 def save(self,body):
  if set(body)-{'profile','expected_revision'} or not isinstance(body.get('profile'),dict):raise ValueError('Ein Markenprofil angeben.')
  p=body['profile'];allowed={'id','name','tagline','audience','product','tone','colors','website','goal'}
  if set(p)-allowed:raise ValueError('Unbekanntes Markenfeld.')
  checked={};limits={'name':80,'tagline':180,'audience':400,'product':600,'tone':100,'website':300,'goal':300}
  for key,limit in limits.items():
   value=p.get(key,'')
   if not isinstance(value,str) or len(value)>limit:raise ValueError('Ungültiges Markenfeld: '+key)
   checked[key]=value.strip()
  if not checked['name']:raise ValueError('Der Markenname fehlt.')
  colors=p.get('colors',['#e8ce83','#78b9d9','#111b2a'])
  if not isinstance(colors,list) or not 1<=len(colors)<=5 or any(not isinstance(c,str) or not re.fullmatch('#[0-9a-fA-F]{6}',c) for c in colors):raise ValueError('1 bis 5 gültige Markenfarben angeben.')
  ident=p.get('id') or secrets.token_hex(16)
  if not isinstance(ident,str) or not re.fullmatch('[A-Za-z0-9_-]{1,64}',ident):raise ValueError('Ungültige Markenkennung.')
  checked.update(id=ident,colors=colors)
  with self.lock:
   data=self.all();old=next((x for x in data['profiles'] if x['id']==ident),None);revision=old.get('revision',0) if old else 0
   if old and body.get('expected_revision')!=revision:raise ValueError('Dieses Markenprofil wurde am Mac geändert. Zuerst die Mac-Version laden oder deine Version als neue Marke speichern.')
   checked['revision']=revision+1
   if old:data['profiles'][data['profiles'].index(old)]=checked
   else:
    if len(data['profiles'])>=20:raise ValueError('Maximal 20 Marken auf dem Mac.')
    data['profiles'].append(checked)
   self.path.parent.mkdir(parents=True,exist_ok=True,mode=0o700);temp=self.path.with_suffix('.tmp');temp.write_text(json.dumps(data,ensure_ascii=False));temp.chmod(0o600);temp.replace(self.path);return checked
