# JARVIS einfach benutzen

## Einmal einrichten, später starten

Lade das Projekt-ZIP herunter und entpacke es. Öffne **1-JARVIS-einrichten.command**. Python 3.10+, macOS 14+ und eine unterstützte Mac-Architektur müssen vorhanden sein. Der Helfer prüft die Downloadquellen, Größe, Architektur und SHA256-Prüfsummen. Er lädt eine passende Qwen2.5-0.5B-4-Bit-Variante unter 450 MB und ein offizielles llama.cpp-Startpaket unter 150 MB. Falls beim offiziellen Qwen-Repository keine passende prüfbare Variante verfügbar ist, wird dasselbe kleine Modell von bartowski geprüft; die Quelle wird angezeigt. Keine größere KI wird automatisch geladen. Internet wird einmal für diese Einrichtung benötigt.

Die deutsche Spracherzeugung und ihre Sprachdaten sind bereits im Projekt enthalten, einschließlich der freien Quellen und Lizenztexte. Kein Stimmenkonto, keine Systemstimme und keine separate Stimmeninstallation. Das Sprachpaket samt Quellen vergrößert den entpackten Projektordner um ungefähr 10 MB; es ist kein großes neuronales Sprachmodell.

Der Einrichter startet JARVIS nach erfolgreicher Einrichtung. Später nur **2-JARVIS-starten.command** öffnen. Das Terminal bleibt offen. **Control + C** beendet JARVIS und nur die vom Starter erzeugte lokale KI. Nicht beide Startdateien gleichzeitig öffnen. Eine bestehende gültige Installation im selben Projektordner wird wiederverwendet. Wenn du die letzte Version neu entpackst, lasse den alten JARVIS-Ordner daneben liegen. Der Einrichter sucht ausschließlich benachbarte JARVIS-Ordner nach passenden bereits geprüften KI-Dateien ab und übernimmt sie nach erneuter SHA256-Prüfung. Er kopiert keine Schlüssel, Dokumente oder alten Programmdateien und verändert den alten Ordner nicht. So wird bei einer gültigen alten Einrichtung kein neuer großer Modelldownload benötigt.

Alternativ im Terminal: `cd ` mit Leerzeichen eingeben, den entpackten JARVIS-Ordner hineinziehen, Enter drücken. Einmal `python3 -m backend --setup-small-ai`, später `python3 -m backend --easy-local`.

## Mit dem Kern sprechen

Tippe den goldenen Kern an oder klicke **Mit Jarvis sprechen**. Beim ersten Mal bestätigst du die Mikrofoninformation und die Browserfreigabe. Nach einem erkannten Satz wird der Text automatisch gesendet; JARVIS antwortet mit der mitgelieferten Stimme und hört danach wieder zu. Das funktioniert auch bei geöffneter Agentenansicht. Getippte Entwürfe werden nicht automatisch mitgeschickt.

Erneutes Antippen oder **Gespräch beenden** stoppt das Gespräch. Laufende Agentenaufträge laufen davon unabhängig weiter und lassen sich in ihrer Ergebnisansicht separat abbrechen. Der Stop-Knopf beendet auch die Klatscherkennung. Beim Ausblenden der Seite werden Mikrofone und Gespräch gestoppt. Nach einem Neustart hört JARVIS nicht automatisch zu.

Optional: **Doppelklatschen aktivieren**. Dafür bleibt das Mikrofon sichtbar eingeschaltet. Zwei kurze Klatscher starten oder beenden ein Gespräch. Die Klatscher werden lokal ausgewertet; die Erkennung kann bei Hintergrundgeräuschen unzuverlässig sein. Auch während JARVIS spricht, versetzt Doppelklatschen das Gespräch in den Schlafmodus und stoppt die Ausgabe; laufende Agentenaufträge bleiben aktiv. Erneutes Doppelklatschen weckt das Gespräch.

Die **Spracherkennung** hängt vom Browser ab und kann durch dessen Anbieter online verarbeitet werden. Sie ist nicht garantiert offline. Der Einwilligungsdialog erklärt dies, bevor du sie nutzt. Die **Sprachausgabe** ist davon unabhängig und wird mit der mitgelieferten Engine lokal erzeugt. Ohne Browser-Spracherkennung kannst du schreiben und trotzdem die JARVIS-Stimme hören.

