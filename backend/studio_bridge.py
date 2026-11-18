"""Explicit local Roblox Studio bridge; only bounded starter scenes, never model Lua."""
import copy
import hmac
import json
import math
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
    def __init__(self):self.lock=threading.RLock();self.sessions={};self.server=None
    def prepare(self,owner):
        with self.lock:
            if self.server is None:
                bridge=self
                class Handler(BaseHTTPRequestHandler):
                    def log_message(self,*args):pass
                    def handle_request(self):
                        self.connection.settimeout(5)
                        try:
                            if self.headers.get('Host')!='127.0.0.1:'+str(self.server.server_port) or self.headers.get('Origin') or self.headers.get('Sec-Fetch-Site')=='cross-site':raise ValueError('Nur lokales Studio.')
                            key=self.headers.get('X-Jarvis-Studio','')
                            if self.command=='GET' and self.path=='/poll':data=bridge.poll(key)
                            elif self.command=='POST' and self.path=='/result':
                                size=int(self.headers.get('Content-Length','0'))
                                if not 1<=size<=4000 or self.headers.get('Transfer-Encoding') or self.headers.get_content_type()!='application/json':raise ValueError('Ungültiges Ergebnis.')
                                data=bridge.result(key,json.loads(self.rfile.read(size)))
                            else:raise ValueError('Unbekannte Aktion.')
                            status=200
                        except (ValueError,TypeError,KeyError):data={'error':'Studio-Brücke nicht freigegeben oder abgelaufen.'};status=403
                        raw=json.dumps(data).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(raw)
                    do_GET=do_POST=handle_request
                self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
                threading.Thread(target=self.server.serve_forever,daemon=True,name='jarvis-studio-bridge').start()
            old=self.sessions.get(owner)
            if old and old['pending'] and old['pending']['status'] in {'queued','building'}:raise ValueError('Bitte den laufenden Studio-Auftrag erst abschließen oder die Brücke trennen.')
            key=secrets.token_urlsafe(32);self.sessions[owner]={'key':key,'expires':time.monotonic()+8*3600,'last_seen':0,'pending':None}
            source=(Path(__file__).resolve().parent.parent/'frontend/roblox-plugin.lua').read_text().replace('__BRIDGE_URL__','http://127.0.0.1:'+str(self.server.server_port)).replace('__BRIDGE_KEY__',key)
            xml='<roblox version="4"><Item class="Script" referent="RBX0"><Properties><string name="Name">JarvisStudio</string><ProtectedString name="Source"><![CDATA['+source.replace(']]>',']]]]><![CDATA[>')+']]></ProtectedString></Properties></Item></roblox>'
            return {'filename':'JarvisStudio.rbxmx','plugin':xml,'message':'Lokales Plugin für diese Serverlaufzeit vorbereitet. In den lokalen Plugins-Ordner von Roblox Studio legen, Studio neu starten und dem Plugin den HTTP-Zugriff auf 127.0.0.1 erlauben. Kein Plugin-Store nötig.'}
    def _session(self,key):
        if not isinstance(key,str) or len(key)>100:raise ValueError('Ungültiger Schlüssel.')
        for value in self.sessions.values():
            if hmac.compare_digest(value['key'],key) and value['expires']>time.monotonic():return value
        raise ValueError('Brücke abgelaufen.')
    def status(self,owner):
        with self.lock:
            s=self.sessions.get(owner)
            return {'prepared':bool(s and s['expires']>time.monotonic()),'connected':bool(s and s['expires']>time.monotonic() and s['last_seen']>0 and time.monotonic()-s['last_seen']<12),'job':copy.deepcopy(s['pending']) if s else None}
    def queue(self,owner,body):
        plan=scene(body)
        with self.lock:
            s=self.sessions.get(owner)
            if not s or not self.status(owner)['connected']:raise ValueError('Roblox Studio ist noch nicht verbunden. Erst das lokale Plugin einrichten.')
            if s['pending'] and s['pending']['status'] in {'queued','building'}:raise ValueError('Studio baut bereits einen Auftrag. Bitte abwarten.')
            s['pending']={'id':uuid.uuid4().hex,'status':'queued','scene':plan,'message':'An Studio übergeben; noch nicht gebaut.','count':0};return self.status(owner)
    def poll(self,key):
        with self.lock:
            s=self._session(key);s['last_seen']=time.monotonic();j=s['pending']
            if j and j['status']=='queued':j['status']='building';return {'job':copy.deepcopy(j)}
            return {'job':None}
    def result(self,key,body):
        with self.lock:
            s=self._session(key);j=s['pending']
            if not isinstance(body,dict) or set(body)!={'id','status','count','message'} or not j or body['id']!=j['id'] or j['status']!='building' or body['status'] not in {'progress','done','error'} or type(body['count']) is not int or not j['count']<=body['count']<=len(j['scene']['parts']) or not isinstance(body['message'],str) or len(body['message'])>500:raise ValueError('Ungültiges Studio-Ergebnis.')
            if body['status']=='done' and body['count']!=len(j['scene']['parts']):raise ValueError('Studio hat noch nicht alle Teile bestätigt.')
            j.update(status='building' if body['status']=='progress' else body['status'],count=body['count'],message=body['message']);s['last_seen']=time.monotonic();return {'ok':True}
    def disconnect(self,owner):
        with self.lock:self.sessions.pop(owner,None)
        return {'prepared':False,'connected':False,'job':None}
    def stop(self):
        if self.server:self.server.shutdown();self.server.server_close();self.server=None
