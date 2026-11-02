"""Configure cloud credentials without files, command-line secrets or logs.

Session-only configuration works on every platform. Explicit persistence uses
the current user's macOS Keychain. Native commands are tested with controlled
subprocess responses; their actual behavior still needs a physical Mac check.
"""
from __future__ import annotations

import hmac
import os
import platform
import re
import subprocess
import threading

from .providers import provider_status


_PROVIDERS = {
    "gemini": ("GEMINI_API_KEY", "com.jarvis.gemini"),
    "elevenlabs": ("ELEVENLABS_API_KEY", "com.jarvis.elevenlabs"),
}
_LOCK = threading.RLock()
_KEY_PATTERN = re.compile(r"[A-Za-z0-9_.-]{10,512}", re.ASCII)


def _provider(provider):
    if not isinstance(provider, str) or provider not in _PROVIDERS:
        raise ValueError("Bitte Gemini oder ElevenLabs als Anbieter wählen.")
    return _PROVIDERS[provider]


def _valid_key(value):
    return isinstance(value, str) and _KEY_PATTERN.fullmatch(value) is not None


def _read_keychain(service):
    try:
        result = subprocess.run(
            ["/usr/bin/security", "find-generic-password", "-a", "jarvis", "-s", service, "-w"],
            capture_output=True, text=True, timeout=10, check=False,
        )
    except (OSError, subprocess.SubprocessError, UnicodeError):
        return None
    if result.returncode != 0:
        return None
    # security adds a line terminator. Do not trim spaces or otherwise turn an
    # invalid stored credential into an accepted one.
    value = result.stdout.rstrip("\r\n")
    return value if _valid_key(value) else None


def _write_keychain(service, api_key):
    # Key alphabet and provider/service are validated before this command is
    # composed. No shell is used and the secret is sent through stdin only.
    command = f"add-generic-password -U -a jarvis -s {service} -w {api_key}\n"
    try:
        result = subprocess.run(
            ["/usr/bin/security", "-i"],
            input=command, capture_output=True, text=True, timeout=10, check=False,
        )
    except (OSError, subprocess.SubprocessError, UnicodeError):
        raise ValueError("Der macOS-Schlüsselbund ist nicht erreichbar. Der Schlüssel wurde nicht aktiviert.") from None
    if result.returncode != 0:
        raise ValueError("Der Schlüssel konnte nicht im macOS-Schlüsselbund gespeichert werden. Bitte die Systemfreigabe prüfen.")
    # Interactive security can report individual command failures on stderr.
    # Verify the stored value instead of trusting its process exit status alone.
    saved = _read_keychain(service)
    if saved is None or not hmac.compare_digest(saved, api_key):
        raise ValueError("Die Speicherung im macOS-Schlüsselbund konnte nicht bestätigt werden. Der Schlüssel wurde nicht aktiviert.")


def configure(provider, api_key, persist=True):
    """Set one provider key after validation and explicit persistence choice.

    Return presence metadata only. Configuration does not test a provider API,
    enable cloud services, change budgets or guarantee free provider quota.
    """
    variable, service = _provider(provider)
    if not _valid_key(api_key):
        raise ValueError("Der API-Schlüssel muss 10 bis 512 ASCII-Zeichen enthalten; erlaubt sind Buchstaben, Ziffern, Punkt, Unterstrich und Bindestrich.")
    if type(persist) is not bool:
        raise ValueError("Bitte ausdrücklich zwischen Sitzung und Schlüsselbund wählen.")
    with _LOCK:
        if persist:
            if platform.system() != "Darwin":
                raise ValueError("Dauerhaftes Speichern benötigt den macOS-Schlüsselbund. Bitte nur für diese Sitzung verwenden.")
            _write_keychain(service, api_key)
        # Do not replace a working environment binding if persistence failed.
        os.environ[variable] = api_key
    return {
        "provider": provider,
        "persisted": persist,
        "configured": True,
        "message": ("API-Schlüssel im macOS-Schlüsselbund gespeichert."
                    if persist else "API-Schlüssel nur für diese Serversitzung eingerichtet."),
    }


def load_saved_keys():
    """Load existing Mac keys without replacing injected environment bindings.

    A missing/locked Keychain must not prevent local-only startup. Return only
    presence flags, never key values or native command output.
    """
    with _LOCK:
        if platform.system() == "Darwin":
            for variable, service in _PROVIDERS.values():
                if os.environ.get(variable):
                    continue
                saved = _read_keychain(service)
                if saved is not None:
                    os.environ[variable] = saved
        return provider_status()
