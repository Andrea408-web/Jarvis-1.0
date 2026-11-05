"""Small deterministic missing-input state, separate from language-model history."""
import threading,time

class Dialogue:
 def __init__(self):self.lock=threading.RLock();self.pending=None
 def get(self):
  with self.lock:
   if self.pending and time.monotonic()>self.pending['expires']:self.pending=None
   return {k:self.pending[k] for k in ['kind','question']} if self.pending else None
 def ask(self,kind,question,**data):
  with self.lock:self.pending={'kind':kind,'question':question,'data':data,'expires':time.monotonic()+600}
  return {'reply':question,'proposals':[],'pending':self.get()}
 def clear(self):
  with self.lock:self.pending=None
 def answer(self,text):
  with self.lock:
   if not self.get():return None
   kind=self.pending['kind'];data=self.pending['data']
   if kind=='note':
    from .notes import request
    complete=request(text)
    if complete is not None:
     if not complete['body']:raise ValueError(self.pending['question'])
     return {'goal':text}
    return {'goal':'Erstelle eine Notiz: '+text}
   from .desktop import resolve_app,website
   if kind=='app':return {'goal':'Öffne '+resolve_app(text.strip().rstrip('.!?'))['name']}
   if kind=='website':
    value=text.strip().rstrip('.!');url=website(value if '://' in value else 'https://'+value)
    return {'goal':'Webseite öffnen: '+url,'steps':[{'type':'website','url':url}]}
   if kind=='typing_app':
    app=resolve_app(text.strip().rstrip('.!?'));steps=[{'type':'open','app':app['name']},{'type':'wait','seconds':1}]
    if app['bundle']=='com.apple.Notes':steps.append({'type':'key','key':'n','modifiers':['command']})
    steps.append({'type':'text','text':data['text']})
    return {'goal':'Text in '+app['name']+' eingeben','steps':steps}
   return None
