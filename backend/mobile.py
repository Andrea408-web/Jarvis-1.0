"""Explicit private-LAN pairing. No public tunnel, account or global trust changes."""
from pathlib import Path
import hashlib,hmac,ipaddress,json,os,plistlib,secrets,ssl,subprocess,threading,time,uuid
from http.cookies import SimpleCookie


class DeviceAuth:
    SESSION_SECONDS=30*24*3600
    def __init__(self,path=None):
        self.lock=threading.Lock();self.ticket=None;self.expires=0;self.sessions={};self.path=Path(path) if path else None
        if self.path and self.path.is_file():
            try:
                data=json.loads(self.path.read_text())
                self.sessions={key:end for key,end in data.items() if isinstance(key,str) and len(key)==64 and isinstance(end,(int,float)) and time.time()<end<=time.time()+self.SESSION_SECONDS}
            except (OSError,ValueError,TypeError,AttributeError):self.sessions={}
    def _save(self):
        if not self.path:return
        self.path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        tmp=self.path.with_suffix('.tmp')
        fd=os.open(tmp,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
        with os.fdopen(fd,'w') as stream:json.dump(self.sessions,stream)
        os.replace(tmp,self.path)
    def revoke(self):
        with self.lock:self.sessions={};self.ticket=None;self._save()
    def issue(self):
        with self.lock:self.ticket=secrets.token_urlsafe(32);self.expires=time.monotonic()+300;return self.ticket
    def pair(self,ticket):
        with self.lock:
            if not isinstance(ticket,str) or not self.ticket or time.monotonic()>self.expires or not hmac.compare_digest(ticket.encode(),self.ticket.encode()):raise ValueError('Kopplung ungültig oder abgelaufen. Bitte am Mac einen neuen QR-Code anzeigen.')
            token=secrets.token_urlsafe(32);self.ticket=None
            self.sessions={key:end for key,end in self.sessions.items() if end>time.time()}
            if len(self.sessions)>=8:self.sessions.pop(next(iter(self.sessions)))
            self.sessions[hashlib.sha256(token.encode()).hexdigest()]=time.time()+self.SESSION_SECONDS;self._save();return token
    def valid(self,header):
        try:
            cookie=SimpleCookie();cookie.load(header or '');token=cookie['jarvis_device'].value
        except Exception:return False
        with self.lock:return self.sessions.get(hashlib.sha256(token.encode()).hexdigest(),0)>time.time()


def private_ip():
    try:
        route=subprocess.run(['/sbin/route','-n','get','default'],capture_output=True,text=True,timeout=5,check=True).stdout
        interface=next(line.split(':',1)[1].strip() for line in route.splitlines() if line.strip().startswith('interface:'))
        import re
        if not re.fullmatch(r'[A-Za-z0-9]{1,16}',interface):raise ValueError()
        value=subprocess.run(['/usr/sbin/ipconfig','getifaddr',interface],capture_output=True,text=True,timeout=5,check=True).stdout.strip()
        address=ipaddress.ip_address(value)
        if address.version!=4 or not address.is_private or address.is_loopback or address.is_link_local:raise ValueError()
        return str(address)
    except (OSError,ValueError,StopIteration,subprocess.SubprocessError):
        raise ValueError('Keine private WLAN-/LAN-Adresse gefunden. Mac und Handy müssen im selben vertrauenswürdigen Heimnetz sein.') from None


def certificates(directory,address,hostname=None):
    address=str(ipaddress.IPv4Address(address));directory=Path(directory);directory.mkdir(parents=True,exist_ok=True,mode=0o700)
    ca=directory/'ca.pem';key=directory/'ca.key';leaf=directory/'server.pem';leafkey=directory/'server.key'
    def run(args):
        try:subprocess.run(['/usr/bin/openssl',*args],capture_output=True,check=True,timeout=20)
        except (OSError,subprocess.SubprocessError):raise ValueError('Die lokalen HTTPS-Zertifikate konnten nicht erstellt werden. Es wurden keine System-Vertrauensregeln verändert.') from None
    if not ca.is_file() or not key.is_file():
        config=directory/'ca.cnf';config.write_text('[req]\ndistinguished_name=dn\nx509_extensions=ca\nprompt=no\n[dn]\nCN=JARVIS privates Heimnetz\n[ca]\nbasicConstraints=critical,CA:true,pathlen:0\nkeyUsage=critical,keyCertSign,cRLSign\n')
        run(['req','-x509','-newkey','rsa:2048','-nodes','-days','1825','-keyout',str(key),'-out',str(ca),'-config',str(config)])
    import re
    if hostname and not re.fullmatch(r'[A-Za-z0-9-]{1,63}\.local',hostname):raise ValueError('Ungültiger lokaler Mac-Name.')
    san=f'IP:{address}'+(',DNS:'+hostname if hostname else '')
    config=directory/'server.cnf';config.write_text(f'basicConstraints=critical,CA:false\nkeyUsage=critical,digitalSignature,keyEncipherment\nextendedKeyUsage=serverAuth\nsubjectAltName={san}\n')
    csr=directory/'server.csr'
    run(['req','-new','-newkey','rsa:2048','-nodes','-keyout',str(leafkey),'-out',str(csr),'-subj','/CN=JARVIS privat'])
    run(['x509','-req','-in',str(csr),'-CA',str(ca),'-CAkey',str(key),'-CAcreateserial','-out',str(leaf),'-days','365','-sha256','-extfile',str(config)])
    key.chmod(0o600);leafkey.chmod(0o600)
    der=ssl.PEM_cert_to_DER_cert(ca.read_text());fingerprint=hashlib.sha256(der).hexdigest()
    profile={'PayloadContent':[{'PayloadType':'com.apple.security.root','PayloadVersion':1,'PayloadIdentifier':'local.jarvis.ca.'+fingerprint[:12],'PayloadUUID':str(uuid.uuid4()),'PayloadDisplayName':'JARVIS privates Heimnetz','PayloadContent':der}],
             'PayloadType':'Configuration','PayloadVersion':1,'PayloadIdentifier':'local.jarvis.profile.'+fingerprint[:12],'PayloadUUID':str(uuid.uuid4()),'PayloadDisplayName':'JARVIS privates Heimnetz','PayloadDescription':'Vertrauen für deinen eigenen JARVIS-Mac. Nur im vertrauenswürdigen Heimnetz installieren; Fingerabdruck am Mac vergleichen. Keine Verwaltung, VPN oder Kamera-Berechtigung wird installiert.'}
    profile_path=directory/'JARVIS-Heimnetz.mobileconfig';profile_path.write_bytes(plistlib.dumps(profile))
    return leaf,leafkey,profile_path,fingerprint


class MobileLink:
    def __init__(self,app):self.app=app;self.server=None;self.auth=DeviceAuth(app.store.data_dir/'mobile'/'devices.json');self.lock=threading.Lock();self.enabled_path=app.store.data_dir/'mobile'/'enabled'
    def resume(self):
        if self.enabled_path.is_file() or self.auth.sessions:return self.start()
        return None
    def start(self):
        import platform
        if platform.system()!='Darwin':raise ValueError('Die einfache Handykopplung wird auf dem Mac gestartet. Hier ist nur die Entwicklungsumgebung verfügbar.')
        with self.lock:
            if self.server is None:
                from .server import JarvisServer
                address=private_ip();self.hostname=None
                try:
                    import re
                    name=subprocess.run(['/usr/sbin/scutil','--get','LocalHostName'],capture_output=True,text=True,timeout=3).stdout.strip()
                    if re.fullmatch(r'[A-Za-z0-9-]{1,63}',name):self.hostname=name+'.local'
                except (OSError,subprocess.SubprocessError):pass
                cert,key,self.profile,self.fingerprint=certificates(self.app.store.data_dir/'mobile',address,self.hostname)
                server=JarvisServer((address,8766),self.app,secure=True);server.device_auth=self.auth
                if self.hostname:server.allowed_hosts.add(self.hostname.lower())
                context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);context.minimum_version=ssl.TLSVersion.TLSv1_2;context.load_cert_chain(cert,key)
                server.socket=context.wrap_socket(server.socket,server_side=True,do_handshake_on_connect=False)
                self.server=server;threading.Thread(target=server.serve_forever,daemon=True).start()
            self.enabled_path.parent.mkdir(parents=True,exist_ok=True,mode=0o700);self.enabled_path.touch(mode=0o600)
            ticket=self.auth.issue();address=self.server.server_address[0];display=self.hostname or address
            return {'url':f'https://{display}:8766/#pair='+ticket,'ip_url':f'https://{address}:8766/#pair='+ticket,'fingerprint':self.fingerprint,'expires_seconds':300,'instructions':'Mac und Handy im selben vertrauenswürdigen WLAN. Erst das Zertifikatsprofil per AirDrop übertragen, auf iOS installieren und das Vertrauen bewusst aktivieren. Danach QR-Code scannen. Ohne Zertifikatsvertrauen kann iOS die Kamera nicht freigeben.'}
    def profile_data(self):
        if self.server is None:raise ValueError('Bitte zuerst Handykopplung vorbereiten.')
        return {'filename':self.profile.name,'content':self.profile.read_text(),'fingerprint':self.fingerprint}
    def reveal_profile(self):
        if self.server is None:raise ValueError('Bitte zuerst Handykopplung vorbereiten.')
        try:subprocess.run(['/usr/bin/open','-R',str(self.profile)],capture_output=True,check=True,timeout=5)
        except (OSError,subprocess.SubprocessError):raise ValueError('Die Profil-Datei konnte im Finder nicht angezeigt werden.') from None
    def stop(self,revoke=True):
        with self.lock:
            if self.server:self.server.shutdown();self.server.server_close();self.server=None
            if revoke:self.auth.revoke();self.enabled_path.unlink(missing_ok=True)
