# Geprüfter Stand

Datum: 2. November 2026. Ausführung in einer Linux-x86_64-Cloud mit Python 3.12.14; der persönliche Mac und das iPhone waren nicht angeschlossen.

## Bestanden

- `python3 -m unittest discover -s tests -v`: **48 Tests**, alle bestanden, kein Test übersprungen. Laufzeit rund 13 Sekunden. Für Loopback-Sockets wurde die vorgesehene Cloud-Sandboxfreigabe genutzt.
- Darunter echte HTTP-/HTTPS-Verbindungen, explizit vertrautes temporäres TLS-Zertifikat, Basic-Authentifizierung, Origin-/Host-Prüfungen und Prozess-Token.
- Maximal 24 Handler gleichzeitig; langsame Header laufen aus; ein Client ohne TLS-Handshake blockiert andere Clients nicht.
- Persistenz von Gesprächen, Einstellungen, Tageslimits und Erinnerungen; atomare Budgetgrenzen bei parallelen Anfragen.
- Bestätigung vor Dateivorgängen; Einmaligkeit und Ablauf; Schutz vor Pfadwechseln, symbolischen Links, Hardlink-Lesen und Überschreiben.
- Echte native Rückgabecodes werden ausgewertet. Auf Linux liefert eine Mac-Aktion einen klaren Fehler, keinen Erfolg.
- Offizielle Gemini-/ElevenLabs-Anfrageformate mit kontrollierten Testantworten, Kontext, Funktionsvorschläge, Bildformatgrenzen, Quoten und sichere Anbieterfehler.
- `node --check frontend/app.js`, Python-Kompilierung und Shell-Syntaxprüfung des Mac-Starters.
- Browserprüfung mit vorhandenem Chromium: lokale Verbindung, Hilfe/Status, Rechner-Bestätigung mit korrekter Linux-Fehlermeldung, Einstellungen, Erinnerung speichern und erledigen. Keine JavaScript-Fehler. Desktop und 390-Pixel-Mobilansicht ohne horizontalen Überlauf.
- Laufender lokaler Server: authentifizierte Status-, Verlaufs- und Erinnerungsabfragen antworten mit HTTP 200. Cloud-Funktionen ausgeschaltet.
- Kein geteilter Original-API-Schlüssel in Projektdateien. Keine Pakete installiert und keine Systemberechtigungen erweitert.

## Noch nicht live verifiziert

- Echte Gemini-Antworten, Bildanalyse beim Anbieter und ElevenLabs-Audio: benötigten bewusst freigegebenes, nachweislich kostenloses Anbieterkontingent und sichere Schlüsselkonfiguration. Die Tests senden keine externen Anbieteranfragen.
- Physischer Mac: tatsächliche Hardware/macOS-Version, Rechner-App, weitere Apps und lokale Dateifreigaben.
- Echtes iPhone: vertrauenswürdiges LAN-TLS, Anmeldung, Safari-Mikrofon und lokale deutsche Systemstimme.
- Tatsächliche Mikrofoneingabe, ElevenLabs-Wiedergabe und vom Betriebssystem bereitgestellte Sprachstimmen. Die Steuerelemente und Fehlerpfade sind implementiert; ein Browser-Bildtest ist kein Audio-Gerätetest.

## Gespeicherte Cloud-Konfiguration

`start_skill`, optionale sichere Schlüsselanforderungen für `GEMINI_API_KEY` und `ELEVENLABS_API_KEY` sowie der tatsächliche Repositorypfad sind als Entwurf gespeichert. API-Ziele `generativelanguage.googleapis.com` und `api.elevenlabs.io` wurden ergänzt. Kein Installationsskript nötig, da keine Fremdpakete benötigt werden.

Entwurf speichern ist keine Veröffentlichung und wendet neue Schlüssel nicht automatisch an. In den Umgebungseinstellungen Änderungen prüfen und speichern, erneuerte Schlüssel sicher eintragen und die Umgebung bei Bedarf veröffentlichen. Eine Wiederherstellung in einer neuen Aufgabe wurde noch nicht geprüft.

Der ursprüngliche GitHub-Remote war leer. Die Commit-Historie des Repositorys dokumentiert den auf GitHub verfügbaren Projektstand. API-Schlüssel und lokale Nutzungsdaten gehören nicht zum Projektcode.
