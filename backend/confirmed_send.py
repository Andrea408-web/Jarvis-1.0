"""Explicit, single-use confirmation before native Mac Mail/Messages submission.
Pending payloads stay in RAM for two minutes. No credentials, cloud service or log.
"""
import base64,hashlib,json,platform,re,secrets,subprocess,threading,time

SCRIPT=r'''function run() {
 ObjC.import('Foundation');
 const raw=ObjC.unwrap($.NSString.alloc.initWithDataEncoding($.NSFileHandle.fileHandleWithStandardInput.readDataToEndOfFile,$.NSUTF8StringEncoding));
 const p=JSON.parse(raw); let attempted=false;
 try {
  if(p.kind==='mail') {
   const app=Application('com.apple.mail');
   if(!app.accounts().length)return JSON.stringify({accepted:false,reason:'no_account'});
   const message=app.OutgoingMessage({subject:p.subject,content:p.text+'\n',visible:true});
   app.outgoingMessages.push(message);
   message.toRecipients.push(app.ToRecipient({address:p.address}));
   app.activate();attempted=true;
   const result=app.send(message);
   return JSON.stringify({accepted:result===true,reason:result===true?'accepted':'uncertain'});
  }
  const app=Application('com.apple.iChat'),all=app.services();
  const type=s=>String(s.serviceType()).toLowerCase().trim();
  const service=all.find(s=>type(s)==='sms')||all.find(s=>['imessage','imsg'].includes(type(s)));
  if(!service)return JSON.stringify({accepted:false,reason:'no_service'});
  const buddy=service.buddies.byName(p.address);
  app.activate();attempted=true;app.send(p.text,{to:buddy});
  return JSON.stringify({accepted:true,reason:'accepted'});
 }catch(error){return JSON.stringify({accepted:false,reason:attempted?'uncertain':Number(error.errorNumber||error.number)===-1743?'permission':'not_configured'});}
}'''

class NativeSendError(Exception):
 def __init__(self,message,uncertain=False):super().__init__(message);self.uncertain=uncertain

def native_send(payload):
 if platform.system()!='Darwin':raise NativeSendError('Direkter Versand benötigt Jarvis auf dem verbundenen Mac.')
 if payload.get('audio'):
  from .audio_send import native_audio_send
  return native_audio_send(payload)
 try:
  result=subprocess.run(['/usr/bin/osascript','-l','JavaScript','-e',SCRIPT],input=json.dumps(payload,ensure_ascii=False),text=True,capture_output=True,timeout=60)
 except subprocess.TimeoutExpired:raise NativeSendError('Keine rechtzeitige Bestätigung vom Mac. Prüfe Mail/Nachrichten vor einem neuen Versandversuch.',True) from None
 except OSError:raise NativeSendError('Der native Versand konnte nicht gestartet werden.') from None
 if result.returncode or len(result.stdout)>2000:raise NativeSendError('Versandstatus unklar. Prüfe Mail/Nachrichten vor einem neuen Versandversuch.',True)
 try:status=json.loads(result.stdout)
 except ValueError:raise NativeSendError('Keine bestätigte Rückmeldung der Mac-App. Prüfe dort, ob die Nachricht versendet wurde.',True) from None
 if not isinstance(status,dict):raise NativeSendError('Unbekannter Versandstatus. Bitte in der Mac-App prüfen.',True)
 if status.get('accepted') is True:return
 reasons={'no_account':'In Apple Mail ist kein Konto eingerichtet.','no_service':'In Apple Nachrichten ist kein nutzbarer Dienst eingerichtet. SMS braucht gegebenenfalls die iPhone-Weiterleitung.','permission':'macOS hat den Zugriff abgelehnt. Unter Datenschutz & Sicherheit → Automation den Zugriff des Jarvis-Terminals auf Mail/Nachrichten erlauben.','not_configured':'Mail/Nachrichten ist nicht bereit oder macOS hat den Zugriff nicht freigegeben.','uncertain':'Versand nicht bestätigt. Prüfe die Mac-App vor einem neuen Versuch.'}
 raise NativeSendError(reasons.get(status.get('reason'),'Unbekannter Versandstatus. Bitte in der Mac-App prüfen.'),status.get('reason') not in {'no_account','no_service','permission','not_configured'})

