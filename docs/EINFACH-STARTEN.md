# JARVIS einfach einrichten

Du brauchst **einen ZIP-Download** des Projekts und musst keine KI-Dateien selbst auswählen.

## Einmalig

1. Lade JARVIS über den grünen GitHub-Button **Code → Download ZIP** herunter und entpacke die ZIP-Datei.
2. Beende eine alte JARVIS-Sitzung in deren Terminal mit **Control + C**.
3. Öffne im entpackten Ordner **1-JARVIS-einrichten.command**.
4. Lass das Terminal geöffnet und warte. Der Helfer erkennt deinen Mac, lädt das passende llama.cpp-Paket und das kleine KI-Modell, prüft beide Dateien und startet danach KI und JARVIS zusammen. Der Browser öffnet sich automatisch.

Die Auswahl „Kleine lokale KI“, die Verbindung und die kostenlose Systemstimme werden gesetzt. **Du musst keinen API-Schlüssel, keine Voice ID und keinen Port eingeben.** Es wird nichts in eine Cloud-Ausweichroute geschickt.

Falls du den Start lieber im Terminal ausführst: `cd ` mit Leerzeichen eingeben, den entpackten JARVIS-Ordner hineinziehen, Enter drücken und dann:

```bash
python3 -m backend --setup-small-ai
```

## Später

Nur **2-JARVIS-starten.command** öffnen. Das startet KI und JARVIS gemeinsam, prüft eine echte lokale Textantwort und öffnet den Browser. Dieser normale Start lädt nichts neu herunter und benötigt nach der Einrichtung kein Internet. Das Terminal geöffnet lassen; **Control + C** beendet JARVIS und nur den von diesem Starter erzeugten KI-Prozess.

Alternativ im Projektordner:

```bash
python3 -m backend --easy-local
```

## Was geladen wird

- Eine kleine 4-Bit-Variante von **Qwen2.5-0.5B-Instruct**, ungefähr 400 MB. Der Helfer versucht Q4_K_M, Q4_K_S und Q4_0. Ist beim offiziellen Qwen-Repository keine prüfbare Variante unter der Grenze verfügbar, prüft er dasselbe Modell im Community-Repository **bartowski/Qwen2.5-0.5B-Instruct-GGUF**. Quelle und tatsächliche Größe werden angezeigt. Der Helfer prüft die tatsächliche Größe vorab und lädt kein Modell über **450 MB**.
- Das zur tatsächlichen Mac-Architektur passende offizielle **llama.cpp**-Paket, höchstens **150 MB**. Die genaue Größe wird vor dem Download angezeigt.

Es sind also zwei automatische Dateien im Hintergrund; du wählst sie nicht selbst aus. Die Dateien landen nur im entpackten Projektordner. Für Download und Entpacken sollten mindestens **1,5 GB Speicher frei** sein. Das Modell und sein Arbeitsspeicher sind zusätzliche Daten; völlig ohne Modelldownload kann keine neue Offline-KI bereitgestellt werden. Das kleine Modell ist deutlich schwächer als ChatGPT.

## Voraussetzungen und Sicherheit

Du brauchst den Mac mit **macOS 14 oder neuer**, eine unterstützte ARM64- oder Intel-Architektur, **Python 3.10 oder neuer** sowie für die einmalige Einrichtung Internet. Python wird nicht automatisch installiert. Die tatsächliche Kompatibilität des offiziellen Startpakets wird spätestens beim lokalen Start geprüft; eine Architekturauswahl allein garantiert noch keinen funktionierenden Modellbetrieb.

Downloads verwenden macOS-curl mit aktivierter HTTPS-Prüfung, um nicht vom zuvor gemeldeten Python-Zertifikatsspeicher abhängig zu sein. Es werden SHA256-Prüfsummen aus den Release-Metadaten von llama.cpp und den Metadaten der angezeigten Modellquelle geprüft. Wenn die Prüfsumme fehlt oder nicht stimmt, wird nichts ausgeführt. Modellrevision und Downloadgrößen sind fest an diese Metadaten gebunden. Es gibt keine automatische Wahl eines größeren Modells, keine Ausführung von Installationsskripten aus dem Internet, keine Änderungen an Systemeinstellungen, kein sudo und kein Umgehen von macOS-Sicherheitsmeldungen. Nur die ausdrücklich heruntergeladenen, geprüften lokalen Programmdateien erhalten die für ihren Start nötigen Dateirechte.

