"""Dependency-free, authenticated local JARVIS HTTP application."""
from __future__ import annotations

import argparse
import base64
import getpass
import hmac
import ipaddress
import json
import mimetypes
import os
import platform
from pathlib import Path
import re
import secrets
import ssl
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

from .ai import GeminiClient, ProviderError, provider_status
from .voice import VoiceClient
from .natural_voice import NaturalVoice
from .hub import MiniHub
from .desktop import Desktop
from .mobile import MobileLink
from .agents import AgentOffice
from .task_router import task_request
from .cameras import CAMERAS, SPORTS
from .training import plan as training_plan
from .openai_client import OpenAIClient
from .local_ai import LocalClient, local_status
from .llamacpp import LlamaCppClient, status as llama_status
from .small_model import start as start_small_model
from .storage import Store
from .mac_control import PendingActions
from .system_info import snapshot
from .credentials import configure as configure_credential, load_saved_keys
from .diagnostics import check_connection
from .certificates import repair_certificates

FRONTEND = Path(__file__).resolve().parent.parent / 'frontend'
MAX_BODY = 32_768


class Application:
    def __init__(self, data_dir=None):
        self.store = Store(data_dir)
        self.actions = PendingActions(self.store)
        self.ai = GeminiClient(self.store)
        self.openai = OpenAIClient(self.store)
        self.local_ai = LocalClient(self.store)
        self.llamacpp = LlamaCppClient(self.store)
        self.voice = VoiceClient(self.store)
        self.natural_voice = NaturalVoice(self.store.data_dir)
        self.token = secrets.token_urlsafe(32)
        self.chat_lock = threading.Lock()
        self.mobile = MobileLink(self)
        self.office = AgentOffice(self)
        self.hub = MiniHub(self.store)
        self.desktop = Desktop(self)

    def settings(self):
        values = self.store.settings()
        providers = provider_status()
        providers = {
            'gemini_configured': providers.get('gemini_key_configured', False),
            'openai_configured': bool(os.environ.get('OPENAI_API_KEY')),
            'elevenlabs_configured': providers.get('elevenlabs_key_configured', False),
        }
        usage = self.store.usage()
        return {'settings': values, 'providers': providers,
                'credentials': {'persistent_available': platform.system() == 'Darwin'}, 'usage': {
            'date': usage['date'],
            'openai': {'used': usage['openai_requests'], 'limit': values['openai_daily_limit']},
            'gemini': {'used': usage['gemini_requests'], 'limit': values['gemini_daily_limit']},
            'elevenlabs': {'used': usage['elevenlabs_characters'], 'limit': values['elevenlabs_daily_char_limit']},
        }}

    def selected_client(self):
        provider = self.store.settings()["ai_provider"]
        return self.llamacpp if provider == "llamacpp" else self.local_ai if provider == "ollama" else self.openai if provider == "openai" else self.ai

    def status(self):
        result = self.settings()
        result['system'] = snapshot(self.store.data_dir)
        result['capabilities'] = {
            'mac_control': result['system'].get('is_macos', False),
            'file_scope': str(self.actions.file_root),
            'web_research': False, 'email': False, 'phone': False,
            'camera': True, 'camera_image_analysis': False, 'agent_image_classification': platform.system()=='Darwin', 'bundled_voice':True, 'public_camera_map': True, 'wake_word': False,
        }
        return result

    def dispatch_agent(self,text,attachment=None):
        if not isinstance(text,str) or not 1<=len(text.strip())<=12000:raise ValueError('Bitte einen gültigen Auftrag eingeben.')
        task=task_request(text)
        if not task:return None
        if not task['task']:return {'reply':'Sir, was genau soll der Agent erstellen?','proposals':[],'view':'office'}
        job=self.office.submit({**task,**(attachment or {})})
        return {'reply':'Sir, der Auftrag wurde tatsächlich angelegt. Auftragsnummer: '+job['id'][:8]+'. Status und Ergebnis stehen in der Werkstatt.','proposals':[],'view':'office','job_id':job['id']}

    def chat(self, text):
        if not isinstance(text, str) or not text.strip() or len(text) > 12000:
            raise ValueError('Bitte eine Nachricht mit 1 bis 12.000 Zeichen eingeben.')
        text=re.sub(r'^(?:astra|asta|astda|astrid|jarvis)[,: ]+(?=(?:ich|mein|wie|wer|was|wo|wann|warum|wieso|kannst|könntest|würdest|öffne|starte|mach|erstelle|baue|modelliere|bitte|hallo|hi|danke|erklär|sag|zeig|nenne)\b)','',text.strip(),flags=re.I)
        user_name=re.fullmatch(r'(?:ich heiße|ich heisse|mein name ist|nenne mich)\s+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ ’\'-]{0,59})[.!]?',text.strip(),re.I)
        if user_name:
            value=user_name[1].strip();self.store.update_settings({'user_name':value})
            reply='Ich merke mir deinen Namen: '+value+'.'
            self.store.append('user',text);self.store.append('assistant',reply)
            return {'reply':reply,'proposals':[]}
        if re.fullmatch(r'(?:wie heiße ich|wie heisse ich|wie ist mein name)[?!. ]*',text.strip(),re.I):
            value=self.store.settings().get('user_name')
            return {'reply':'Du heißt '+value+'.' if value else 'Deinen Namen habe ich noch nicht gespeichert. Wie heißt du?','proposals':[]}
        if re.fullmatch(r'(?:wie (?:heißt|heisst) du|wer bist du|wie ist dein name)[?!. ]*',text.strip(),re.I):
            from .persona import name
            return {'reply':'Ich bin '+name(self.store)+', Sir.','proposals':[]}
        routed=self.dispatch_agent(text)
        if routed:return routed
        if re.search(r'\bagent(?:en)?\b|werkstatt',text,re.I):
            return {'reply':'Sir, die Werkstatt zeigt deine wirklichen Aufträge und Ergebnisse. Es wurde durch diese Frage kein neuer Auftrag angelegt. Zum Starten: „Beauftrage einen Agenten: …“ oder den Knopf „Auftrag starten“ verwenden.','proposals':[],'view':'office'}
        if not self.chat_lock.acquire(blocking=False):
            raise ProviderError('Eine Anfrage läuft bereits. Bitte kurz warten.', 409)
        try:
            command = text.strip().casefold().rstrip('.!?')
            action = None
            apps = {'rechner': 'Calculator', 'safari': 'Safari', 'kalender': 'Calendar',
                    'notizen': 'Notes', 'musik': 'Music', 'finder': 'Finder',
                    'systemeinstellungen': 'System Settings'}
            for german, app in apps.items():
                if command in {f'{german} öffnen', f'öffne {german}', f'öffne den {german}', f'starte {german}'}:
                    action = self.actions.prepare('open_app', {'app': app})
                    break
            if action:
                reply = 'Sir, die Aktion ist vorbereitet. Bitte bestätigen Sie die Ausführung.'
                self.store.append('user', text)
                self.store.append('assistant', reply)
                return {'reply': reply, 'proposals': [action]}
            if command in {'status', 'systemstatus', 'hilfe', 'help'}:
                if command in {'hilfe', 'help'}:
                    reply = ('Sir, lokal können Sie „Rechner öffnen“ oder „Status“ eingeben und Erinnerungen speichern. '
                             'Für freie Gespräche wählen Sie die lokale KI oder einen verfügbaren Cloud-Anbieter in den Einstellungen. '
                             'Mac-Aktionen benötigen Ihre Bestätigung; die Oberfläche führt sie auf dem Servergerät aus.')
                else:
                    system = snapshot(self.store.data_dir)
                    reply = f"Server: {system.get('platform', 'unbekannt')} · Architektur: {system.get('machine', 'unbekannt')}. "
                    reply += ('Mac-Steuerung verfügbar, Sir.' if system.get('is_macos') else
                              'Mac-Steuerung ist auf diesem Server nicht verfügbar, Sir.')
                self.store.append('user', text)
                self.store.append('assistant', reply)
                return {'reply': reply, 'proposals': []}
            client = self.selected_client()
            result = client.chat(text)
            proposals = []
            for proposal in result.get('proposed_actions', []):
                try:
                    arguments = {k: v for k, v in proposal.items() if k != 'kind'}
                    if proposal.get('kind') == 'create_text' and 'text' in arguments:
                        arguments['content'] = arguments.pop('text')
                    proposals.append(self.actions.prepare(proposal['kind'], arguments))
                except (KeyError, TypeError, ValueError):
                    result['reply'] += '\nEine ungültige Aktion wurde verworfen und nicht ausgeführt.'
            return {'reply': result['reply'], 'proposals': proposals}
        finally:
            self.chat_lock.release()


class JarvisServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address, app, password=None, secure=False):
        super().__init__(address, Handler)
        self._workers = threading.BoundedSemaphore(24)
        self.app = app
        self.password = password
        self.secure = secure
        self.allowed_hosts = {'localhost', '127.0.0.1', '::1', address[0].lower()}
        self.auth_failures = {}
        self.auth_lock = threading.Lock()
        self.device_auth = None

    def get_request(self):
        connection, address = super().get_request()
        # Bound header and TLS-handshake reads before BaseHTTPRequestHandler runs.
        connection.settimeout(10)
        return connection, address

    def process_request(self, request, client_address):
        if not self._workers.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except Exception:
            self._workers.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self._workers.release()

    def handle_error(self, request, client_address):
        # Never let the stdlib dump request/traceback data to shared logs.
        pass


class Handler(BaseHTTPRequestHandler):
    server_version = 'Jarvis'
    sys_version = ''

    def log_message(self, format, *args):
        # Paths, queries, headers and provider output can contain personal data.
        pass

    def _headers(self, status, content_type, length, cookie=None):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        if cookie:
            self.send_header('Set-Cookie',cookie)
        self.send_header('Content-Length', str(length))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Permissions-Policy', 'camera=(self), microphone=(self), geolocation=()')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; worker-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https://images.tagesschau.de https://www.tagesschau.de https://tagesschau.de https://i.ytimg.com; media-src 'self' blob:; connect-src 'self'; frame-src https://www.youtube-nocookie.com https://www.tiktok.com https://zugspitze.panomax.com https://www.muenchen.de https://www.berlin.de https://www.earthcam.com https://www.abbeyroad.com https://www.livefromiceland.is https://www.skylinewebcams.com; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'")
        if self.server.secure:
            self.send_header('Strict-Transport-Security', 'max-age=86400')
        self.end_headers()

    def _json(self, value, status=200, cookie=None):
        body = json.dumps(value, ensure_ascii=False).encode('utf-8')
        self._headers(status, 'application/json; charset=utf-8', len(body),cookie)
        self.wfile.write(body)

    def _guard(self):
        host = self.headers.get('Host', '')
        try:
            url = urlsplit('//' + host)
            if url.hostname not in self.server.allowed_hosts or url.port != self.server.server_port:
                raise ValueError()
            if url.username or url.password or url.path or url.query or url.fragment:
                raise ValueError()
        except ValueError:
            self._json({'error': 'Ungültiger Host.'}, 403)
            return False
        expected = ('https' if self.server.secure else 'http') + '://' + host
        origin = self.headers.get('Origin')
        if (origin and origin != expected) or self.headers.get('Sec-Fetch-Site') == 'cross-site':
            self._json({'error': 'Anfragen von anderen Webseiten sind gesperrt.'}, 403)
            return False
        if self.server.password:
            peer = self.client_address[0]
            with self.server.auth_lock:
                now = time.monotonic()
                recent = [t for t in self.server.auth_failures.get(peer, []) if now-t < 60]
                self.server.auth_failures[peer] = recent
            if len(recent) >= 10:
                self._json({'error': 'Zu viele Anmeldeversuche. Bitte eine Minute warten.'}, 429)
                return False
            try:
                scheme, encoded = self.headers.get('Authorization', '').split(' ', 1)
                credentials = base64.b64decode(encoded, validate=True).decode('utf-8')
                authorized = scheme == 'Basic' and hmac.compare_digest(credentials.encode(), ('jarvis:' + self.server.password).encode())
            except (ValueError, UnicodeError):
                authorized = False
            if not authorized:
                if self.headers.get('Authorization'):
                    with self.server.auth_lock:
                        self.server.auth_failures[peer].append(time.monotonic())
                body = b'Anmeldung erforderlich.'
                self.send_response(401)
                self.send_header('WWW-Authenticate', 'Basic realm="JARVIS", charset="UTF-8"')
                self.send_header('Content-Type', 'text/plain; charset=utf-8')
                self.send_header('Content-Length', str(len(body)))
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                self.wfile.write(body)
                return False
        path = urlsplit(self.path).path
        if self.server.device_auth:
            if path == '/api/mobile/pair' and self.command == 'POST':
                return True
            if not self.server.device_auth.valid(self.headers.get('Cookie')):
                if self.command == 'GET' and path in {'/','/pair.js','/style.css'}:
                    return True
                self._json({'error':'Bitte dieses Gerät über den aktuellen QR-Code am Mac koppeln.'},401)
                return False
        if path.startswith('/api/') and path != '/api/session':
            token = self.headers.get('X-Jarvis-Token', '')
            if not hmac.compare_digest(token.encode('utf-8'), self.server.app.token.encode('utf-8')):
                self._json({'error': 'Sitzung abgelaufen. Bitte Seite neu laden.'}, 401)
                return False
        return True

    def _body(self):
        if self.headers.get('Transfer-Encoding'):
            raise ValueError('Transfer-Encoding wird nicht unterstützt.')
        try:
            length = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            raise ValueError('Ungültige Nachrichtenlänge.') from None
        maximum = 6 * 1024 * 1024 if urlsplit(self.path).path in {'/api/image','/api/agents','/api/agents/dispatch'} else MAX_BODY
        if length < 1 or length > maximum:
            raise ValueError('Die Anfrage ist leer oder überschreitet das Größenlimit.')
        if self.headers.get_content_type() != 'application/json':
            raise ValueError('JSON-Anfrage erforderlich.')
        try:
            body = json.loads(self.rfile.read(length))
        except (ValueError, UnicodeError):
            raise ValueError('Die Anfrage enthält kein gültiges JSON.') from None
        if not isinstance(body, dict):
            raise ValueError('Ein JSON-Objekt ist erforderlich.')
        return body

    def _dispatch(self):
        self.connection.settimeout(35)
        if not self._guard():
            return
        path = urlsplit(self.path).path
        app = self.server.app
        method = self.command
        if method == 'GET':
            if self.server.device_auth and not self.server.device_auth.valid(self.headers.get('Cookie')) and path == '/':
                body=(FRONTEND/'pair.html').read_bytes()
                self._headers(200,'text/html; charset=utf-8',len(body))
                return self.wfile.write(body)
            if path == '/api/session':
                return self._json({'token': app.token})
            if re.fullmatch(r'/api/agents/[0-9a-f]{32}/image',path):
                data,mime=app.office.image(path.split('/')[3]);self._headers(200,mime,len(data));return self.wfile.write(data)
            if path == '/api/hub':return self._json(app.hub.snapshot())
            if path=='/api/desktop/render':
                app.desktop.model_file()
                image=Path(app.desktop.snapshot()['plan']['artifact']).parent/'Vorschau.png'
                if not image.is_file() or image.stat().st_size>10000000:raise ValueError('Noch kein Renderbild vorhanden.')
                data=image.read_bytes()
                if not data.startswith(b'\x89PNG\r\n\x1a\n'):raise ValueError('Ungültiges Renderbild.')
                self._headers(200,'image/png',len(data));return self.wfile.write(data)
            if path == '/api/desktop/model':
                data=app.desktop.model_file();self._headers(200,'application/octet-stream',len(data));return self.wfile.write(data)
            if path == '/api/desktop':return self._json(app.desktop.snapshot())
            if path == '/api/natural-voice/status':
                return self._json(app.natural_voice.status())
            if path == '/api/agents':
                return self._json(app.office.snapshot())
            if path == '/api/cameras':
                return self._json({'cameras': CAMERAS,'sports':SPORTS})
            if path == '/api/status':
                return self._json(app.status())
            if path == '/api/settings':
                return self._json(app.settings())
            if path == '/api/history':
                return self._json({'messages': app.store.history()})
            if path == '/api/reminders':
                return self._json({'reminders': app.store.reminders()})
            # Exact static allowlist: no arbitrary files, keys or directory listings.
            static = {'/': 'index.html', '/index.html': 'index.html',
                      '/style.css': 'style.css', '/app.js': 'app.js', '/pair.js':'pair.js', '/qr.js':'qr.js', '/extras.js':'extras.js', '/extras.css':'extras.css', '/world.geojson':'world.geojson', '/globe.js':'globe.js', '/office.js':'office.js', '/artifacts.js':'artifacts.js', '/jarvis-voice.js':'jarvis-voice.js', '/voice-worker.js':'voice-worker.js', '/conversation.js':'conversation.js', '/mini-hub.js':'mini-hub.js', '/world-news.js':'world-news.js', '/astra.js':'astra.js', '/astra.css':'astra.css', '/astra-panel.html':'astra-panel.html', '/astra-panel.js':'astra-panel.js'}
            for name in ['ESpeak.js','mespeak.js','config.json','jarvis-de.json','de.json','COPYING','NOTICE.txt','UPSTREAM-README.md','mespeak-2.0.2-source.tgz','speak-source-9c6f642.tar.gz']:
                static['/vendor/voice/'+name]='vendor/voice/'+name
            if path in static:
                file = FRONTEND / static[path]
                body = file.read_bytes()
                content_type = mimetypes.guess_type(file.name)[0] or 'application/octet-stream'
                self._headers(200, content_type + '; charset=utf-8', len(body))
                return self.wfile.write(body)
        elif method == 'DELETE' and path == '/api/history':
            if not app.chat_lock.acquire(blocking=False):
                raise ProviderError('Bitte die laufende Antwort abwarten.', 409)
            try:
                app.store.clear_history()
            finally:
                app.chat_lock.release()
            return self._json({'ok': True})
        elif method in {'POST', 'PUT', 'PATCH'}:
            body = self._body()
            if method=='POST' and path.startswith('/api/desktop/'):
                if self.server.device_auth:raise ValueError('Desktop-Steuerung ist nur direkt am Mac verfügbar, nicht über die Handy-Kopplung.')
                if path=='/api/desktop/companion':return self._json(app.desktop.companion(body))
                if path=='/api/desktop/sync':return self._json(app.desktop.sync_ui(body))
                if path=='/api/desktop/prepare':return self._json(app.desktop.prepare(body))
                if path=='/api/desktop/start':
                    if set(body)!={'id'}:raise ValueError('Nur die geprüfte Ablaufkennung angeben.')
                    return self._json(app.desktop.start(body['id']))
                if path=='/api/desktop/speech':
                    if set(body)!={'muted'}:raise ValueError('Ungültiger Sprachstatus.')
                    return self._json(app.desktop.speech(body['muted']))
                if body:raise ValueError('Diese Desktop-Aktion braucht keine Parameter.')
                if path=='/api/desktop/panel-ready':return self._json(app.desktop.panel_ready())
                if path=='/api/desktop/stop':return self._json(app.desktop.stop())
                if path=='/api/desktop/panel':
                    port=self.server.server_port
                    return self._json(app.desktop.open_panel(('https' if self.server.secure else 'http')+'://127.0.0.1:'+str(port)+'/astra-panel.html'))
            if method=='POST' and path in {'/api/hub/news','/api/hub/channels'}:
                if body:raise ValueError('Keine Parameter für die Hub-Aktualisierung erforderlich.')
                return self._json(app.hub.news() if path.endswith('/news') else app.hub.channels())
            if method=='POST' and path=='/api/natural-voice/cancel':
                if set(body)!={'id'}:raise ValueError('Nur die Sprachkennung angeben.')
                return self._json(app.natural_voice.cancel(body['id']))
            if method == 'POST' and path == '/api/natural-voice/speak':
                if set(body)-{'text','preset','id','background'}:raise ValueError('Unbekannte Sprachfelder.')
                audio=app.natural_voice.synthesize(body.get('text'),body.get('preset','jarvis'),request_id=body.get('id'),background=body.get('background',False)) if 'id' in body or 'background' in body else app.natural_voice.synthesize(body.get('text'),body.get('preset','jarvis'))
                self._headers(200,'audio/wav',len(audio))
                return self.wfile.write(audio)
            if method == 'POST' and path == '/api/agents/dispatch':
                if set(body)-{'text','image','mime'}:raise ValueError('Unbekannte Auftragsfelder.')
                routed=app.dispatch_agent(body.get('text'),{key:body[key] for key in ('image','mime') if key in body})
                if not routed:raise ValueError('Bitte einen konkreten Agentenauftrag formulieren.')
                return self._json(routed)
            if method=='POST' and path=='/api/agents/group':return self._json(app.office.submit_group(body),202)
            if method == 'POST' and path == '/api/agents':
                return self._json(app.office.submit(body),202)
            if method == 'POST' and path == '/api/agents/cancel':
                if set(body)!={'id'}:raise ValueError('Bitte nur die Auftragskennung angeben.')
                return self._json(app.office.cancel(body['id']))
            if method == 'POST' and path == '/api/training/plan':
                return self._json(training_plan(body))
            if method == 'POST' and path == '/api/mobile/pair' and self.server.device_auth:
                if set(body)!={'ticket'}:
                    raise ValueError('Ungültige Kopplungsanfrage.')
                session=self.server.device_auth.pair(body['ticket'])
                return self._json({'ok':True},cookie='jarvis_device='+session+'; Path=/; Secure; HttpOnly; SameSite=Strict; Max-Age=43200')
            if method == 'POST' and path in {'/api/mobile/start','/api/mobile/profile','/api/mobile/reveal','/api/mobile/stop'}:
                if self.server.device_auth or not ipaddress.ip_address(self.client_address[0]).is_loopback:
                    return self._json({'error':'Handykopplung nur direkt am Mac verwalten.'},403)
                if body:
                    raise ValueError('Keine Parameter für die Handykopplung erforderlich.')
                if path.endswith('/start'): return self._json(app.mobile.start())
                if path.endswith('/profile'): return self._json(app.mobile.profile_data())
                if path.endswith('/reveal'):
                    app.mobile.reveal_profile()
                    return self._json({'ok':True})
                app.mobile.stop()
                return self._json({'ok':True})
            if method == 'POST' and path == '/api/llamacpp/status':
                if body:
                    raise ValueError('Die lokale Prüfung benötigt keine Parameter.')
                return self._json(llama_status())
            if method == 'POST' and path == '/api/local/status':
                if body:
                    raise ValueError('Die lokale Prüfung benötigt keine Parameter.')
                return self._json(local_status())
            if method == 'POST' and path == '/api/connections':
                if set(body) != {'provider'}:
                    raise ValueError('Bitte ausschließlich den Anbieter für die Verbindungsprüfung angeben.')
                if not isinstance(body['provider'], str) or body['provider'] not in {'gemini', 'elevenlabs', 'openai'}:
                    raise ValueError('Bitte Gemini oder ElevenLabs als Anbieter wählen.')
                return self._json(check_connection(body['provider']))
            if method == 'POST' and path == '/api/credentials':
                if set(body) - {'provider', 'api_key', 'persist'}:
                    raise ValueError('Ungültige Felder für die Schlüsselkonfiguration.')
                return self._json(configure_credential(body.get('provider'), body.get('api_key'), body.get('persist', True)))
            if method == 'POST' and path == '/api/chat':
                return self._json(app.chat(body.get('text')))
            if method == 'POST' and path == '/api/image':
                encoded = body.get('image')
                if not isinstance(encoded, str) or len(encoded) > 5_592_408:
                    raise ValueError('Bitte ein gültiges Bild bis 4 MiB auswählen.')
                try:
                    image = base64.b64decode(encoded, validate=True)
                except ValueError:
                    raise ValueError('Die Bilddaten sind ungültig.') from None
                if not app.chat_lock.acquire(blocking=False):
                    raise ProviderError('Eine Anfrage läuft bereits. Bitte kurz warten.', 409)
                try:
                    client = app.selected_client()
                    result = client.analyze_image(body.get('text', ''), image, body.get('mime', 'image/jpeg'))
                finally:
                    app.chat_lock.release()
                return self._json({'reply': result['reply'], 'proposals': []})
            if method == 'PUT' and path == '/api/settings':
                app.store.update_settings(body)
                return self._json(app.settings())
            if method == 'POST' and path == '/api/actions/prepare':
                return self._json(app.actions.prepare(body.get('action'), body.get('arguments', {})))
            if method == 'POST' and path == '/api/actions/confirm':
                result = app.actions.confirm(body.get('id'))
                result['message'] = result.get('message') or result.get('error') or 'Aktionsausführung abgeschlossen.'
                app.store.append('assistant', '[Backend-Ergebnis: ' + ('Erfolg' if result.get('ok') else 'Fehler') + '] ' + result['message'])
                return self._json(result)
            if method == 'POST' and path == '/api/actions/cancel':
                app.actions.cancel(body.get('id'))
                return self._json({'ok': True, 'message': 'Aktion verworfen.'})
            if method == 'POST' and path == '/api/reminders':
                return self._json(app.store.create_reminder(body.get('text'), body.get('due_at')), 201)
            if method == 'PATCH' and re.fullmatch(r'/api/reminders/[0-9]+', path):
                return self._json(app.store.update_reminder(int(path.rsplit('/', 1)[1]), body.get('status')))
            if method == 'POST' and path == '/api/voice':
                audio = app.voice.synthesize(body.get('text'))
                self._headers(200, 'audio/mpeg', len(audio))
                return self.wfile.write(audio)
        self._json({'error': 'Diese Schnittstelle existiert nicht.'}, 404)

    def _handle(self):
        try:
            self._dispatch()
        except ProviderError as error:
            self._json({'error': str(error)}, error.status)
        except (ValueError, TypeError) as error:
            self._json({'error': str(error)}, 400)
        except (BrokenPipeError, ConnectionResetError, TimeoutError):
            return
        except Exception:
            # Do not expose tracebacks, file contents, request text or credentials.
            self._json({'error': 'Interner Fehler. Bitte die Aktion prüfen und erneut versuchen.'}, 500)

    do_GET = do_POST = do_PUT = do_PATCH = do_DELETE = _handle


