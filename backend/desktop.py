"""Local, reviewable desktop input plans. No shell scripts or remote AI fallback."""
import ctypes
import json
import math
import plistlib
import shutil
from urllib.parse import urlsplit
import platform
import re
import secrets
import subprocess
import threading
import time
from pathlib import Path

from .providers import ProviderError
from .input_access import label_point
from .notes import request as note_request,create as create_note
from .models import recipe,validate_scene,write_scene

APPS={'Safari':'com.apple.Safari','Finder':'com.apple.finder','Notizen':'com.apple.Notes','Kalender':'com.apple.iCal','Rechner':'com.apple.calculator','Musik':'com.apple.Music','Blender':'org.blenderfoundation.blender','Spotify':'com.spotify.client'}
KEYS={'enter':36,'tab':48,'escape':53,'space':49,'backspace':51,'left':123,'right':124,'down':125,'up':126,'a':0,'c':8,'v':9,'s':1,'z':6,'n':45,'o':31,'f':3}
FLAGS={'command':1<<20,'shift':1<<17,'option':1<<19,'control':1<<18}


def app_catalog(include_downloads=False):
    apps={name:{'name':name,'bundle':bundle} for name,bundle in APPS.items()}
    if platform.system()=='Darwin':
        roots=[Path('/Applications'),Path.home()/'Applications',Path('/System/Applications')]
        if include_downloads:
            roots.extend([Path.home()/'Downloads',Path.home()/'Desktop'])
            try:roots.extend(path for path in list(Path('/Volumes').iterdir())[:30] if path.is_dir())
            except OSError:pass
        for root in roots:
            try:paths=(list(root.glob('*.app'))+list(root.glob('*/*.app')))[:400]
            except OSError:continue
            for path in paths:
                try:
                    info=plistlib.loads((path/'Contents/Info.plist').read_bytes());bundle=info.get('CFBundleIdentifier');name=path.stem
                    if name.casefold() in {'terminal','iterm','iterm2','script editor','skripteditor'}:continue
                    if isinstance(bundle,str) and re.fullmatch(r'[A-Za-z0-9_.-]{3,180}',bundle):
                        item={'name':name,'bundle':bundle,'path':str(path.resolve())}
                        if name not in apps or apps[name]['bundle']==bundle and 'path' not in apps[name]:apps[name]=item
                        for alias in [info.get('CFBundleDisplayName'),info.get('CFBundleName')]:
                            if isinstance(alias,str) and 1<=len(alias)<=100:
                                if alias not in apps or apps[alias]['bundle']==bundle and 'path' not in apps[alias]:apps[alias]=item
                except (OSError,ValueError,TypeError):pass
    return apps

def resolve_app(value,include_downloads=False):
    if not isinstance(value,str):raise ValueError('Bitte einen App-Namen eingeben.')
    aliases={'notes':'Notizen','calculator':'Rechner','calendar':'Kalender','music':'Musik'}
    value=value.strip()
    if value.casefold().endswith('.app'):value=value[:-4]
    value=aliases.get(value.casefold(),value)
    for name,item in app_catalog(include_downloads).items():
        if name.casefold()==value.casefold():return item
    if not include_downloads:return resolve_app(value,True)
    raise ValueError('Diese App wurde nicht in Programme, Downloads, auf dem Schreibtisch oder einem geöffneten Installationslaufwerk gefunden. Eine ZIP-/DMG-Datei allein ist noch keine startbare App. Bitte den genauen App-Namen prüfen.')

def website(value):
    if not isinstance(value,str) or not 1<=len(value)<=2000:raise ValueError('Ungültige Webseitenadresse.')
    try:
        parsed=urlsplit(value)
        if parsed.scheme not in {'http','https'} or not parsed.hostname or parsed.username or parsed.password or any(ord(c)<=32 for c in value):raise ValueError()
        _=parsed.port
    except ValueError:raise ValueError('Nur vollständige HTTP-/HTTPS-Webseiten ohne Zugangsdaten öffnen.') from None
    return value