Vorhandene fremde Prozesse werden nicht beendet. Wenn ein Port belegt ist, schließe deine alte Sitzung in ihrem Terminal. Bei einer Sicherheitsmeldung nutze die regulären macOS-Freigaben für eine vertrauenswürdige Quelle; der Helfer entfernt keine Sicherheitsmarkierungen.

## Stimme ändern

In JARVIS: **Einstellungen → Lokale Sprachausgabe → Deutsche Systemstimme → Systemstimme verwenden → Lokale Stimme testen**. Die Liste zeigt nur tatsächlich vom Browser gemeldete deutsche lokale Stimmen.

## Wenn die Einrichtung stoppt

Lass die genaue Meldung im Terminal stehen und teile sie ohne Schlüssel. Ein abgebrochener Download wird nicht als gültig behandelt. Bereits vollständig geprüfte Downloads werden bei einem erneuten Einrichten wiederverwendet. Sobald die gesamte Installation gültig ist, braucht auch ein erneutes Einrichten keinen weiteren Download.

**Prüfstand:** Der Einrichtungsablauf wurde in der Linux-Cloud mit kontrollierten Download-Daten, Archiven, Prozessen und HTTP-Antworten geprüft. Echte Modell-/Binärdownloads und die Ausführung auf deinem Mac sind dort nicht verifiziert. Die offiziellen Metadaten-APIs waren aus der Cloud nicht erreichbar; falls die Quelle auf deinem Mac keine Prüfsumme oder kein passendes Paket bereitstellt, stoppt der Helfer mit einer Erklärung.

Der Helfer unterstützt auch offizielle stabile Veröffentlichungen, die statt Binärpaketen nur eine Datei `nightly-tag.txt` enthalten: Er prüft deren SHA256 und verwendet exakt den darin genannten offiziellen Build. Die Datei-, Architektur- und Prüfsummenkontrollen der eigentlichen Downloads bleiben aktiv.


## Sprechen, Weltkarte und Handy

- Mikrofon anklicken, sprechen und eine Pause machen: Der erkannte Text wird automatisch gesendet. Unter **Einstellungen → Sprache und Kamera** lässt sich das abschalten. Getippte Entwürfe bleiben erhalten. Spracheingabe hängt von Safari/Browserunterstützung ab und kann durch den Browser online verarbeitet werden.
- **Welt & Kameras** öffnet einen lokal gezeichneten, drehbaren Globus. Beispiel: „Zeig öffentliche Kameras in London“. Auch New York, Reykjavík und Venedig sind hinterlegt. JARVIS fokussiert den Standort und zeigt den offiziellen Link. „Kamera öffnen“ öffnet die öffentliche Seite in einem neuen Tab. Blockierbare Einbettungen entfallen; Verfügbarkeit und etwaige Anmeldung liegen beim Anbieter. Es werden keine privaten Kameras gesucht oder Schutzmechanismen umgangen.
- **Handy verbinden** am Mac zeigt die Kopplung. Mac und iPhone/iPad bleiben im selben vertrauenswürdigen WLAN; der Mac muss weiterlaufen. Einmalig wird ein eigenes HTTPS-Zertifikatsprofil erzeugt. Per Finder/AirDrop übertragen, in iOS installieren und unter **Allgemein → Info → Zertifikatsvertrauenseinstellungen** bewusst vertrauen. Vergleiche den Fingerabdruck mit dem Mac. Das Profil enthält nur das öffentliche Zertifikat, keine privaten Schlüssel oder Geräteverwaltung. Vertraue ausschließlich deinem eigenen Profil; entferne es nach Ende der Nutzung wieder.
- Danach den QR-Code scannen: Er gilt fünf Minuten und nur einmal, gekoppelte Sitzungen höchstens zwölf Stunden. Den Kopplungslink nicht öffentlich weitergeben. **Verbindung beenden** widerruft alle Sitzungen. Ein neuer Mac-Start benötigt eine neue Kopplung. Ohne das Zertifikatsvertrauen gibt Safari die Kamera nicht frei; die App verändert keine System-Vertrauensregeln automatisch. Bei geändertem WLAN/IP die Verbindung neu vorbereiten.
- In Safari über **Teilen → Zum Home-Bildschirm** ablegen. JARVIS läuft weiterhin auf dem Mac; das Handy installiert keine KI-Gewichte.
- **Kamera → Eigene Kamera erlauben**, anschließend **Kamera starten**. Minecraft-Übungen lassen sich dort optional aufklappen. Die Vorschau stoppt beim Schließen, Ausblenden oder Widerrufen der Einstellung. Es werden keine Bilder gespeichert oder hochgeladen.

