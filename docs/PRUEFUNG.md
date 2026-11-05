# Prüfstand

Stand: 3. November 2026. Linux-Cloud; der persönliche Mac und das iPhone sind nicht verbunden.

## Verifiziert

- **202 Python-Tests bestanden**, keine übersprungen. Python-Suite mit echten lokalen HTTP-/TLS-Verbindungen, Host-/Origin-/Token-Prüfung, privater Ablage, Budgetgrenzen und sicheren bestätigten Aktionen. Temporäre TLS-Zertifikate werden explizit vertraut; TLS-Prüfung wird nicht abgeschaltet.
- Agentenaufträge: natürliche Formulierungen führen zu einem tatsächlichen Job. Queue, Fehler, Abbruch, Neustart und getrennte Gespräche sind getestet. Sprachmodellantworten sind hierfür kontrollierte Fixtures; daraus wird keine echte Modellqualität abgeleitet.
- Bildanhänge: Format-/Größenprüfung, private Dateien mit Modus0600, Migration bestehender Datenbanken, Rückgabe lokaler Bildbefunde und Übergabe als Daten statt auszuführende Befehle. Auf Nicht-Macs wird kein vorhandenes Bildverständnis behauptet.
- Eigene deutsche Stimme: echte eSpeak/meSpeak-Spracherzeugung im Browser, decodierbare PCM-Daten mit Sprachsignal und echte Web-Audio-Wiedergabe. Jeder Systemstimmen-Aufruf wird im Integrationstest als Fehler behandelt. Keine externen Sprachrequests. Die Engine ist keine neu trainierte neuronale Stimme; es handelt sich um eine mitgelieferte freie Formantengine mit eigener Konfiguration.
- Gesprächsablauf: Kernaktivierung, Mikrofoninformation, automatisches Senden, Wiederaufnahme nach einer Antwort, Agentenansicht während des Gesprächs, tatsächlicher Job nach gesprochenem Auftrag und vollständiger Mikrofon-Stop. Spracherkennung und Mikrofon sind simuliert; die ausgehende Stimme ist echt. Ein Rennen zwischen Einwilligungsdialog und sehr kurzer erster Spracheingabe wurde behoben.
- Lokale Doppelklatscherkennung: synthetische Mikrofonimpulse laufen durch den tatsächlichen RMS-Detektor. Start/Stop und Freigabe aller Audiotracks sind geprüft. Das ist kein Nachweis für zuverlässige Erkennung in jedem physischen Raum.
- Produktfilm: generiertes Testfoto wird über den normalen Bildauftrag hochgeladen, im Film tatsächlich verwendet und mit der echten mitgelieferten Sprecherstimme exportiert. `ffprobe` bestätigt Video- und Audiotrack sowie 720×720 Pixel; `ffmpeg` decodiert ein Bild. Eine unbrauchbar kleine Aufnahme wird nicht als Erfolg angeboten. Keine generierten Filmszenen oder echte Film-KI wird behauptet.
- Mobiles Layout: 390 Pixel Breite, Deutschlandfilter, öffentliche Anbieterlinks, Sportverzeichnis, eigene Kameravorschau mit simuliertem Video und ausdrücklich gewählte Aufnahme an Agenten; danach enden die Kameratracks.
- Update ohne unnötigen KI-Neudownload: passende Dateien aus einem benachbarten alten JARVIS-Ordner werden nur nach Architektur-/SHA256-Prüfung wiederverwendet. Geänderte Dateien, falsche Architektur, Konflikte und Dateien außerhalb des Cachebereichs werden abgewiesen. Alte Schlüssel und Dokumente werden nicht übernommen. Entfernen des alten Ordners zerstört die übernommenen Dateien nicht.
- Kein Nutzer-API-Schlüssel in Projektdateien; keine systemweiten Vertrauens- oder Sicherheitsänderungen. Das offizielle Release- und Modell-Downloadverfahren behält HTTPS-, Architektur-, Größen- und Prüfsummenkontrollen.

**Sieben Browserprüfungen bestanden:** gebündelte Stimme, Gespräch, Produktfilm, Navigation, Hub, natürliche Stimme und getrenntes Abbrechen der Gesprächsausgabe. Optionale reproduzierbare Browserprüfungen stehen in [tests/browser](../tests/browser/README.md). Die Anwendung selbst benötigt weder Playwright noch ffmpeg.

## Nicht auf echter Hardware oder live geprüft

