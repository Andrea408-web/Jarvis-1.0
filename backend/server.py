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
from urllib.parse import urlsplit, unquote

from .ai import GeminiClient, ProviderError, provider_status
from .voice import VoiceClient
from .natural_voice import NaturalVoice
from .hub import MiniHub
from .desktop import Desktop
from .notes import request as note_request
from .dialogue import Dialogue
from .web_assistant import WebAssistant
from .website import requested as website_requested
from .everyday import arithmetic,film_ideas,news_request,news_answer
from .mobile import MobileLink
from .agents import AgentOffice
from .task_router import task_request
from .cameras import CAMERAS, SPORTS
from .training import plan as training_plan
from .openai_client import OpenAIClient
from .local_ai import _bare_confirmation,LocalClient, local_status
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
        from .personal_profile import PersonalProfile
        self.personal_profile = PersonalProfile(self.store)
        self.dialogue=Dialogue()
        self.pose_lock=threading.Lock()
        self.voice_install_lock=threading.Lock();self.voice_install_state={'state':'idle','message':''}
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
        from .device_ai import DeviceAI
        from .brands import Brands
        self.device_ai=DeviceAI(self.store.data_dir)
        self.brands=Brands(self.store.data_dir)
        from .confirmed_send import ConfirmedSend
        self.confirmed_send=ConfirmedSend()
        from .quest_window import QuestWindow
        self.quest_window=QuestWindow()
        from .companion_window import CompanionWindow
        self.companion_window=CompanionWindow(self.store.data_dir)
        from .video_editor import VideoEditor
        self.video_editor=VideoEditor(self.store.data_dir)
        self.office = AgentOffice(self)
        self.hub = MiniHub(self.store)
        self.desktop = Desktop(self)
        self.web = WebAssistant(self)
        from .code_room import CodeRoom
        self.code_room = CodeRoom(self)
        from .workshop_jobs import WorkshopJobs
        self.workshop = WorkshopJobs(self)
        from .studio_bridge import StudioBridge
        self.studio_bridge = StudioBridge(self.store.data_dir)

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
        result['dialogue']=self.dialogue.get()
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
        return {'reply':'Sir, der Auftrag wurde tatsächlich angelegt. Auftragsnummer: '+job['id'][:8]+'. Status und Ergebnis stehen in der Werkstatt.','proposals':[],'view':'office','job_id':job['id'],**({'artifact':'website'} if task['role']=='builder' and website_requested(task['task']) else {})}

    def install_thorsten(self):
        import platform
        if platform.system()!='Darwin':raise ValueError('Thorsten bitte auf deinem Mac einrichten.')
        with self.voice_install_lock:
            if self.voice_install_state['state']=='running':return dict(self.voice_install_state)
            self.voice_install_state={'state':'running','message':'Thorsten wird eingerichtet. Einmalig ungefähr 100–104 MB, falls das Paket fehlt. Terminal geöffnet lassen.'}
        def worker():
            try:
                from .natural_voice import install
                voice=install(self.store.data_dir)
                if not voice.status()['installed']:raise ValueError('Thorsten konnte nicht geprüft werden.')
                self.natural_voice=voice
                self.store.update_settings({'voice_engine':'natural','voice_enabled':True,'elevenlabs_enabled':False})
                result={'state':'done','message':'Thorsten ist eingerichtet und fest ausgewählt.'}
            except Exception as error:result={'state':'error','message':str(error)[:500]}
            with self.voice_install_lock:self.voice_install_state=result
        threading.Thread(target=worker,daemon=True).start()
        return {'state':'running','message':'Thorsten wird eingerichtet. Bitte warten.'}

    def clear_chat(self):
        with self.dialogue.lock:
            self.dialogue.clear();self.store.clear_all_history()
        with self.desktop.lock:
            self.desktop.commands.clear()
            if self.desktop.plan and self.desktop.plan['state']=='review':self.desktop.stop()
        return {'ok':True,'pending':None}

    def chat(self, text):
        if not isinstance(text, str) or not text.strip() or len(text) > 12000:
            raise ValueError('Bitte eine Nachricht mit 1 bis 12.000 Zeichen eingeben.')
        text=re.sub(r'^(?:aeris|abriss|astra|asta|astda|astrid|asuka|jarvis)[,: ]+(?=(?:ich|mein|wie|wer|was|wo|wann|warum|wieso|kannst|könntest|würdest|öffne|starte|mach|erstelle|baue|modelliere|bitte|hallo|hi|danke|erklär|sag|zeig|nenne|schreibe|schreib|notiere|speichere|tippe|bewege|wieviel|rechne|berechne|eins|zwei|drei|vier|fünf|sechs|sieben|acht|neun|zehn|[0-9]+|chat|vergiss|lösche|alles|abbrechen|stopp?)\b)','',text.strip(),flags=re.I)
        if re.search(r'(?:wechsel|wechsle|werde|aktiviere|öffne).{0,30}(?:aeris|abriss)',text,re.I):
            self.dialogue.clear();return {'reply':'Aeris ist bereit, Sir.','proposals':[],'pending':None,'view':'aeris'}
        if re.fullmatch(r'(?:chat löschen|lösche (?:den )?chat|alles vergessen|vergiss (?:bitte )?alles|alles da vergessen)[.! ]*',text,re.I):
            self.clear_chat();return {'reply':'Gesprächsverläufe, gemerkter Name und offene Rückfragen sind gelöscht.','proposals':[],'pending':None,'cleared':True}
        if re.fullmatch(r'(?:abbrechen|stopp?|vergiss das|neue aufgabe)[.! ]*',text,re.I) and self.dialogue.get():
            self.dialogue.clear();return {'reply':'Rückfrage abgebrochen. Was möchtest du als Nächstes machen?','proposals':[],'pending':None}
        if _bare_confirmation(text) and not self.dialogue.get():
            with self.desktop.lock:review=bool(self.desktop.plan and self.desktop.plan['state']=='review')
            with self.actions._lock:action=any(value[0]>time.time() for value in self.actions._pending.values())
            reply=('Ein konkreter Auftrag wartet, Sir. Prüfe ihn und nutze den zugehörigen Start- oder Bestätigungsknopf.' if review or action else 'Gerade gibt es keine Aktion zu bestätigen, Sir. Stell mir bitte deine Frage direkt; dafür ist keine Bestätigung nötig.')
            return {'reply':reply,'proposals':[],'pending':None}
        math_reply=arithmetic(text)
        pending=self.dialogue.get()
        if math_reply and (not pending or pending['kind'].startswith('web_') or re.match(r'was|wie|rechne|berechne',text,re.I)):
            self.dialogue.clear();return {'reply':math_reply,'proposals':[],'pending':None}
        movie=film_ideas(text)
        if movie and note_request(text) is None and (not pending or pending['kind'].startswith('web_') or re.match(r'was|welche|empfiehl',text,re.I)):
            with self.dialogue.lock:
                self.dialogue.clear();self.store.append('user',text);self.store.append('assistant',movie['reply'])
            return movie
        news=news_request(text)
        if news and note_request(text) is None:
            epoch=self.store.memory_epoch();result=news_answer(self,news)
            with self.dialogue.lock:
                if self.store.memory_epoch()!=epoch:raise ValueError('Der Chat wurde inzwischen gelöscht.')
                self.dialogue.clear();self.store.append('user',text,expected_epoch=epoch);self.store.append('assistant',result['reply'],expected_epoch=epoch)
            return result
        if task_request(text):self.dialogue.clear()
        answer=self.dialogue.answer(text)
        if answer:
            data=self.desktop.prepare(answer);self.dialogue.clear()
            return {'reply':'Die Antwort ist übernommen. Der konkrete Auftrag ist vorbereitet; ein Erfolg wird erst nach der Ausführung gemeldet.','proposals':[],'view':'desktop','desktop':data,'pending':None}
        if re.fullmatch(r'(?:öffne|starte)\s+(?:(?:eine?|die|das)\s+)?(?:app|programm)[.!? ]*',text,re.I):return self.dialogue.ask('app','Welche App soll ich öffnen?')
        if re.fullmatch(r'(?:öffne|starte)\s+(?:(?:eine?|die)\s+)?(?:webseite|website|seite)[.!? ]*',text,re.I):return self.dialogue.ask('website','Welche Webseitenadresse soll ich öffnen?')
        typing=re.fullmatch(r'(?:tippe|schreibe (?:den|folgenden) text)[: ]+(.+)',text,re.I|re.S)
        if typing and not re.search(r'\s+in\s+|notiz',text,re.I):return self.dialogue.ask('typing_app','In welche App soll ich diesen Text eingeben?',text=typing[1])
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
        note=note_request(text)
        if note is not None:
            if not note['body']:return self.dialogue.ask('note','Was soll in der Notiz stehen, Master?')
            data=self.desktop.prepare({'goal':text})
            return {'reply':'Notizauftrag vorbereitet. Noch keine Notiz erstellt; der sichtbare Auftrag meldet das bestätigte Ergebnis.','proposals':[],'view':'desktop','desktop':data}
        if re.match(r'^(?:öffne|starte|mach|erstelle|baue|modelliere)\b',text,re.I) and re.search(r'\bblender\b',text,re.I):
            data=self.desktop.prepare({'goal':text})
            return {'reply':'Der Blender-Auftrag ist vorbereitet, Master. Er ist noch nicht ausgeführt. Prüfe den sichtbaren Ablauf und starte ihn.','proposals':[],'view':'desktop','desktop':data}
        if re.search(r'tafel|auftragsübersicht',text,re.I) and re.search(r'öffne|zeig|ansehen',text,re.I):return {'reply':'Sir, die Live-Auftragstafel zeigt deine wirklichen Aufträge und Ergebnisse.','proposals':[],'view':'taskboard'}
        routed=self.dispatch_agent(text)
        if routed:return routed
        if re.search(r'\bagent(?:en)?\b|werkstatt',text,re.I):
            return {'reply':'Sir, die Werkstatt zeigt deine wirklichen Aufträge und Ergebnisse. Es wurde durch diese Frage kein neuer Auftrag angelegt. Zum Starten: „Beauftrage einen Agenten: …“ oder den Knopf „Auftrag starten“ verwenden.','proposals':[],'view':'office'}
        web_result=self.web.handle(text)
        if web_result:return web_result
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
        contact_panel=urlsplit(self.path).path=='/contacts-panel'
        self.send_header('X-Frame-Options', 'SAMEORIGIN' if contact_panel else 'DENY')
        ancestors="'self'" if contact_panel else "'none'"
        self.send_header('Permissions-Policy', 'camera=(self), microphone=(self), xr-spatial-tracking=(self), geolocation=()')
        device= urlsplit(self.path).path in {'/tablet','/brands'} or urlsplit(self.path).path=='/' and (self.server.device_auth or re.search(r'iPhone|iPad|iPod|Macintosh.*Mobile',self.headers.get('User-Agent',''),re.I))
        script_policy="'self' 'wasm-unsafe-eval'" if device else "'self'"
        worker_policy="'self' blob:" if device else "'self'"
        self.send_header('Content-Security-Policy', f"default-src 'self'; script-src {script_policy}; worker-src {worker_policy}; style-src 'self' 'unsafe-inline'; img-src 'self' blob: data: https://images.tagesschau.de https://www.tagesschau.de https://tagesschau.de https://i.ytimg.com; media-src 'self' blob:; connect-src 'self' blob:; frame-src 'self' https://www.youtube-nocookie.com https://www.tiktok.com https://zugspitze.panomax.com https://www.muenchen.de https://www.berlin.de https://www.earthcam.com https://www.abbeyroad.com https://www.livefromiceland.is https://www.skylinewebcams.com; object-src 'none'; base-uri 'none'; frame-ancestors {ancestors}; form-action 'self'")
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
                if self.command == 'GET' and path in {'/','/mobile','/quest','/tablet','/brands','/pair.js','/style.css','/manifest.webmanifest','/app-icon.png'}:
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
        maximum = 6*1024*1024 if urlsplit(self.path).path=='/api/communication/prepare' else 512000 if urlsplit(self.path).path in {'/api/aeris/pose','/api/video-call','/api/video-editor/start','/api/video-editor/assist','/api/video-editor/plan','/api/video-editor/assist-plan','/api/video-editor/story','/api/workshop/design','/api/workshop/jobs'} else 6 * 1024 * 1024 if urlsplit(self.path).path in {'/api/image','/api/agents','/api/agents/dispatch','/api/aeris/pose'} else MAX_BODY
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
            if self.server.device_auth and not self.server.device_auth.valid(self.headers.get('Cookie')) and path in {'/','/mobile','/quest','/tablet','/brands'}:
                body=(FRONTEND/'pair.html').read_bytes()
                self._headers(200,'text/html; charset=utf-8',len(body))
                return self.wfile.write(body)
            if re.fullmatch(r'/site/[0-9a-f]{32}',path):
                data=app.office.site(path.split('/')[-1])
                self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Security-Policy',"sandbox; default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'; frame-ancestors 'self'")
                if 'download=1' in urlsplit(self.path).query:self.send_header('Content-Disposition','attachment; filename="Jarvis-Website.html"')
                self.end_headers();return self.wfile.write(data)
            if path=='/api/personal-profile':return self._json(app.personal_profile.read())
            if path=='/api/code-room/jobs':return self._json(app.code_room.recent(self.client_address[0]+'|'+self.headers.get('Cookie','')))
            if path=='/api/code-room/studio':return self._json(app.studio_bridge.status(self.client_address[0]+'|'+self.headers.get('Cookie','')))
            if path=='/api/code-room/models':return self._json(app.code_room.models())
            code_job=re.fullmatch(r'/api/code-room/jobs/([a-f0-9]{32})',path)
            code_preview=re.fullmatch(r'/code-preview/([a-f0-9]{32})',path)
            if code_job or code_preview:
                owner=self.client_address[0]+'|'+self.headers.get('Cookie','')
                if code_job:return self._json(app.code_room.snapshot(code_job[1],owner))
                data=app.code_room.preview(code_preview[1],owner)
                self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
                self.send_header('Content-Security-Policy',"sandbox allow-scripts; default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data: blob:; connect-src 'none'; frame-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'self'")
                self.end_headers();return self.wfile.write(data)
            if path=='/api/device-ai/status':return self._json(app.device_ai.status())
            if path=='/api/brands':return self._json(app.brands.all())
            if path=='/api/device-ai/model' or path.startswith('/device-runtime/'):
                if path=='/api/device-ai/model':source,_=app.device_ai.model();kind='application/octet-stream'
                else:
                    match=re.fullmatch(r'/device-runtime/3\.13\.0/(wllama\.js|wllama\.wasm|compat\.js|compat\.wasm|LICENSE)',path)
                    if not match:raise ValueError('Unbekannte Browser-Laufzeitdatei.')
                    source,kind=app.device_ai.asset(match[1])
                self._headers(200,kind,source.stat().st_size)
                with source.open('rb') as stream:
                    while True:
                        chunk=stream.read(256*1024)
                        if not chunk:break
                        self.wfile.write(chunk)
                return
            if path == '/api/session':
                return self._json({'token': app.token,'remote_device':bool(self.server.device_auth)})
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
            if path == '/api/desktop/input-status':
                from .input_access import status
                return self._json(status())
            if path == '/api/desktop':return self._json(app.desktop.snapshot())
            if path == '/api/natural-voice/status':
                return self._json({**app.natural_voice.status(),'installation':dict(app.voice_install_state)})
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
            media=re.fullmatch(r'/edit-media/([a-f0-9]{32})',path);render=re.fullmatch(r'/edit-result/([a-f0-9]{32})/(youtube|shorts)',path)
            if media or render:
                if self.server.device_auth or not ipaddress.ip_address(self.client_address[0]).is_loopback:return self._json({'error':'Videoschnitt-Dateien sind nur direkt am Mac verfügbar.'},403)
                source,name=app.video_editor.file(media[1]) if media else app.video_editor.file(render[1],render[2]);size=source.stat().st_size;start=0;end=size-1;status=200;range_header=self.headers.get('Range')
                if range_header:
                    match=re.fullmatch(r'bytes=(\d*)-(\d*)',range_header)
                    if not match or not (match[1] or match[2]) or (match[1] and int(match[1])>=size) or (not match[1] and int(match[2])==0):
                        self.send_response(416);self.send_header('Content-Range','bytes */'+str(size));self.send_header('Content-Length','0');self.end_headers();return
                    if match[1]:start=int(match[1]);end=min(end,int(match[2]) if match[2] else end)
                    else:start=max(0,size-int(match[2]))
                    if end<start:raise ValueError('Ungültiger Medienbereich.')
                    status=206
                self.send_response(status);self.send_header('Content-Type',mimetypes.guess_type(source.name)[0] or 'application/octet-stream');self.send_header('Content-Length',str(end-start+1));self.send_header('Accept-Ranges','bytes');self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
                if status==206:self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
                if urlsplit(self.path).query=='download=1':self.send_header('Content-Disposition','attachment; filename="Astra-'+(render[2]+'-'+render[1][:8] if render else 'Original')+'.mp4"')
                self.end_headers()
                with source.open('rb') as data:
                    data.seek(start);remaining=end-start+1
                    while remaining>0:
                        chunk=data.read(min(65536,remaining))
                        if not chunk:break
                        self.wfile.write(chunk);remaining-=len(chunk)
                return
            if path=='/api/video-editor':
                if self.server.device_auth or not ipaddress.ip_address(self.client_address[0]).is_loopback:return self._json({'error':'Videoschnitt bitte direkt am Mac verwenden.'},403)
                return self._json(app.video_editor.snapshot())
            if path=='/api/objects/info':
                from .object_models import capabilities
                return self._json(capabilities())
            static = {'/': 'device.html' if self.server.device_auth or re.search(r'iPhone|iPad|iPod|Macintosh.*Mobile',self.headers.get('User-Agent',''),re.I) else 'index.html', '/index.html': 'index.html', '/mobile':'mobile.html','/mobile-app.js':'mobile-app.js','/boot.js':'boot.js','/task-board.js':'task-board.js','/discover.js':'discover.js','/quest':'aeris.html','/quest-assistant.js':'quest-assistant.js','/quest-hands.js':'quest-hands.js','/aeris':'aeris.html','/aeris.js':'aeris.js','/aeris-assistant.js':'aeris-assistant.js','/aeris-xr.js':'aeris-xr.js','/aeris-pose.js':'aeris-pose.js','/vr-guide':'vr-guide.html','/video-editor':'video-editor.html','/video-editor.js':'video-editor.js','/video-renderer.js':'video-renderer.js','/companion':'call.html','/companion-actions.js':'companion-actions.js','/companion.js':'companion.js','/companion.css':'companion.css','/jarvis-orb.js':'jarvis-orb.js','/call':'call.html','/call-bridge.js':'call-bridge.js','/aeris-model.js':'aeris-model.js','/aeris-projects.js':'aeris-projects.js','/aeris-tracking.js':'aeris-tracking.js','/video-call.js':'video-call.js','/video-call.css':'video-call.css','/aeris-gestures.js':'aeris-gestures.js','/aeris-shell.css':'aeris-shell.css','/aeris-shell.js':'aeris-shell.js','/aeris-icon.svg':'aeris-icon.svg','/aeris-sw.js':'aeris-sw.js',
                      '/device-polish.css':'device-polish.css','/quick-help.js':'quick-help.js','/contacts-panel':'contacts-panel.html','/contacts-panel.js':'contacts-panel.js','/tablet':'device.html','/brands':'device.html','/device-app.js':'device-app.js','/contact-request.js':'contact-request.js','/device-desk.js':'device-desk.js','/device-business.js':'device-business.js','/hud-core.js':'hud-core.js','/device-ai.js':'device-ai.js','/device-store.js':'device-store.js','/device-style.css':'device-style.css','/manifest.webmanifest':'manifest.webmanifest','/app-icon.png':'app-icon.png','/style.css': 'style.css', '/app.js': 'app.js', '/pair.js':'pair.js', '/qr.js':'qr.js', '/extras.js':'extras.js', '/extras.css':'extras.css', '/world.geojson':'world.geojson', '/globe.js':'globe.js', '/office.js':'office.js','/office-3d.js':'office-3d.js', '/lowpoly-stage.js':'lowpoly-stage.js', '/artifacts.js':'artifacts.js', '/jarvis-voice.js':'jarvis-voice.js', '/voice-worker.js':'voice-worker.js', '/conversation.js':'conversation.js', '/mini-hub.js':'mini-hub.js', '/world-news.js':'world-news.js', '/astra.js':'astra.js', '/astra.css':'astra.css', '/astra-panel.html':'astra-panel.html', '/astra-panel.js':'astra-panel.js'}
            for name in ['three.module.min.js','GLTFLoader.js','OrbitControls.js','BufferGeometryUtils.js','RoomEnvironment.js','LICENSE','NOTICE.txt']:
                static['/vendor/three/'+name]='vendor/three/'+name
            static.update({'/workshop-conversation.js':'workshop-conversation.js','/workshop.js':'workshop.js','/workshop.css':'workshop.css','/personal-brain.js':'personal-brain.js','/vendor/brain/fsaverage5.bin':'vendor/brain/fsaverage5.bin','/vendor/brain/LICENSE.txt':'vendor/brain/LICENSE.txt','/vendor/brain/NOTICE.txt':'vendor/brain/NOTICE.txt','/personal-store.js':'personal-store.js','/personal-memory.js':'personal-memory.js','/personal-memory.css':'personal-memory.css','/offline-ready.js':'offline-ready.js','/offline-ready.css':'offline-ready.css','/invention-lab.js':'invention-lab.js','/invention-lab.css':'invention-lab.css','/layout-switch.js':'layout-switch.js','/layout-switch.css':'layout-switch.css','/code-companion.js':'code-companion.js','/code-room.js':'code-room.js','/code-room.css':'code-room.css','/studio-tools.js':'studio-tools.js','/studio-tools.css':'studio-tools.css','/chess-pieces.js':'chess-pieces.js','/play-chess.js':'play-chess.js','/chess-ai.js':'chess-ai.js','/chess-worker.js':'chess-worker.js','/vendor/chess/chess.js':'vendor/chess/chess.js','/vendor/chess/LICENSE':'vendor/chess/LICENSE','/vendor/chess/NOTICE.txt':'vendor/chess/NOTICE.txt','/play.js':'play.js','/play.css':'play.css','/object-viewer.js':'object-viewer.js','/object-viewer.css':'object-viewer.css'})
            for name in ['ESpeak.js','mespeak.js','config.json','jarvis-de.json','de.json','COPYING','NOTICE.txt','UPSTREAM-README.md','mespeak-2.0.2-source.tgz','speak-source-9c6f642.tar.gz']:
                static['/vendor/voice/'+name]='vendor/voice/'+name
            if path in static:
                file = FRONTEND / static[path]
                body = file.read_bytes()
                content_type = mimetypes.guess_type(file.name)[0] or 'application/octet-stream'
                self._headers(200, content_type + '; charset=utf-8', len(body))
                return self.wfile.write(body)
        elif method == 'DELETE' and path == '/api/history':
            return self._json(app.clear_chat())
        elif method in {'POST', 'PUT', 'PATCH'} or method=='DELETE' and path=='/api/personal-profile':
            if method=='POST' and path=='/api/video-editor/upload':
                if self.server.device_auth or not ipaddress.ip_address(self.client_address[0]).is_loopback:return self._json({'error':'Videoimport bitte direkt am Mac verwenden.'},403)
                # Raw bytes are streamed before the small JSON-body reader.
                self.close_connection=True
                if self.headers.get('Transfer-Encoding') or self.headers.get_content_type()!='application/octet-stream':raise ValueError('Videodatei mit bekannter Länge erforderlich.')
                try:length=int(self.headers.get('Content-Length','0'))
                except ValueError:raise ValueError('Ungültige Dateigröße.') from None
                return self._json({'assets':app.video_editor.upload(self.rfile,length,unquote(self.headers.get('X-Video-Name','clip.mp4')))})
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
                if path=='/api/desktop/open-accessibility':
                    if platform.system()!='Darwin':raise ValueError('Diese Freigabe wird direkt am Mac eingerichtet.')
                    import subprocess
                    subprocess.run(['/usr/bin/open','x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility'],check=True,timeout=5)
                    return self._json({'ok':True})
                if path=='/api/desktop/panel-ready':return self._json(app.desktop.panel_ready())
                if path=='/api/desktop/stop':return self._json(app.desktop.stop())
                if path=='/api/desktop/panel':
                    port=self.server.server_port
                    return self._json(app.desktop.open_panel(('https' if self.server.secure else 'http')+'://127.0.0.1:'+str(port)+'/astra-panel.html'))
            if method=='POST' and path in {'/api/hub/news','/api/hub/channels'}:
                if body:raise ValueError('Keine Parameter für die Hub-Aktualisierung erforderlich.')
                return self._json(app.hub.news() if path.endswith('/news') else app.hub.channels())
            if method=='POST' and path=='/api/natural-voice/install':
                if self.server.device_auth or not ipaddress.ip_address(self.client_address[0]).is_loopback:return self._json({'error':'Thorsten bitte direkt am Mac einrichten.'},403)
                if body:raise ValueError('Keine Parameter für die Thorsten-Einrichtung erforderlich.')
                return self._json(app.install_thorsten())
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
                return self._json({'ok':True},cookie='jarvis_device='+session+'; Path=/; Secure; HttpOnly; SameSite=Strict; Max-Age=2592000')
            if method=='POST' and path in {'/api/video-editor/choose','/api/video-editor/start','/api/video-editor/stop','/api/video-editor/assist','/api/video-editor/plan','/api/video-editor/assist-plan','/api/video-editor/story'}:
                if self.server.device_auth or not ipaddress.ip_address(self.client_address[0]).is_loopback:return self._json({'error':'Videoschnitt bitte direkt am Mac verwenden.'},403)
                if path.endswith('/choose'):
                    if body:raise ValueError('Keine Dateipfade aus dem Browser angeben. Die Dateiauswahl am Mac verwenden.')
                    return self._json({'assets':app.video_editor.choose()})
                if path.endswith('/stop'):
                    if set(body)!={'id'}:raise ValueError('Auftragskennung erforderlich.')
                    return self._json(app.video_editor.stop(body['id']))
                if path.endswith('/story'):
                    if not app.chat_lock.acquire(blocking=False):raise ProviderError('Eine KI-Anfrage läuft bereits.',409)
                    try:return self._json(app.video_editor.story(app,body))
                    finally:app.chat_lock.release()
                if path.endswith('/plan'):return self._json(app.video_editor.start(body,plan_only=True))
                if path.endswith('/assist') or path.endswith('/assist-plan'):
                    if not app.chat_lock.acquire(blocking=False):raise ProviderError('Eine KI-Anfrage läuft bereits. Bitte kurz warten.',409)
                    try:return self._json(app.video_editor.assist(app,body,plan_only=path.endswith('/assist-plan')),202)
                    finally:app.chat_lock.release()
                return self._json(app.video_editor.start(body),202)
            if method=='POST' and path in {'/api/companion/open','/api/companion/mode','/api/companion/close','/api/companion/browser','/api/companion/screen','/api/companion/motion','/api/companion/editor'}:
                if self.server.device_auth or not ipaddress.ip_address(self.client_address[0]).is_loopback:return self._json({'error':'Das Mac-Fenster bitte direkt am Mac öffnen.'},403)
                if path.endswith('/motion'):
                    if set(body)!={'enabled'}:raise ValueError('Nur den Bewegungsstatus angeben.')
                    return self._json(app.companion_window.motion(body['enabled']))
                if path.endswith('/editor'):
                    if set(body)-{'budget_minutes','animation'}:raise ValueError('Nur die Arbeitszeit angeben.')
                    budget=body.get('budget_minutes')
                    if budget is not None and (isinstance(budget,bool) or not isinstance(budget,(int,float)) or not 1<=budget<=120):raise ValueError('Arbeitszeit zwischen 1 und 120 Minuten angeben.')
                    animation=body.get('animation')
                    if animation is not None and (not isinstance(animation,str) or not 1<=len(animation)<=1500):raise ValueError('Animationswunsch bis 1500 Zeichen angeben.')
                    import webbrowser
                    from urllib.parse import urlencode
                    query=urlencode({**({'budget':budget} if budget else {}),**({'animation':animation} if animation else {})})
                    webbrowser.open(('https' if self.server.secure else 'http')+'://localhost:'+str(self.server.server_port)+'/video-editor'+('?'+query if query else ''));return self._json({'ok':True})
                if path.endswith('/browser'):
                    if body:raise ValueError('Keine Parameter erforderlich.')
                    import webbrowser
                    webbrowser.open(('https' if self.server.secure else 'http')+'://localhost:'+str(self.server.server_port)+'/companion?mode=helper');return self._json({'ok':True})
                if path.endswith('/screen'):
                    if set(body)!={'action'} or body['action'] not in {'start','stop'}:raise ValueError('Bildschirmfreigabe starten oder stoppen.')
                    return self._json(app.companion_window.start_screen() if body['action']=='start' else app.companion_window.screen.stop())
                if path.endswith('/close'):
                    if body:raise ValueError('Keine Parameter erforderlich.')
                    app.companion_window.close();return self._json({'ok':True})
                if set(body)!={'mode'}:raise ValueError('Nur die Helferansicht angeben.')
                if path.endswith('/mode'):return self._json(app.companion_window.change(body['mode']))
                return self._json(app.companion_window.open(('https' if self.server.secure else 'http')+'://localhost:'+str(self.server.server_port)+'/companion?native=1',body['mode']))
            if method=='POST' and path in {'/api/communication/prepare','/api/communication/send','/api/communication/cancel'}:
                actor=self.client_address[0]+'|'+self.headers.get('Cookie','')
                if path.endswith('/prepare'):return self._json(app.confirmed_send.prepare(body,actor))
                if path.endswith('/send'):return self._json(app.confirmed_send.execute(body,actor))
                if set(body)!={'id'} or not isinstance(body['id'],str):raise ValueError('Ungültige Versandbestätigung.')
                return self._json(app.confirmed_send.cancel(body['id'],actor))
            if method=='POST' and path in {'/api/apple-contacts/open','/api/apple-contacts/selected'}:
                if body:raise ValueError('Keine Suchbegriffe oder Kontaktdaten angeben.')
                from . import apple_contacts
                return self._json(apple_contacts.open_contacts() if path.endswith('/open') else apple_contacts.selected())
            if method in {'PUT','DELETE'} and path=='/api/personal-profile':
                if method=='PUT':
                    if set(body)!={'profile','expected'}:raise ValueError('Profil und aktuelle Fassung erforderlich.')
                    return self._json(app.personal_profile.save(body['profile'],body['expected']))
                if set(body)!={'expected'}:raise ValueError('Nur die aktuelle Profilfassung angeben.')
                return self._json(app.personal_profile.forget(body['expected']))
            if method=='POST' and path.startswith('/api/code-room/'):
                owner=self.client_address[0]+'|'+self.headers.get('Cookie','')
                if path=='/api/code-room/talk':return self._json(app.code_room.talk(owner,body))
                if path=='/api/code-room/studio/prepare':
                    if body:raise ValueError('Keine Parameter erforderlich.')
                    return self._json(app.studio_bridge.prepare(owner))
                if path=='/api/code-room/studio/reconnect':
                    if body:raise ValueError('Keine Parameter erforderlich.')
                    return self._json(app.studio_bridge.reconnect(owner))
                if path=='/api/code-room/studio/build':return self._json(app.studio_bridge.queue(owner,body))
                if path=='/api/code-room/studio/disconnect':
                    if body:raise ValueError('Keine Parameter erforderlich.')
                    return self._json(app.studio_bridge.disconnect(owner))
                if path=='/api/code-room/jobs':return self._json(app.code_room.submit(body,owner),202)
                match=re.fullmatch(r'/api/code-room/jobs/([a-f0-9]{32})/(save|cancel|download)',path)
                if not match or body:raise ValueError('Ungültige Code-Aktion.')
                if match[2]=='download':
                    data=app.code_room.archive(match[1],owner);self._headers(200,'application/zip',len(data));return self.wfile.write(data)
                return self._json(app.code_room.action(match[1],owner,match[2]))
            if method=='POST' and path in {'/api/workshop/jobs','/api/workshop/jobs/status','/api/workshop/jobs/cancel'}:
                owner=self.client_address[0]+'|'+self.headers.get('Cookie','')
                if path=='/api/workshop/jobs':return self._json(app.workshop.submit(body,owner),202)
                if set(body)!={'id'}:raise ValueError('Bitte nur die Werkstatt-Auftragskennung angeben.')
                return self._json(app.workshop.cancel(body['id'],owner)if path.endswith('/cancel')else app.workshop.status(body['id'],owner))
            if method=='POST' and path=='/api/workshop/research':
                if set(body)!={'query'} or not isinstance(body['query'],str) or not 1<=len(body['query'].strip())<=500:raise ValueError('Bitte eine Baufrage mit höchstens 500 Zeichen angeben.')
                if not app.store.settings().get('web_enabled',True):return self._json({'reply':'Die öffentliche Websuche ist ausgeschaltet, Sir.','sources':[]})
                return self._json(app.web.answer({'kind':'web','query':body['query'].strip()}))
            if method=='POST' and path=='/api/workshop/hologram-guide':
                from .hologram_project import guide as hologram_guide
                return self._json(hologram_guide(body))
            if method=='POST' and path=='/api/workshop/hologram-project':
                from .hologram_project import design as hologram_design
                return self._json(hologram_design(body))
            if method=='POST' and path=='/api/workshop/design':
                from .workshop import design
                return self._json(design(body,app=app))
            if method=='POST' and path=='/api/inventions/design':
                from .inventions import design
                if not app.chat_lock.acquire(blocking=False):raise ProviderError('Die lokale KI arbeitet gerade. Bitte den laufenden Auftrag abwarten.',409)
                try:return self._json(design(app,body))
                finally:app.chat_lock.release()
            if method=='POST' and path=='/api/device-ai/chat':
                if set(body)-{'mode','text','history','profile'}:raise ValueError('Unbekannte Geräte-Chatfelder.')
                mode=body.get('mode','jarvis')
                if mode not in {'jarvis','astra','aeris'}:raise ValueError('Unbekannter Assistent.')
                from .video_call import answer
                from .personal_profile import validate as validate_profile
                personal=validate_profile(body['profile']) if 'profile' in body else None
                payload={k:v for k,v in body.items() if k not in {'mode','profile'}}
                if not app.chat_lock.acquire(blocking=False):raise ProviderError('Eine lokale KI-Anfrage läuft bereits.',409)
                try:return self._json(answer(app,payload,identity=mode,text_only=True,personal_profile=personal))
                finally:app.chat_lock.release()
            if method=='POST' and path=='/api/device-ai/prepare':
                if body:raise ValueError('Keine Parameter für die Geräte-Einrichtung erforderlich.')
                return self._json(app.device_ai.prepare())
            if method=='POST' and path=='/api/brands':return self._json({'profile':app.brands.save(body)})
            if method=='POST' and path=='/api/quest-link/start':
                if self.server.device_auth or not ipaddress.ip_address(self.client_address[0]).is_loopback:return self._json({'error':'Den Brillen-Kopplungslink bitte direkt am Mac erstellen.'},403)
                if body:raise ValueError('Keine Parameter erforderlich.')
                return self._json(app.mobile.start_quest())
            if method=='POST' and path in {'/api/quest-window/start','/api/quest-window/stop'}:
                if self.server.device_auth or not ipaddress.ip_address(self.client_address[0]).is_loopback:return self._json({'error':'Den Brillen-Link bitte direkt am Mac erstellen.'},403)
                if body:raise ValueError('Keine Parameter erforderlich.')
                if path.endswith('/start'):return self._json(app.quest_window.start())
                app.quest_window.stop();return self._json({'ok':True})
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
            if method=='POST' and path=='/api/video-call':
                if body.get('native_screen') and (self.server.device_auth or not ipaddress.ip_address(self.client_address[0]).is_loopback):return self._json({'error':'Native Bildschirmaufnahme ist nur direkt am Mac erlaubt.'},403)
                if not app.chat_lock.acquire(blocking=False):raise ProviderError('Eine Anfrage läuft bereits. Bitte kurz warten.',409)
                try:
                    from .video_call import answer
                    return self._json(answer(app,body))
                finally:app.chat_lock.release()
            if method=='POST' and path=='/api/objects/load':
                if set(body)!={'url'}:raise ValueError('Bitte genau einen Modell-Link angeben.')
                from .object_models import load_model
                model=load_model(body['url'])
                self._headers(200,'model/gltf-binary',len(model))
                return self.wfile.write(model)
            if method=='POST' and path=='/api/aeris/pose':
                if set(body)!={'image'} or not isinstance(body['image'],str) or len(body['image'])>400000:raise ValueError('Bitte ein JPEG-Frame bis 300 KB senden.')
                try:image=base64.b64decode(body['image'],validate=True)
                except ValueError:raise ValueError('Ungültiges Kamerabild.') from None
                if not app.pose_lock.acquire(blocking=False):return self._json({'error':'Die Pose-Auswertung ist belegt.'},409)
                try:
                    from .arm_pose import detect
                    return self._json(detect(image))
                finally:app.pose_lock.release()
            if method == 'POST' and path == '/api/chat':
                text=body.get('text')
                if self.server.device_auth and isinstance(text,str):
                    pending=app.dialogue.get()
                    native=re.match(r'^(?:(?:jarvis|astra|asta)[, :]+)?(?:öffne|starte|klicke?|bewege?|tippe)\b',text,re.I) or note_request(text) is not None
                    if native and not (pending and pending['kind']=='web_open'):
                        url=re.search(r'https://[^\s]+',text)
                        if url:
                            from .web_assistant import public_url
                            if public_url(url[0]):return self._json({'reply':'Hier ist die Website, Sir. Tippe auf den Link.','proposals':[],'sources':[{'title':'Website','url':url[0]}]})
                        return self._json({'reply':'Desktop-Aufträge bitte in Jarvis direkt auf dem Mac starten. Website- und Film-Aufträge sowie Chat funktionieren hier auf dem Handy.','proposals':[]})
                if body.get('mode') in {'jarvis','astra','aeris'}:
                    with app.store.identity_context(body['mode']):return self._json(app.chat(text))
                return self._json(app.chat(text))
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
    parser.add_argument('--easy-companion',action='store_true',help='Vorhandene lokale KI mit schwebendem Helfer statt Hauptbrowser starten')
    parser.add_argument('--open-companion',action='store_true',help='Schwebenden Jarvis-Helfer am Mac öffnen')
    parser.add_argument('--local-only', action='store_true', help='Lokalen Modus ohne API-Schlüsselbund starten')
    args = parser.parse_args(argv)
    if args.setup_small_ai or args.easy_local or args.easy_companion:
        from .easy_start import run
        try:
            if args.easy_companion:run(setup=False,companion=True)
            else:run(setup=args.setup_small_ai)
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
    try:
        if app.mobile.resume():print('Handy-Zugang im Heimnetz wieder gestartet.',flush=True)
    except (OSError,ValueError):print('Handy-Zugang konnte nicht starten. Am Mac „Handy verbinden“ öffnen und das WLAN prüfen.',flush=True)
    if args.open_companion:
        try:app.companion_window.open(('https' if args.cert else 'http')+f'://localhost:{server.server_port}/companion?native=1','island')
        except (OSError,ValueError) as error:
            print(str(error)+f' Browser-Helfer: http://localhost:{server.server_port}/companion',flush=True)
            import webbrowser
            webbrowser.open(f'http://localhost:{server.server_port}/companion?mode=helper')
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
            app.studio_bridge.stop()
            app.office.stop()
            app.workshop.stop()
            app.mobile.stop(revoke=False)
            app.quest_window.stop()
            app.companion_window.close()
            app.video_editor.close()
        finally:
            server.server_close()


if __name__ == '__main__':
    main()
