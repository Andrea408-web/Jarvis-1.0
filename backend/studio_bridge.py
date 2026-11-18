"""Explicit local Roblox Studio bridge; only bounded starter scenes, never model Lua."""
import copy
import hmac
import json
import math
import os
import re
import secrets
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path


def scene(body):
    if not isinstance(body,dict) or set(body)!={'name','platforms','coins'} or not isinstance(body['name'],str) or not 1<=len(body['name'].strip())<=80 or type(body['platforms']) is not int or not 3<=body['platforms']<=20 or type(body['coins']) is not bool:raise ValueError('Bitte Spielname, 3–20 Plattformen und Münzen auswählen.')
    parts=[{'kind':'spawn','position':[0,1,0],'size':[14,1,14]}]
    for n in range(1,body['platforms']+1):
        x=math.sin(n*.8)*7;y=1+n*.7;z=-n*9
        parts.append({'kind':'platform','position':[round(x,2),round(y,2),z],'size':[8,1,7]})
        if body['coins']:parts.append({'kind':'coin','position':[round(x,2),round(y+3,2),z],'size':[1.7,1.7,1.7]})
    last=parts[-1]['position'];parts.append({'kind':'goal','position':[last[0],1+body['platforms']*.7+1.2,-body['platforms']*9],'size':[5,2,5]})
    return {'name':body['name'].strip(),'parts':parts}

