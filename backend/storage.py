"""Private local settings, conversation history, budgets, and reminders.

Credentials are deliberately not supported by this store. Each operation gets
its own SQLite connection so HTTP request threads never share a connection.
"""
from __future__ import annotations

import json
import os
import platform
import re
import sqlite3
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path


DEFAULT_SETTINGS = {
    "cloud_enabled": False,
    "gemini_model": "gemini-2.5-flash",
    "gemini_daily_limit": 20,
    "elevenlabs_enabled": False,
    "elevenlabs_voice_id": "",
    "elevenlabs_daily_char_limit": 1500,
    "voice_enabled": False,
    "local_voice_uri": "",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_data_dir() -> Path:
    configured = os.environ.get("JARVIS_DATA_DIR")
    if configured:
        return Path(configured).expanduser()
    if platform.system() == "Darwin":
        return Path.home() / "Library" / "Application Support" / "Jarvis"
    return Path.home() / ".local" / "share" / "jarvis"


class Store:
    def __init__(self, data_dir: str | Path | None = None):
        self.data_dir = Path(data_dir) if data_dir is not None else default_data_dir()
        self.data_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.path = self.data_dir / "jarvis.sqlite3"
        # Create with private permissions before SQLite opens it. Existing data
        # is preserved; chmod only applies to our own database.
        fd = os.open(self.path, os.O_CREAT | os.O_WRONLY, 0o600)
        os.close(fd)
        os.chmod(self.path, 0o600)
        with self._connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS settings (
                    name TEXT PRIMARY KEY, value TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation TEXT NOT NULL,
                    role TEXT NOT NULL,
                    text TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS messages_conversation
                    ON messages(conversation, id);
                CREATE TABLE IF NOT EXISTS usage (
                    day TEXT NOT NULL,
                    service TEXT NOT NULL,
                    amount INTEGER NOT NULL,
                    PRIMARY KEY(day, service)
                );
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL,
                    due_at TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT NOT NULL
                );
            """)

    def _connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=10000")
        return db

    def settings(self) -> dict:
        result = dict(DEFAULT_SETTINGS)
        with self._connect() as db:
            for row in db.execute("SELECT name, value FROM settings"):
                if row["name"] in DEFAULT_SETTINGS:
                    result[row["name"]] = json.loads(row["value"])
        return result

    def update_settings(self, values: dict) -> dict:
        if not isinstance(values, dict):
            raise ValueError("Die Einstellungen müssen ein Objekt sein.")
        unknown = set(values) - set(DEFAULT_SETTINGS)
        if unknown:
            raise ValueError("Unbekannte Einstellung. Schlüssel gehören nicht in die Einstellungen.")
        for key, value in values.items():
            if key in {"cloud_enabled", "elevenlabs_enabled", "voice_enabled"}:
                if type(value) is not bool:
                    raise ValueError("Diese Einstellung muss ein Wahrheitswert sein.")
            elif key == "gemini_daily_limit":
                if type(value) is not int or not 0 <= value <= 1000:
                    raise ValueError("Das Gemini-Tageslimit muss zwischen 0 und 1000 liegen.")
            elif key == "elevenlabs_daily_char_limit":
                if type(value) is not int or not 0 <= value <= 100000:
                    raise ValueError("Das Zeichenlimit muss zwischen 0 und 100000 liegen.")
            elif key == "gemini_model":
                if not isinstance(value, str) or not re.fullmatch(r"gemini-[a-zA-Z0-9._-]{1,90}", value):
                    raise ValueError("Ungültiger Gemini-Modellname.")
            elif key == "elevenlabs_voice_id":
                if not isinstance(value, str) or (value and not re.fullmatch(r"[a-zA-Z0-9_-]{1,100}", value)):
                    raise ValueError("Ungültige ElevenLabs Voice ID.")
            elif key == "local_voice_uri":
                # Opaque browser voice identifier: never interpreted as a URL,
                # fetched, or used as a shell argument by this backend.
                if (not isinstance(value, str) or len(value) > 1024
                        or any(unicodedata.category(char) in {"Cc", "Cs", "Zl", "Zp"} for char in value)):
                    raise ValueError("Die Systemstimme benötigt eine Kennung mit höchstens 1024 Zeichen ohne Steuerzeichen.")
        with self._connect() as db:
            for key, value in values.items():
                db.execute("INSERT INTO settings(name, value) VALUES (?, ?) "
                           "ON CONFLICT(name) DO UPDATE SET value=excluded.value",
                           (key, json.dumps(value)))
        return self.settings()

    @staticmethod
    def _conversation(conversation: str) -> str:
        if not isinstance(conversation, str) or not re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", conversation):
            raise ValueError("Ungültige Gesprächskennung.")
        return conversation

    def history(self, conversation: str = "default") -> list[dict]:
        conversation = self._conversation(conversation)
        with self._connect() as db:
            rows = db.execute("SELECT * FROM (SELECT * FROM messages WHERE conversation=? "
                              "ORDER BY id DESC LIMIT 100) ORDER BY id", (conversation,)).fetchall()
        return [dict(row) for row in rows]

    def append(self, role: str, text: str, conversation: str = "default") -> dict:
        conversation = self._conversation(conversation)
        if role not in {"user", "assistant", "system", "tool"}:
            raise ValueError("Ungültige Gesprächsrolle.")
        if not isinstance(text, str) or not text.strip() or len(text) > 100000:
            raise ValueError("Der Gesprächseintrag ist leer oder zu lang.")
        created_at = utc_now()
        with self._connect() as db:
            cursor = db.execute("INSERT INTO messages(conversation, role, text, created_at) VALUES (?, ?, ?, ?)",
                                (conversation, role, text, created_at))
            item_id = cursor.lastrowid
        return {"id": item_id, "conversation": conversation, "role": role,
                "text": text, "created_at": created_at}

    def clear_history(self, conversation: str = "default") -> None:
        with self._connect() as db:
            db.execute("DELETE FROM messages WHERE conversation=?", (self._conversation(conversation),))

    def reserve_usage(self, service: str, amount: int, limit: int) -> dict:
        """Reserve before the request; failed/ambiguous requests remain counted.

        This is a local safety ceiling, not a guarantee that an account has a
        free quota. Counters use UTC days and concurrent requests are atomic.
        """
        if service not in {"gemini_requests", "elevenlabs_characters"}:
            raise ValueError("Unbekannter Nutzungszähler.")
        if type(amount) is not int or amount < 1 or type(limit) is not int or limit < 0:
            raise ValueError("Ungültiges Nutzungslimit.")
        day = datetime.now(timezone.utc).date().isoformat()
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT amount FROM usage WHERE day=? AND service=?", (day, service)).fetchone()
            used = row[0] if row else 0
            if used + amount > limit:
                raise ValueError("Das lokale Tageslimit ist erreicht. Es wurde keine neue API-Anfrage gesendet.")
            used += amount
            db.execute("INSERT INTO usage(day, service, amount) VALUES (?, ?, ?) "
                       "ON CONFLICT(day, service) DO UPDATE SET amount=excluded.amount", (day, service, used))
        return {"service": service, "date": day, "used": used, "limit": limit, "remaining": limit-used}

    def usage(self) -> dict:
        day = datetime.now(timezone.utc).date().isoformat()
        result = {"date": day, "gemini_requests": 0, "elevenlabs_characters": 0}
        with self._connect() as db:
            for row in db.execute("SELECT service, amount FROM usage WHERE day=?", (day,)):
                result[row["service"]] = row["amount"]
        return result

    def reminders(self) -> list[dict]:
        with self._connect() as db:
            rows = db.execute("SELECT * FROM reminders ORDER BY CASE WHEN status='pending' THEN 0 ELSE 1 END, "
                              "due_at, id LIMIT 250").fetchall()
        return [dict(row) for row in rows]

    def list_reminders(self) -> list[dict]:
        return self.reminders()

    def add_reminder(self, text: str, due_at: str) -> dict:
        return self.create_reminder(text, due_at)

    def create_reminder(self, text: str, due_at: str) -> dict:
        if not isinstance(text, str) or not text.strip() or len(text) > 500:
            raise ValueError("Eine Erinnerung benötigt einen Text mit höchstens 500 Zeichen.")
        if not isinstance(due_at, str):
            raise ValueError("Bitte einen Zeitpunkt mit Zeitzone angeben.")
        try:
            due = datetime.fromisoformat(due_at.replace("Z", "+00:00"))
            if due.tzinfo is None or due.utcoffset() is None:
                raise ValueError()
            due = due.astimezone(timezone.utc)
        except (ValueError, TypeError, OverflowError) as exc:
            raise ValueError("Bitte einen gültigen Zeitpunkt mit Zeitzone angeben.") from exc
        if due < datetime.now(timezone.utc) - timedelta(seconds=5):
            raise ValueError("Der Erinnerungszeitpunkt liegt in der Vergangenheit.")
        with self._connect() as db:
            cursor = db.execute("INSERT INTO reminders(text, due_at, created_at) VALUES (?, ?, ?)",
                                (text.strip(), due.isoformat(), utc_now()))
            row = db.execute("SELECT * FROM reminders WHERE id=?", (cursor.lastrowid,)).fetchone()
        return dict(row)

    def update_reminder(self, reminder_id: int, status: str) -> dict:
        if status not in {"done", "cancelled"} or type(reminder_id) is not int:
            raise ValueError("Ungültige Erinnerung oder Status.")
        with self._connect() as db:
            cursor = db.execute("UPDATE reminders SET status=? WHERE id=? AND status='pending'",
                                (status, reminder_id))
            if cursor.rowcount != 1:
                raise ValueError("Diese Erinnerung wurde nicht gefunden oder ist bereits abgeschlossen.")
            row = db.execute("SELECT * FROM reminders WHERE id=?", (reminder_id,)).fetchone()
        return dict(row)
