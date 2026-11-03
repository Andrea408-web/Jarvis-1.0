"""Explicit launcher for user-provided llama.cpp and a small local GGUF."""
from pathlib import Path
import os
import platform
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent.parent
MODEL = 'qwen2.5-0.5b-instruct-q4_k_m.gguf'


def locate():
    if platform.system() != 'Darwin':
        raise ValueError('Dieser Starter ist für den Mac vorbereitet. Hier wird nichts installiert.')
    if (ROOT / '.jarvis' / 'installed.json').is_file():
        from .easy_setup import read_installation
        return read_installation()
    executable = ROOT / 'runtime' / 'llama-server'
    if not executable.is_file():
        found = shutil.which('llama-server')
        if not found:
            raise ValueError('llama-server fehlt. Bitte das offizielle llama.cpp-Paket passend zur Mac-Architektur herunterladen und dessen Dateien in den JARVIS-Unterordner runtime entpacken. Die Anleitung steht in docs/KLEINE-KI.md.')
        executable = Path(found)
    candidates = [ROOT / 'models' / MODEL, Path.home() / 'Downloads' / MODEL]
    model = next((p for p in candidates if p.is_file()), None)
    if model is None:
        raise ValueError('Das kleine Modell fehlt. Bitte die Datei ' + MODEL + ' in den JARVIS-Unterordner models oder in Downloads legen. Anleitung: docs/KLEINE-KI.md.')
    if not 1_000_000 <= model.stat().st_size <= 500 * 1024 * 1024:
        raise ValueError('Bitte das kleine Q4_K_M-Modell verwenden (maximal 500 MiB). Es wird kein größeres Modell automatisch geladen.')
    with model.open('rb') as handle:
        if handle.read(4) != b'GGUF':
            raise ValueError('Die Modelldatei ist kein GGUF. Bitte die echte Modelldatei herunterladen, keine HTML-Seite.')
    return executable.resolve(), model.resolve()


def start():
    executable, model = locate()
    print('Starte llama.cpp lokal auf Port 8081. Dieses Terminal geöffnet lassen. Keine Downloads oder API-Aufrufe.', flush=True)
    try:
        result = subprocess.run([str(executable), '--model', str(model), '--host', '127.0.0.1', '--port', '8081',
                                 '--ctx-size', '4096', '--parallel', '1', '--threads', str(min(4, os.cpu_count() or 1))], check=False)
    except OSError:
        raise ValueError('llama-server konnte nicht gestartet werden. Bitte Architektur, mitgelieferte Bibliotheken und macOS-Sicherheitsmeldung prüfen. Sicherheitsabfragen nicht umgehen.') from None
    if result.returncode:
        raise ValueError('llama-server wurde mit einem Fehler beendet. Bitte die Meldung im KI-Terminal prüfen.')