**Keine echte Bildanalyse:** Das zugelassene kleine Modell versteht nur Text. Es wird kein zusätzliches Bildmodell heruntergeladen. Der 10-Minuten-Minecraft-Plan beruht auf Edition, Version, Steuerung und Übungsziel; er beurteilt keine Kamerabilder und erkennt keine Spiele oder Gegenstände. Java bis 1.8, Java ab 1.9 und Bedrock werden unterschiedlich erklärt. Für andere Lernfragen kannst du dem Textassistenten beschreiben, was du üben möchtest.

**Prüfgrenzen:** Die Weboberfläche wird in Chromium mit simuliertem Mikrofon/Kamerastream und die Handykopplung mit lokalem TLS und explizit vertrauenswürdigem Testzertifikat geprüft. Echte Safari-/iOS-Freigaben, AirDrop, öffentliche Livevideos und die KI-Ausführung auf einem Mac sind in der Linux-Cloud nicht überprüfbar.


## Neue Stimmprofile und Agentenwerkstatt

**Stimme → JARVIS · Ruhig** wählt und testet das tiefere Stimmprofil mit einem Klick. Es nutzt ausschließlich eine vorhandene lokale deutsche Stimme; es wird keine neue Stimme installiert. Falls du den Klang nicht magst, teste **Klar** oder **System pur**. In den Einstellungen kannst du weiterhin eine konkrete vorhandene Stimme wählen. Es handelt sich um Stimmprofile, keine mitgelieferte neuronale Filmstimme. Auf Geräten ohne lokale deutsche Stimme ist der Wunsch nach beliebiger Sprache ohne vorhandene Sprachdaten technisch nicht erfüllbar; JARVIS zeigt das an.

**Agenten** öffnet die Werkstatt. Wähle einen Agenten, beschreibe den Auftrag und klicke **Auftrag starten**. Oder sage: **„Beauftrage Nova: Schreibe eine freundliche Begrüßung.“** ATLAS plant, NOVA schreibt Entwürfe, SENTINEL prüft einen übergebenen Text. In **Aufträge & Ergebnisse** klappst du das Resultat auf und kannst es kopieren. Die Ansicht lässt sich von 3D auf Liste umschalten. Die Computer leuchten beim tatsächlichen Arbeiten; es gibt keine erfundenen Prozentanzeigen.

Das bereits vorhandene lokale Modell wird gemeinsam genutzt: höchstens acht offene Aufgaben, nacheinander verarbeitet. Ein Auftrag wartet, solange das Modell im Chat beschäftigt ist. Fehlende KI erscheint als Fehler. Beim Abbrechen wird ein verspätetes Ergebnis verworfen; die laufende Berechnung kann noch auslaufen. Beim Serverneustart werden offene Aufträge als unterbrochen markiert und nicht automatisch neu ausgeführt. Aufgaben und fertige Ergebnisse bleiben im privaten JARVIS-Datenordner gespeichert, getrennt vom normalen Chatverlauf. Das Löschen des Chatverlaufs löscht diese Aufträge nicht.

Die Agenten sind Rollen für lokale Textaufgaben. Sie haben keine eigenständige Websuche, keine Kameraaugen und führen keine Änderungen an deinen Geräten durch. Ein fertiger Entwurf ist kein Nachweis, dass eine darin beschriebene reale Aktion ausgeführt wurde. Fakten bitte prüfen. Ohne größeres oder externes Modell bleibt die Sprach- und Denkqualität der kleinen KI begrenzt.
