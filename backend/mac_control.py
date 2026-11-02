"""Explicit, short-lived action proposals, kept separate from AI decisions.

There is no arbitrary command execution, deletion, overwrite, or file moving.
File operations walk a user-approved root by directory descriptors with
O_NOFOLLOW, so a symlink swapped between validation and execution cannot
escape the granted directory. Every operation, including reads, is confirmed.
"""
from __future__ import annotations

import os
import platform
import secrets
import stat
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

APPS = {
    "calculator": ("Rechner", "com.apple.calculator"),
    "safari": ("Safari", "com.apple.Safari"),
    "calendar": ("Kalender", "com.apple.iCal"),
    "notes": ("Notizen", "com.apple.Notes"),
    "music": ("Musik", "com.apple.Music"),
    "finder": ("Finder", "com.apple.finder"),
    "system_settings": ("Systemeinstellungen", "com.apple.systempreferences"),
}
_APP_ALIASES = {"rechner": "calculator", "kalender": "calendar", "notizen": "notes",
                "musik": "music", "systemeinstellungen": "system_settings",
                "system settings": "system_settings", "system preferences": "system_settings"}
_ACTIONS = {"open_app", "open_url", "create_folder", "create_text", "read_text", "list_files"}


def _file_parts(value: str, allow_root: bool = False) -> tuple[str, ...]:
    if not isinstance(value, str) or not value or len(value) > 500 or "\x00" in value or "\\" in value:
        raise ValueError("Ungültiger relativer Dateipfad.")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("Dateien dürfen nur im freigegebenen Ordner liegen.")
    parts = tuple(part for part in path.parts if part != ".")
    if not parts and not allow_root:
        raise ValueError("Bitte einen Dateinamen angeben.")
    return parts