class StudioBridge:
    def __init__(self,directory=None):
        self.lock=threading.RLock();self.sessions={};self.server=None;self.suspended=False
        self.config=Path(directory)/'studio-link.json' if directory is not None else None;self.saved=None
        self.config_error=None
        if self.config and self.config.exists():
            try:
                if self.config.is_symlink() or self.config.stat().st_size>4096:raise ValueError()
                value=json.loads(self.config.read_text())
                if not isinstance(value,dict) or set(value)!={'port','key','version'} or value['version']!=2 or type(value['port']) is not int or not 1<=value['port']<=65535 or not isinstance(value['key'],str) or not re.fullmatch(r'[A-Za-z0-9_-]{43}',value['key']):raise ValueError()
                self.saved=value
            except (OSError,ValueError,TypeError):self.config_error='Gespeicherte Studio-Verbindung ungültig. Jarvis bleibt nutzbar; Plugin v2 bitte neu einrichten.'
    def reconnect(self,owner):
        if not self.saved:raise ValueError('Noch keine dauerhafte Verbindung eingerichtet. Bitte einmal das neue Studio-Plugin installieren.')
        self.prepare(owner)
        return self.status(owner)
    def prepare(self,owner):
        with self.lock:
            if self.config and self.config.is_symlink():raise ValueError('Die Studio-Konfiguration ist eine Verknüpfung. Bitte prüfen; es wird nichts überschrieben.')
            if self.server is None:
                bridge=self
                class Handler(BaseHTTPRequestHandler):
                    def log_message(self,*args):pass
                    def handle_request(self):
                        self.connection.settimeout(5)
                        try:
                            if self.headers.get('Host')!='127.0.0.1:'+str(self.server.server_port) or self.headers.get('Origin') or self.headers.get('Sec-Fetch-Site')=='cross-site':raise ValueError('Nur lokales Studio.')
                            key=self.headers.get('X-Jarvis-Studio','')
                            if self.command=='GET' and self.path=='/poll':data=bridge.poll(key,2 if self.headers.get('X-Jarvis-Plugin-Version')=='2' else 1,self.headers.get('X-Jarvis-Place','')[:120])
                            elif self.command=='POST' and self.path=='/result':
                                size=int(self.headers.get('Content-Length','0'))
                                if not 1<=size<=4000 or self.headers.get('Transfer-Encoding') or self.headers.get_content_type()!='application/json':raise ValueError('Ungültiges Ergebnis.')
                                data=bridge.result(key,json.loads(self.rfile.read(size)))
                            else:raise ValueError('Unbekannte Aktion.')
                            status=200
                        except (ValueError,TypeError,KeyError):data={'error':'Studio-Brücke nicht freigegeben oder abgelaufen.'};status=403
                        raw=json.dumps(data).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(raw)
                    do_GET=do_POST=handle_request
                try:self.server=ThreadingHTTPServer(('127.0.0.1',self.saved['port'] if self.saved else 0),Handler)
                except OSError:raise ValueError('Der gespeicherte lokale Studio-Port ist belegt. Bitte die andere Jarvis-Instanz beenden; die Verbindung wurde nicht ersetzt.') from None
                threading.Thread(target=self.server.serve_forever,daemon=True,name='jarvis-studio-bridge').start()
            old=self.sessions.get(owner)
            if old and old['pending'] and old['pending']['status'] in {'queued','building'}:raise ValueError('Bitte den laufenden Studio-Auftrag erst abschließen oder die Brücke trennen.')
            if self.config and any(s['pending'] and s['pending']['status'] in {'queued','building'} for s in self.sessions.values()):raise ValueError('Studio baut bereits. Verbindung erst nach Abschluss wechseln.')
            key=self.saved['key'] if self.config and self.saved else secrets.token_urlsafe(32)
            if self.config:self.sessions.clear()
            self.suspended=False
            self.sessions[owner]={'key':key,'expires':float('inf') if self.config else time.monotonic()+8*3600,'last_seen':0,'pending':None,'plugin_version':0,'place':''}
            if self.config:
                value={'version':2,'key':key,'port':self.server.server_port};self.config.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
                temp=self.config.with_name('studio-link.'+secrets.token_hex(5)+'.tmp')
                fd=os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
                with os.fdopen(fd,'w') as f:json.dump(value,f)
                temp.replace(self.config);self.saved=value;self.config_error=None
            source=(Path(__file__).resolve().parent.parent/'frontend/roblox-plugin.lua').read_text().replace('__BRIDGE_URL__','http://127.0.0.1:'+str(self.server.server_port)).replace('__BRIDGE_KEY__',key)
            base=Path(__file__).resolve().parent.parent/'frontend'
            source=source.replace('__HERO_CLIENT__',(base/'roblox-hero-client.lua').read_text()).replace('__HERO_SERVER__',(base/'roblox-hero-server.lua').read_text())
            xml='<roblox version="4"><Item class="Script" referent="RBX0"><Properties><string name="Name">JarvisStudio</string><ProtectedString name="Source"><![CDATA['+source.replace(']]>',']]]]><![CDATA[>')+']]></ProtectedString></Properties></Item></roblox>'
            return {'filename':'JarvisStudio.rbxmx','plugin':xml,'message':'Studio-Plugin v2 einmalig installieren oder die alte Datei ersetzen. Danach bleiben Port und Kennung lokal gespeichert; nach einem Jarvis-Neustart genügt Wiederverbinden. In Studio HTTP-Zugriff auf 127.0.0.1 und das Einfügen der mitgelieferten Spielskripte erlauben.'}
    def _session(self,key):
        if not isinstance(key,str) or len(key)>100:raise ValueError('Ungültiger Schlüssel.')
        for value in self.sessions.values():
            if hmac.compare_digest(value['key'],key) and value['expires']>time.monotonic():return value
        raise ValueError('Brücke abgelaufen.')
    def status(self,owner):
        with self.lock:
            if self.saved and not self.sessions and not self.suspended:self.prepare(owner)
            s=self.sessions.get(owner)
            return {'diagnostic':self.config_error,'reusable':bool(self.saved),'plugin_version':s.get('plugin_version',0) if s else 0,'place':s.get('place','') if s else '', 'prepared':bool(s and s['expires']>time.monotonic()),'connected':bool(s and s['expires']>time.monotonic() and s['last_seen']>0 and time.monotonic()-s['last_seen']<12),'job':copy.deepcopy(s['pending']) if s else None}
    def queue(self,owner,body):
        if isinstance(body,dict) and body.get('kind')=='hero-city':
            from .roblox_plan import city
            if set(body)!={'kind','name','buildings'}:raise ValueError('Ungültiger Stadt-Bauplan.')
            plan=city({k:v for k,v in body.items() if k!='kind'})
        else:plan=scene(body)
        return self.queue_plan(owner,plan)
    def queue_plan(self,owner,plan):
        with self.lock:
            connected=self.status(owner);s=self.sessions.get(owner)
            if not s or not connected['connected']:raise ValueError('Roblox Studio ist nicht verbunden. Im Reiter Roblox Studio das vorhandene Plugin wiederverbinden oder einmalig v2 installieren.')
            if plan.get('requires_version',1)>s.get('plugin_version',1):raise ValueError('Für die Superhelden-Stadt ist einmalig Studio-Plugin v2 nötig. Das alte Plugin kann nur den Parcours bauen.')
            if s['pending'] and s['pending']['status'] in {'queued','building'}:raise ValueError('Studio baut bereits einen Auftrag. Bitte abwarten.')
            s['pending']={'id':uuid.uuid4().hex,'status':'queued','scene':copy.deepcopy(plan),'message':'An Studio übergeben; noch nicht gebaut.','count':0};return self.status(owner)
    def poll(self,key,version=1,place=''):
        with self.lock:
            s=self._session(key);s['last_seen']=time.monotonic();s['plugin_version']=version;s['place']=place;j=s['pending']
            if j and j['status']=='queued':j['status']='building';return {'job':copy.deepcopy(j)}
            return {'job':None}
    def result(self,key,body):
        with self.lock:
            s=self._session(key);j=s['pending']
            if j and j['status']=='cancelled' and isinstance(body,dict) and body.get('id')==j['id']:return {'ok':False,'cancelled':True}
            if not isinstance(body,dict) or not {'id','status','count','message'}<=set(body) or set(body)-{'id','status','count','message','gameplay_ready'} or not j or body['id']!=j['id'] or j['status']!='building' or body['status'] not in {'progress','done','error'} or type(body['count']) is not int or not j['count']<=body['count']<=len(j['scene']['parts']) or not isinstance(body['message'],str) or len(body['message'])>500:raise ValueError('Ungültiges Studio-Ergebnis.')
            if body['status']=='done' and body['count']!=len(j['scene']['parts']):raise ValueError('Studio hat noch nicht alle Teile bestätigt.')
            if body['status']=='done' and j['scene'].get('requires_version')==2 and body.get('gameplay_ready') is not True:raise ValueError('Die Spielskripte wurden noch nicht bestätigt.')
            j.update(status='building' if body['status']=='progress' else body['status'],count=body['count'],message=body['message']);s['last_seen']=time.monotonic();return {'ok':True}
    def disconnect(self,owner):
        with self.lock:self.sessions.pop(owner,None);self.suspended=True
        return {'prepared':False,'connected':False,'job':None}
    def cancel_job(self,owner,key):
        with self.lock:
            s=self.sessions.get(owner);j=s['pending'] if s else None
            if not j or j['id']!=key:raise ValueError('Studio-Auftrag nicht gefunden.')
            if j['status'] in {'queued','building'}:j.update(status='cancelled',message='Bau gestoppt. Bereits erstellte Teile bleiben im Studio stehen.')
            return self.status(owner)
    def stop(self):
        if self.server:self.server.shutdown();self.server.server_close();self.server=None