def main(argv=None):
    parser = argparse.ArgumentParser(description='JARVIS – lokaler persönlicher Assistent')
    parser.add_argument('--host', default='127.0.0.1', help='Standard: nur dieser Computer')
    parser.add_argument('--port', default=8765, type=int)
    parser.add_argument('--data-dir', type=Path)
    parser.add_argument('--cert', type=Path, help='Vertrauenswürdiges TLS-Zertifikat für LAN-Zugriff')
    parser.add_argument('--key', type=Path, help='Privater TLS-Schlüssel')
    parser.add_argument('--ask-keys', action='store_true', help='API-Schlüssel verdeckt für diese Sitzung eingeben')
    parser.add_argument('--open-browser', action='store_true', help='Nach dem Start die lokale Oberfläche im Browser öffnen')
    parser.add_argument('--diagnose', action='store_true', help='Tatsächliche Hardware und Software anzeigen, ohne Serverstart')
    parser.add_argument('--check-connection', choices=['gemini', 'elevenlabs', 'openai'], help='HTTPS-Verbindung ohne API-Schlüssel und ohne Generierung prüfen')
    parser.add_argument('--repair-certificates', action='store_true', help='Auf ausdrücklichen Auftrag das offizielle python.org-Zertifikatsskript auf macOS ausführen')
    parser.add_argument('--start-small-ai', action='store_true', help='Vorhandene kleine lokale KI ohne Download starten')
    parser.add_argument('--setup-small-ai', action='store_true', help='Kleine lokale KI ausdrücklich herunterladen, prüfen und JARVIS starten')
    parser.add_argument('--easy-local', action='store_true', help='Bereits eingerichtete lokale KI und JARVIS zusammen offline starten')
    parser.add_argument('--local-only', action='store_true', help='Lokalen Modus ohne API-Schlüsselbund starten')
    args = parser.parse_args(argv)
    if args.setup_small_ai or args.easy_local:
        from .easy_start import run
        try:
            run(setup=args.setup_small_ai)
        except KeyboardInterrupt:
            pass
        except (ValueError, OSError) as error:
            parser.exit(1, str(error) + '\n')
        return
    if args.start_small_ai:
        try:
            start_small_model()
        except ValueError as error:
            parser.exit(1, str(error) + '\n')
        except KeyboardInterrupt:
            pass
        return
    if args.diagnose:
        print(json.dumps(snapshot(), ensure_ascii=False, indent=2))
        return
    if args.check_connection:
        print(check_connection(args.check_connection)['message'])
        return
    if args.repair_certificates:
        try:
            print(repair_certificates())
        except ValueError as error:
            parser.exit(1, str(error) + '\n')
        return
    try:
        local = args.host == 'localhost' or ipaddress.ip_address(args.host).is_loopback
    except ValueError:
        parser.error('--host muss localhost oder eine konkrete IP-Adresse sein.')
    if not local and args.host in {'0.0.0.0', '::'}:
        parser.error('Für LAN bitte die konkrete private IP-Adresse des Macs angeben.')
    if not local and not ipaddress.ip_address(args.host).is_private:
        parser.error('Öffentliche Serveradressen sind nicht unterstützt.')
    if bool(args.cert) != bool(args.key):
        parser.error('--cert und --key müssen zusammen angegeben werden.')
    password = os.environ.get('JARVIS_ACCESS_PASSWORD')
    if not local and (not args.cert or not password or len(password) < 16):
        parser.error('LAN benötigt TLS (--cert und --key) und JARVIS_ACCESS_PASSWORD mit mindestens 16 Zeichen.')
    if args.ask_keys and not args.local_only:
        for name, label in [('GEMINI_API_KEY', 'Gemini API-Schlüssel'), ('ELEVENLABS_API_KEY', 'ElevenLabs API-Schlüssel')]:
            value = getpass.getpass(label + ' (leer = überspringen): ').strip()
            if value:
                os.environ[name] = value
    if not args.local_only:
        load_saved_keys()
    app = Application(args.data_dir)
    if args.local_only:
        app.store.update_settings({'ai_provider':'llamacpp','cloud_enabled':False,'elevenlabs_enabled':False,'voice_enabled':True})
    if ':' in args.host:
        import socket
        JarvisServer.address_family = socket.AF_INET6
    server = JarvisServer((args.host, args.port), app, password, bool(args.cert))
    if args.cert:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.load_cert_chain(args.cert, args.key)
        # Handshake occurs in bounded handler workers with an accepted-socket
        # timeout, so a silent TLS peer cannot block the accept loop.
        server.socket = context.wrap_socket(server.socket, server_side=True, do_handshake_on_connect=False)
    print(f'JARVIS läuft auf Port {server.server_port}. Beenden mit Strg+C.', flush=True)
    print('Cloud-Funktionen verwenden ausschließlich Ihre gespeicherten Freigaben.', flush=True)
    if args.open_browser:
        import webbrowser
        address = f'[{args.host}]' if ':' in args.host else args.host
        try:
            webbrowser.open(('https' if args.cert else 'http') + f'://{address}:{server.server_port}')
        except OSError:
            print('Bitte die lokale JARVIS-Adresse manuell im Browser öffnen.', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        try:
            app.desktop.stop()
            if app.desktop.thread:app.desktop.thread.join(timeout=2)
            if app.desktop.panel and app.desktop.panel.poll() is None:app.desktop.panel.terminate()
            app.office.stop()
            app.mobile.stop()
        finally:
            server.server_close()


if __name__ == '__main__':
    main()
