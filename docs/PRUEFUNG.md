# Prüfstand

Stand: 3. November 2026. Linux-Cloud; der persönliche Mac und das iPhone sind nicht verbunden.

## Verifiziert

- **145 Python-Tests bestanden**, keine übersprungen. Python-Suite mit echten lokalen HTTP-/TLS-Verbindungen, Host-/Origin-/Token-Prüfung, privater Ablage, Budgetgrenzen und sicheren bestätigten Aktionen. Temporäre TLS-Zertifikate werden explizit vertraut; TLS-Prüfung wird nicht abgeschaltet.
- Agentenaufträge: natürliche Formulierungen führen zu einem tatsächlichen Job. Queue, Fehler, Abbruch, Neustart und getrennte Gespräche sind getestet. Sprachmodellantworten sind hierfür kontrollierte Fixtures; daraus wird keine echte Modellqualität abgeleitet.
- Bildanhänge: Format-/Größenprüfung, private Dateien mit Modus0600, Migration bestehender Datenbanken, Rückgabe lokaler Bildbefunde und Übergabe als Daten statt auszuführende Befehle. Auf Nicht-Macs wird kein vorhandenes Bildverständnis behauptet.
- Eigene deutsche Stimme: echte eSpeak/meSpeak-Spracherzeugung im Browser, decodierbare PCM-Daten mit Sprachsignal und echte Web-Audio-Wiedergabe. Jeder Systemstimmen-Aufruf wird im Integrationstest als Fehler behandelt. Keine externen Sprachrequests. Die Engine ist keine neu trainierte neuronale Stimme; es handelt sich um eine mitgelieferte freie Formantengine mit eigener Konfiguration.
- Gesprächsablauf: Kernaktivierung, Mikrofoninformation, automatisches Senden, Wiederaufnahme nach einer Antwort, Agentenansicht während des Gesprächs, tatsächlicher Job nach gesprochenem Auftrag und vollständiger Mikrofon-Stop. Spracherkennung und Mikrofon sind simuliert; die ausgehende Stimme ist echt. Ein Rennen zwischen Einwilligungsdialog und sehr kurzer erster Spracheingabe wurde behoben.
- Lokale Doppelklatscherkennung: synthetische Mikrofonimpulse laufen durch den tatsächlichen RMS-Detektor. Start/Stop und Freigabe aller Audiotracks sind geprüft. Das ist kein Nachweis für zuverlässige Erkennung in jedem physischen Raum.
- Produktfilm: generiertes Testfoto wird über den normalen Bildauftrag hochgeladen, im Film tatsächlich verwendet und mit der echten mitgelieferten Sprecherstimme exportiert. `ffprobe` bestätigt Video- und Audiotrack sowie 720×720 Pixel; `ffmpeg` decodiert ein Bild. Eine unbrauchbar kleine Aufnahme wird nicht als Erfolg angeboten. Keine generierten Filmszenen oder echte Film-KI wird behauptet.
- Mobiles Layout: 390 Pixel Breite, Deutschlandfilter, öffentliche Anbieterlinks, Sportverzeichnis, eigene Kameravorschau mit simuliertem Video und ausdrücklich gewählte Aufnahme an Agenten; danach enden die Kameratracks.
- Update ohne unnötigen KI-Neudownload: passende Dateien aus einem benachbarten alten JARVIS-Ordner werden nur nach Architektur-/SHA256-Prüfung wiederverwendet. Geänderte Dateien, falsche Architektur, Konflikte und Dateien außerhalb des Cachebereichs werden abgewiesen. Alte Schlüssel und Dokumente werden nicht übernommen. Entfernen des alten Ordners zerstört die übernommenen Dateien nicht.
- Kein Nutzer-API-Schlüssel in Projektdateien; keine systemweiten Vertrauens- oder Sicherheitsänderungen. Das offizielle Release- und Modell-Downloadverfahren behält HTTPS-, Architektur-, Größen- und Prüfsummenkontrollen.

**Vier Browserprüfungen bestanden.** Optionale reproduzierbare Browserprüfungen stehen in [tests/browser](../tests/browser/README.md). Die Anwendung selbst benötigt weder Playwright noch ffmpeg.

## Nicht auf echter Hardware oder live geprüft

- Native Apple-Vision-Klassifikation/OCR auf einem physischen Mac. Die öffentlichen Framework-APIs sind implementiert; Datenfluss und Nichtverfügbarkeit sind mit Testbefunden geprüft. Kein erfolgreicher Mac-Lauf wird behauptet.
- Tatsächliche Mac-Inferenz mit dem kleinen Qwen-Modell und dem offiziellen llama.cpp-Binärpaket. Tests verwenden kontrollierte lokale Antworten; die Cloud lädt keine großen Modellgewichte.
- Reale Mikrofone, Raumklatscher, Safari-/iOS-Spracherkennung, AirDrop und Zertifikatsfreigaben am persönlichen Gerät. Die Browser-Spracheingabe kann einen Dienst des Browseranbieters verwenden; vollständige Offline-Erkennung wird nicht zugesichert.
- Externe Webcam-Videos und Fußballspiele. Anbieterrechte, Einbettung, Anmeldung und Standort können den Zugang begrenzen. Der Katalog enthält öffentliche Anbieterseiten, keine garantierten Direktstreams aller Spiele.
- TikTok-Videos von Moritz Maacker. TikTok war aus der Cloud nicht erreichbar; eine Analyse sämtlicher Videos oder ein Funktionsvergleich wird nicht erfunden.

Mit nur wenig zusätzlicher Größe und ohne externen KI-Dienst enthält JARVIS keine generative Video-KI und kein großes visuelles Sprachmodell. Die Produktfilmfunktion montiert das eigene Bild mit einem lokalen KI-Skript und lokaler Spracherzeugung.