- Native Apple-Vision-Klassifikation/OCR auf einem physischen Mac. Die öffentlichen Framework-APIs sind implementiert; Datenfluss und Nichtverfügbarkeit sind mit Testbefunden geprüft. Kein erfolgreicher Mac-Lauf wird behauptet.
- Tatsächliche Mac-Inferenz mit dem kleinen Qwen-Modell und dem offiziellen llama.cpp-Binärpaket. Tests verwenden kontrollierte lokale Antworten; die Cloud lädt keine großen Modellgewichte.
- Reale Mikrofone, Raumklatscher, Safari-/iOS-Spracherkennung, AirDrop und Zertifikatsfreigaben am persönlichen Gerät. Die Browser-Spracheingabe kann einen Dienst des Browseranbieters verwenden; vollständige Offline-Erkennung wird nicht zugesichert.
- Externe Webcam-Videos und Fußballspiele. Anbieterrechte, Einbettung, Anmeldung und Standort können den Zugang begrenzen. Der Katalog enthält öffentliche Anbieterseiten, keine garantierten Direktstreams aller Spiele.
- TikTok-Videos von Moritz Maacker. TikTok war aus der Cloud nicht erreichbar; eine Analyse sämtlicher Videos oder ein Funktionsvergleich wird nicht erfunden.

Mit nur wenig zusätzlicher Größe und ohne externen KI-Dienst enthält JARVIS keine generative Video-KI und kein großes visuelles Sprachmodell. Die Produktfilmfunktion montiert das eigene Bild mit einem lokalen KI-Skript und lokaler Spracherzeugung.

## Nachrüstung: natürliche Stimme und Mini-Hub

- Echte neuronale Thorsten-Ausgabe mit offizieller sherpa-onnx-Linux-Engine erzeugt, als PCM geprüft und über den geschützten lokalen Endpunkt im Browser decodiert und abgespielt. Kein Systemstimmen-Aufruf. Der native Mac-Selbsttest bleibt Voraussetzung für Aktivierung auf dem Gerät.
- Hub-Browserprüfung mit kontrollierten RSS-/Plattformdaten: Länderfilter, gespeicherte Kanalnamen, Planer, Systemanzeige, laufender Agentenauftrag und schmales Layout. Das belegt keine Live-Verfügbarkeit von tagesschau.de, YouTube oder TikTok; deren Abruf ist in dieser Cloud eingeschränkt.
- Gesprächsprüfung umfasst Doppelklatschen während einer Antwort, Schlafen und Aufwecken. Eine zusätzliche Prüfung trennt das Abbrechen der Gesprächsausgabe von weiterlaufender Tonerzeugung für Hintergrundexporte.
- Additives Update von Basis 232ba23 geprüft: vorhandene Einstellungen, Verlauf, Planer und Textmodell bleiben erhalten. Prüfsummen, unbekannte Änderungen und Rollback werden geprüft. Der kleine ZIP-Helfer enthält keine Modellgewichte.

## Astra-Update · 4. November 2026

Der Mini-Hub ist aus der Oberfläche entfernt; sein Nachfolger ist die Weltansicht mit Länderfilter und öffentlichen Nachrichten. Die Desktop-Funktionen ergänzen überprüfbare Eingabeabläufe; sie sind kein allgemeiner Computer-Agent.

- Browserprüfung: Astra per gesprochenem Text aktivieren, Partikelansicht, Rückkehr zu Jarvis, Welt-Nachrichtenfilter, geprüfte Desktop-Schritte mit kontrolliertem Eingabetreiber, unabhängiges Stummschalten, Popup-Websteuerung und mobiles Layout.
- Backend-Prüfungen: keine Ausführung vor Start, Token/Schema/Ablaufkennung, Stop während Countdown, abgewiesene Modellkoordinaten, echte Aufrufreihenfolge des kontrollierten Treibers, Fehler statt erfundenem Erfolg sowie öffentliches Nachrichten-JSON als RSS-Fallback.
- Additives Astra-Paket enthält keine Modelle und überspringt ausdrücklich die Stimmeninstallation. Migration von beiden zuletzt bereitgestellten Versionen und Erhalt der persönlichen Daten werden geprüft.
- Native CoreGraphics-Maus-/Tastatureingaben, Bedienungshilfen-Freigabe und AppKit/WebKit-Fenster sind in der Linux-Cloud nicht ausgeführt. Live-Erreichbarkeit der Nachrichtenquelle ist ebenfalls nicht nachgewiesen. Kein autonomer 3D-Bildnachbau wird behauptet.

## Korrekturen für Apps, Astra und Blender

