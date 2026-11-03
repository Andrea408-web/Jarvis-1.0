"""One explicitly started setup, then a single offline launcher for both services."""
import os
import socket
import subprocess
import time

from . import easy_setup
from .providers import ProviderError
from .llamacpp import request_local
from .storage import Store


def _free_port(port):
    try:
        with socket.socket() as connection:
            connection.bind(('127.0.0.1', port))
    except OSError:
        raise ValueError(f'Port {port} ist noch belegt. Bitte die alte JARVIS-/KI-Sitzung in ihrem Terminal mit Control+C beenden. Es wird kein fremder Prozess gestoppt.') from None


def run(setup=False):
    architecture = easy_setup.preflight(check_space=False)
    executable, model = easy_setup.prepare() if setup else easy_setup.read_installation(architecture)
    _free_port(8081)
    _free_port(8765)
    child = None
    try:
        environment = dict(os.environ)
        for name in ['GEMINI_API_KEY', 'OPENAI_API_KEY', 'ELEVENLABS_API_KEY']:
            environment.pop(name, None)
        child = subprocess.Popen([str(executable), '--model', str(model), '--host', '127.0.0.1', '--port', '8081',
                                  '--ctx-size', '4096', '--parallel', '1', '--threads', str(min(4, os.cpu_count() or 1))], env=environment)
        print('Die kleine KI lädt. Bitte dieses Terminal geöffnet lassen …', flush=True)
        deadline = time.monotonic() + 60
        ready = False
        while time.monotonic() < deadline:
            if child.poll() is not None:
                raise ValueError('Das KI-Startprogramm wurde beendet. Bitte die macOS-Meldung und die Ausgabe dieses Terminals prüfen. Sicherheitsabfragen werden nicht umgangen.')
            try:
                ready = request_local('/health').get('status') == 'ok'
            except ProviderError:
                pass
            if ready:
                break
            time.sleep(0.5)
        if not ready:
            raise ValueError('Die lokale KI wurde nicht rechtzeitig bereit. Bitte den Mac und das Startprogramm prüfen.')
        # A health endpoint alone does not prove that text generation works.
        result = request_local('/v1/chat/completions', {'messages': [{'role': 'user', 'content': 'Antworte kurz mit Bereit.'}],
                                                       'max_tokens': 8, 'stream': False})
        try:
            message = result['choices'][0]['message']['content']
            if not isinstance(message, str) or not message.strip() or child.poll() is not None:
                raise ValueError()
        except (KeyError, IndexError, TypeError, ValueError):
            raise ValueError('Die lokale KI lieferte noch keine bestätigte Textantwort. JARVIS wurde nicht als bereit ausgegeben.') from None
        Store().update_settings({'ai_provider': 'llamacpp', 'cloud_enabled': False, 'elevenlabs_enabled': False, 'voice_enabled': True})
        print('Lokale Textantwort geprüft. Öffne JARVIS mit der integrierten JARVIS-Stimme …', flush=True)
        from .server import main
        main(['--open-browser', '--local-only'])
    except OSError:
        raise ValueError('Das lokale Startprogramm konnte nicht ausgeführt werden. Bitte die macOS-Sicherheitsmeldung prüfen. Es werden keine Sicherheitseinstellungen geändert.') from None
    finally:
        if child is not None and child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=5)
