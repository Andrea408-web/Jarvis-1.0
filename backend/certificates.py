"""Explicit, optional certificate setup for an official python.org Mac install.

Nothing runs on import or ordinary application startup. The caller must invoke
this helper only after the user chooses the certificate-repair command. The
official script may install/update certifi; no alternative installer, sudo,
certificate-verification bypass or implicit system permission change is used.
"""
from __future__ import annotations

from pathlib import Path
import platform
import re
import stat
import subprocess
import sys


def _runtime_layout():
    """Return this interpreter's actual version and resolved installation root."""
    version = f"{sys.version_info.major}.{sys.version_info.minor}"
    return version, Path(sys.base_prefix).resolve()


def _official_script(version):
    script = Path(f"/Applications/Python {version}/Install Certificates.command")
    try:
        metadata = script.lstat()
        # Reject symbolic links and other nonregular files, including a path
        # redirected through a symlinked parent directory.
        if not stat.S_ISREG(metadata.st_mode) or script.resolve(strict=True) != script:
            raise ValueError("Das Zertifikatsprogramm muss eine reguläre Datei ohne symbolische Links am erwarteten Ort sein.")
    except OSError:
        raise ValueError("Das passende offizielle Programm „Install Certificates.command“ wurde im Programme/Python-Ordner nicht gefunden. Bitte die python.org-Installation prüfen.") from None
    return script


def repair_certificates():
    """Run only the installed official helper for this exact Python version.

    Completion proves only the helper's exit status. It does not prove a remote
    API connection, provider access or remaining free provider quota.
    """
    if platform.system() != "Darwin":
        raise ValueError("Die Zertifikatsreparatur ist nur auf dem Mac verfügbar. Auf dieser Entwicklungsumgebung wird nichts installiert oder verändert.")
    try:
        version, prefix = _runtime_layout()
    except (OSError, RuntimeError):
        raise ValueError("Der Installationspfad dieses Python konnte nicht sicher bestimmt werden. Es wurde kein Zertifikatsprogramm gestartet.") from None
    if (not isinstance(version, str) or not re.fullmatch(r"[0-9]+\.[0-9]+", version)
            or prefix != Path(f"/Library/Frameworks/Python.framework/Versions/{version}")):
        raise ValueError("Diese automatische Hilfe unterstützt nur die passende python.org-Framework-Installation. Bitte die Zertifikatseinrichtung Ihrer Python-Distribution prüfen; es wurde nichts installiert.")
    script = _official_script(version)
    try:
        result = subprocess.run(
            [str(script)], capture_output=True, text=True, timeout=120, check=False,
        )
    except subprocess.TimeoutExpired:
        raise ValueError("Das offizielle Zertifikatsprogramm wurde nach 120 Sekunden abgebrochen. Bitte die Python-Installation und Internetverbindung prüfen. Die Zertifikatsprüfung bleibt aktiviert.") from None
    except (OSError, subprocess.SubprocessError, UnicodeError):
        raise ValueError("Das offizielle Zertifikatsprogramm konnte nicht ausgeführt werden. Bitte die python.org-Installation und das Programm im Programme/Python-Ordner prüfen.") from None
    if result.returncode != 0:
        raise ValueError("Das offizielle Zertifikatsprogramm konnte nicht erfolgreich abgeschlossen werden. Bitte Internetverbindung und die passende python.org-Installation prüfen. Die Zertifikatsprüfung bleibt aktiviert.")
    return ("Das offizielle Python-Zertifikatsprogramm wurde abgeschlossen. "
            "Gemini und ElevenLabs wurden damit noch nicht auf Erreichbarkeit geprüft. "
            "Starten Sie JARVIS neu und verwenden Sie anschließend den Verbindungstest.")
