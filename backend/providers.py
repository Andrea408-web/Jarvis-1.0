"""Small verified-HTTPS transport shared by the optional cloud integrations.

No upstream error bodies, URLs, headers or credentials enter application errors.
Requests deliberately have no automatic retry: a failed call can still consume
provider quota. TLS verification and the platform's inherited proxy remain active.
"""

import errno
import json
import os
import socket
import ssl
import urllib.error
import urllib.request
from urllib.parse import urlsplit


_PROVIDER_NAMES = {
    "generativelanguage.googleapis.com": "Google Gemini",
    "api.elevenlabs.io": "ElevenLabs",
}


def _provider_name(url):
    # Names come only from this fixed mapping, never from a raw URL or an error.
    try:
        return _PROVIDER_NAMES.get(urlsplit(url).hostname, "Der Anbieter")
    except (TypeError, ValueError):
        return "Der Anbieter"


def _network_message(provider, error):
    """Classify typed network errors without exposing exception text.

    urllib wraps platform exceptions in URLError.reason. Some proxy layers add
    more than one wrapper, so follow a bounded, cycle-safe exception chain.
    Classification does not prove what needs changing on the user's machine.
    """
    pending, seen, causes = [error], set(), []
    while pending and len(seen) < 12:
        current = pending.pop(0)
        if id(current) in seen:
            continue
        seen.add(id(current))
        causes.append(current)
        if isinstance(current, urllib.error.URLError):
            pending.append(current.reason)
        if isinstance(current, BaseException):
            for related in (current.__cause__, current.__context__):
                if related is not None:
                    pending.append(related)
    certificate_failure = any(
        isinstance(item, ssl.SSLCertVerificationError)
        or (isinstance(item, ssl.SSLError) and getattr(item, "reason", None) == "CERTIFICATE_VERIFY_FAILED")
        or (isinstance(item, str) and "CERTIFICATE_VERIFY_FAILED" in item)
        for item in causes
    )
    if certificate_failure:
        return (
            f"Python kann das HTTPS-Zertifikat für {provider} nicht prüfen. "
            "Prüfen Sie Datum/Uhrzeit und den Zertifikatsspeicher. "
            "Bei Python von python.org auf macOS: Prüfen Sie die Zertifikatseinrichtung "
            "mit „Install Certificates.command“ im passenden Programme/Python-Ordner. "
            "Die Zertifikatsprüfung bleibt aktiviert."
        )
    if any(isinstance(item, TimeoutError) or (isinstance(item, OSError) and item.errno == errno.ETIMEDOUT) for item in causes):
        return f"{provider} hat nicht innerhalb der Wartezeit geantwortet. Prüfen Sie die Verbindung; es erfolgt kein automatischer Neuversuch."
    if any(isinstance(item, socket.gaierror) for item in causes):
        return f"Die Netzwerkadresse für {provider} konnte nicht aufgelöst werden (DNS). Prüfen Sie Internetverbindung, DNS und gegebenenfalls Proxy oder VPN."
    if any(isinstance(item, ConnectionRefusedError) or (isinstance(item, OSError) and item.errno == errno.ECONNREFUSED) for item in causes):
        return f"Die Verbindung zu {provider} wurde abgelehnt. Prüfen Sie Netzwerk, Firewall und gegebenenfalls Proxy oder VPN."
    if any(isinstance(item, ssl.SSLError) for item in causes):
        return f"Die sichere HTTPS-Verbindung zu {provider} konnte nicht aufgebaut werden. Prüfen Sie die Python-/TLS-Einrichtung und gegebenenfalls den Proxy. Die Zertifikatsprüfung bleibt aktiviert."
    if any(isinstance(item, OSError) and item.errno in {errno.ENETDOWN, errno.ENETUNREACH, errno.EHOSTUNREACH} for item in causes):
        return f"Für {provider} ist momentan keine Netzwerkverbindung verfügbar. Prüfen Sie Internetverbindung und gegebenenfalls Proxy oder VPN."
    if any(isinstance(item, ConnectionError) for item in causes):
        return f"Die Verbindung zu {provider} wurde unterbrochen. Prüfen Sie das Netzwerk; es erfolgt kein automatischer Neuversuch."
    return f"{provider} ist momentan nicht erreichbar. Prüfen Sie Internetverbindung und gegebenenfalls Proxy oder VPN."


def safe_network_message(url, error):
    """Public diagnostic helper: fixed provider name and safe error category."""
    return _network_message(_provider_name(url), error)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # API credentials must never follow an upstream redirect to another host.
        raise urllib.error.HTTPError(req.full_url, code, "Redirect blocked", headers, fp)


def _open_request(request, timeout=45):
    # build_opener retains the default proxy handler and verified HTTPS handler.
    return urllib.request.build_opener(_NoRedirect()).open(request, timeout=timeout)


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
    provider = _provider_name(url)
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
                f"{provider} hat den Zugriff abgelehnt. Prüfen Sie Schlüssel, API-Freigabe und Berechtigungen.",
                502,
            ) from None
        if status == 429:
            raise ProviderError(
                f"Das Kontingent oder Anfragelimit für {provider} ist erreicht. Es erfolgt kein automatischer Neuversuch.",
                429,
            ) from None
        if status == 404:
            raise ProviderError(f"Modell oder Stimme ist bei {provider} nicht verfügbar.", 502) from None
        raise ProviderError(f"{provider} konnte die Anfrage nicht verarbeiten.", 502) from None
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise ProviderError(safe_network_message(url, error), 502) from None
    if len(body) > max_bytes:
        raise ProviderError(f"Die Antwort von {provider} überschreitet das Größenlimit.", 502)
    if content_type != expected_type:
        raise ProviderError(f"{provider} hat ein unerwartetes Antwortformat geliefert.", 502)
    return body


def request_json(url, payload, headers):
    raw = request_bytes(url, payload, headers)
    try:
        result = json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        raise ProviderError(f"Die Antwort von {_provider_name(url)} ist ungültig.", 502) from None
    if not isinstance(result, dict):
        raise ProviderError(f"Die Antwort von {_provider_name(url)} ist ungültig.", 502)
    return result