class PendingActions:
    def __init__(self, store, file_root: str | Path | None = None, ttl_seconds: int = 120):
        self.store = store
        explicit_root = file_root or os.environ.get("JARVIS_ALLOWED_FOLDER")
        self.file_root = Path(explicit_root).expanduser() if explicit_root else store.data_dir / "files"
        self.file_root.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.file_root.is_symlink():
            raise ValueError("Der freigegebene Stammordner darf kein symbolischer Link sein.")
        self.ttl_seconds = ttl_seconds
        self._pending = {}
        self._lock = threading.Lock()

    def prepare(self, action: str, arguments: dict | None = None) -> dict:
        if not isinstance(action, str) or action not in _ACTIONS:
            raise ValueError("Diese Aktion ist nicht freigegeben.")
        if arguments is None:
            arguments = {}
        if not isinstance(arguments, dict):
            raise ValueError("Aktionsparameter müssen ein Objekt sein.")
        args = dict(arguments)
        if action == "open_app":
            if set(args) != {"app"} or not isinstance(args["app"], str):
                raise ValueError("Bitte eine erlaubte App angeben.")
            app = args["app"].lower().strip()
            app = _APP_ALIASES.get(app, app)
            if app not in APPS:
                raise ValueError("Diese App ist nicht in der Freigabeliste.")
            args = {"app": app}
            description = f"{APPS[app][0]} auf diesem Mac öffnen"
        elif action == "open_url":
            if set(args) != {"url"} or not isinstance(args["url"], str) or len(args["url"]) > 2000:
                raise ValueError("Bitte eine gültige HTTP- oder HTTPS-Adresse angeben.")
            value = args["url"]
            try:
                url = urlsplit(value)
                if (url.scheme not in {"http", "https"} or not url.hostname
                        or url.username or url.password or any(ord(char) < 33 for char in value)):
                    raise ValueError()
                _ = url.port
            except ValueError as exc:
                raise ValueError("Nur vollständige HTTP-/HTTPS-Adressen ohne Zugangsdaten sind erlaubt.") from exc
            description = f"Webseite auf diesem Mac öffnen: {value}"
        else:
            allowed = {"path", "content"} if action == "create_text" else {"path"}
            if set(args) - allowed or ("path" not in args and action != "list_files"):
                raise ValueError("Ungültige Dateiparameter.")
            args.setdefault("path", ".")
            _file_parts(args["path"], allow_root=action == "list_files")
            if action == "create_text":
                if "content" not in args or not isinstance(args["content"], str) or len(args["content"].encode("utf-8")) > 100000:
                    raise ValueError("Eine Textdatei darf höchstens 100 KB enthalten.")
                if not args["path"].lower().endswith((".txt", ".md", ".csv", ".json")):
                    raise ValueError("Bitte eine Textdatei mit .txt, .md, .csv oder .json angeben.")
            descriptions = {"create_folder": "Neuen Ordner erstellen", "create_text": "Neue Textdatei erstellen",
                            "read_text": "Lokale Textdatei lesen", "list_files": "Lokale Dateiliste lesen"}
            description = f"{descriptions[action]}: {args['path']}"
        now = time.time()
        item = {"id": secrets.token_urlsafe(24), "action": action, "arguments": args,
                "description": description, "requires_confirmation": True,
                "expires_at": datetime.fromtimestamp(now+self.ttl_seconds, timezone.utc).isoformat(),
                "platform_supported": action not in {"open_app", "open_url"} or platform.system() == "Darwin"}
        with self._lock:
            self._pending = {key: value for key, value in self._pending.items() if value[0] > now}
            if len(self._pending) >= 100:
                raise ValueError("Zu viele unbestätigte Aktionen. Bitte kurz warten.")
            # Retain a private copy so mutations to a returned JSON object cannot
            # change what will be executed after confirmation.
            self._pending[item["id"]] = (now+self.ttl_seconds, {**item, "arguments": dict(args)})
        return item

    def cancel(self, action_id: str) -> dict:
        if not isinstance(action_id, str):
            raise ValueError("Ungültige Aktionskennung.")
        with self._lock:
            found = self._pending.pop(action_id, None)
        if not found:
            raise ValueError("Diese Aktion wurde nicht gefunden oder bereits bestätigt.")
        return {"ok": True, "action": found[1]["action"], "cancelled": True}

    def confirm(self, action_id: str) -> dict:
        if not isinstance(action_id, str):
            raise ValueError("Ungültige Aktionskennung.")
        with self._lock:
            pending = self._pending.pop(action_id, None)
        if not pending:
            raise ValueError("Diese Aktion ist unbekannt oder wurde bereits bestätigt.")
        expires, item = pending
        if time.time() > expires:
            raise ValueError("Die Bestätigung ist abgelaufen. Bitte die Aktion erneut anfordern.")
        action, args = item["action"], item["arguments"]
        if action in {"open_app", "open_url"}:
            if platform.system() != "Darwin":
                return {"ok": False, "action": action,
                        "error": "Mac-Steuerung ist auf diesem Linux-/Entwicklungssystem nicht verfügbar. Bitte JARVIS lokal auf dem Mac starten."}
            command = (["/usr/bin/open", "-b", APPS[args["app"]][1]] if action == "open_app"
                       else ["/usr/bin/open", "--", args["url"]])
            try:
                result = subprocess.run(command, capture_output=True, timeout=10, check=False)
                if result.returncode != 0:
                    return {"ok": False, "action": action, "error": "macOS konnte die Aktion nicht ausführen. Bitte App und Systemberechtigungen prüfen."}
                return {"ok": True, "action": action,
                        "message": "macOS hat den Öffnen-Auftrag erfolgreich angenommen."}
            except (OSError, subprocess.SubprocessError):
                return {"ok": False, "action": action, "error": "Der macOS-Öffnen-Auftrag konnte nicht abgeschlossen werden."}
        try:
            return {"ok": True, "action": action, **self._execute_file(action, args)}
        except (OSError, UnicodeError, ValueError) as exc:
            if isinstance(exc, FileExistsError):
                message = "Die Datei oder der Ordner existiert bereits. Vorhandene Inhalte werden nicht überschrieben."
            elif isinstance(exc, FileNotFoundError):
                message = "Der angegebene Pfad wurde im freigegebenen Ordner nicht gefunden."
            elif isinstance(exc, UnicodeError):
                message = "Diese Datei enthält keinen gültigen UTF-8-Text."
            elif isinstance(exc, ValueError):
                message = str(exc)
            else:
                message = "Zugriff abgewiesen. Nur reguläre Dateien und Ordner ohne symbolische Links im freigegebenen Ordner sind erlaubt."
            return {"ok": False, "action": action, "error": message}

    def _execute_file(self, action: str, args: dict) -> dict:
        parts = _file_parts(args["path"], allow_root=action == "list_files")
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        fd = os.open(self.file_root, flags)
        try:
            directories = parts if action == "list_files" else parts[:-1]
            for part in directories:
                next_fd = os.open(part, flags, dir_fd=fd)
                os.close(fd)
                fd = next_fd
            if action == "list_files":
                names = sorted(os.listdir(fd))
                entries = []
                for name in names[:250]:
                    meta = os.stat(name, dir_fd=fd, follow_symlinks=False)
                    entries.append({"name": name, "directory": stat.S_ISDIR(meta.st_mode),
                                    "symlink": stat.S_ISLNK(meta.st_mode), "size_bytes": meta.st_size})
                return {"entries": entries, "truncated": len(names) > 250,
                        "message": f"{len(entries)} Einträge im freigegebenen Ordner gelesen."}
            name = parts[-1]
            if action == "create_folder":
                os.mkdir(name, mode=0o700, dir_fd=fd)
                return {"path": args["path"], "message": "Ordner erstellt."}
            if action == "create_text":
                file_fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=fd)
                with os.fdopen(file_fd, "w", encoding="utf-8") as handle:
                    handle.write(args["content"])
                return {"path": args["path"], "message": "Neue Textdatei erstellt."}
            file_fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
            with os.fdopen(file_fd, "rb") as handle:
                info = os.fstat(handle.fileno())
                if not stat.S_ISREG(info.st_mode) or info.st_size > 100000 or info.st_nlink > 1:
                    raise ValueError("Nur reguläre Textdateien bis 100 KB ohne zusätzliche Hardlinks sind erlaubt.")
                content = handle.read(100001)
                if len(content) > 100000:
                    raise ValueError("Die Datei ist zu groß.")
            return {"path": args["path"], "content": content.decode("utf-8"), "message": "Textdatei gelesen."}
        finally:
            os.close(fd)
