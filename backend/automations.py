"""Persistent local reminders. Delivery requires the server and browser open."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone


def due_reminders(store) -> list[dict]:
    now = datetime.now(timezone.utc)
    return [row for row in store.reminders()
            if row["status"] == "pending" and datetime.fromisoformat(row["due_at"]) <= now]


def create_timer(store, seconds: int, text: str = "Timer abgelaufen") -> dict:
    if type(seconds) is not int or not 1 <= seconds <= 604800:
        raise ValueError("Ein Timer muss zwischen einer Sekunde und sieben Tagen liegen.")
    due_at = datetime.now(timezone.utc) + timedelta(seconds=seconds)
    return store.create_reminder(text, due_at.isoformat())