def validate_steps(steps):
    if not isinstance(steps,list) or not 1<=len(steps)<=12:raise ValueError('Ein Ablauf braucht 1–12 überprüfbare Schritte.')
    result=[]
    for step in steps:
        if not isinstance(step,dict):raise ValueError('Ungültiger Desktop-Schritt.')
        kind=step.get('type')
        fields={'open':{'type','app'},'website':{'type','url'},'move':{'type','x','y'},'click':{'type','x','y'},'text':{'type','text'},'key':{'type','key','modifiers'},'wait':{'type','seconds'},'click_label':{'type','label'}}
        if not isinstance(kind,str) or kind not in fields or set(step)!=fields[kind]:raise ValueError('Nicht unterstützter Desktop-Schritt; kein Programmcode wird ausgeführt.')
        if kind=='click_label' and (not isinstance(step['label'],str) or not 1<=len(step['label'])<=100):raise ValueError('Bitte eine konkrete Schaltflächenbeschriftung nennen.')
        if kind=='open':resolve_app(step['app'])
        if kind=='website':website(step['url'])
        if kind in {'move','click'} and any(type(step[k]) not in {int,float} or not math.isfinite(step[k]) or not 0<=step[k]<=1 for k in ['x','y']):raise ValueError('Mauspositionen müssen zwischen 0 und 1 liegen.')
        if kind=='text' and (not isinstance(step['text'],str) or not 1<=len(step['text'])<=2000 or '\x00' in step['text']):raise ValueError('Ungültiger Eingabetext.')
        if kind=='key' and (not isinstance(step['key'],str) or step['key'] not in KEYS or not isinstance(step['modifiers'],list) or len(step['modifiers'])>4 or any(not isinstance(m,str) or m not in FLAGS for m in step['modifiers'])):raise ValueError('Nicht unterstützte Tastenkombination.')
        if kind=='wait' and (type(step['seconds']) not in {int,float} or not math.isfinite(step['seconds']) or not 0<=step['seconds']<=5):raise ValueError('Wartezeit höchstens 5 Sekunden.')
        result.append(dict(step))
    if result[0]['type'] not in {'open','website'}:raise ValueError('Der Ablauf muss mit einer ausdrücklich genannten App beginnen.')
    return result

class Point(ctypes.Structure):_fields_=[('x',ctypes.c_double),('y',ctypes.c_double)]