- Öffnen von Apps/Webseiten ohne Laden der Eingabe-Frameworks bzw. ohne AX-Berechtigung geprüft. Spotify-native/Web-Fallback und deterministische URL-Aufträge geprüft.
- Astra-Identität bleibt in der privaten Datenbank und wird an das lokale Modell übergeben; konkrete Selbstvorstellungen werden korrigiert. Daraus wird kein allgemeines Niveau wie ChatGPT abgeleitet.
- Popup-Prozessfehler und fehlende Ladebestätigung führen zu sichtbaren Fehlern. Browser-Popup kann dieselben privaten Steuerungen ohne URL-Token über die lokale Sitzung laden. Native AppKit-Ereignispumpe wurde korrigiert; Mac-Hardware bleibt ungeprüft.
- Echter Blender-Lauf unter Linux: Auto (6 Meshes), Haus (5 Meshes), Roboter (8 Meshes), Dateien jeweils gespeichert und mit einem zweiten Blender-Prozess erneut geladen. Abbruch vor dem ersten Mesh verhindert Erstellung und Erfolgsmeldung. Keine Gewichtsdateien wurden geladen.
- Freie 3D-Beschreibungen werden nur als streng validierte Grundkörperdaten an einen festen Blender-Baustein übergeben. Kein KI-generiertes Python wird ausgeführt. Grenzen, ungültige Werte und fehlender lokaler Anbieter sind geprüft. Das ist kein Nachweis für präzisen Bildnachbau oder jede beliebige Modellierungsaufgabe.

Zusätzlich wurde der vollständige Desktop-Modellweg mit echtem Blender im Headless-Modus geprüft: Auftrag vorbereiten, Start, Blender-Prozess, sechs Auto-Meshes, gespeicherte und zum Download validierte `.blend`-Datei. Einzelne eindeutige App-/Webbefehle starten im Frontend jetzt direkt; die Backend-Vorbereitung allein führt weiterhin nichts aus.

Blender-Erkennung: versioniertes App-Bundle im Downloadordner, Start über den tatsächlichen Pfad nach gescheiterter Bundle-Suche und Auffinden der Blender-Programmdatei sind mit realen Plist-Dateien in Testordnern geprüft. Nutzername wird separat dauerhaft gespeichert; direkte Namensabfrage und falsche Selbstnamen als Begrüßung sind geprüft. Native Mac-Ausführung bleibt hier ungeprüft.

Regression geprüft: „Öffne Blender“ und „Kannst du Blender öffnen?“ werden als App-Start und nicht als Modellierungsauftrag verarbeitet. Anrede „Astrid“ wird akzeptiert; persönliche Angaben mit vorangestellter Assistentenanrede werden nicht mehr als Desktop-Aufträge abgefangen.

Stimme/Companion: gezielter Abbruch neuronaler Ausgabe, frei werdende Engine-Sperre, Companion-Heartbeat und zustellbare UI-Aufträge sowie 40 reale Team-Teilaufträge getestet. Browser: tatsächliche neuronale Thorsten-Ausgabe, Astra-Abläufe und Hintergrundton nach Stummschaltung bestanden. Blender-CPU-Rendering mit Kamera/Licht erzeugt ein echtes PNG (400305 Bytes im Prüflauf). Mac-Mikrofon, native Maus und AppKit bleiben hier ungeprüft; Browser-Hintergrund-ASR kann eingeschränkt sein. Kein autonomer Videoschnitt oder vollständiger 3D-Fotonachbau wird behauptet.

Referenzstil: anklickbare farbige Arbeitsinseln mit echten Zuständen und festgehaltenem ausgewähltem Auftrag; separate Details zu Auftrag und Ergebnis. Browserprüfung zeigt Schlafen/Arbeiten/Fertig mit kontrollierter lokaler Inferenz. Prozedurale Low-Poly-Bühne wird zu einem realen 720p-Video exportiert und mit ffprobe geprüft. Bestehender Produktfoto-Export mit echter Sprecher-Audiospur bleibt geprüft. Kein frei generierendes Film-Modell wird behauptet.

## 5. November: 3D-Werkstatt und Bedienung

Die perspektivische 3D-Szene wurde tatsächlich im Browser gerendert. Figuren-Picking per Maus, Listenfallback und echter 720p-Low-Poly-Videoexport sind geprüft. Die Szene zeichnet lokale 3D-Polygone, ohne neue Modellgewichte oder Netzressourcen.