## JARVIS-Stimme

**Stimme → JARVIS · Ruhig**, **Klar** oder **Dunkel** wählt und testet den Klang mit einem Klick. Die Stimme basiert auf einer eigenen deutschen Formant-Konfiguration der mitgelieferten freien meSpeak/eSpeak-Engine. Sie benutzt keine Systemstimme und lädt keinen externen Sprachdienst. Sie klingt synthetisch und robotisch, nicht wie eine neu trainierte menschliche Filmstimme. Lautstärke und Stop findest du unter dem Kern.

## Agenten und Bilder

**Agenten** öffnet die Werkstatt. ATLAS plant, NOVA schreibt, SENTINEL prüft Texte, BAUER erstellt eine anklickbare Checkliste und STUDIO erstellt Werbeskripte und Produktclips. Die 3D-Ansicht hat einen einstellbaren Blickwinkel und lässt sich auf eine Liste umschalten. Bewegungen und Licht zeigen tatsächliche Arbeit; es gibt keine erfundenen Prozentwerte.

Beispiele: **„Beauftrage einen Agenten, der einen Lernplan erstellt“**, **„Beauftrage Nova: Schreibe eine Begrüßung“**, **„Ein Agent soll eine anklickbare Checkliste erstellen“**. Nur wenn tatsächlich ein Auftrag angelegt wurde, bekommst du eine Auftragskennung. Ergebnisse stehen unter **Aufträge & Ergebnisse**. Eine fehlende lokale KI erscheint als Fehler, nicht als Erfolg.

Ein bereits vorhandenes lokales Textmodell verarbeitet höchstens acht offene Aufgaben nacheinander. Beim Abbrechen werden späte Resultate verworfen; eine laufende Berechnung kann noch auslaufen. Nach einem Serverneustart werden offene Jobs als unterbrochen markiert und nicht automatisch neu ausgeführt.

Unter **Bild anhängen** wählst du ein Foto und beschreibst, was du möchtest. Vor dem Senden wird es auf höchstens 1280 Pixel verkleinert und als JPEG neu erzeugt; ursprüngliche Metadaten werden dabei nicht übernommen. Erst **Auftrag starten** oder ein ausdrücklich gesprochener Agentenauftrag überträgt es an deinen eigenen JARVIS-Server. Bilder und Ergebnisse werden privat im JARVIS-Datenordner gespeichert, nicht an einen externen KI-Dienst gesendet. Das Löschen des normalen Chatverlaufs löscht die Agentenaufträge und ihre Bilder nicht.

Auf dem Mac versucht JARVIS **Apple Vision** für lokale Bildklassifikation und Texterkennung zu verwenden. Dafür wird kein neues großes Modell geladen. Die Labels, Konfidenzen und erkannten Texte werden dem kleinen Textmodell als unsicherer Befund übergeben. Das ist kein vollständiges Bildverständnis, keine laufende Videoanalyse und kein verlässliches Minecraft-Coaching. Außerhalb des Macs oder bei einem Analysefehler wird das deutlich angezeigt. Dein Bild kann dann weiterhin als Gestaltungsmaterial für STUDIO dienen; JARVIS behauptet keine erkannten Bildinhalte.

## Werbung mit eigenem Produktfoto

Wähle **STUDIO**, hänge ein Produktfoto an und beschreibe das Produkt und die gewünschte Werbung. Das kleine Textmodell schreibt das Skript. Im fertigen Ergebnis kannst du die Vorschau ansehen und den Film exportieren. Der Clip verwendet dein Foto mit Kamerabewegungen, Szenentexten und optional der mitgelieferten JARVIS-Sprecherstimme. Die reine Vorschau ist stumm; die Sprecherstimme wird beim Export hinzugefügt.

Lasse den Bereich während des Exports sichtbar geöffnet. Je nach Skript dauert er etwa 9–30 Sekunden. Unterstützte Browser liefern WebM oder MP4. Ein ausgeblendeter Tab unterbricht den Export. Eine unbrauchbar kleine Datei wird nicht als Erfolg angeboten.

