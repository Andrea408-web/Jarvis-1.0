"""Small verified-HTTPS transport shared by the optional cloud integrations.

No upstream error bodies, URLs, headers or credentials enter application errors.
Requests deliberately have no automatic retry: a failed call can still consume
provider quota. TLS verification and the platform's inherited proxy remain active.
"""

import json
import os
import urllib.error
import urllib.request


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # API credentials must never follow an upstream redirect to another host.
        raise urllib.error.HTTPError(req.full_url, code, "Redirect blocked", headers, fp)


def _open_request(request):
    # build_opener retains the default proxy handler and verified HTTPS handler.
    return urllib.request.build_opener(_NoRedirect()).open(request, timeout=45)


class ProviderError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def provider_status():
    """Presence only; a configured key does not prove remote authorization."""
    return {
        "gemini_key_configured": bool(os.environ.get("GEMINI_API_KEY")),
        "elevenlabs_key_configured": bool(os.environ.get("ELEVENLABS_API_KEY")),
    }


def reserve(store, service, amount, limit):
    try:
        outcome = store.reserve_usage(service, amount, limit)
    except ValueError:
        raise ProviderError(
            "Das lokale Tageslimit ist erreicht. Bitte prüfen Sie die Nutzung in den Einstellungen.",
            429,
        ) from None
    if outcome is False:
        raise ProviderError("Das lokale Tageslimit ist erreicht.", 429)


def request_bytes(url, payload, headers, *, expected_type="application/json", max_bytes=2_000_000):
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json", **headers}, method="POST"
    )
    try:
        with _open_request(request) as response:
            content_type = response.headers.get("Content-Type", "").split(";", 1)[0].lower()
            body = response.read(max_bytes + 1)
    except urllib.error.HTTPError as error:
        status = error.code
        error.close()
        if status in (401, 403):
            raise ProviderError(
                "Der Anbieter hat den Zugriff abgelehnt. Prüfen Sie Schlüssel, API-Freigabe und Berechtigungen.",
                502,
            ) from None
        if status == 429:
            raise ProviderError(
                "Das Kontingent oder Anfragelimit des Anbieters ist erreicht. Es erfolgt kein automatischer Neuversuch.",
                429,
            ) from None
        if status == 404:
            raise ProviderError("Modell oder Stimme ist beim Anbieter nicht verfügbar.", 502) from None
        raise ProviderError("Der Anbieter konnte die Anfrage nicht verarbeiten.", 502) from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise ProviderError("Der Anbieter ist momentan nicht erreichbar.", 502) from None
    if len(body) > max_bytes:
        raise ProviderError("Die Antwort des Anbieters überschreitet das Größenlimit.", 502)
    if content_type != expected_type:
        raise ProviderError("Der Anbieter hat ein unerwartetes Antwortformat geliefert.", 502)
    return body


def request_json(url, payload, headers):
    raw = request_bytes(url, payload, headers)
    try:
        result = json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        raise ProviderError("Die Antwort des Anbieters ist ungültig.", 502) from None
    if not isinstance(result, dict):
        raise ProviderError("Die Antwort des Anbieters ist ungültig.", 502)
    return result
