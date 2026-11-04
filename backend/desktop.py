"""Local, reviewable desktop input plans. No shell scripts or remote AI fallback."""
import ctypes
import json
import math
import platform
import re
import secrets
import subprocess
import threading
import time
from pathlib import Path

from .providers import ProviderError

APPS={'Safari':'com.apple.Safari','Finder':'com.apple.finder','Notizen':'com.apple.Notes','Kalender':'com.apple.iCal','Rechner':'com.apple.calculator','Musik':'com.apple.Music','Blender':'org.blenderfoundation.blender'}
KEYS={'enter':36,'tab':48,'escape':53,'space':49,'backspace':51,'left':123,'right':124,'down':125,'up':126,'a':0,'c':8,'v':9,'s':1,'z':6,'n':45,'o':31,'f':3}
FLAGS={'command':1<<20,'shift':1<<17,'option':1<<19,'control':1<<18}

def validate_steps(steps):
    if not isinstance(steps,list) or not 1<=len(steps)<=12:raise ValueError('Ein Ablauf braucht 1–12 überprüfbare Schritte.')
    result=[]
    for step in steps:
        if not isinstance(step,dict):raise ValueError('Ungültiger Desktop-Schritt.')
        kind=step.get('type')
        fields={'open':{'type','app'},'move':{'type','x','y'},'click':{'type','x','y'},'text':{'type','text'},'key':{'type','key','modifiers'},'wait':{'type','seconds'}}
        if not isinstance(kind,str) or kind not in fields or set(step)!=fields[kind]:raise ValueError('Nicht unterstützter Desktop-Schritt; kein Programmcode wird ausgeführt.')
        if kind=='open' and (not isinstance(step['app'],str) or step['app'] not in APPS):raise ValueError('Diese App ist nicht für Desktop-Abläufe eingetragen.')
        if kind in {'move','click'} and any(type(step[k]) not in {int,float} or not math.isfinite(step[k]) or not 0<=step[k]<=1 for k in ['x','y']):raise ValueError('Mauspositionen müssen zwischen 0 und 1 liegen.')
        if kind=='text' and (not isinstance(step['text'],str) or not 1<=len(step['text'])<=2000 or '\x00' in step['text']):raise ValueError('Ungültiger Eingabetext.')
        if kind=='key' and (not isinstance(step['key'],str) or step['key'] not in KEYS or not isinstance(step['modifiers'],list) or len(step['modifiers'])>4 or any(not isinstance(m,str) or m not in FLAGS for m in step['modifiers'])):raise ValueError('Nicht unterstützte Tastenkombination.')
        if kind=='wait' and (type(step['seconds']) not in {int,float} or not math.isfinite(step['seconds']) or not 0<=step['seconds']<=5):raise ValueError('Wartezeit höchstens 5 Sekunden.')
        result.append(dict(step))
    if result[0]['type']!='open':raise ValueError('Der Ablauf muss mit einer ausdrücklich genannten App beginnen.')
    return result

class Point(ctypes.Structure):_fields_=[('x',ctypes.c_double),('y',ctypes.c_double)]