Kombinierte Blender-Aufträge und echte gespeicherte Sportwagen-Meshes sowie Abbruch sind geprüft. Konkrete Richtungsbefehle für den Mauszeiger und Texteingabe in ausdrücklich genannte Apps erzeugen validierte Schritte. Native Mac-Eingaben sind hier nicht ausgeführt. Das Begleitfenster zeigt jetzt echten Mikrofon-/Fehlerstatus aus dem geöffneten Hauptbrowser.

Chromium-Aufrufe von www.tiktok.com/@moritz.maaker und www.instagram.com/moritz.maaker/ endeten mit ERR_TUNNEL_CONNECTION_FAILED. Keine Videos wurden gesehen. Ein Domainfreigabe-Entwurf wurde gespeichert; die Freigabe ist noch nicht aktiviert.

Der Installer verändert die gewählte Stimme nicht mehr automatisch.

Audiohinweis: verweigerte Browserwiedergabe im modalen Stimmfenster nachgestellt. Hinweis im aktiven Dialog tatsächlich anklickbar; Schließen verhindert sofortiges Wiedererscheinen; Aktivieren bei anschließend freigegebener Wiedergabe erfolgreich. Mehrere automatische Antworten ohne wiederholte Wiedergabeklicks bleiben geprüft.

Notizen-Regression: alter 3D-/Videospielverlauf wird gezielt vorgegeben. Notizen-Aufträge umgehen das Sprachmodell, fehlender Inhalt führt zu Rückfrage, native Skriptdaten werden als argv und escaped HTML übergeben. Kein done ohne Notes-Kennung. Browserablauf durch den kontrollierten Notes-Adapter bestätigt; echte Mac-Notes-Ausführung weiterhin ungeprüft.

## Rückfragen und vollständiger Chat-Reset

Notizinhalt, App, Webseitenadresse und Ziel-App für Texteingabe werden als konkrete Rückfragen gespeichert. Folgeantworten umgehen das Sprachmodell. Tests prüfen das Löschen aller Gesprächsbereiche und des gemerkten Namens sowie das Verwerfen einer verspäteten Modellantwort nach dem Löschen. Bereits erstellte Dateien und Notizen werden dabei nicht entfernt. Native Mac-Ausführung bleibt hier ungeprüft.

Im Chromium zusätzlich geprüft: zweistufige Notiz-Erstellung mit einfachem Inhalt als Folgeantwort, bestätigter Adapteraufruf, Chat-löschen-Knopf inklusive offener Rückfrage und anschließend „Öffne eine App“ → „Spotify“.

Ein-Klick-Start im Chromium geprüft: Start ohne vorhandenen Ablauf, Hinweis bei leerem Textfeld, neuer Auftrag nach abgeschlossenem Ablauf, sichtbarer Berechtigungsfehler und erfolgreicher erneuter Start. Kontrollierter Eingabetreiber; native Mac-Berechtigungen und App-Ereignisse hier nicht geprüft.

Handy-Nachbesserung: HTTPS-Kopplung, öffentliche App-Metadaten und Icon ohne Sitzung, Home-Bildschirm-Start ohne Einmal-Ticket, manuelle Kopplung im separaten App-Kontext sowie gespeicherte Sitzungs-Hashes und Widerruf sind geprüft. Eine tatsächliche iPhone-Installation und iOS-Zertifikatsfreigabe sind in dieser Linux-Umgebung nicht geprüft.

Feste Thorsten-Präferenz: Standard, alte gespeicherte Roboterstimmen-Auswahl und Updates alter Clients bleiben bei Thorsten. Sprachpaket-Einrichtung läuft einzeln im Hintergrund, aktiviert nur eine geprüfte Stimme und ist nur direkt am Mac erreichbar. Kein Formant- oder Systemstimmen-Fallback.

Die echte Thorsten-Inferenz mit lokal vorhandenem neuronalen Modell und anschließender Browserwiedergabe ist bestanden. Separat ist automatisches Vorlesen mehrerer Antworten unter Browser-Autoplay-Beschränkung mit kontrollierten WAV-Antworten am Thorsten-Endpunkt geprüft.

Studio-Überarbeitung: eigene prozedurale Jarvis-Figur statt der Referenz-Dreiergruppe. Echter Produktfoto-Export mit Thorsten enthält überprüfte Video- und Audiospuren. Der Low-Poly-Stil wird als echtes 720p-Video exportiert. Vorschau, Satz-Untertitel und derselbe Thorsten-Audiopuffer im Export sind im Browser geprüft; fehlende Sprachdaten ergeben einen sichtbaren Fehler ohne synthetische Ersatzstimme.
