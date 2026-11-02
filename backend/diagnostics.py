"""Explicit, read-only HTTPS checks without keys or generated content."""
import urllib.error
import urllib.request

from .providers import _open_request, safe_network_message


_ENDPOINTS = {
    'gemini': ('Google Gemini', 'https://generativelanguage.googleapis.com/v1beta/models'),
    'elevenlabs': ('ElevenLabs', 'https://api.elevenlabs.io/v1/voices'),
}


def check_connection(provider, opener=None):
    if not isinstance(provider, str) or provider not in _ENDPOINTS:
        raise ValueError('Bitte Gemini oder ElevenLabs als Anbieter wählen.')
    name, url = _ENDPOINTS[provider]
    request = urllib.request.Request(url, method='GET', headers={'Accept': 'application/json'})
    try:
        response = (opener or _open_request)(request, timeout=10)
        try:
            status = response.status
        finally:
            response.close()
    except urllib.error.HTTPError as error:
        status = error.code
        error.close()
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        return {'provider': provider, 'ok': False, 'http_status': None,
                'message': safe_network_message(url, error)}
    if status in {200, 400, 401}:
        message = (f'{name}: HTTPS-Antwort erhalten (HTTP {status}). '
                   'Dieser Test verwendet keinen API-Schlüssel; Schlüsselgültigkeit, Stimme und Kontingent wurden nicht geprüft.')
        ok = True
    elif status == 403:
        message = (f'{name}: HTTP 403 – Zugriff abgelehnt. Eine Netzrichtlinie oder der Anbieter kann den Zugriff sperren. '
                   'Dieser Test verwendet keinen API-Schlüssel; eine funktionierende Anbieteranmeldung ist damit nicht bestätigt.')
        ok = False
    else:
        message = (f'{name}: HTTP-Antwort {status} erhalten. Die Verbindung konnte damit nicht vollständig geprüft werden. '
                   'Es wurde kein API-Schlüssel gesendet und kein Text oder Audio erzeugt.')
        ok = False
    return {'provider': provider, 'ok': ok, 'http_status': status, 'message': message}
