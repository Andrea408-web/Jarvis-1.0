# Geprüfter Stand

Datum: 2. November 2026. Ausführung in einer Linux-x86_64-Cloud mit Python 3.12.14; der persönliche Mac und das iPhone waren nicht angeschlossen.

## Bestanden

- `python3 -m unittest discover -s tests -v`: **102 Tests**, alle bestanden, kein Test übersprungen. Laufzeit rund 12 Sekunden. Für Loopback-Sockets wurde die vorgesehene Cloud-Sandboxfreigabe genutzt.
- Darunter echte HTTP-/HTTPS-Verbindungen, explizit vertrautes temporäres TLS-Zertifikat, Basic-Authentifizierung, Origin-/Host-Prüfungen und Prozess-Token.
- Maximal 24 Handler gleichzeitig; langsame Header laufen aus; ein Client ohne TLS-Handshake blockiert andere Clients nicht.
- Persistenz von Gesprächen, Einstellungen, Tageslimits und Erinnerungen; atomare Budgetgrenzen bei parallelen Anfragen.
- Bestätigung vor Dateivorgängen; Einmaligkeit und Ablauf; Schutz vor Pfadwechseln, symbolischen Links, Hardlink-Lesen und Überschreiben.
- Echte native Rückgabecodes werden ausgewertet. Auf Linux liefert eine Mac-Aktion einen klaren Fehler, keinen Erfolg.
- Offizielle Gemini-/ElevenLabs-Anfrageformate mit kontrollierten Testantworten, Kontext, Funktionsvorschläge, Bildformatgrenzen, Quoten und sichere Anbieterfehler.
- `node --check frontend/app.js`, Python-Kompilierung und Shell-Syntaxprüfung des Mac-Starters.
- Browserprüfung mit vorhandenem Chromium: lokale Verbindung, Hilfe/Status, Rechner-Bestätigung mit korrekter Linux-Fehlermeldung, Einstellungen, Erinnerung speichern und erledigen. Keine JavaScript-Fehler. Desktop und 390-Pixel-Mobilansicht ohne horizontalen Überlauf.
- Schlüsseleinrichtung im echten Browser mit erfundenen Sitzungsschlüsseln für beide Anbieter geprüft: Eingaben geleert, keine Schlüssel in Browser-Speichern, Statusantworten oder SQLite, Cloud-Freigaben bleiben ausgeschaltet. Native Schlüsselbundbefehle mit kontrollierten Rückgaben geprüft, einschließlich fehlgeschlagener Speicherung und sicherem Laden ohne Überschreiben vorhandener Umgebungsbindungen.
- Verbindungsdiagnose mit kontrollierten Antworten geprüft: Zertifikatsfehler, DNS, Zeitüberschreitung und andere Transportfehler bleiben unterscheidbar, ohne Schlüssel oder rohe Fehlertexte auszugeben. Nur ausdrücklich ausgelöster GET-Katalogabruf, keine automatische Prüfung, keine Schlüsselübertragung, kein Generieren von Text oder Audio; HTTP 403 wird nicht als bestätigte Anbieterbereitschaft ausgegeben.
- Browserprüfungen mit kontrollierten Sprachstimmen: nachgeladene lokale deutsche Stimme erkannt, entfernte Stimmen und lokale englische Stimmen abgewiesen, Lautstärke berücksichtigt, Stop verhindert verspätete Ausgabe. Der lokale Stimmtest ruft weder Mikrofon noch ElevenLabs auf. Verbindungsschaltflächen lösen genau eine Anfrage aus. Keine JavaScript-Fehler.
- Auswahl aus zwei kontrollierten lokalen deutschen Stimmen im Browser geprüft: Auswahl spricht vor dem Speichern, bleibt bei Nachladen der Stimmen erhalten und wird dauerhaft gespeichert. „Systemstimme verwenden“ schaltet ausschließlich ElevenLabs aus und Sprachausgabe ein. Fehlende gespeicherte Stimme bleibt erhalten, automatischer Ersatz wird angezeigt. Kein Anbieteraufruf.
- Optionalen Zertifikatshelfer mit kontrollierten Prozessantworten geprüft: Linux und unpassende Python-Installationen abgewiesen; nur exakter vorhandener python.org-Skriptpfad für die laufende Version; keine Shell oder sudo, begrenzte Laufzeit, keine Ausgabe vertraulicher Installationsdetails. CLI startet weder Server noch API, Schlüsselabfrage oder Browser. Im Test wurde kein Installer ausgeführt.
- Laufender lokaler Server: authentifizierte Status-, Verlaufs- und Erinnerungsabfragen antworten mit HTTP 200. Cloud-Funktionen ausgeschaltet.
- Kein geteilter Original-API-Schlüssel in Projektdateien. Keine Pakete installiert und keine Systemberechtigungen erweitert.

