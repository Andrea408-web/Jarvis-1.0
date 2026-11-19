"""Local file-based cuts with a real export and a user-defined processing budget.
Input files are explicitly chosen, read-only; output is always a new private file.
"""
import json,math,os,platform,re,secrets,shutil,subprocess,threading,time
from pathlib import Path

class VideoEditor:
 def __init__(self,directory):
  self.root=Path(directory)/'video-edits';self.assets={};self.jobs={};self.lock=threading.RLock();self.worker=None;self.active_id=None;self.cancel=threading.Event();self.process=None
  if self.root.is_dir():
   for path in list(self.root.glob('*/job.json'))[-50:]:
    try:
     data=json.loads(path.read_text());ident=path.parent.name
     if re.fullmatch('[a-f0-9]{32}',ident) and data.get('id')==ident:
      if data.get('state') in {'running','queued'}:data['state']='interrupted';data['message']='Server wurde beendet. Fertige Exporte bleiben erhalten.'
      self.jobs[ident]=data
    except (OSError,ValueError,TypeError):pass
 def tools(self):
  def find(name):
   return shutil.which(name) or next((str(p) for p in [Path('/opt/homebrew/bin')/name,Path('/usr/local/bin')/name,Path('/opt/local/bin')/name] if p.is_file() and os.access(p,os.X_OK)),None)
  ffmpeg,probe=find('ffmpeg'),find('ffprobe');engine='ffmpeg' if ffmpeg and probe else 'avfoundation' if platform.system()=='Darwin' else None
  return {'engine':engine,'ffmpeg':ffmpeg,'ffprobe':probe,'silence':engine=='ffmpeg','message':'FFmpeg: Schnitte, Formate, Tonanpassung und Pausenkürzung.' if engine=='ffmpeg' else 'Mac-Export: Schnitte, Formate und kurze Audio-Blenden. Automatisches Pausenkürzen ist ohne vorhandenes FFmpeg nicht verfügbar.' if engine else 'Für Videoexport wird macOS oder ein bereits installiertes FFmpeg benötigt. Kein automatischer Download.'}
 def choose(self):
  if platform.system()!='Darwin':raise ValueError('Die Dateiauswahl bitte direkt auf deinem Mac öffnen.')
  script="function run(){var a=Application.currentApplication();a.includeStandardAdditions=true;return JSON.stringify(a.chooseFile({withPrompt:'Videoclips für Astra auswählen (maximal 8)',ofType:['public.movie'],multipleSelectionsAllowed:true}).map(p=>p.toString()));}"
  try:raw=subprocess.run(['/usr/bin/osascript','-l','JavaScript','-e',script],capture_output=True,text=True,check=True,timeout=180).stdout;paths=json.loads(raw)
  except (OSError,subprocess.SubprocessError,ValueError):raise ValueError('Dateiauswahl abgebrochen oder nicht verfügbar.') from None
  return self.import_paths(paths)
 def upload(self,stream,length,name):
  # Bounded streaming import: never hold a full video in Python memory.
  if not isinstance(length,int) or not 1<=length<=4*1024**3:raise ValueError('Bitte eine Videodatei bis 4 GB auswählen.')
  name=Path(name).name;suffix=Path(name).suffix.lower()
  if suffix not in {'.mp4','.mov','.m4v','.mkv','.webm','.avi','.mpeg','.mpg','.mts','.m2ts','.ts','.3gp','.ogv','.mxf','.wmv','.flv','.vob'}:raise ValueError('Bitte eine unterstützte Videodatei auswählen, z. B. MP4, MOV, AVI oder WebM.')
  folder=self.root/'imports';folder.mkdir(parents=True,exist_ok=True,mode=0o700)
  if shutil.disk_usage(folder).free<length+128*1024**2:raise ValueError('Nicht genug freier Speicher für die Videokopie.')
  path=folder/(secrets.token_hex(16)+suffix)
  try:
   with path.open('xb') as output:
    path.chmod(0o600);remaining=length
    while remaining:
     chunk=stream.read(min(1024*1024,remaining))
     if not chunk:raise ValueError('Videoübertragung wurde unterbrochen.')
     output.write(chunk);remaining-=len(chunk)
   assets=self.import_paths([str(path)])
   with self.lock:self.assets[assets[0]['id']]['name']=name[:240]
   assets[0]['name']=name[:240];return assets
  except Exception:
   path.unlink(missing_ok=True);raise
 def assist(self,app,body,plan_only=False):
  if set(body)-{'assets','instruction','formats','budget_minutes','short_seconds','style','captions','remove_silence','caption_spread','auto_edit','hook'}:raise ValueError('Unbekannte Schnittfelder.')
  ids=body.get('assets');instruction=body.get('instruction','')
  if not isinstance(ids,list) or not 1<=len(ids)<=8 or any(not isinstance(i,str) or i not in self.assets for i in ids) or len(set(ids))!=len(ids):raise ValueError('Zuerst 1 bis 8 Clips auswählen.')
  if not isinstance(instruction,str) or len(instruction)>1500:raise ValueError('Schnittwunsch bis 1500 Zeichen eingeben.')
  auto=body.get('auto_edit','');hook=body.get('hook','')
  if not isinstance(auto,str) or auto not in {'','dynamic','full'} or not isinstance(hook,str) or len(hook)>120:raise ValueError('Ungültiger Automatik-Stil oder zu langer Hook.')
  if auto and any(type(body.get(k,False))is not bool for k in ['caption_spread','remove_silence']):raise ValueError('Ungültiger Automatik-Schalter.')
  if auto:return self.automatic(body,ids,auto,hook,plan_only)
  from .video_style import validate
  style,captions=validate(body.get('style'),body.get('captions'))
  if re.search(r'untertitel|captions?',instruction,re.I) and not captions:raise ValueError('Bitte zuerst Untertiteltext oder eine SRT-Datei eintragen. Die kleine Text-KI kann die Tonspur nicht automatisch transkribieren.')
  selected=[self.public_asset(self.assets[i]) for i in ids]
  cuts=[{'asset':a['id'],'start':0,'end':a['duration']} for a in selected]
  silence=body.get('remove_silence',self.tools()['silence']);message='Automatischer technischer Schnitt: Clips zusammenfügen, Formate anpassen'+(' und längere stille Stellen kürzen.' if silence else '. Pausenkürzen ist ohne FFmpeg nicht verfügbar.')
  if instruction.strip():
   settings=app.store.settings();provider=settings['ai_provider']
   if provider not in {'llamacpp','ollama'}:raise ValueError('Für einen freien Schnittwunsch muss die lokale KI laufen. Ohne Text kannst du den automatischen technischen Schnitt starten.')
   system=('Du planst einen Videoschnitt. Du siehst KEINE Bilder und hörst KEIN Audio. Du kennst nur Dateinamen und Dauer. '
           'Erlaubt: Clips nach Wunsch anordnen, Bereiche in Sekunden ausschneiden, stille Stellen kürzen. '
           'Keine erfundenen Szenen, Highlights, gesprochenen Untertitel oder Musik. Bei nicht unterstütztem Wunsch antworte nur mit JSON {"error":"kurze Erklärung"}. '
           'Sonst nur JSON {"cuts":[{"clip":1,"start":0,"end":10}],"remove_silence":false,"style":{}}. Stil darf look (natural, cinematic, neon, mono, warm), transition (cut, fade), zoom, vignette, sharpen (bool), speed (0.5 bis 2) enthalten. Nur gewünschte Effekte setzen. '
           'Maximal 32 Bereiche. Nummeriere Clips ab 1 wie in den Clipdaten. Nutze gültige Zeitgrenzen. Ohne Zeitwunsch vollständige Clips behalten. '
           'Pausenkürzen verfügbar: '+str(silence)+'. Clipdaten: '+json.dumps([{'clip':i+1,'name':a['name'],'duration':a['duration']} for i,a in enumerate(selected)],ensure_ascii=False))
   client=app.llamacpp if provider=='llamacpp' else app.local_ai
   result=client.transport('/api/chat',{'model':settings['local_model'],'messages':[{'role':'system','content':system},{'role':'user','content':instruction.strip()}],'stream':False,'options':{'num_ctx':4096,'num_predict':1000,'temperature':0},'keep_alive':'5m'})
   try:
    if result.get('done') is not True or result.get('message',{}).get('tool_calls'):raise ValueError()
    raw=result['message']['content'].strip();raw=re.sub(r'^```(?:json)?\s*|\s*```$','',raw);plan=json.loads(raw)
    if not isinstance(plan,dict):raise ValueError()
   except (KeyError,TypeError,ValueError):raise ValueError('Die lokale KI hat keinen gültigen Schnittplan geliefert. Formuliere konkrete Sekundenangaben oder nutze den automatischen Schnitt ohne Text.') from None
   if 'error' in plan:raise ValueError('Schnittwunsch noch nicht unterstützt: '+str(plan['error'])[:300])
   if set(plan)-{'cuts','remove_silence','style'} or not {'cuts','remove_silence'}<=set(plan) or not isinstance(plan['cuts'],list) or any(not isinstance(c,dict) or set(c)!={'clip','start','end'} or type(c.get('clip')) is not int or not 1<=c['clip']<=len(ids) for c in plan['cuts']):raise ValueError('Die KI hat einen ungültigen Schnittplan geliefert. Es wurde nichts gestartet.')
   style,_=validate({**style,**plan.get('style',{})},captions)
   cuts=[{'asset':ids[c['clip']-1],'start':c['start'],'end':c['end']} for c in plan['cuts']];silence=plan['remove_silence'];message='Schnittplan der lokalen KI geprüft und zur Ausführung gestartet.'
  job=self.start({'cuts':cuts,'formats':body.get('formats',['youtube','shorts']),'budget_minutes':body.get('budget_minutes',10),'short_seconds':body.get('short_seconds',60),'remove_silence':silence,'style':style,'captions':captions,'caption_spread':body.get('caption_spread',False)},plan_only=plan_only)
  return {'job':job,'message':message}
 def automatic(self,body,ids,mode,hook,plan_only=False):
  """A real, bounded editing recipe; no claim of semantic highlight recognition."""
  from .video_style import validate
  style,captions=validate(body.get('style'),body.get('captions'))
  cuts=[]
  for ident in ids:
   duration=self.assets[ident]['duration']
   if mode=='full' or duration<=9:cuts.append({'asset':ident,'start':0,'end':duration});continue
   # Evenly sample beginning/middle/end; preserve order and never invent scene labels.
   length=min(4,duration/3)
   for start in [0,(duration-length)/2,duration-length]:cuts.append({'asset':ident,'start':round(start,3),'end':min(duration,round(start+length,3))})
  if mode=='dynamic':style={**style,'look':'cinematic','transition':'fade','zoom':True,'vignette':True,'subtitle_style':'pop'}
  duration=sum(c['end']-c['start']for c in cuts)/style['speed']
  if body.get('caption_spread',False):
   from .video_style import spread
   captions=spread(captions,duration)
  if hook.strip():
   end=min(2.8,duration);combined=[]
   if not captions or captions[0]['start']>0:combined.append({'start':0,'end':min(end,captions[0]['start'])if captions else end,'text':hook.strip()})
   for cue in captions:
    if cue['start']>=end:combined.append(cue);continue
    title=hook.strip()+'\n'+cue['text']
    if len(title)>240:raise ValueError('Hook und erster Untertitel sind zusammen zu lang. Bitte den Hook kürzen.')
    combined.append({**cue,'end':min(end,cue['end']),'text':title})
    if cue['end']>end:combined.append({**cue,'start':end})
   captions=combined
  job=self.start({'cuts':cuts,'formats':body.get('formats',['youtube','shorts']),'budget_minutes':body.get('budget_minutes',10),'short_seconds':body.get('short_seconds',60),'remove_silence':bool(body.get('remove_silence',False)) and self.tools()['silence'],'style':style,'captions':captions,'caption_spread':False},plan_only=plan_only)
  return {'job':job,'message':('Dynamische Kurzfassung: Anfang, Mitte und Ende der Clips, Blenden, Zoom und Kino-Look.' if mode=='dynamic' else 'Vollständiger Schnitt: alle Clips in Reihenfolge.')+(' Hook als Texteinblendung gesetzt.' if hook.strip()else '')+(' Vorhandene Untertitel werden eingebrannt.' if captions else ' Keine Wort-Untertitel: Es liegt kein Transkript vor.')+' Schnittbereiche und Fortschritt sind sichtbar. Keine automatische inhaltliche Szenenerkennung.'}
 def story(self,app,body):
  prompt=body.get('prompt')
  if set(body)!={'prompt'} or not isinstance(prompt,str) or not 1<=len(prompt.strip())<=1500:raise ValueError('Animationswunsch bis 1500 Zeichen angeben.')
  settings=app.store.settings();provider=settings['ai_provider']
  if provider not in {'llamacpp','ollama'}:raise ValueError('Bitte die vorhandene lokale Text-KI starten oder den Sprechertext selbst eintragen.')
  client=app.llamacpp if provider=='llamacpp' else app.local_ai
  result=client.transport('/api/chat',{'model':settings['local_model'],'messages':[{'role':'system','content':'Schreibe drei kurze deutsche Sprechersätze für einen Animationsfilm mit einer eigenen Jarvis-Figur. Jeder Satz höchstens 120 Zeichen. Antworte ausschließlich mit JSON {"lines":["Satz 1","Satz 2","Satz 3"],"style":"lowpoly"}. style kann lowpoly, hologram oder kinetic sein. Keine behauptete freie Filmszenen-Generierung. Keine Regieanweisungen im gesprochenen Text.'},{'role':'user','content':prompt.strip()}],'stream':False,'options':{'num_ctx':2048,'num_predict':350,'temperature':.4}})
  try:
   if result.get('done') is not True:raise ValueError()
   raw=result['message']['content'].strip();data=json.loads(re.sub(r'^```(?:json)?\s*|\s*```$','',raw));lines=data['lines'];kind=data.get('style','lowpoly')
   if not isinstance(lines,list) or not 1<=len(lines)<=3 or any(not isinstance(s,str) or not 1<=len(s.strip())<=120 for s in lines) or kind not in {'lowpoly','hologram','kinetic'}:raise ValueError()
  except (KeyError,TypeError,ValueError):raise ValueError('Die kleine KI hat kein gültiges Kurzskript geliefert. Bitte drei kurze Sätze selbst eintragen oder den Wunsch einfacher formulieren.') from None
  return {'lines':lines,'style':kind,'message':'Kurzskript erstellt. Der lokale Animationsrenderer erzeugt den Film.'}
 def probe(self,path,deadline=None):
  tools=self.tools()
  if tools['ffprobe']:
   try:
    command=[tools['ffprobe'],'-v','error','-protocol_whitelist','file,pipe','-show_entries','format=duration:stream=codec_type,width,height','-of','json',str(path)];raw=json.loads(self._command(command,deadline)[0] if deadline else subprocess.run(command,capture_output=True,text=True,check=True,timeout=20).stdout);video=next(s for s in raw['streams'] if s.get('codec_type')=='video');duration=float(raw['format']['duration']);width=int(video['width']);height=int(video['height']);audio=any(s.get('codec_type')=='audio' for s in raw['streams'])
   except (TimeoutError,InterruptedError):raise
   except (OSError,ValueError,KeyError,StopIteration,subprocess.SubprocessError):raise ValueError('Videodatei konnte nicht gelesen werden.') from None
  elif tools['engine']=='avfoundation' and Path(path).suffix.lower() in {'.mp4','.mov','.m4v'}:
   from .video_metadata import probe
   try:raw=probe(path);duration=float(raw['duration']);width=int(raw['width']);height=int(raw['height']);audio=raw['audio']
   except (OSError,ValueError,KeyError) as error:raise ValueError('MP4/MOV konnte nicht gelesen werden: '+str(error)) from None
  elif tools['engine']=='avfoundation':
   try:
    command=['/usr/bin/osascript','-l','JavaScript',str(Path(__file__).with_name('video_native.js')),'probe',str(path)];raw=json.loads(self._command(command,deadline)[0] if deadline else subprocess.run(command,capture_output=True,text=True,check=True,timeout=25).stdout);duration=float(raw['duration']);width=int(raw['width']);height=int(raw['height']);audio=bool(raw['audio'])
   except (TimeoutError,InterruptedError):raise
   except (OSError,ValueError,KeyError,subprocess.SubprocessError):raise ValueError('macOS kann dieses Videoformat nicht lesen. MP4/MOV verwenden; weitere Formate benötigen vorhandenes FFmpeg.') from None
  else:raise ValueError(tools['message'])
  if not math.isfinite(duration) or not .05<=duration<=43200 or not 1<=width<=16384 or not 1<=height<=16384:raise ValueError('Ungeeignete Videodatei oder Dauer über 12 Stunden.')
  return {'duration':duration,'width':width,'height':height,'audio':audio}
 def import_paths(self,paths):
  if not isinstance(paths,list) or not 1<=len(paths)<=8:raise ValueError('Bitte 1 bis 8 Videodateien auswählen.')
  pending=[]
  for value in paths:
   path=Path(value).expanduser().resolve()
   if path.suffix.lower() not in {'.mp4','.mov','.m4v','.mkv','.webm','.avi','.mpeg','.mpg','.mts','.m2ts','.ts','.3gp','.ogv','.mxf','.wmv','.flv','.vob'} or not path.is_file():raise ValueError('Bitte eine unterstützte Videodatei auswählen, z. B. MP4, MOV, AVI oder WebM.')
   pending.append({'id':secrets.token_hex(16),'name':path.name,'path':str(path),**self.probe(path)})
  with self.lock:
   if len(self.assets)+len(pending)>64:raise ValueError('Zu viele ausgewählte Dateien. Jarvis neu starten oder vorhandene Clips weiterverwenden.')
   self.assets.update({a['id']:a for a in pending})
  return [self.public_asset(a) for a in pending]
 @staticmethod
 def public_asset(asset):return {k:v for k,v in asset.items() if k!='path'}
 def snapshot(self):
  with self.lock:return {'tools':{k:v for k,v in self.tools().items() if k not in {'ffmpeg','ffprobe'}},'assets':[self.public_asset(a) for a in self.assets.values()],'jobs':json.loads(json.dumps(list(self.jobs.values())[-30:]))}
 def _save(self,job):
  folder=self.root/job['id'];folder.mkdir(parents=True,exist_ok=True,mode=0o700);path=folder/'job.json';temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(job,ensure_ascii=False));temporary.chmod(0o600);temporary.replace(path)
 def start(self,body,plan_only=False):
  if set(body)-{'cuts','formats','budget_minutes','short_seconds','remove_silence','style','captions','caption_spread'}:raise ValueError('Unbekannte Schnittfelder.')
  cuts=body.get('cuts');formats=body.get('formats');budget=body.get('budget_minutes',10);short=body.get('short_seconds',60);silence=body.get('remove_silence',False)
  if not isinstance(cuts,list) or not 1<=len(cuts)<=32:raise ValueError('Bitte 1 bis 32 Schnittbereiche angeben.')
  if not isinstance(formats,list) or not formats or len(formats)>2 or len(set(formats))!=len(formats) or any(f not in {'youtube','shorts'} for f in formats):raise ValueError('YouTube und/oder Shorts auswählen.')
  if isinstance(budget,bool) or not isinstance(budget,(float,int)) or not math.isfinite(budget) or not 1<=budget<=120:raise ValueError('Arbeitszeit zwischen 1 und 120 Minuten angeben.')
  if isinstance(short,bool) or not isinstance(short,(float,int)) or not math.isfinite(short) or not 5<=short<=180 or not isinstance(silence,bool):raise ValueError('Shorts-Länge 5 bis 180 Sekunden angeben.')
  from .video_style import validate,active
  style,captions=validate(body.get('style'),body.get('captions'))
  tools=self.tools()
  if not plan_only and active(style,captions) and tools['engine']!='ffmpeg':raise ValueError('Untertitel und Effekte bitte mit Browser-Export verwenden; FFmpeg ist auf diesem Mac nicht vorhanden.')
  if not tools['engine'] and not plan_only:raise ValueError(tools['message'])
  if silence and not tools['silence']:raise ValueError('Pausenkürzen benötigt bereits installiertes FFmpeg. Ohne diese Option kann macOS schneiden und exportieren.')
  checked=[]
  with self.lock:
   if self.worker and self.worker.is_alive():raise ValueError('Ein Videoschnitt läuft bereits. Erst beenden oder stoppen.')
   for cut in cuts:
    if not isinstance(cut,dict) or set(cut)!={'asset','start','end'} or cut['asset'] not in self.assets:raise ValueError('Ungültiger Clip in der Schnittliste.')
    a,b=cut['start'],cut['end'];asset=self.assets[cut['asset']]
    if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in [a,b]) or not 0<=a<b<=asset['duration']+.03 or b-a<.1:raise ValueError('Schnittzeiten liegen außerhalb der Datei oder sind zu kurz.')
    checked.append({'asset':asset['id'],'start':float(a),'end':min(float(b),asset['duration'])})
   if type(body.get('caption_spread',False)) is not bool:raise ValueError('Ungültige Untertitel-Verteilung.')
   if body.get('caption_spread'):
    from .video_style import spread
    captions=spread(captions,sum(c['end']-c['start'] for c in checked)/style['speed'])
   if plan_only:return {'cuts':checked,'formats':formats,'budget_minutes':budget,'short_seconds':short,'remove_silence':silence,'style':style,'captions':captions}
   ident=secrets.token_hex(16);job={'id':ident,'state':'queued','stage':'Schnittliste geprüft','message':'Noch kein Export erstellt.','created':time.time(),'budget_minutes':budget,'short_seconds':short,'formats':formats,'remove_silence':silence,'style':style,'captions':captions,'caption_spread':body.get('caption_spread',False),'cuts':checked,'sources':[{'id':a['id'],'name':a['name']} for a in self.assets.values() if a['id'] in {c['asset'] for c in checked}],'outputs':[],'engine':tools['engine']};self.jobs[ident]=job;self._save(job);self.cancel.clear();self.active_id=ident;self.worker=threading.Thread(target=self._run,args=(job,tools),daemon=True);self.worker.start();return json.loads(json.dumps(job))
 def _command(self,args,deadline,cwd=None):
  if self.cancel.is_set():raise InterruptedError('Vom Nutzer gestoppt.')
  if time.monotonic()>=deadline:raise TimeoutError('Arbeitszeit erreicht.')
  process=subprocess.Popen(args,cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.PIPE);self.process=process
  try:
   while True:
    if self.cancel.is_set():raise InterruptedError('Vom Nutzer gestoppt.')
    remaining=deadline-time.monotonic()
    if remaining<=0:raise TimeoutError('Arbeitszeit erreicht.')
    try:out,err=process.communicate(timeout=min(.25,remaining));break
    except subprocess.TimeoutExpired:continue
   if process.returncode:raise ValueError('Videoverarbeitung fehlgeschlagen. Quelldatei, unterstütztes Format und freien Speicher prüfen.')
   return out,err[-2000000:]
  finally:
   if process.poll() is None:
    process.terminate()
    try:process.communicate(timeout=2)
    except subprocess.TimeoutExpired:process.kill();process.communicate()
   self.process=None
 def _silence(self,cut,tools,deadline):
  asset=self.assets[cut['asset']]
  if not asset['audio']:return [cut]
  length=cut['end']-cut['start'];_,err=self._command([tools['ffmpeg'],'-hide_banner','-nostdin','-protocol_whitelist','file,pipe','-ss',str(cut['start']),'-t',str(length),'-i',asset['path'],'-vn','-af','silencedetect=noise=-35dB:d=0.8','-f','null','-'],deadline)
  starts=[];pauses=[]
  for kind,value in re.findall(r'silence_(start|end):\s*([0-9.]+)',err.decode(errors='replace')):
   value=max(0,min(length,float(value)))
   if kind=='start':starts.append(value)
   elif starts:pauses.append((starts.pop(0),value))
  pauses.extend((v,length) for v in starts);cursor=0;kept=[]
  for a,b in pauses:
   left=max(cursor,a+.15);right=max(left,b-.15)
   if right-left<.4:continue
   if left-cursor>=.1:kept.append({'asset':cut['asset'],'start':cut['start']+cursor,'end':cut['start']+left})
   cursor=right
  if length-cursor>=.1:kept.append({'asset':cut['asset'],'start':cut['start']+cursor,'end':cut['end']})
  return kept if sum(c['end']-c['start'] for c in kept)>=max(.5,length*.05) else [cut]
 @staticmethod
 def short_cuts(cuts,limit):
  out=[]
  for cut in cuts:
   length=min(limit,cut['end']-cut['start'])
   if length<.1:break
   out.append({**cut,'end':cut['start']+length});limit-=length
   if limit<=.01:break
  return out
 def _ffmpeg(self,cuts,kind,path,tools,deadline,job=None):
  from .video_style import validate,filters as style_filters,ass
  style,captions=validate((job or {}).get('style'),(job or {}).get('captions'));w,h=(1920,1080) if kind=='youtube' else (1080,1920);args=[tools['ffmpeg'],'-hide_banner','-loglevel','error','-nostdin','-y','-filter_complex_threads','1'];filters=[]
  for i,cut in enumerate(cuts):
   asset=self.assets[cut['asset']];length=cut['end']-cut['start'];args+=['-protocol_whitelist','file,pipe','-ss',str(cut['start']),'-t',str(length),'-threads','1','-i',asset['path']]
   fit=f'scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2' if kind=='youtube' else f'scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}'
   fade=f',fade=t=in:d=0.15,fade=t=out:st={max(0,length-.15)}:d=0.15' if style['transition']=='fade' else ''
   filters.append(f'[{i}:v:0]trim=duration={length},setpts=PTS-STARTPTS,{fit},setsar=1,fps=30,format=yuv420p{fade}[v{i}]')
   audio=f'[{i}:a:0]atrim=duration={length},asetpts=PTS-STARTPTS' if asset['audio'] else f'anullsrc=r=48000:cl=stereo,atrim=duration={length}'
   filters.append(audio+f',aformat=sample_rates=48000:channel_layouts=stereo,afade=t=in:d=0.03,afade=t=out:st={max(0,length-.03)}:d=0.03[a{i}]')
  filters.append(''.join(f'[v{i}][a{i}]' for i in range(len(cuts)))+f'concat=n={len(cuts)}:v=1:a=1[v][a]');filters.append('[a]dynaudnorm=f=150:g=15:p=0.89:m=8,alimiter=limit=0.89'+(',atempo='+str(style['speed']) if style['speed']!=1 else '')+'[aout]')
  video_filters=style_filters(style,w,h)
  if captions:
   caption_file=path.parent/'captions.ass';caption_file.write_text(ass(captions,w,h,style['subtitle_style']),encoding='utf-8');caption_file.chmod(0o600);video_filters.append('subtitles=filename=captions.ass')
  filters.append('[v]'+','.join(video_filters or ['null'])+'[styled]')
  args+=['-filter_complex',';'.join(filters),'-map','[styled]','-map','[aout]','-c:v','libx264','-preset','fast','-crf','20','-threads','2','-c:a','aac','-b:a','192k','-movflags','+faststart',str(path.resolve())];self._command(args,deadline,cwd=path.parent)
 def _native(self,cuts,kind,path,folder,deadline):
  config=folder/'export.json';config.write_text(json.dumps({'cuts':[{**cut,'path':self.assets[cut['asset']]['path']} for cut in cuts],'kind':kind,'output':str(path)}));config.chmod(0o600)
  self._command(['/usr/bin/osascript','-l','JavaScript',str(Path(__file__).with_name('video_native.js')),'export',str(config)],deadline)
 def _run(self,job,tools):
  deadline=time.monotonic()+job['budget_minutes']*60;folder=self.root/job['id'];job['state']='running';job['stage']='Schnitt vorbereiten';self._save(job)
  try:
   cuts=[]
   for cut in job['cuts']:
    if job['remove_silence']:job['stage']='Stille Stellen analysieren';self._save(job);cuts.extend(self._silence(cut,tools,deadline))
    else:cuts.append(cut)
   if len(cuts)>128:raise ValueError('Mehr als 128 Teilstücke erkannt. Kleinere Auswahl wählen oder Pausenkürzen ausschalten.')
   if job.get('caption_spread'):
    from .video_style import spread
    job['captions']=spread(job.get('captions',[]),sum(c['end']-c['start'] for c in cuts)/job.get('style',{}).get('speed',1))
   job['actual_cuts']=cuts;self._save(job)
   for kind in job['formats']:
    selected=self.short_cuts(cuts,job['short_seconds']*job.get('style',{}).get('speed',1)) if kind=='shorts' else cuts;job['stage']='Export '+('YouTube 16:9' if kind=='youtube' else 'Shorts 9:16');self._save(job);temporary=folder/(kind+'.partial.mp4');final=folder/(kind+'.mp4')
    if tools['engine']=='ffmpeg':self._ffmpeg(selected,kind,temporary,tools,deadline,job=job)
    else:self._native(selected,kind,temporary,folder,deadline)
    info=self.probe(temporary,deadline);temporary.replace(final);job['outputs'].append({'format':kind,'name':'Astra-'+kind+'-'+job['id'][:8]+'.mp4',**info});self._save(job)
   job['state']='completed';job['stage']='Export geprüft';job['message']='Neue Videodatei'+('en' if len(job['outputs'])>1 else '')+' tatsächlich erstellt. Originaldateien unverändert.'
  except TimeoutError:job['state']='timed_out';job['message']='Arbeitszeit erreicht. Fertige Exporte bleiben erhalten; unfertiger Export wurde gestoppt.'
  except InterruptedError:job['state']='cancelled';job['message']='Vom Nutzer gestoppt. Fertige Exporte bleiben erhalten.'
  except Exception as error:job['state']='failed';job['message']=str(error)[:500]
  finally:
   for name in ['youtube.partial.mp4','shorts.partial.mp4']:(folder/name).unlink(missing_ok=True)
   job['finished']=time.time();self._save(job);self.active_id=None
 def stop(self,ident=None):
  if ident and ident not in self.jobs:raise ValueError('Auftrag nicht gefunden.')
  if ident and ident!=self.active_id:return {'ok':True,'message':'Dieser Auftrag läuft nicht mehr.'}
  self.cancel.set();return {'ok':True,'message':'Stopp angefordert.'}
 def file(self,ident,kind=None):
  if kind is None:
   asset=self.assets.get(ident)
   if not asset:raise ValueError('Clip nicht ausgewählt.')
   return Path(asset['path']),asset['name']
  if not re.fullmatch('[a-f0-9]{32}',ident) or kind not in {'youtube','shorts'} or ident not in self.jobs or not any(o['format']==kind for o in self.jobs[ident]['outputs']):raise ValueError('Noch kein fertiger Export verfügbar.')
  path=self.root/ident/(kind+'.mp4')
  if not path.is_file() or path.is_symlink():raise ValueError('Exportdatei nicht verfügbar.')
  return path,'Astra-'+kind+'.mp4'
 def close(self):
  self.cancel.set()
  if self.worker:self.worker.join(timeout=3)
