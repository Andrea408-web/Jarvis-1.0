"""Small local model through llama.cpp, never a remote inference service."""
import json
import urllib.error
import urllib.request

from .local_ai import LocalClient
from .providers import ProviderError, _NoRedirect

BASE = 'http://127.0.0.1:8081'


def request_local(path, payload=None):
    if path not in {'/health', '/v1/chat/completions'}:
        raise ValueError('Ungültige lokale Schnittstelle.')
    request = urllib.request.Request(BASE + path, data=None if payload is None else json.dumps(payload).encode(), headers={'Content-Type':'application/json'})
    try:
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
        error.close()
        raise ProviderError('Die kleine lokale KI ist noch nicht bereit oder konnte die Anfrage nicht verarbeiten. Bitte das llama-server-Terminal prüfen.', 503) from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise ProviderError('Die kleine lokale KI läuft noch nicht. Bitte zuerst „1-JARVIS-einrichten.command“ ausführen, danach „2-JARVIS-starten.command“ verwenden. Kein Ollama und kein API-Schlüssel nötig.', 503) from None
    except (ValueError, UnicodeError):
        raise ProviderError('Die kleine lokale KI hat keine gültige Antwort geliefert.', 502) from None


def status():
    try:
        result = request_local('/health')
        ready = result.get('status') == 'ok'
        return {'ok': ready, 'message': 'llama.cpp meldet ein geladenes Modell.' if ready else 'llama.cpp lädt noch oder meldet keinen Bereitschaftsstatus.'}
    except ProviderError as error:
        return {'ok': False, 'message': str(error)}


class LlamaCppClient(LocalClient):
    def __init__(self, store, transport=None):
        self.store = store
        self.endpoint_transport = transport or request_local
        self.transport = self._adapt

    def _adapt(self, path, payload):
        # The actual model is the local GGUF loaded by llama-server. Never use
        # an HF URL, automatic model fetch, tools, or a cloud fallback here.
        result = self.endpoint_transport('/v1/chat/completions', {
            'messages': payload['messages'], 'stream': False, 'max_tokens': 512,
        })
        try:
            choice = result['choices'][0]
            if choice.get('finish_reason') not in {'stop', 'length'}:
                raise ValueError()
            message = choice['message']
            if message.get('tool_calls'):
                raise ValueError()
            return {'done': True, 'message': {'content': message['content']}}
        except (KeyError, IndexError, TypeError, ValueError):
            raise ProviderError('Das kleine Modell hat keine fertige Textantwort geliefert.', 502) from None