class MacInput:
    def __init__(self):
        if platform.system()!='Darwin':raise ValueError('Desktop-Steuerung benötigt Jarvis auf deinem Mac.')
        self.active_app=None
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
        if kind not in {'open','wait'}:
            probe=subprocess.run(['/usr/bin/osascript','-l','JavaScript','-e',"ObjC.import('AppKit');ObjC.unwrap($.NSWorkspace.sharedWorkspace.frontmostApplication.bundleIdentifier);"],capture_output=True,text=True,timeout=5)
            if probe.returncode or probe.stdout.strip()!=self.active_app:raise ValueError('Die Ziel-App ist nicht mehr im Vordergrund. Ablauf gestoppt, damit keine Eingabe in eine andere App gelangt.')
        if kind=='open':
            result=subprocess.run(['/usr/bin/open','-b',APPS[step['app']]],capture_output=True,timeout=10)
            if result.returncode:raise ValueError('Die gewählte App ist nicht installiert oder konnte nicht geöffnet werden.')
            self.active_app=APPS[step['app']]
        elif kind in {'move','click'}:
            point=Point(step['x']*max(1,self.width-1),step['y']*max(1,self.height-1))
            self.post(self.cg.CGEventCreateMouseEvent(None,5,point,0))
            if kind=='click':
                for event in [1,2]:self.post(self.cg.CGEventCreateMouseEvent(None,event,point,0))
        elif kind in {'key','text'}:
            chunks=[step['text'][i:i+10] for i in range(0,len(step['text']),10)] if kind=='text' else [None]
            for chunk in chunks:
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
        self.app=app;self.driver=driver or MacInput;self.lock=threading.RLock();self.cancel=threading.Event();self.plan=None;self.thread=None;self.muted=False;self.panel=None
    def snapshot(self):
        with self.lock:return {'supported':platform.system()=='Darwin','muted':self.muted,'plan':json.loads(json.dumps(self.plan)) if self.plan else None}
    def prepare(self,body):
        if set(body)-{'goal','steps'}:raise ValueError('Unbekannte Desktop-Felder.')
        goal=body.get('goal','')
        if not isinstance(goal,str) or not 1<=len(goal.strip())<=3000:raise ValueError('Bitte einen konkreten Desktop-Auftrag eingeben.')
        with self.lock:
            if self.thread and self.thread.is_alive():raise ProviderError('Ein Desktop-Ablauf läuft. Zuerst stoppen oder abwarten.',409)
        steps=body.get('steps')
        if steps is None:
            # Straightforward commands do not depend on a small model guessing JSON.
            match=re.fullmatch(r'(?:bitte\s+)?(?:öffne|starte)\s+(?:die app\s+)?('+ '|'.join(APPS) +r')[.!]?',goal.strip(),re.I)
            if match:
                app=next(a for a in APPS if a.casefold()==match[1].casefold())
                steps=[{'type':'open','app':app}]
        if steps is None:
            if self.app.store.settings()['ai_provider'] not in {'llamacpp','ollama'}:raise ValueError('Astra-Desktopplanung benötigt deine lokale Text-KI. Kein externer KI-Dienst wird verwendet.')
            instruction='Erstelle nur JSON: {"steps":[...]}. Maximal 12 Schritte, erster Schritt open. Apps: '+', '.join(APPS)+'. Erlaubt: {"type":"open","app":"Notizen"}, {"type":"wait","seconds":1}, {"type":"key","key":"n","modifiers":["command"]}, {"type":"text","text":"Hallo"}. Keine Shell, kein Code, keine erfundenen Koordinaten. Nur einfache App-Aufgaben. Bei komplexen 3D-/Bildaufgaben: {"unsupported":true}. Du siehst keinen Bildschirm. Auftrag: '+goal
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
            driver=self.driver() # Permission failure leaves review intact.
            self.cancel.clear();self.plan.update(state='running',message='Start in 3 Sekunden. Aktionen stoppen beendet den Ablauf; Reden stoppen lässt ihn weiterlaufen.')
            self.thread=threading.Thread(target=self._run,args=(driver,),daemon=True);self.thread.start();return self.snapshot()
    def _run(self,driver):
        try:
            if self.cancel.wait(3):return
            for step in self.plan['steps']:
                if self.cancel.is_set():break
                if step['type']=='wait':self.cancel.wait(step['seconds'])
                else:driver.execute(step)
                if self.cancel.is_set():break
                with self.lock:self.plan['completed']+=1
                if self.cancel.wait(.35):break
            with self.lock:self.plan.update(state='stopped' if self.cancel.is_set() else 'done',message='Gestoppt.' if self.cancel.is_set() else 'Eingabeschritte ausgeführt. Das Ergebnis wurde nicht visuell überprüft.')
        except Exception as error:
            with self.lock:self.plan.update(state='error',message=str(error)[:500])
        finally:
            with self.lock:
                if self.plan['state']=='running':self.plan.update(state='stopped',message='Gestoppt.')
    def stop(self):
        self.cancel.set()
        with self.lock:
            if self.plan and self.plan['state']=='review':self.plan.update(state='stopped',message='Verworfen.')
            return self.snapshot()
    def speech(self,muted):
        if type(muted) is not bool:raise ValueError('Ungültiger Sprachstatus.')
        with self.lock:self.muted=muted;return self.snapshot()
    def open_panel(self,url):
        if platform.system()!='Darwin':raise ValueError('Das schwebende Astra-Fenster benötigt macOS.')
        with self.lock:
            if self.panel and self.panel.poll() is None:return {'ok':True}
            config=self.app.store.data_dir/'astra-panel-url.txt';config.write_text(url+'#'+self.app.token);config.chmod(0o600)
            script=Path(__file__).with_name('astra_panel.js')
            self.panel=subprocess.Popen(['/usr/bin/osascript','-l','JavaScript',str(script),str(config)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            return {'ok':True,'message':'Schwebendes Fenster angefordert. macOS-Ausführung auf diesem Gerät prüfen.'}