def validate(body):
 if not isinstance(body,dict) or set(body)-{'kind','name','address','subject','text','audio'} or not {'kind','name','address','subject','text'}<=set(body):raise ValueError('Bitte Empfänger, Kanal, Betreff und Nachricht angeben.')
 p={}
 for key,limit in {'kind':4,'name':100,'address':200,'subject':180,'text':8000}.items():
  v=body[key]
  if not isinstance(v,str) or len(v)>limit or '\0' in v:raise ValueError('Ungültiges Nachrichtenfeld.')
  p[key]=v.strip()
 if p['kind'] not in {'mail','sms'} or not p['name'] or (not p['text'] and 'audio' not in body):raise ValueError('Kanal, Kontakt und Nachricht vollständig angeben.')
 if '\n' in p['subject'] or '\r' in p['subject']:raise ValueError('Der Betreff muss eine Zeile sein.')
 if p['kind']=='mail':
  if not re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",p['address']):raise ValueError('Genau eine gültige E-Mail-Adresse auswählen.')
 else:
  if not re.fullmatch(r'\+?[0-9 ()/.-]{3,60}',p['address']):raise ValueError('Genau eine Telefonnummer auswählen.')
  p['address']=re.sub(r'[^+0-9]','',p['address'])
  if not re.fullmatch(r'\+?\d{3,30}',p['address']):raise ValueError('Ungültige Telefonnummer.')
 if 'audio' in body:
  audio=body['audio'];limit=4*1024*1024
  if p['kind']!='mail':raise ValueError('Direkter Audio-Versand nutzt Apple Mail. Für Nachrichten bitte ausdrücklich Audio teilen wählen.')
  if not isinstance(audio,dict) or set(audio)!={'mime','data'} or not isinstance(audio.get('mime'),str) or not isinstance(audio.get('data'),str) or len(audio['data'])>limit*4//3+16:raise ValueError('Ungültige oder zu große Audioaufnahme (maximal 4 MB).')
  mime=audio['mime'].split(';',1)[0].strip().lower()
  try:raw=base64.b64decode(audio['data'],validate=True)
  except ValueError:raise ValueError('Ungültige Audiodaten.') from None
  if not 16<=len(raw)<=limit:raise ValueError('Audioaufnahme muss zwischen 16 Byte und 4 MB groß sein.')
  formats={'audio/wav':('wav',raw[:4]==b'RIFF' and raw[8:12]==b'WAVE'),'audio/x-wav':('wav',raw[:4]==b'RIFF' and raw[8:12]==b'WAVE'),'audio/mp4':('m4a',raw[4:8]==b'ftyp'),'audio/webm':('webm',raw[:4]==bytes.fromhex('1a45dfa3')),'audio/ogg':('ogg',raw[:4]==b'OggS')}
  if mime not in formats or not formats[mime][1]:raise ValueError('Bitte eine gültige WAV-, M4A-, WebM- oder Ogg-Aufnahme verwenden.')
  p['audio']={'bytes':raw,'mime':mime,'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'filename':'Jarvis-Sprachnachricht.'+formats[mime][0]}
  if not p['subject']:p['subject']='Sprachnachricht'
  if not p['text']:p['text']='Sprachnachricht im Anhang.'
 return p

class ConfirmedSend:
 def __init__(self,sender=None,clock=None):self.sender=sender or native_send;self.clock=clock or time.monotonic;self.pending={};self.receipts={};self.lock=threading.RLock()
 def _expire(self,ident):
  with self.lock:self.pending.pop(ident,None)
 def _clean(self):
  now=self.clock()
  for key,value in list(self.pending.items()):
   if value['until']<=now:value['timer'].cancel();self.pending.pop(key,None)
  self.receipts={k:v for k,v in self.receipts.items() if v['until']>now}
 def prepare(self,body,actor):
  p=validate(body)
  if self.sender is native_send and platform.system()!='Darwin':raise ValueError('Direkter Versand braucht den verbundenen Mac mit eingerichtetem Apple Mail bzw. Nachrichten.')
  with self.lock:
   self._clean()
   if len(self.pending)>=16:raise ValueError('Zu viele offene Versandbestätigungen. Alte Bestätigung schließen oder kurz warten.')
   ident=secrets.token_urlsafe(24);timer=threading.Timer(120,self._expire,args=(ident,));timer.daemon=True;self.pending[ident]={'payload':p,'actor':actor,'until':self.clock()+120,'timer':timer};timer.start()
  preview={key:value for key,value in p.items() if key!='audio'}
  if p.get('audio'):preview['audio']={key:value for key,value in p['audio'].items() if key!='bytes'}
  return {'id':ident,'expires_in':120,'preview':preview,'app':'Apple Mail' if p['kind']=='mail' else 'Apple Nachrichten (SMS/iMessage je nach Einrichtung)','sender':'Das in der Mac-App eingerichtete Konto'}
 def cancel(self,ident,actor):
  with self.lock:
   self._clean();receipt=self.receipts.get(ident)
   if receipt and receipt['actor']==actor:return dict(receipt['result'])
   p=self.pending.get(ident)
   if p and p['actor']==actor:p['timer'].cancel();self.pending.pop(ident,None)
  return {'state':'cancelled','message':'Versand abgebrochen.'}
 def execute(self,body,actor):
  if not isinstance(body,dict) or set(body)!={'id','confirm'} or body['confirm'] is not True or not isinstance(body['id'],str):raise ValueError('Die angezeigte Nachricht ausdrücklich bestätigen.')
  ident=body['id']
  with self.lock:
   self._clean();receipt=self.receipts.get(ident)
   if receipt:
    if receipt['actor']!=actor:raise ValueError('Diese Bestätigung gehört zu einer anderen Sitzung.')
    return dict(receipt['result'])
   p=self.pending.get(ident)
   if not p or p['actor']!=actor:raise ValueError('Bestätigung abgelaufen oder nicht vorhanden. Nachricht erneut prüfen.')
   self.pending.pop(ident);p['timer'].cancel();self.receipts[ident]={'actor':actor,'until':self.clock()+300,'result':{'state':'running','message':'Versandauftrag läuft. Nicht erneut auslösen.'}}
  try:
   self.sender(p['payload']);result={'state':'accepted','message':('Apple Mail' if p['payload']['kind']=='mail' else 'Apple Nachrichten')+' hat den Versandauftrag angenommen. Die Zustellung beim Empfänger ist damit nicht bestätigt.'}
  except NativeSendError as error:result={'state':'uncertain' if error.uncertain else 'failed','message':str(error)}
  except Exception:result={'state':'uncertain','message':'Versandstatus unklar. Bitte vor einem neuen Versuch in Mail/Nachrichten prüfen.'}
  with self.lock:self.receipts[ident]={'actor':actor,'until':self.clock()+300,'result':result}
  return dict(result)
