# J.A.R.V.I.S.

Ein lokaler, modularer Assistent mit einer animierten goldenen HUD-Oberfläche, echtem Gemini-Chat, optionaler ElevenLabs-Stimme und ausdrücklich bestätigten Mac-Aktionen. Kein Paketmanager, kein Framework, keine automatische Installation: Python-Standardbibliothek, HTML, CSS und JavaScript.

## Auf deinem Mac starten

1. Lade das Projekt herunter und entpacke es.
2. Öffne **Terminal**, tippe `cd ` (mit Leerzeichen), ziehe den Projektordner ins Terminal und drücke die Eingabetaste.
3. Prüfe zuerst dein tatsächliches Gerät:

   ```bash
   python3 --version
   python3 -m backend --diagnose
   ```

   Benötigt wird **Python 3.10 oder neuer**. Das Projekt installiert nichts. Falls Python fehlt, entscheide selbst über eine Installation von [python.org](https://www.python.org/downloads/macos/). Die Diagnose liest Architektur, Betriebssystem, CPU, RAM und vorhandene Ressourcen direkt vom ausführenden Gerät. Die Cloud-Testmaschine ist kein Nachweis für die Hardware deines Macs. Ein A18-Chip darf nicht ohne Prüfung als Mac-Prozessor vorausgesetzt werden.

4. Starte ohne Cloud-Schlüssel:

   ```bash
   python3 -m backend
   ```

5. Öffne auf **diesem Mac** im Browser die Adresse `http://127.0.0.1:8765`.
6. Klicke auf **Rechner öffnen**, prüfe den Bestätigungsdialog und bestätige. Auf macOS wird die echte Rechner-App über ihre feste App-ID geöffnet. Auf anderen Betriebssystemen zeigt JARVIS einen Fehler, keinen simulierten Erfolg. Erfolgreich bedeutet hier: macOS hat den Öffnen-Auftrag angenommen; eine sichtbare App wird nicht durch Bildschirmüberwachung überprüft.

Mit **Strg+C** im Terminal beendest du den Server. `Start-JARVIS.command` ist ein alternativer Mac-Starter, der den Browser direkt öffnet; Schlüssel gibst du anschließend in den Einstellungen ein. Falls macOS das Öffnen blockiert, verwende den obigen Terminalbefehl; JARVIS umgeht keine Sicherheitsabfrage.

## Gemini und ElevenLabs verbinden

Die im ursprünglichen Chat geteilten Schlüssel gehören nicht in Git oder JavaScript. Erneuere sie beim Anbieter. Gib neue Schlüssel nicht im Chat ein.

**Einfachster Weg:** Starte JARVIS normal mit `python3 -m backend`. Öffne im Browser die **Einstellungen**, füge unter **Gemini** den Schlüssel ins verdeckte Feld ein und klicke **Schlüssel hinterlegen**. Auf deinem Mac kann JARVIS ihn auf deinen ausdrücklichen Auftrag im **macOS-Schlüsselbund** speichern. Danach aktiviere **Cloud-KI** und speichere die Einstellungen. Für ElevenLabs funktioniert das entsprechend; zusätzlich benötigst du deine Voice ID.

Die Schlüssel werden nicht in Git, SQLite oder im Browserspeicher abgelegt. Auf macOS wird ein bewusst gespeicherter Schlüssel beim nächsten Serverstart aus dem Schlüsselbund geladen. Außerhalb von macOS ist nur eine Sitzung bis zum Serverneustart möglich. Die Anzeige „konfiguriert“ bestätigt die Hinterlegung, noch nicht die Gültigkeit beim Anbieter.

Alternativ kannst du die Schlüssel weiterhin im Terminal verdeckt eingeben:

```bash
python3 -m backend --ask-keys
```

Die Terminaleingaben werden nicht angezeigt und bleiben nur im Speicher dieses Serverprozesses. Leere Eingabe überspringt den jeweiligen Dienst. Alternativ liest JARVIS bereits vorhandene Server-Umgebungsvariablen `GEMINI_API_KEY` und `ELEVENLABS_API_KEY`, beispielsweise aus einem Passwortmanager. Diese haben Vorrang vor gespeicherten Schlüsselbund-Einträgen. `.env.example` beschreibt nur die Namen; `.env`-Dateien werden nicht automatisch geladen.

Öffne anschließend die **Einstellungen** in der Oberfläche:

- **Gemini** bewusst aktivieren, Modell wählen und Tageslimit setzen. Standard ist `gemini-2.5-flash`; seine Verfügbarkeit hängt vom Google-Konto ab. Gespeicherte Gesprächsnachrichten werden für Kontext an Google übertragen (maximal die letzten 24 Nachrichten, zusätzlich begrenzt).
- **ElevenLabs** bewusst aktivieren und deine **Voice ID** eintragen. Der aktuelle Antworttext wird zur Spracherzeugung übertragen. Begrenzung nach Zeichen, deutsche mehrsprachige Stimme.
- **Sprachausgabe** aktivieren. Ohne ElevenLabs kann eine verfügbare lokale deutsche Browser-/Systemstimme verwendet werden. Ob eine solche Stimme installiert ist, hängt vom Gerät ab.

**Kostenlose Systemstimme wählen:** Öffne **Einstellungen → Lokale Sprachausgabe**, wähle in der Stimmenliste eine installierte deutsche Stimme und klicke **Systemstimme verwenden**. Das speichert die Auswahl, schaltet ElevenLabs aus und die normale Sprachausgabe ein. Die Cloud-KI-Einstellung bleibt erhalten. **Lokale Stimme testen** spricht eine kurze Probe mit der ausgewählten Stimme, auch schon vor dem Speichern. „Automatisch“ verwendet eine verfügbare lokale deutsche Stimme. Ist eine gespeicherte Stimme auf einem anderen Gerät nicht vorhanden, zeigt JARVIS das an und verwendet eine dort verfügbare lokale deutsche Stimme.

Es ist kein API-Schlüssel und keine Voice ID nötig. JARVIS wartet kurz, falls der Browser seine Stimmenliste erst nachlädt. Mit Stop kannst du auch eine wartende Ausgabe abbrechen. Ohne installierte deutsche lokale Stimme zeigt JARVIS eine verständliche Meldung und startet keinen Download. Die Liste hängt vom jeweiligen Browser und Gerät ab. Weitere Systemstimmen kannst du selbst in macOS unter **Systemeinstellungen → Bedienungshilfen → Lesen & Sprechen** (je nach macOS-Version **Gesprochene Inhalte**) verwalten. Nach einer bewusst gewählten Installation gegebenenfalls den Browser neu öffnen; JARVIS installiert keine Stimmen. Die Auswahl innerhalb von JARVIS überschreibt nicht die globale macOS-Stimme.

### Wenn „Anbieter nicht erreichbar“ erscheint

Klicke beim betroffenen Dienst in den Einstellungen auf **Verbindung prüfen**. Der Test ruft nur eine feste öffentliche Katalog-URL per HTTPS ab, ohne Schlüssel und ohne Text- oder Audioerzeugung. Eine Antwort bestätigt noch nicht die Gültigkeit deines Schlüssels, die Freischaltung deiner Stimme oder ein kostenloses Kontingent. HTTP 403 kann durch eine Netzrichtlinie oder den Anbieter entstehen. Der Test läuft niemals automatisch.

Alternativ im Projektordner:

```bash
python3 -m backend --check-connection elevenlabs
```

Die neue Fehlermeldung unterscheidet Zertifikatsfehler, Namensauflösung (DNS), Zeitüberschreitung und abgelehnte Verbindungen. Ein Zertifikatsfehler bei einer Python-Installation von python.org auf macOS kann durch fehlende Python-Zertifikate entstehen. Im zu deiner Python-Version passenden Ordner unter `/Applications/Python 3.x/` gibt es dafür **Install Certificates.command**. Dieses offizielle Hilfsskript installiert beziehungsweise aktualisiert ein Zertifikatspaket: Starte es nur, wenn du diese Änderung bewusst möchtest. JARVIS führt es nicht automatisch aus. Bei einer anderen Python-Distribution deren dokumentierten Zertifikatsweg verwenden. TLS-Prüfung nicht ausschalten; eine Firewall oder ein Zertifikatsfehler ist durch eine andere Voice ID nicht behoben.

Wenn du diese Zertifikatseinrichtung ausdrücklich ausführen möchtest, kannst du im Projektordner **Zertifikate-reparieren.command** starten oder folgenden Befehl verwenden:

```bash
python3 -m backend --repair-certificates
```

Der Helfer prüft, ob die tatsächlich verwendete Python-Version eine passende python.org-Framework-Installation auf macOS ist und das offizielle Skript vorliegt. Nur dann startet er es. Auf Linux, bei Homebrew-Python oder fehlendem Skript beendet er sich ohne Installation mit einer Erklärung. Das Skript läuft nie beim normalen JARVIS-Start. Anschließend die Verbindung erneut prüfen. Eine kostenlose Systemstimme repariert keine HTTPS-Verbindung zu Gemini: Für KI-Antworten muss das Zertifikatsproblem weiterhin gelöst sein.

**Kosten:** Lokale Limits sind keine Zusage kostenloser Nutzung. JARVIS kann das Abrechnungsmodell deines Kontos nicht kontrollieren. Aktiviere Cloud-Dienste ausschließlich mit einem Anbieter-Konto ohne kostenpflichtige Abrechnung und überprüfe dessen Gratis-Kontingent. Es gibt keine automatischen Wiederholungen, kein automatisches Modell-Upgrade und keine Käufe. Fehlgeschlagene oder unklare API-Aufrufe zählen vorsorglich zum lokalen Limit. Limits gelten pro UTC-Tag und lokalem Datenverzeichnis; sie erfassen nicht deine Nutzung in anderen Apps.

## Was bereits echt funktioniert

| Bereich | Verhalten |
| --- | --- |
| HUD | Echte Zustände für Bereit, Zuhören, Denken, Sprechen und Fehler; rotierende SVG-Ringe, responsive Darstellung, reduzierte Bewegung berücksichtigt. |
| Systemdaten | Messwerte des **Servergeräts**, keine Zufallsdaten. Fehlende Messwerte bleiben unbekannt. Unter Linux können Host- und Containerressourcen voneinander abweichen. |
| Lokaler Chat | `Hilfe`, `Status`, `Rechner öffnen` und weitere erlaubte App-Befehle funktionieren ohne KI. Freie Gespräche benötigen Gemini. |
| Gemini | Offizielle REST-API, deutsche Persönlichkeit, gespeicherter Gesprächskontext, strukturierte Aktionsvorschläge, echte API-Fehler statt erfundener Antworten. |
| Bilder | Ausgewählte PNG/JPEG/WebP-Bilder bis 4 MiB auf ausdrücklichen Auftrag mit Gemini beschreiben; Bilder werden nicht lokal archiviert. Keine Kameraaktivierung. |
| Stimme | ElevenLabs über offizielle REST-API, Voice ID, Lautstärke, Stop und lokale Browserstimme als Fallback. Bei WebAudio-Wiedergabe stammt der Pegel aus dem echten Audio. Für Systemstimmen ist kein Audio-Wellenformzugriff zugesichert. |
| Mikrofon | Nur nach Klick und ausdrücklicher Zustimmung, über unterstützte Browser-Spracherkennung. Browser können Audiodaten an ihren Erkennungsdienst senden; dies ist keine garantierte Offline-Erkennung. Kein Wakeword/Dauerlauschen. |
| Apps | Rechner, Safari, Kalender, Notizen, Musik, Finder und Systemeinstellungen auf macOS; feste IDs, keine freie Shell. |
| Webseiten | Bestätigtes Öffnen vollständiger HTTP-/HTTPS-URLs auf dem Mac. Kein automatisches Abrufen privater Webseiten. |
| Dateien | Lesen, Auflisten, neue Ordner und neue Textdateien im freigegebenen Ordner. Keine Löschung, kein Verschieben, kein Überschreiben. Auch Lesen benötigt Bestätigung. |
| Erinnerungen | Lokal in SQLite gespeichert; fällige Einträge werden in der geöffneten Oberfläche angezeigt. Der Browser prüft nach Rückkehr auch überfällige Erinnerungen. Kein garantierter Alarm bei geschlossenem Browser, ausgeschaltetem Server oder schlafendem Mac. |

Für eine Zusammenfassung ausgewählten Text in den Chat eingeben. Dateiinhalte werden nach bestätigtem Lesen angezeigt, aber nicht automatisch an Google geschickt. Allgemeinwissen des Modells ist keine Live-Recherche.

## Daten und Freigaben

Einstellungen, Chatverlauf, Nutzungszähler und Erinnerungen liegen lokal:

- macOS: `~/Library/Application Support/Jarvis/`
- Linux: `~/.local/share/jarvis/`
- Überschreibbar mit `JARVIS_DATA_DIR` oder `--data-dir`.

Die SQLite-Datei wird mit privaten Dateirechten angelegt. Lokale Daten sind nicht zusätzlich verschlüsselt; verwende den Schutz deines Betriebssystems. **Verlauf löschen** entfernt gespeicherte Nachrichten; Anbieter können bereits gesendete Daten weiterhin gemäß ihren eigenen Regeln speichern.

Dateifunktionen dürfen standardmäßig nur auf den Unterordner `files` dort zugreifen. Wenn du bewusst einen anderen Ordner freigeben möchtest, setze beim Start `JARVIS_ALLOWED_FOLDER` auf einen gesonderten, unkritischen Ordner. Gib weder dein gesamtes Benutzerverzeichnis noch Schlüssel- oder Passwortordner frei. Absolute Aktionspfade, `..`, Symlink-Durchläufe, Hardlink-Dateilesen und vorhandene Zieldateien werden abgewiesen. Ein vorbereiteter Auftrag verfällt nach zwei Minuten und kann nur einmal bestätigt werden. Ein bloßer Modellvorschlag führt nichts aus.

## iPhone im lokalen Netzwerk

Die Oberfläche passt sich dem iPhone an. Der Server bleibt standardmäßig ausschließlich auf dem Mac erreichbar. LAN-Zugriff wird ohne **TLS und Passwort** abgewiesen; keine Portfreigabe, kein Tunnel und kein öffentlicher Zugriff werden eingerichtet.

Voraussetzungen, die du bewusst selbst bereitstellst:

1. Ein Zertifikat samt privatem Schlüssel, das für die private IP-Adresse deines Macs gültig ist und dem dein iPhone vertraut. Die Einrichtung einer Zertifizierungsstelle oder Vertrauensänderung wird nicht automatisch vorgenommen.
2. Mac und iPhone im selben vertrauenswürdigen WLAN, konkrete private IPv4-Adresse des Macs.
3. Ein langes Zugriffspasswort als `JARVIS_ACCESS_PASSWORD` (mindestens 16 Zeichen). Gib es verdeckt ein, ohne es in der Shell-Historie abzulegen:

   ```bash
   read -s -r -p 'JARVIS-Passwort: ' JARVIS_ACCESS_PASSWORD; echo
   export JARVIS_ACCESS_PASSWORD
   python3 -m backend --host 192.168.1.42 --cert /pfad/mac-cert.pem --key /pfad/mac-key.pem
   ```

Die Beispiel-IP musst du durch die deines Macs ersetzen. Öffne auf dem iPhone `https://DEINE-MAC-IP:8765`, Benutzername **jarvis**, dein Passwort. Bei Zertifikatsfehlern erst die Vertrauenskette korrigieren; Zertifikatsprüfung nicht umgehen. Authentifizierung schützt den Zugriff auf den Assistenten, Bestätigungsdialoge bleiben zusätzlich notwendig. Mikrofon und Stimmen hängen von iOS/Safari ab. LAN/TLS ist technisch abgesichert, wurde in der Linux-Cloud aber nicht auf deinem echten iPhone getestet.

## Bewusst noch nicht freigeschaltet

E-Mail, Nachrichtenversand, Kontakte, Telefonanrufe, Live-Webrecherche, Wetter, Kamerastreams, Wakeword, wiederkehrende Routinen und Hintergrund-Systembenachrichtigungen sind **noch nicht integriert**. Es gibt dafür keine versteckten Platzhalter-Erfolge. Diese Erweiterungen benötigen eigene offizielle Integrationen, Geräteprüfungen, Berechtigungen und Tests. Die aktuelle Version liest keine Mails und kann weder Nachrichten senden noch selbstständig telefonieren.

## Entwicklung und Tests

```bash
python3 -m unittest discover -s tests -v
python3 -m backend --data-dir /tmp/jarvis-dev
```

Tests prüfen Datenpersistenz, konkurrierende Budgets, echte Dateivorgänge in temporären Ordnern, Bestätigungen, Pfadgrenzen, API-Verträge und Fehler. Cloud-Dienste werden in automatisierten Tests durch kontrollierte HTTP-Antworten ersetzt; das ist keine Behauptung eines Live-API-Erfolgs. Eine echte Cloud-Anfrage wird nur nach bewusster Aktivierung im eigenen Konto ausgeführt. Mac-Startbefehle werden unter Linux mit festen Argumenten geprüft; der echte Mac bleibt ein eigener Gerätetest.

Architektur und HTTP-Schnittstellen: [docs/ARCHITEKTUR.md](docs/ARCHITEKTUR.md).

## OpenAI verwenden

In Einstellungen den **KI-Anbieter OpenAI** wählen. Unter **OpenAI** den API-Schlüssel verdeckt eingeben und **Schlüssel hinterlegen** anklicken. Auf macOS ist die Speicherung im Schlüsselbund möglich, sonst nur für die Serversitzung. Anschließend **Cloud-KI aktivieren** und **Einstellungen speichern**. Es gibt keine automatische Anfrage beim Hinterlegen oder Anbieterwechsel.

Standardmodell: `gpt-4o-mini`, separates lokales Tageslimit: 10 Anfragen, maximal 1536 Ausgabetokens pro Anfrage. Die OpenAI-API wird separat von ChatGPT bezahlt. Anfragelimits sind keine Geldobergrenze; Anbieterbudget und tatsächliche Abrechnung im OpenAI-Konto prüfen. Chat, Gesprächskontext, Bildanalyse und bestätigte Aktionsvorschläge verwenden den gewählten Anbieter. Bei einem Fehler wird nicht automatisch zu einem anderen kostenpflichtigen Anbieter gewechselt. Der vorhandene Python-Zertifikatsfehler muss auch für OpenAI behoben sein.

Der Verbindungstest für OpenAI ruft ausschließlich den Modellkatalog ohne API-Schlüssel ab. Ein HTTP401-Ergebnis bestätigt eine HTTPS-Antwort, keine gültige Anmeldung. Schlüssel werden nie in Git, SQLite, API-Antworten oder Browserspeichern abgelegt.
