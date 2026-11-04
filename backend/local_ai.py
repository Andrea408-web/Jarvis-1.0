"""Offline Ollama text chat. Fixed loopback destination, no keys or downloads."""
import json
import re
import urllib.error
import urllib.request

from .providers import ProviderError, _NoRedirect
from .persona import instruction as persona_instruction,correct_identity

BASE = 'http://127.0.0.1:11434'


def local_request(path, payload=None):
    if path not in {'/api/chat', '/api/tags'}:
        raise ValueError('Ungültige lokale Schnittstelle.')
    request = urllib.request.Request(BASE + path, data=None if payload is None else json.dumps(payload).encode(),
                                     headers={'Content-Type': 'application/json'})
    try:
        # Only the fixed loopback service bypasses an Internet proxy. Never
        # follow a redirect that could send conversation data outside the Mac.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect())
        with opener.open(request, timeout=120 if payload is not None else 5) as response:
            raw = response.read(1_000_001)
        if len(raw) > 1_000_000:
            raise ValueError()
        result = json.loads(raw)
        if not isinstance(result, dict):
            raise ValueError()
        return result
    except urllib.error.HTTPError as error:
        status = error.code
        error.close()
        message = ('Das lokale Modell fehlt. Lade es einmal in Ollama, zum Beispiel mit „ollama pull qwen2.5:1.5b“.'
                   if status == 404 else 'Ollama konnte die lokale Anfrage nicht verarbeiten. Bitte Modell und Ollama prüfen.')
        raise ProviderError(message, 502) from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise ProviderError('Die lokale KI ist nicht erreichbar. Bitte Ollama auf demselben Mac öffnen und ein Modell laden. Kein API-Schlüssel erforderlich.', 503) from None
    except (ValueError, UnicodeError):
        raise ProviderError('Ollama hat keine gültige lokale Antwort geliefert.', 502) from None


def validate_model(model):
    if (not isinstance(model, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/-]{0,119}', model)
            or 'cloud' in model.lower() or '://' in model):
        raise ValueError('Bitte einen lokalen Ollama-Modellnamen ohne Cloud-Modell oder Internetadresse wählen.')


def local_status():
    try:
        response = local_request('/api/tags')
        names = []
        for item in response.get('models', [])[:100]:
            if not isinstance(item, dict):
                continue
            name = item.get('name')
            try:
                validate_model(name)
                names.append(name)
            except ValueError:
                continue
        return {'ok': True, 'models': names, 'message': 'Ollama erreichbar. Lokal vorhandene Modelle: ' + (', '.join(names) or 'noch keines')}
    except (ProviderError, TypeError):
        return {'ok': False, 'models': [], 'message': 'Ollama ist nicht erreichbar. Bitte Ollama auf diesem Mac öffnen. Das Modell muss einmal heruntergeladen werden.'}


class LocalClient:
    def __init__(self, store, transport=None):
        self.store = store
        self.transport = transport or local_request

    def chat(self, text, conversation='default'):
        if not isinstance(text, str) or not text.strip() or len(text) > 6000:
            raise ProviderError('Bitte für das kleine lokale Modell 1 bis 6.000 Zeichen eingeben.')
        model = self.store.settings()['local_model']
        validate_model(model)
        messages, remaining = [], 6000
        history=self.store.history(conversation)[-12:]
        # A past gaming discussion is not a standing instruction for new topics.
        if not re.search(r'minecraft|pvp|bedrock|\bjava\b|weiter|dazu|darauf|genauer|das spiel',text,re.I):
            filtered=[];gaming=False
            for entry in history:
                if entry['role']=='user':gaming=bool(re.search(r'minecraft|pvp|bedrock|\bjava\b',entry['text'],re.I))
                if not gaming:filtered.append(entry)
            history=filtered
        for item in reversed(history):
            if item['role'] not in {'user', 'assistant'}:
                continue
            if len(item['text']) > remaining:
                break
            remaining -= len(item['text'])
            messages.append({'role': item['role'], 'content': item['text']})
        instruction=persona_instruction(self.store)
        payload = {'model': model, 'messages': [{'role': 'system', 'content': instruction}, *reversed(messages), {'role': 'user', 'content': text.strip()}],
                   'stream': False, 'options': {'num_ctx': 4096, 'num_predict': 512}, 'keep_alive': '5m'}
        result = self.transport('/api/chat', payload)
        message = result.get('message')
        reply = message.get('content') if isinstance(message, dict) else None
        if (result.get('done') is not True or not isinstance(reply, str) or not reply.strip()
                or len(reply) > 24000 or message.get('tool_calls')):
            raise ProviderError('Das lokale Modell hat keine abgeschlossene Textantwort geliefert.', 502)
        reply=correct_identity(reply,self.store)
        self.store.append('user', text.strip(), conversation)
        self.store.append('assistant', reply, conversation)
        return {'reply': reply, 'proposed_actions': [], 'conversation': conversation}

    def analyze_image(self, *args, **kwargs):
        raise ProviderError('Die lokale KI unterstützt hier Textgespräche. Bildanalyse ist in diesem Modus ausgeschaltet.', 409)