## Noch nicht live verifiziert

- Echte Gemini-Antworten, Bildanalyse beim Anbieter und ElevenLabs-Audio: benötigten bewusst freigegebenes, nachweislich kostenloses Anbieterkontingent und sichere Schlüsselkonfiguration. Die Tests senden keine externen Anbieteranfragen.
- Physischer Mac: tatsächliche Hardware/macOS-Version, Rechner-App, weitere Apps und lokale Dateifreigaben.
- Tatsächliches Schreiben und Lesen des macOS-Schlüsselbunds auf einem Mac. Hier wurde der native Ablauf durch kontrollierte Prozessantworten geprüft.
- Echtes iPhone: vertrauenswürdiges LAN-TLS, Anmeldung, Safari-Mikrofon und lokale deutsche Systemstimme.
- Tatsächliche Mikrofoneingabe, ElevenLabs-Wiedergabe und vom Betriebssystem bereitgestellte Sprachstimmen. Die Steuerelemente und Fehlerpfade sind implementiert; ein Browser-Bildtest ist kein Audio-Gerätetest.
- Der Nutzer meldete inzwischen einen konkreten HTTPS-Zertifikatsprüfungsfehler für Google Gemini. Die genaue Ursache im Zertifikatsspeicher seines Macs und der Erfolg des optionalen offiziellen Reparaturskripts dort sind noch nicht überprüft. Zertifikatsprüfung und bestehender Vertrauensspeicher wurden in der Cloud unverändert beibehalten.

## Gespeicherte Cloud-Konfiguration

`start_skill`, optionale sichere Schlüsselanforderungen für `GEMINI_API_KEY` und `ELEVENLABS_API_KEY` sowie der tatsächliche Repositorypfad sind als Entwurf gespeichert. API-Ziele `generativelanguage.googleapis.com` und `api.elevenlabs.io` wurden ergänzt. Kein Installationsskript nötig, da keine Fremdpakete benötigt werden.

Entwurf speichern ist keine Veröffentlichung und wendet neue Schlüssel nicht automatisch an. In den Umgebungseinstellungen Änderungen prüfen und speichern, erneuerte Schlüssel sicher eintragen und die Umgebung bei Bedarf veröffentlichen. Eine Wiederherstellung in einer neuen Aufgabe wurde noch nicht geprüft.

Der ursprüngliche GitHub-Remote war leer. Die Commit-Historie des Repositorys dokumentiert den auf GitHub verfügbaren Projektstand. API-Schlüssel und lokale Nutzungsdaten gehören nicht zum Projektcode.

OpenAI-Erweiterung: separates Tageslimit, Kontext und bestätigte Aktionsvorschläge mit Testantworten geprüft; Bilder werden nicht gespeichert. Browserprüfung mit erfundenem Schlüssel und kontrollierter Chatantwort bestätigt Auswahl, verdecktes Hinterlegen, leere Browser-Speicher und bewusste Cloud-Freigabe. Keine echte OpenAI-Anfrage ausgeführt; Anbieterzugriff und Abrechnung bleiben kontospezifisch.

Lokale KI: Anbindung mit kontrollierten Antworten und echtem Loopback-HTTP-Testserver geprüft. Keine API-Schlüssel oder Cloud-Aufrufe, keine Modell-Downloads und keine automatische Installation; Cloud-Modellnamen und Weiterleitungen abgewiesen. Browser bestätigt lokalen Modus, abgeschaltete Cloud-/ElevenLabs-Funktionen, klare Meldung bei fehlendem Ollama sowie Chat mit kontrollierter Testantwort. Ein echtes KI-Modell wurde in dieser Cloud nicht installiert oder ausgeführt. Bereitstellung von Ollama und Modell auf dem persönlichen Mac bleibt Voraussetzung; Offline-KI-Betrieb dort noch nicht verifiziert.
