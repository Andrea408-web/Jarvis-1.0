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

- Das kleine offizielle **Qwen2.5-0.5B-Instruct Q4_K_M**-Modell, ungefähr 400 MB. Der Helfer prüft die tatsächliche Größe vorab und lädt kein Modell über **450 MB**.
- Das zur tatsächlichen Mac-Architektur passende offizielle **llama.cpp**-Paket, höchstens **150 MB**. Die genaue Größe wird vor dem Download angezeigt.

Es sind also zwei automatische Dateien im Hintergrund; du wählst sie nicht selbst aus. Die Dateien landen nur im entpackten Projektordner. Für Download und Entpacken sollten mindestens **1,5 GB Speicher frei** sein. Das Modell und sein Arbeitsspeicher sind zusätzliche Daten; völlig ohne Modelldownload kann keine neue Offline-KI bereitgestellt werden. Das kleine Modell ist deutlich schwächer als ChatGPT.

## Voraussetzungen und Sicherheit

Du brauchst den Mac mit **macOS 14 oder neuer**, eine unterstützte ARM64- oder Intel-Architektur, **Python 3.10 oder neuer** sowie für die einmalige Einrichtung Internet. Python wird nicht automatisch installiert. Die tatsächliche Kompatibilität des offiziellen Startpakets wird spätestens beim lokalen Start geprüft; eine Architekturauswahl allein garantiert noch keinen funktionierenden Modellbetrieb.

Downloads verwenden macOS-curl mit aktivierter HTTPS-Prüfung, um nicht vom zuvor gemeldeten Python-Zertifikatsspeicher abhängig zu sein. Es werden SHA256-Prüfsummen aus den offiziellen Release-/Modell-Metadaten geprüft. Wenn die Prüfsumme fehlt oder nicht stimmt, wird nichts ausgeführt. Modellrevision und Downloadgrößen sind fest an diese Metadaten gebunden. Es gibt keine automatische Wahl eines größeren Modells, keine Ausführung von Installationsskripten aus dem Internet, keine Änderungen an Systemeinstellungen, kein sudo und kein Umgehen von macOS-Sicherheitsmeldungen. Nur die ausdrücklich heruntergeladenen, geprüften lokalen Programmdateien erhalten die für ihren Start nötigen Dateirechte.

Vorhandene fremde Prozesse werden nicht beendet. Wenn ein Port belegt ist, schließe deine alte Sitzung in ihrem Terminal. Bei einer Sicherheitsmeldung nutze die regulären macOS-Freigaben für eine vertrauenswürdige Quelle; der Helfer entfernt keine Sicherheitsmarkierungen.

## Stimme ändern

In JARVIS: **Einstellungen → Lokale Sprachausgabe → Deutsche Systemstimme → Systemstimme verwenden → Lokale Stimme testen**. Die Liste zeigt nur tatsächlich vom Browser gemeldete deutsche lokale Stimmen.

## Wenn die Einrichtung stoppt

Lass die genaue Meldung im Terminal stehen und teile sie ohne Schlüssel. Ein abgebrochener Download wird nicht als gültig behandelt. Bereits vollständig geprüfte Downloads werden bei einem erneuten Einrichten wiederverwendet. Sobald die gesamte Installation gültig ist, braucht auch ein erneutes Einrichten keinen weiteren Download.

**Prüfstand:** Der Einrichtungsablauf wurde in der Linux-Cloud mit kontrollierten Download-Daten, Archiven, Prozessen und HTTP-Antworten geprüft. Echte Modell-/Binärdownloads und die Ausführung auf deinem Mac sind dort nicht verifiziert. Die offiziellen Metadaten-APIs waren aus der Cloud nicht erreichbar; falls die Quelle auf deinem Mac keine Prüfsumme oder kein passendes Paket bereitstellt, stoppt der Helfer mit einer Erklärung.

Der Helfer unterstützt auch offizielle stabile Veröffentlichungen, die statt Binärpaketen nur eine Datei `nightly-tag.txt` enthalten: Er prüft deren SHA256 und verwendet exakt den darin genannten offiziellen Build. Die Datei-, Architektur- und Prüfsummenkontrollen der eigentlichen Downloads bleiben aktiv.
