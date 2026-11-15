"""Small native Tk helper. All widgets stay on the UI thread; no osascript/WebKit."""
import json,math,os,queue,re,signal,subprocess,sys,tempfile,threading,time,urllib.error,urllib.parse,urllib.request,uuid
from pathlib import Path

class Client:
 def __init__(self,url):
  parsed=urllib.parse.urlsplit(url)
  if parsed.scheme not in {'http','https'} or parsed.hostname not in {'localhost','127.0.0.1','::1'} or not parsed.port:raise ValueError('Der Helfer verbindet sich nur mit dem lokalen Jarvis-Server.')
  self.base=urllib.parse.urlunsplit((parsed.scheme,parsed.netloc,'','',''));self.token='';self.opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
 def request(self,path,body=None,binary=False):
  if not path.startswith('/api/'):raise ValueError('Ungültiger Helferpfad.')
  request=urllib.request.Request(self.base+path,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json','X-Jarvis-Token':self.token})
  try:
   with self.opener.open(request,timeout=120) as response:data=response.read(16*1024*1024)
  except urllib.error.HTTPError as error:
   try:message=json.loads(error.read(8192)).get('error','Jarvis-Anfrage fehlgeschlagen.')
   except ValueError:message='Jarvis-Anfrage fehlgeschlagen.'
   raise ValueError(message) from None
  return data if binary else json.loads(data)
 def connect(self):self.token=self.request('/api/session')['token']

class Buddy:
 def __init__(self,config,ready):
  import tkinter as tk
  from tkinter import ttk
  self.tk=tk;self.path=Path(config);self.ready=Path(ready);self.config=json.loads(self.path.read_text());self.client=Client(self.config['url']);self.events=queue.Queue();self.closed=False;self.busy=False;self.screen=False;self.history=[];self.voice_generation=0;self.player=None;self.audio_path=None;self.plan=None;self.pending_note=False;self.last_input=time.monotonic();self.mode=None;self.dictating=False;self.dictation_at=None;self.watch_busy=False;self.last_watch=0;self.watch_signature=None
  self.root=tk.Tk();self.root.title('Jarvis · kleiner Helfer');self.root.configure(bg='#101a26');self.root.attributes('-topmost',True);self.root.protocol('WM_DELETE_WINDOW',self.close);self.root.minsize(340,190)
  theme=ttk.Style(self.root)
  if 'clam' in theme.theme_names():theme.theme_use('clam')
  theme.configure('Buddy.TButton',background='#213548',foreground='#e7d29b',bordercolor='#40556b',font=('Helvetica',9),padding=(5,4));theme.map('Buddy.TButton',background=[('active','#314e64')],foreground=[('disabled','#697d8b')]);theme.configure('Mini.TButton',background='#172b3b',foreground='#c8d9e6',font=('Helvetica',8),padding=(3,3))
  self.root.bind('<Motion>',lambda e:self.touch());self.root.bind('<Key>',lambda e:self.touch());self.root.bind('<ButtonPress-1>',self.drag_start);self.root.bind('<B1-Motion>',self.drag_move)
  self.canvas=tk.Canvas(self.root,height=160,bg='#101a26',highlightthickness=0);self.canvas.pack(fill='x');self.canvas.bind('<Button-1>',lambda e:self.entry.focus_set())
  self.status=tk.StringVar(value='Verbinde mit deinem lokalen Jarvis …');tk.Label(self.root,textvariable=self.status,bg='#101a26',fg='#e8d7a5',wraplength=390,font=('Helvetica',10)).pack(fill='x',padx=10)
  self.input=tk.StringVar();self.entry=tk.Entry(self.root,textvariable=self.input,bg='#1c2b3b',fg='#eef7ff',insertbackground='white',font=('Helvetica',12),relief='flat',highlightthickness=1,highlightbackground='#4b637c',highlightcolor='#e6c88a');self.entry.pack(fill='x',padx=10,pady=8);self.entry.bind('<Return>',lambda e:self.send());self.input.trace_add('write',self.dictation_changed)
  bar=tk.Frame(self.root,bg='#101a26');bar.pack(fill='x',padx=7)
  def button(label,fn):b=ttk.Button(bar,text=label,command=fn,style='Buddy.TButton');b.pack(side='left',padx=2);return b
  button('Senden',self.send);button('Stimme stoppen',self.mute);button('Auftrag stoppen',self.stop_actions);button('Diktieren',self.dictate)
  second=tk.Frame(self.root,bg='#101a26');second.pack(fill='x',padx=8,pady=5)
  for title,fn in [('Oben',lambda:self.change_mode('island')),('Helfer',lambda:self.change_mode('helper')),('Groß',lambda:self.change_mode('expanded')),('Bewegung',self.motion),('Bildschirm',self.share),('Sprachfenster',self.browser)]:ttk.Button(second,text=title,command=fn,style='Mini.TButton').pack(side='left',padx=1)
  self.transcript=tk.Text(self.root,height=9,bg='#0d1621',fg='#cfdeea',wrap='word',font=('Helvetica',11),state='disabled');self.transcript.pack(fill='both',expand=True,padx=9,pady=5)
  self.run_button=ttk.Button(self.root,style='Buddy.TButton',text='Geprüften Ablauf ausführen',command=self.run_plan,state='disabled');self.run_button.pack(fill='x',padx=9,pady=3)
  self.voice=tk.BooleanVar(value=True);tk.Checkbutton(self.root,text='Thorsten liest Antworten vor',variable=self.voice,command=lambda:None if self.voice.get() else self.mute(),bg='#101a26',fg='#acbed0',selectcolor='#101a26',font=('Helvetica',9)).pack()
  self.root.update_idletasks();self.layout(self.config);self.root.deiconify();self.root.lift();self.root.update();
  if not self.root.winfo_ismapped():raise ValueError('Das native Python-Fenster wurde nicht sichtbar.')
  self.ready.write_text('visible');self.ready.chmod(0o600)
  if hasattr(signal,'SIGTERM'):signal.signal(signal.SIGTERM,lambda *args:setattr(self,'closed',True))
  self.background(self.client.connect,lambda _:self.status.set('Bereit, Sir. Bildschirm ist aus.'));self.root.after(40,self.tick)
 def touch(self):self.last_input=time.monotonic()
 def drag_start(self,event):
  self.touch();self.drag=(event.x_root,event.y_root,self.root.winfo_x(),self.root.winfo_y()) if event.widget==self.canvas else None
 def drag_move(self,event):
  if getattr(self,'drag',None):
   x,y,a,b=self.drag;self.root.geometry(f'+{max(0,a+event.x_root-x)}+{max(0,b+event.y_root-y)}');self.touch()
 def background(self,fn,done=None):
  def work():
   try:result=fn();self.events.put((done,result,None))
   except Exception as error:self.events.put((None,None,str(error)))
  threading.Thread(target=work,daemon=True).start()
 def layout(self,state):
  if self.mode==state['mode']:return
  self.mode=state['mode'];w,h={'island':(380,285),'helper':(440,540),'expanded':(580,640)}[self.mode]
  x=max(0,(self.root.winfo_screenwidth()-w)//2) if self.mode=='island' else max(0,self.root.winfo_x());y=8 if self.mode=='island' else max(0,self.root.winfo_y());self.root.geometry(f'{w}x{h}+{x}+{y}');self.canvas.configure(height=110 if self.mode=='island' else 170)
  if self.mode=='island':self.transcript.pack_forget();self.run_button.pack_forget()
  else:self.transcript.pack(fill='both',expand=True,padx=9,pady=5);self.run_button.pack(fill='x',padx=9,pady=3)
 def append(self,role,text):
  self.transcript.configure(state='normal');self.transcript.insert('end',role+': '+text+'\n\n');self.transcript.see('end');self.transcript.configure(state='disabled');self.status.set(text[:100 if self.mode=='island' else 180]+(' …' if len(text)>180 else ''))
 def answer(self,text):
  self.busy=False;self.append('Jarvis',text)
  if self.voice.get():self.speak(text)
 def send(self):
  text=self.input.get().strip()
  if not text or self.busy:return
  self.input.set('');self.dictating=False;self.busy=True;self.mute();self.append('Du',text)
  def request():
   if re.fullmatch(r'stopp?[.! ]*',text,re.I):self.client.request('/api/desktop/stop',{});return 'Stopp für den Mac-Auftrag angefordert, Sir.'
   if re.fullmatch(r'(?:erstelle|mach) (?:mir )?(?:eine )?notiz[.! ]*',text,re.I):self.pending_note=True;return 'Was soll in der Notiz stehen, Sir?'
   if re.search(r'(?:video.*(?:schneid|bearbeit)|(?:schneid|bearbeit).*video|animation|zeichentrick)',text,re.I):
    self.client.request('/api/companion/editor',{'animation':text[:1500]} if re.search(r'animation|zeichentrick',text,re.I) else {});return 'Die Schnitt- und Animationswerkstatt wurde angefordert, Sir.'
   goal='Erstelle eine Notiz: '+text if self.pending_note else text;was_note=self.pending_note;self.pending_note=False
   if was_note or re.match(r'^(?:öffne|starte|klicke|bewege|tippe|drücke)\b',text,re.I):
    plan=self.client.request('/api/desktop/prepare',{'goal':goal})['plan'];self.plan=plan
    if len(plan['steps'])==1 and plan['steps'][0]['type'] in {'open','website','note'}:
     self.client.request('/api/desktop/start',{'id':plan['id']});return 'Auftrag gestartet. Ein Ergebnis wird erst vom Mac-Ausführer bestätigt, Sir.'
    self.events.put((lambda _:(self.change_mode('helper'),self.run_button.configure(state='normal')),None,None));return plan['message']+'\n'+json.dumps(plan['steps'],ensure_ascii=False)+'\nPrüfe den Ablauf und wähle Ausführen.'
   body={'text':text,'history':self.history[-6:]}
   if self.screen:body.update(native_screen=True,source='screen')
   result=self.client.request('/api/video-call',body);self.history.extend([{'role':'user','content':text},{'role':'assistant','content':result['reply'][:2000]}]);self.history=self.history[-6:];return result['reply']
  self.background(request,self.answer)
 def run_plan(self):
  if self.plan:self.run_button.configure(state='disabled');self.background(lambda:self.client.request('/api/desktop/start',{'id':self.plan['id']}),lambda _:self.status.set('Geprüfter Mac-Auftrag gestartet.'))
 def stop_actions(self):
  self.mute();self.pending_note=False
  self.background(lambda:self.client.request('/api/desktop/stop',{}),lambda _:self.status.set('Mac-Auftrag wird gestoppt.'))
 def mute(self):
  self.voice_generation+=1
  if self.player and self.player.poll() is None:self.player.terminate()
  self.player=None
  if self.audio_path:self.audio_path.unlink(missing_ok=True);self.audio_path=None
 def speak(self,text):
  version=self.voice_generation
  def play():
   data=self.client.request('/api/natural-voice/speak',{'text':text[:1800],'preset':'jarvis'},binary=True)
   if self.closed or version!=self.voice_generation:return
   if not Path('/usr/bin/afplay').is_file():raise ValueError('Thorsten-Audio ist verfügbar; der Mac-Audioplayer afplay fehlt.')
   path=None
   try:
    with tempfile.NamedTemporaryFile(prefix='jarvis-voice-',suffix='.wav',delete=False) as wav:path=Path(wav.name);wav.write(data)
    if self.closed or version!=self.voice_generation:return
    self.audio_path=path
    player=subprocess.Popen(['/usr/bin/afplay',str(path)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);self.player=player;code=player.wait()
    if self.player is player:self.player=None
    if code and not self.closed and version==self.voice_generation:raise ValueError('Thorsten konnte nicht abgespielt werden. Bitte die Mac-Tonausgabe prüfen.')
   finally:
    if path:path.unlink(missing_ok=True)
    if self.audio_path==path:self.audio_path=None
  self.background(play)
 def dictate(self):
  self.entry.focus_set();self.dictating=True;self.status.set('macOS-Diktieren mit Mikrofontaste oder deinem Diktierkürzel starten (je nach Systemeinstellung mit Onlineverarbeitung). Nach 2 Sekunden Textpause wird gesendet. Mit Escape abbrechen.');self.entry.bind('<Escape>',lambda e:self.cancel_dictation())
 def cancel_dictation(self):self.dictating=False;self.dictation_at=None;self.status.set('Diktiermodus beendet.')
 def dictation_changed(self,*args):
  if self.dictating:self.dictation_at=time.monotonic()
 def browser(self):
  import webbrowser
  webbrowser.open(self.client.base+'/companion?mode=helper')
 def change_mode(self,value):self.background(lambda:self.client.request('/api/companion/mode',{'mode':value}))
 def motion(self):self.background(lambda:self.client.request('/api/companion/motion',{'enabled':not self.config.get('wandering',True)}))
 def share(self):
  def done(data):self.screen=bool(data.get('active'));self.status.set('Bildschirm freigegeben · Einzelbild nur bei einer Frage.' if self.screen else data.get('message','Bildschirm aus.'))
  self.background(lambda:self.client.request('/api/companion/screen',{'action':'stop' if self.screen else 'start'}),done)
 def tick(self):
  if self.closed:self.close();return
  try:
   while True:
    callback,data,error=self.events.get_nowait()
    if error:self.busy=False;self.watch_busy=False;self.status.set(error)
    elif callback:callback(data)
  except queue.Empty:pass
  try:self.config=json.loads(self.path.read_text());self.layout(self.config)
  except (OSError,ValueError,KeyError):pass
  if self.plan and not self.watch_busy and time.monotonic()-self.last_watch>1:
   self.watch_busy=True;self.last_watch=time.monotonic()
   def watched(data):
    self.watch_busy=False;plan=data.get('plan')
    if not plan or not self.plan or plan['id']!=self.plan['id']:return
    self.plan=plan;signature=(plan.get('state'),plan.get('completed'),plan.get('message'))
    if signature!=self.watch_signature:self.watch_signature=signature;self.status.set(str(plan.get('state'))+' · '+str(plan.get('completed',0))+'/'+str(len(plan['steps']))+' · '+str(plan.get('message',''))[:160])
    if plan.get('state') not in {'review','running'}:self.run_button.configure(state='disabled');self.plan=None
   self.background(lambda:self.client.request('/api/desktop'),watched)
  now=time.monotonic();w=self.canvas.winfo_width();h=self.canvas.winfo_height();x,y=w/2,h/2;r=min(h*.38,62);self.canvas.delete('all')
  for i in range(60):
   a=i*math.pi/30;v=r+9+(4 if i%5==0 else 0);self.canvas.create_line(x+math.cos(a)*(r+6),y+math.sin(a)*(r+6),x+math.cos(a)*v,y+math.sin(a)*v,fill='#e6bd82',width=2 if i%5==0 else 1)
  for i in range(18,0,-1):
   radius=r*i/18;value=12+int((18-i)*1.2);self.canvas.create_oval(x-radius,y-radius,x+radius,y+radius,fill=f'#{value:02x}{value+10:02x}{value+24:02x}',outline='')
  blink=now%5<.12;eye=2 if blink else r*.22
  for side in [-1,1]:self.canvas.create_oval(x+side*r*.27-5,y-r*.12-eye/2,x+side*r*.27+5,y-r*.12+eye/2,fill='#f4fcff',outline='')
  talking=self.player and self.player.poll() is None;mouth=4+(abs(math.sin(now*12))*10 if talking else 0);self.canvas.create_oval(x-6,y+r*.28-mouth/2,x+6,y+r*.28+mouth/2,fill='#fff7df',outline='')
  if self.busy or (self.plan and self.plan.get('state')=='running'):
   for i in range(8):a=now*2+i*math.pi/4;self.canvas.create_oval(x+math.cos(a)*(r+20),y+math.sin(a)*(r+20),x+math.cos(a)*(r+20)+2,y+math.sin(a)*(r+20)+2,fill='white',outline='')
  if self.config.get('wandering') and not self.busy and not (self.plan and self.plan.get('state')=='running') and now-self.last_input>10 and self.root.focus_get()!=self.entry:
   px,py=self.root.winfo_pointerxy();over=self.root.winfo_x()<=px<=self.root.winfo_x()+self.root.winfo_width() and self.root.winfo_y()<=py<=self.root.winfo_y()+self.root.winfo_height()
   if not over and int(now*10)%8==0:
    nx=max(0,min(self.root.winfo_screenwidth()-self.root.winfo_width(),self.root.winfo_x()+round(math.sin(now/4)*2)));ny=max(0,min(self.root.winfo_screenheight()-self.root.winfo_height(),self.root.winfo_y()+(0 if self.mode=='island' else round(math.cos(now/6)))));self.root.geometry(f'+{nx}+{ny}')
  if self.dictating and self.dictation_at and now-self.dictation_at>2 and self.input.get().strip() and not self.busy:self.send()
  self.root.after(40,self.tick)
 def close(self):
  self.closed=True;self.mute()
  try:self.root.destroy()
  except self.tk.TclError:pass
 def run(self):self.root.mainloop();self.closed=True;self.mute()

def main():
 try:Buddy(sys.argv[1],sys.argv[2]).run();return 0
 except Exception as error:print('Python-Helfer: '+str(error),flush=True);return 1
if __name__=='__main__':raise SystemExit(main())