**Keine generative Film-KI:** Es werden keine neuen Filmszenen aus einem Prompt erzeugt. Unter der Vorgabe „nur wenig größer, kein externer KI-Dienst“ ist diese Funktion nicht möglich. Dieser Produktfilm ist eine lokale Montage aus deinem Bild und einem KI-Skript, kein Ersatz für ein großes Videomodell. Auch die allgemeine Denkfähigkeit des kleinen Textmodells wird dadurch nicht auf ChatGPT-Niveau angehoben.

## Welt, Nachrichten und Fußball

**Welt** öffnet den lokalen drehbaren Globus. Tippe eine Ländermarkierung an oder wähle das Land im Menü; passende öffentliche Meldungen erscheinen daneben. Ohne erreichbare Nachrichtenquelle bleiben ältere Abrufe gekennzeichnet oder die Liste leer. Die bisherigen öffentlichen Kameralinks sind entfernt. [Astra-Anleitung](ASTRA.md).

**Fußball & Live** zeigt offizielle Angebote von Sportschau, ARD und ZDF, vielfach ohne Konto. Ob ein bestimmtes Spiel als freier Videostream verfügbar ist, hängt von Sendezeit, Standort und Übertragungsrechten ab. Kein vollständiger Bundesliga-Zugang wird versprochen.

## Sprechen, Weltkarte und Handy

Mac und iPhone/iPad müssen im selben vertrauenswürdigen WLAN sein; der Mac bleibt eingeschaltet. **Handy verbinden** erzeugt am Mac eine private HTTPS-Verbindung und einen kurz gültigen einmaligen Kopplungslink samt QR-Code.

1. **Verbindung vorbereiten** anklicken.
2. **Profil im Finder zeigen** und das eigene JARVIS-Heimnetz.mobileconfig per AirDrop auf dein eigenes iPhone/iPad übertragen. Fingerabdruck mit dem Mac vergleichen.
3. Auf iOS unter **Profil geladen** installieren und unter **Allgemein → Info → Zertifikatsvertrauenseinstellungen** bewusst der eigenen JARVIS-Zertifizierungsstelle vertrauen. Das Profil enthält nur das öffentliche Zertifikat, keine privaten Schlüssel oder Geräteverwaltung. Entferne es nach Ende der Nutzung wieder.
4. QR-Code scannen; er gilt fünf Minuten und nur einmal. Sitzungen gelten höchstens zwölf Stunden. Nach einem neuen Serverstart neu koppeln. **Verbindung beenden** widerruft die Sitzungen.
5. In Safari **Teilen → Zum Home-Bildschirm** wählen. **Kamera → Kamera starten** und die Browserfreigabe bestätigen.

Ohne vertrauenswürdiges HTTPS gibt Safari die Handy-Kamera nicht frei. JARVIS verändert keine System-Vertrauensregeln automatisch und deaktiviert keine Sicherheitsprüfungen. Die eigene Kameravorschau stoppt beim Schließen, Verbergen oder Widerrufen. Sie speichert oder überträgt nicht automatisch Bilder; nur ausdrücklich angehängte Agentenbilder werden gesendet.

## Prüfstand und Grenzen

Python- und HTTP/TLS-Tests laufen in Linux. Die Weboberfläche, echte Spracherzeugung, exportierte Video-/Audiotracks und Gesprächsabläufe werden in Chromium geprüft; Mikrofon und Spracherkennung werden dafür simuliert. Apple-Vision-Ausführung, echte Mac-/iOS-Freigaben, AirDrop, native Safari-Spracherkennung und externe Livevideos sind in der Cloud nicht verifiziert. Die Modellqualität wird nicht aus simulierten Testantworten abgeleitet.

TikTok war aus dieser Cloud nicht erreichbar. Eine Analyse sämtlicher Videos von Moritz Maacker wird deshalb nicht behauptet.

## Optional: natürliche Stimme und Astra

Das [Stimmen-Nachrüst-Paket](NATUERLICHE-STIMME.md) ergänzt die natürliche Offline-Stimme. Das separate [Astra-Update](ASTRA.md) lädt keine neue Stimme und kein Textmodell. Der frühere Mini-Hub ist entfernt; Weltansicht und Astra ersetzen ihn.