class MacInput:
    def __init__(self):
        if platform.system()!='Darwin':raise ValueError('Desktop-Steuerung benötigt Jarvis auf deinem Mac.')
        self.active_app=None
        self.last_message=None
        self.cg=None
        self.cancel_event=None
    def ensure_input(self):
        if self.cg is not None:return
        self.cg=ctypes.CDLL('/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics')
        self.cf=ctypes.CDLL('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation')
        self.ax=ctypes.CDLL('/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices')
        self.ax.AXIsProcessTrusted.restype=ctypes.c_bool
        if not self.ax.AXIsProcessTrusted():raise ValueError('macOS: Systemeinstellungen → Datenschutz & Sicherheit → Bedienungshilfen. Erlaube dort deinem Terminal bzw. Python die Steuerung und starte Jarvis neu.')
        self.cg.CGMainDisplayID.restype=ctypes.c_uint32
        display=self.cg.CGMainDisplayID()
        for name in ['CGDisplayPixelsWide','CGDisplayPixelsHigh']:
            function=getattr(self.cg,name);function.argtypes=[ctypes.c_uint32];function.restype=ctypes.c_size_t
        # Mouse events use logical points, not Retina pixel resolution.
        class Size(ctypes.Structure):_fields_=[('width',ctypes.c_double),('height',ctypes.c_double)]
        class Rect(ctypes.Structure):_fields_=[('origin',Point),('size',Size)]
        self.cg.CGDisplayBounds.argtypes=[ctypes.c_uint32];self.cg.CGDisplayBounds.restype=Rect
        bounds=self.cg.CGDisplayBounds(display);self.width=bounds.size.width;self.height=bounds.size.height
        self.cg.CGEventCreateMouseEvent.argtypes=[ctypes.c_void_p,ctypes.c_uint32,Point,ctypes.c_uint32];self.cg.CGEventCreateMouseEvent.restype=ctypes.c_void_p
        self.cg.CGEventCreateKeyboardEvent.argtypes=[ctypes.c_void_p,ctypes.c_uint16,ctypes.c_bool];self.cg.CGEventCreateKeyboardEvent.restype=ctypes.c_void_p
        self.cg.CGEventSetFlags.argtypes=[ctypes.c_void_p,ctypes.c_uint64]
        self.cg.CGEventKeyboardSetUnicodeString.argtypes=[ctypes.c_void_p,ctypes.c_ulong,ctypes.POINTER(ctypes.c_uint16)]
        self.cg.CGEventPost.argtypes=[ctypes.c_uint32,ctypes.c_void_p];self.cf.CFRelease.argtypes=[ctypes.c_void_p]
    def post(self,event):
        if not event:raise ValueError('macOS konnte kein Eingabeereignis erzeugen.')
        try:self.cg.CGEventPost(0,event)
        finally:self.cf.CFRelease(event)
    def execute(self,step):
        kind=step['type']
        if kind not in {'open','website','wait'}:
            self.ensure_input()
            probe=subprocess.run(['/usr/bin/osascript','-l','JavaScript','-e',"ObjC.import('AppKit');ObjC.unwrap($.NSWorkspace.sharedWorkspace.frontmostApplication.bundleIdentifier);"],capture_output=True,text=True,timeout=5)
            if probe.returncode or probe.stdout.strip()!=self.active_app:raise ValueError('Die Ziel-App ist nicht mehr im Vordergrund. Ablauf gestoppt, damit keine Eingabe in eine andere App gelangt.')
        if kind=='open':
            app=resolve_app(step['app'])
            command=['/usr/bin/open','-a',app['path']] if app.get('path') else ['/usr/bin/open','-b',app['bundle']]
            result=subprocess.run(command,capture_output=True,timeout=10)
            if result.returncode and not app.get('path'):
                downloaded=resolve_app(step['app'],True)
                if downloaded.get('path'):
                    app=downloaded;result=subprocess.run(['/usr/bin/open','-a',app['path']],capture_output=True,timeout=10)
            if result.returncode:
                if step['app']=='Spotify':
                    self.execute({'type':'website','url':'https://open.spotify.com'});self.last_message='Spotify als Web-App in Safari geöffnet; die native Spotify-App wurde nicht gefunden.';return
                raise ValueError('Die gewählte App ist nicht installiert oder konnte nicht geöffnet werden.')
            self.active_app=app['bundle']
        elif kind=='website':
            result=subprocess.run(['/usr/bin/open','-b','com.apple.Safari',website(step['url'])],capture_output=True,timeout=10)
            if result.returncode:raise ValueError('Die Webseite konnte in Safari nicht geöffnet werden.')
            self.active_app='com.apple.Safari'
        elif kind=='click_label':
            found=label_point(self.active_app,step['label']);x=found['x']/max(1,self.width-1);y=found['y']/max(1,self.height-1)
            if not 0<=x<=1 or not 0<=y<=1:raise ValueError('Die gefundene Schaltfläche liegt nicht auf dem Hauptbildschirm.')
            self.execute({'type':'click','x':x,'y':y})
        elif kind in {'move','click'}:
            point=Point(step['x']*max(1,self.width-1),step['y']*max(1,self.height-1))
            self.cg.CGEventCreate.argtypes=[ctypes.c_void_p];self.cg.CGEventCreate.restype=ctypes.c_void_p
            self.cg.CGEventGetLocation.argtypes=[ctypes.c_void_p];self.cg.CGEventGetLocation.restype=Point
            event=self.cg.CGEventCreate(None);origin=self.cg.CGEventGetLocation(event);self.cf.CFRelease(event)
            for index in range(1,26):
                if self.cancel_event and self.cancel_event.is_set():return
                t=index/25;t=t*t*(3-2*t);position=Point(origin.x+(point.x-origin.x)*t,origin.y+(point.y-origin.y)*t)
                self.post(self.cg.CGEventCreateMouseEvent(None,5,position,0));time.sleep(.016)
            if kind=='click':
                for event in [1,2]:self.post(self.cg.CGEventCreateMouseEvent(None,event,point,0))
        elif kind in {'key','text'}:
            chunks=[step['text'][i:i+10] for i in range(0,len(step['text']),10)] if kind=='text' else [None]
            for chunk in chunks:
                if self.cancel_event and self.cancel_event.is_set():return
                for down in [True,False]:
                    event=self.cg.CGEventCreateKeyboardEvent(None,KEYS[step['key']] if kind=='key' else 0,down)
                    if not event:raise ValueError('Tastaturereignis nicht verfügbar.')
                    if kind=='text':
                        raw=chunk.encode('utf-16-le');chars=(ctypes.c_uint16*(len(raw)//2)).from_buffer_copy(raw)
                        self.cg.CGEventKeyboardSetUnicodeString(event,len(chars),chars)
                    else:self.cg.CGEventSetFlags(event,sum(FLAGS[m] for m in set(step['modifiers'])))
                    self.post(event)

class Desktop:
    def __init__(self,app,driver=None):
        self.app=app;self.driver=driver or MacInput;self.lock=threading.RLock();self.cancel=threading.Event();self.plan=None;self.thread=None;self.muted=False;self.panel=None;self.panel_state='closed';self.panel_error='';self.panel_started=0;self.model_folder=None;self.model_process=None;self.companion_seen=0;self.commands=[];self.ui_state={};self.snapshot_sequence=0
    def snapshot(self):
        with self.lock:
            if self.panel_state in {'opening','ready'} and self.panel and self.panel.poll() is not None:
                normal=self.panel.poll()==0 and self.panel_state=='ready'
                self.panel_state='closed' if normal else 'failed';self.panel_error='' if normal else 'Das Mac-Fenster wurde beendet. Browser-Pop-up verwenden oder erneut öffnen.'
            if self.panel_state=='opening' and time.monotonic()-self.panel_started>10:self.panel_state='failed';self.panel_error='Das Fenster hat nicht geantwortet. Browser-Pop-up verwenden.'
            self.snapshot_sequence+=1
            return {'sequence':self.snapshot_sequence,'supported':platform.system()=='Darwin','muted':self.muted,'panel':{'state':self.panel_state,'error':self.panel_error},'companion_active':time.monotonic()-self.companion_seen<6,'ui':dict(self.ui_state),'plan':json.loads(json.dumps(self.plan)) if self.plan else None}

    def prepare(self,body):
        if set(body)-{'goal','steps','scene','render'}:raise ValueError('Unbekannte Desktop-Felder.')
        if 'render' in body and type(body['render']) is not bool:raise ValueError('Ungültige Render-Option.')
        goal=body.get('goal','')
        if not isinstance(goal,str) or not 1<=len(goal.strip())<=3000:raise ValueError('Bitte einen konkreten Desktop-Auftrag eingeben.')
        click_label=re.fullmatch(r'(?:klicke?|drücke|betätige)\s+(?:auf\s+)?[„"“]?(.+?)[“"”]?\s+in\s+(.+?)[.!]?$',goal.strip(),re.I)
        if click_label and 'steps' not in body:
            app=resolve_app(click_label[2]);body={**body,'steps':[{'type':'open','app':app['name']},{'type':'wait','seconds':.5},{'type':'click_label','label':click_label[1].strip('„“\"”')}]}
        with self.lock:
            if self.thread and self.thread.is_alive():raise ProviderError('Ein Desktop-Ablauf läuft. Zuerst stoppen oder abwarten.',409)
        note=note_request(goal) if 'steps' not in body and 'scene' not in body else None
        if note is not None:
            if not note['body']:raise ValueError('Was soll in der Notiz stehen? Zum Beispiel: Erstelle eine Notiz: Morgen Milch kaufen.')
            with self.lock:
                if self.thread and self.thread.is_alive():raise ProviderError('Ein Auftrag läuft bereits.',409)
                self.plan={'id':secrets.token_hex(16),'goal':goal.strip(),'kind':'note','note':note,'steps':[{'type':'note','title':note['title'],'text':note['body']}],'state':'review','completed':0,'message':'Eine neue Notiz im Ordner Jarvis anlegen. Noch nicht ausgeführt.','expires':time.time()+600}
                return self.snapshot()
        model_intent=bool(re.search(r'\b3d\b|modellier',goal,re.I) or re.search(r'\bblender\b',goal,re.I) and re.search(r'\b(?:erstell\w*|bau\w*|mach\w*|kreier\w*)\b',goal,re.I))
        scene=validate_scene(body['scene']) if 'scene' in body else recipe(goal) if 'steps' not in body and model_intent else None
        template=scene is not None and 'scene' not in body
        if scene is None and 'steps' not in body and model_intent:scene=self.model_scene(goal)
        if scene:
            with self.lock:
                if self.thread and self.thread.is_alive():raise ProviderError('Ein Desktop-Ablauf läuft bereits.',409)
                self.plan={'id':secrets.token_hex(16),'goal':goal.strip(),'kind':'model','template':template,'render':body.get('render',False),'scene':scene,'steps':[{'type':'model','object':p['name'],'shape':p['shape']} for p in scene['parts']],'state':'review','completed':0,'message':'Vereinfachter Grundkörper-Entwurf, kein exakter Fahrzeugnachbau. Echte 3D-Grundkörper in Blender aufbauen. Eigene neue Szene; vorhandene Dateien werden nicht überschrieben.','expires':time.time()+600}
                return self.snapshot()
        steps=body.get('steps')
        if steps is None:
            move=re.fullmatch(r'(?:bewege|beweg)\s+(?:die\s+)?(?:maus|mauszeiger)\s+(?:nach\s+|zur\s+)?(links|rechts|mitte|oben|unten)\s+in\s+(.+?)[.!?]?',goal.strip(),re.I)
            typing=re.fullmatch(r'(?:tippe|schreibe)\s+["“]?(.*?)["”]?\s+in\s+(.+?)[.!?]?',goal.strip(),re.I)
            if move:
                app=resolve_app(move[2]);x,y={'links':(.25,.5),'rechts':(.75,.5),'mitte':(.5,.5),'oben':(.5,.25),'unten':(.5,.75)}[move[1].casefold()]
                steps=[{'type':'open','app':app['name']},{'type':'wait','seconds':1},{'type':'move','x':x,'y':y}]
            elif typing:
                app=resolve_app(typing[2]);steps=[{'type':'open','app':app['name']},{'type':'wait','seconds':1}]
                if app['bundle']=='com.apple.Notes':steps.append({'type':'key','key':'n','modifiers':['command']})
                steps.append({'type':'text','text':typing[1].strip()})
        if steps is None:
            # Straightforward commands do not depend on a small model guessing JSON.
            command=re.sub(r'^(?:bitte\s+)?(?:öffne|starte|öffnen|starten)\s+(?:mir\s+)?(?:bitte\s+)?(?:die app\s+|die webseite\s+|die seite\s+)?','',goal.strip(),flags=re.I).strip().rstrip('.!?')
            command=re.sub(r'^(?:kannst|könntest|würdest)\s+du\s+(?:mir\s+)?(?:bitte\s+)?','',command,flags=re.I)
            command=re.sub(r'\s+(?:öffnen|starten)$','',command,flags=re.I)
            command=re.sub(r'\s+bitte$','',command,flags=re.I)
            web_names={'youtube':'https://www.youtube.com','google':'https://www.google.com','spotify im browser':'https://open.spotify.com','spotify web':'https://open.spotify.com','chatgpt':'https://chatgpt.com','tiktok':'https://www.tiktok.com'}
            if command.casefold() in web_names:steps=[{'type':'website','url':web_names[command.casefold()]}]
            elif re.fullmatch(r'(?:https?://)?[A-Za-z0-9][^\s]*\.[A-Za-z]{2,}(?:[/:?#][^\s]*)?',command):steps=[{'type':'website','url':website(command if '://' in command else 'https://'+command)}]
            else:
                try:app=resolve_app(command);steps=[{'type':'open','app':app['name']}]
                except ValueError:pass
        if steps is None:
            if self.app.store.settings()['ai_provider'] not in {'llamacpp','ollama'}:raise ValueError('Astra-Desktopplanung benötigt deine lokale Text-KI. Kein externer KI-Dienst wird verwendet.')
            instruction='Erstelle nur JSON: {"steps":[...]}. Maximal 12 Schritte, erster Schritt open. Apps: '+', '.join(app_catalog())[:1200]+'. Erlaubt: {"type":"open","app":"Notizen"}, {"type":"wait","seconds":1}, {"type":"key","key":"n","modifiers":["command"]}, {"type":"text","text":"Hallo"}, {"type":"click_label","label":"Speichern"}. Benannte Schaltflächen werden vor dem Klick in der echten App-Oberfläche gesucht; bei keinem eindeutigen Treffer wird gestoppt. Keine Shell, kein Code, keine erfundenen Koordinaten. Nur einfache App-Aufgaben. Bei komplexen 3D-/Bildaufgaben: {"unsupported":true}. Du siehst keinen Bildschirm. Auftrag: '+goal
            result=self.app.selected_client().chat(instruction,conversation='astra-desktop-plan')
            raw=result.get('reply','').strip()
            if raw.startswith('```'):raw=raw.split('\n',1)[-1].rsplit('```',1)[0].strip()
            try:data=json.loads(raw)
            except (ValueError,TypeError):raise ValueError('Die kleine KI hat keinen ausführbaren Ablauf geliefert. Nichts wurde ausgeführt. Beschreibe eine einfachere App-Aufgabe oder bearbeite einen Ablauf selbst.') from None
            if not isinstance(data,dict) or set(data)!={'steps'}:raise ValueError('Dieser Auftrag ist mit der vorhandenen lokalen KI nicht zuverlässig planbar. Nichts wurde ausgeführt; freie 3D-Modellierung und Bildnachbau sind noch nicht unterstützt.')
            steps=data['steps']
            if isinstance(steps,list) and any(isinstance(s,dict) and s.get('type') in {'click','move'} for s in steps):raise ValueError('Unbeobachtete Mauskoordinaten der Text-KI werden nicht ausgeführt. Positionen bitte selbst im Ablauf festlegen.')
        steps=validate_steps(steps)
        with self.lock:
            if self.thread and self.thread.is_alive():raise ProviderError('Ein Desktop-Ablauf läuft bereits.',409)
            self.plan={'id':secrets.token_hex(16),'goal':goal.strip(),'steps':steps,'state':'review','completed':0,'message':'Ablauf prüfen. Er sieht den Bildschirm nicht und bestätigt kein fertiges Arbeitsergebnis.','expires':time.time()+600}
            return self.snapshot()
    def start(self,ident):
        with self.lock:
            if not self.plan or self.plan['id']!=ident or self.plan['state']!='review' or time.time()>self.plan['expires']:raise ValueError('Dieser Ablauf ist abgelaufen oder wurde bereits gestartet.')
            driver=None if self.plan.get('kind') in {'model','note'} else self.driver()
            if self.plan.get('kind')=='model':self.blender_binary() # Validate before starting.
            if driver is not None and isinstance(driver,MacInput):
                driver.cancel_event=self.cancel
                if any(step['type'] not in {'open','website','wait'} for step in self.plan['steps']):driver.ensure_input()
            self.start_delay=.2 if len(self.plan['steps'])==1 and self.plan['steps'][0]['type'] in {'open','website'} else 3
            self.model_folder=None;self.cancel.clear();self.plan.update(events=[],active_step=None,state='running',message='Öffnen angefordert.' if self.start_delay<1 else 'Start in 3 Sekunden. Aktionen stoppen beendet den Ablauf; Reden stoppen lässt ihn weiterlaufen.')
            self.thread=threading.Thread(target=self._run,args=(driver,),daemon=True);self.thread.start();return self.snapshot()
    def _run(self,driver):
        try:
            if self.cancel.wait(self.start_delay):return
            if self.plan.get('kind')=='note':
                result=create_note(**self.plan['note'])
                with self.lock:self.plan.update(state='done',completed=1,message=result['message'],note_id=result['id'])
                return
            if self.plan.get('kind')=='model':
                self._run_model();return
            for index,step in enumerate(self.plan['steps']):
                if self.cancel.is_set():break
                with self.lock:
                    self.plan['active_step']=index
                    self.plan['events'].append({'step':index+1,'state':'running','type':step['type']})
                if step['type']=='wait':self.cancel.wait(step['seconds'])
                else:driver.execute(step)
                if self.cancel.is_set():break
                with self.lock:
                    self.plan['completed']+=1;self.plan['events'].append({'step':index+1,'state':'done','type':step['type']});self.plan['active_step']=None
                if self.cancel.wait(.35):break
            with self.lock:self.plan.update(state='stopped' if self.cancel.is_set() else 'done',message='Gestoppt.' if self.cancel.is_set() else getattr(driver,'last_message',None) or 'Eingabeschritte ausgeführt. Das Ergebnis wurde nicht visuell überprüft.')
        except Exception as error:
            with self.lock:
                self.plan.setdefault('events',[]).append({'state':'error','message':str(error)[:500]});self.plan.update(state='stopped' if self.cancel.is_set() else 'error',message=str(error)[:500])
        finally:
            with self.lock:
                if self.plan['state']=='running':self.plan.update(state='stopped',message='Gestoppt.')
    def stop(self):
        self.cancel.set()
        if self.model_folder:
            try:(self.model_folder/'cancel').touch(mode=0o600)
            except FileNotFoundError:pass
        with self.lock:
            if self.plan and self.plan['state']=='review':self.plan.update(state='stopped',message='Verworfen.')
            return self.snapshot()
    def speech(self,muted):
        if type(muted) is not bool:raise ValueError('Ungültiger Sprachstatus.')
        with self.lock:self.muted=muted;return self.snapshot()
    def model_scene(self,goal):
        settings=self.app.store.settings();provider=settings['ai_provider']
        if provider not in {'llamacpp','ollama'}:raise ValueError('Für freie 3D-Entwürfe deine lokale KI auswählen. Kein externer KI-Dienst wird verwendet.')
        example={'name':'Entwurf','parts':[{'name':'Körper','shape':'cube','location':[0,0,1],'scale':[1,1,1],'rotation':[0,0,0],'color':[.2,.5,.8]}]}
        system='Return ONLY a JSON scene like '+json.dumps(example)+'. Make a simplified recognizable low-poly object from at most 8 primitives. Allowed shapes: cube, sphere, cylinder, cone, torus. Every part requires name, shape, location[x,y,z], scale[x,y,z] positive, rotation[x,y,z] radians and color[r,g,b] 0..1. Z is up. No Python, no tools, no explanations. Coordinates -100..100, scales .01..30. If impossible return {"unsupported":true}.'
        messages=[{'role':'system','content':system},{'role':'user','content':goal}]
        if provider=='llamacpp':
            data=self.app.llamacpp.endpoint_transport('/v1/chat/completions',{'messages':messages,'stream':False,'max_tokens':1400,'temperature':.15,'response_format':{'type':'json_object'}})
            try:raw=data['choices'][0]['message']['content']
            except (KeyError,IndexError,TypeError):raise ValueError('Die lokale KI hat keinen 3D-Entwurf geliefert.') from None
        else:
            data=self.app.local_ai.transport('/api/chat',{'model':settings['local_model'],'messages':messages,'format':'json','stream':False,'options':{'num_predict':1400,'temperature':.15}})
            raw=data.get('message',{}).get('content','')
        try:return validate_scene(json.loads(raw))
        except (ValueError,TypeError):raise ValueError('Die kleine KI konnte keinen gültigen Grundkörper-Entwurf erstellen. Versuche zum Beispiel Auto, Haus, Tisch, Stuhl, Rakete oder Roboter. Nichts wurde ausgeführt.') from None
    def blender_binary(self):
        candidates=[Path('/Applications/Blender.app/Contents/MacOS/Blender'),Path.home()/'Applications/Blender.app/Contents/MacOS/Blender']
        for candidate in candidates:
            if candidate.is_file():return str(candidate)
        if platform.system()=='Darwin':
            entry=resolve_app('Blender',True)
            if entry.get('path'):
                binary=Path(entry['path'])/'Contents/MacOS/Blender'
                if binary.is_file():return str(binary)
        if platform.system()!='Darwin' and shutil.which('blender'):return shutil.which('blender')
        raise ValueError('Blender wurde nicht gefunden. Blender muss installiert sein; es wird nichts automatisch heruntergeladen.')
    def _run_model(self):
        folder=self.app.store.data_dir/'models'/self.plan['id'];folder.parent.mkdir(exist_ok=True,mode=0o700)
        self.model_folder=folder
        if self.cancel.is_set():return
        write_scene(folder,self.plan['scene'])
        command=[self.blender_binary(),'--factory-startup','--python',str(Path(__file__).with_name('blender_scene.py')),'--',str(folder)]
        with (folder/'blender.log').open('w') as log:
            self.model_process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
        deadline=time.monotonic()+90
        while time.monotonic()<deadline:
            if self.cancel.is_set():
                (folder/'cancel').touch(mode=0o600)
                with self.lock:self.plan.update(state='stopped',message='Modellierung gestoppt. Weitere Objekte werden nicht hinzugefügt.')
                return
            try:
                data=json.loads((folder/'progress.json').read_text())
                with self.lock:self.plan.update(completed=min(len(self.plan['steps']),int(data['completed'])),message=data['message'])
                if data['state']=='done':
                    output=folder/'Astra-Modell.blend'
                    if not output.is_file() or output.stat().st_size<100 or not output.read_bytes()[:7]==b'BLENDER':raise ValueError('Blender hat keine gültige Modelldatei gespeichert.')
                    if self.plan.get('render'):self.render_model(folder,output)
                    with self.lock:self.plan.update(state='stopped' if self.cancel.is_set() else 'done',message='Gestoppt.' if self.cancel.is_set() else 'Echtes Blender-Modell gespeichert: '+str(output),artifact=str(output),rendered=(folder/'Vorschau.png').is_file())
                    return
                if data['state'] in {'error','stopped'}:raise ValueError(data['message'])
            except (FileNotFoundError,json.JSONDecodeError):pass
            if self.model_process.poll() is not None:
                try:final=json.loads((folder/'progress.json').read_text())
                except (OSError,ValueError):final={}
                if final.get('state')=='done':continue
                raise ValueError('Blender wurde vor Abschluss beendet. Diagnose im Auftragsordner: blender.log')
            self.cancel.wait(.15)
        (folder/'cancel').touch(mode=0o600)
        raise ValueError('Blender hat innerhalb von 90 Sekunden keinen Abschluss gemeldet. Modellierung angehalten.')
    def render_model(self,folder,output):
        with self.lock:self.plan['message']='Blender rendert ein echtes Vorschaubild …'
        with (folder/'render.log').open('w') as log:
            process=subprocess.Popen([self.blender_binary(),'--background',str(output),'--python',str(Path(__file__).with_name('render_scene.py')),'--',str(folder)],stdout=log,stderr=subprocess.STDOUT)
        deadline=time.monotonic()+180
        while process.poll() is None:
            if self.cancel.wait(.15) or time.monotonic()>deadline:
                process.terminate()
                try:process.wait(timeout=3)
                except subprocess.TimeoutExpired:process.kill();process.wait()
                if self.cancel.is_set():return
                raise ValueError('Rendering hat zu lange gebraucht. Modelldatei bleibt im Auftragsordner.')
        if process.returncode or not (folder/'Vorschau.png').is_file():raise ValueError('Rendering fehlgeschlagen; Details stehen im Auftragsordner in render.log.')
    def model_file(self):
        with self.lock:
            artifact=self.plan.get('artifact') if self.plan and self.plan.get('state')=='done' else None
        if not artifact:raise ValueError('Noch kein abgeschlossenes Blender-Modell verfügbar.')
        path=Path(artifact);root=self.app.store.data_dir/'models'
        if not path.resolve().is_relative_to(root.resolve()) or path.is_symlink() or not path.is_file() or path.stat().st_size>20000000:raise ValueError('Ungültige Modelldatei.')
        data=path.read_bytes()
        if not data.startswith(b'BLENDER'):raise ValueError('Keine Blender-Modelldatei.')
        return data
    def companion(self,body):
        if set(body)-{'command','text'}:raise ValueError('Ungültiger Begleitfenster-Auftrag.')
        with self.lock:
            self.companion_seen=time.monotonic()
            if body:
                command=body.get('command')
                if command not in {'talk','end','send'}:raise ValueError('Unbekannte Gesprächsaktion.')
                text=body.get('text','')
                if not isinstance(text,str) or len(text)>6000 or (command=='send' and not text.strip()):raise ValueError('Bitte einen kurzen Auftrag eingeben.')
                if len(self.commands)>=8:raise ValueError('Bitte den letzten Auftrag abwarten.')
                self.commands.append({'command':command,'text':text})
            return {'ok':True,'ui':dict(self.ui_state)}
    def sync_ui(self,body):
        if set(body)-{'busy','mode','conversation','recording','consented','error','reply'}:raise ValueError('Ungültiger Gesprächsstatus.')
        if type(body.get('busy')) is not bool or type(body.get('conversation')) is not bool or body.get('mode') not in {'idle','listening','thinking','speaking','error'}:raise ValueError('Ungültiger Gesprächsstatus.')
        with self.lock:
            self.ui_state={'busy':body['busy'],'mode':body['mode'],'conversation':body['conversation'],'recording':body.get('recording') is True,'consented':body.get('consented') is True,'error':str(body.get('error',''))[:300],'reply':str(body.get('reply',''))[:3000],'seen':time.time()}
            index=next((i for i,c in enumerate(self.commands) if not body['busy'] or c['command']!='send'),None)
            commands=[] if index is None else [self.commands.pop(index)]
            return {'commands':commands}
    def panel_ready(self):
        with self.lock:self.panel_state='ready';self.panel_error='';return {'ok':True}
    def open_panel(self,url):
        if platform.system()!='Darwin':raise ValueError('Das schwebende Astra-Fenster benötigt macOS. Das Browser-Pop-up funktioniert auch hier.')
        with self.lock:
            if self.panel and self.panel.poll() is None and self.panel_state in {'opening','ready'}:return {'ok':True,'state':self.panel_state}
            if self.panel and self.panel.poll() is None:self.panel.terminate()
            config=self.app.store.data_dir/'astra-panel-url.txt';config.write_text(url+'?native=1#'+self.app.token);config.chmod(0o600)
            script=Path(__file__).with_name('astra_panel.js');logpath=self.app.store.data_dir/'astra-panel.log'
            with logpath.open('w') as log:self.panel=subprocess.Popen(['/usr/bin/osascript','-l','JavaScript',str(script),str(config)],stdout=log,stderr=subprocess.STDOUT)
            logpath.chmod(0o600);self.panel_state='opening';self.panel_started=time.monotonic();self.panel_error=''
            time.sleep(.25)
            if self.panel.poll() is not None:
                self.panel_state='failed';self.panel_error='macOS konnte das Fenster nicht starten. Nutze das Browser-Pop-up. Details stehen lokal in astra-panel.log.'
                raise ValueError(self.panel_error)
            return {'ok':True,'state':'opening','message':'Mac-Fenster startet; die Oberfläche bestätigt das Laden separat.'}
