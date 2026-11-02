# Architektur und Schnittstellen

`backend/server.py` stellt die statische Oberfläche und eine JSON-API über `ThreadingHTTPServer` bereit. Python 3.10+ ohne Drittanbieterpakete. `python3 -m backend` startet den Server. Es gibt keine Build-Stufe.

| Modul | Aufgabe |
| --- | --- |
| `frontend/` | HTML/CSS/SVG-HUD, echte Statusübergänge, Chat, Mikrofon, Audio, Bestätigungen. |
| `backend/storage.py` | SQLite, Einstellungen, Nachrichten, atomare UTC-Tageslimits, Erinnerungen. |
| `backend/system_info.py` | Hostdiagnose und echte Messwerte auf Linux/macOS. |
| `backend/ai.py` | Gemini REST, Kontext, streng geprüfte Funktionsvorschläge, Bildanalyse. |
| `backend/voice.py` | ElevenLabs REST mit festem maximalem Textumfang. |
| `backend/providers.py` | Verifiziertes HTTPS, begrenzte Antwortgrößen, keine Redirects mit Schlüsseln. |
| `backend/mac_control.py` | Freigabeliste, kurzlebige Einmalbestätigungen, sichere native Öffnen-Aufträge und begrenzte Dateien. |
| `backend/automations.py` | Fällige Erinnerungen und Timer als lokale Datensätze, kein Hintergrunddaemon. |
| `tests/` | Standardbibliothek `unittest`, temporäre Datenverzeichnisse. |

## Transport und Sicherheit

Nur explizit freigegebene statische Dateien werden ausgeliefert. Keine Dateipfade aus URLs, keine Verzeichnisauflistung. Host-/Origin-Prüfung schützt vor DNS-Rebinding und fremden Webseiten. `GET /api/session` liefert nach eventueller TLS-Basic-Anmeldung einen kryptographisch zufälligen Prozess-Token; alle weiteren API-Aufrufe benötigen `X-Jarvis-Token`. Keine CORS-Freigabe. Token werden nicht in URLs oder localStorage abgelegt. Kein Zugriff durch iframes. LAN benötigt TLS und Passwort; Standard ist Loopback.

HTTP-Fehler enthalten `{"error":"verständliche Meldung"}`. Schlüssel/Anbieter-Fehlerkörper werden nicht geloggt. Anfragen haben Größen- und Zeitlimits. Der lokale Server ist kein gehärteter öffentlicher Internetdienst und darf nicht öffentlich weitergeleitet werden.

## HTTP-Vertrag

| Methode/Pfad | Anfrage → Ergebnis |
| --- | --- |
| `GET /api/session` | `{"token": "…"}` |
| `GET /api/status` | Echte `system`-Messwerte, `settings`, `providers` (nur Schlüssel vorhanden/fehlend), `usage`, `capabilities`. |
| `GET /api/settings` | Einstellungen, Anbieterpräsenz und Tageszähler. |
| `PUT /api/settings` | Whitelist-Objekt, etwa `{"cloud_enabled":false,"gemini_daily_limit":20}` → bestätigte Einstellungen. Unbekannte Felder/Schlüssel werden abgewiesen. |
| `GET /api/history` | `{"messages":[{"role":"user","text":"…","created_at":"…"}]}` |
| `DELETE /api/history` | Lokale Nachrichten löschen. |
| `POST /api/chat` | `{"text":"…"}` → `{"reply":"…","proposals":[]}` |
| `POST /api/image` | `{"text":"…","image":"BASE64","mime":"image/png"}` → KI-Antwort, keine Computeraktion. Max. 4 MiB Bild. |
| `POST /api/actions/prepare` | `{"action":"open_app","arguments":{"app":"calculator"}}` → Vorschlag mit `id`, `description`, `arguments`, `expires_at`. |
| `POST /api/actions/confirm` | `{"id":"…"}` → `{"ok":true/false,"message":"…"}`. `ok:false` ist kein Erfolg. Bestätigung wird auch beim Fehler verbraucht. |
| `POST /api/actions/cancel` | `{"id":"…"}` → verwirft Vorschlag. |
| `POST /api/voice` | `{"text":"…"}` → `audio/mpeg` oder JSON-Fehler. |
| `GET /api/reminders` | `{"reminders":[…]}` |
| `POST /api/reminders` | `{"text":"…","due_at":"2026-12-01T15:00:00+01:00"}` → gespeicherte Erinnerung. Zeitzone erforderlich. |
| `PATCH /api/reminders/ID` | `{"status":"done"}` oder `{"status":"cancelled"}`. |

Mac-Aktionsnamen: `open_app`, `open_url`; Dateiaktionen: `list_files`, `read_text`, `create_folder`, `create_text`. Dateiparameter `path` sind relativ; `create_text` verwendet zusätzlich `content`. Die KI hat absichtlich keinen Shell- oder Netzwerk-Werkzeugzugriff. Vorgeschlagene Parameter werden unabhängig vom Modell nochmals geprüft.

Nach einem bestätigten Dateilesen erscheint der Inhalt nur in der Oberfläche. Eine Übertragung an Gemini muss separat durch den Nutzer erfolgen. Kein automatischer Datei-/Mail-Zugriff als Gesprächskontext. Nicht unterstützte Integrationen sind in `capabilities` mit `false` gekennzeichnet.
