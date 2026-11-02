# Kleine lokale KI ohne Ollama und ohne API-Schlüssel

Diese Variante verwendet **llama.cpp** und **Qwen2.5-0.5B-Instruct Q4_K_M**. Das kleine Modell liegt ungefähr im Bereich von 350–450 MB; die genaue Größe zeigt die Downloadseite. Zusätzlich ist ein passendes llama.cpp-Startprogramm nötig. Es wird weder Ollama noch ein kostenpflichtiger API-Zugang benötigt. Nach dem einmaligen Download funktionieren Textgespräche offline.

Ein Modell dieser Größe ist deutlich schwächer als ChatGPT. Es ist für einfache kurze Gespräche geeignet, nicht für verlässliche komplexe Aufgaben. Die Laufzeit auf deinem tatsächlichen Mac wurde hier nicht geprüft. Die Cloud-Tests verwenden kontrollierte Antworten.

## 1. Passendes Startprogramm herunterladen

Öffne die offiziellen Releases: https://github.com/ggml-org/llama.cpp/releases/latest

Wähle das fertige **macOS-Paket** passend zu deinem Mac. Unter ** → Über diesen Mac** siehst du den Chip; alternativ `uname -m` im Mac-Terminal:

- Apple-Chip / `arm64`: macOS ARM64-Paket.
- Intel / `x86_64`: macOS x64-Paket, sofern die aktuelle Version es unterstützt.

Keine Linux-/Windows-Version und kein großes Quellcodearchiv wählen. Benötigt wird die Datei **llama-server** mit den dazugehörigen Bibliotheken aus demselben Paket. Entpacke deren Verzeichnis in den JARVIS-Projektordner und nenne es **runtime**. Dort muss anschließend `runtime/llama-server` liegen. Mitgelieferte Bibliotheken und deren relative Verzeichnisstruktur beibehalten. Falls du llama-server bereits installiert hast und im Terminal aufrufen kannst, erkennt der Starter das ebenfalls.

Verwende nur das offizielle Paket; falls die Release-Seite Prüfsummen bereitstellt, mit ihnen prüfen. macOS-Sicherheitsabfragen nicht umgehen. Ein Berechtigungs- oder Architekturfehler wird vom Starter gemeldet; JARVIS ändert keine Berechtigungen der heruntergeladenen Programme.

## 2. Nur das kleine Modell herunterladen

Offizielles Qwen-Modellverzeichnis:
https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/tree/main

Wähle genau:

`qwen2.5-0.5b-instruct-q4_k_m.gguf`

Nicht das 1.5B-Modell und keine größere Quantisierung laden. Die Webseite zeigt die aktuelle Dateigröße. Die Erreichbarkeit und genaue Größe dieses Downloads konnten aus der Cloud nicht bestätigt werden; JARVIS startet keinen Hintergrunddownload.

Lege diese Datei entweder in deinen Mac-Ordner **Downloads** oder erstelle im JARVIS-Projektordner einen Unterordner **models** und lege sie dort hinein. Der Starter akzeptiert für diese kleine Variante höchstens 500 MiB und prüft das GGUF-Dateiformat. Die Formatprüfung ersetzt keinen Herkunfts- oder Prüfsummencheck. Die SHA256-Prüfsumme kannst du mit `shasum -a 256 DATEIPFAD` berechnen und mit der im offiziellen Dateieintrag angegebenen LFS-SHA256 vergleichen.

## 3. Kleine KI starten

Öffne im Projektordner **Kleine-KI-starten.command**. Alternativ dort im Terminal:

```bash
python3 -m backend --start-small-ai
```

Das Terminal bleibt geöffnet, während die KI läuft. Der Starter führt nur vorhandene lokale Dateien aus, bindet ausschließlich `127.0.0.1:8081` und lädt nichts aus dem Internet. Fehlende Dateien werden verständlich benannt. Für llama.cpp und das Modell muss einmalig Speicherplatz vorhanden sein; die genaue RAM-Nutzung hängt von Gerät und Version ab.

## 4. JARVIS starten

Öffne ein zweites Terminal im JARVIS-Projektordner:

```bash
python3 -m backend --open-browser
```

Dann **Einstellungen → Kleine lokale KI → Kleine KI verwenden → Kleine KI prüfen**.

Die Auswahl schaltet Cloud-KI und ElevenLabs aus und aktiviert die lokale Systemstimme. Die Stimme wählst du weiterhin unter **Lokale Sprachausgabe**. Textgespräche gehen nur an den lokalen llama.cpp-Prozess. Es gibt keinen automatischen Wechsel zu Google, OpenAI oder Ollama, keine API-Schlüssel, keine Bildanalyse und keine KI-Werkzeugausführung. Direkte lokale Befehle wie Rechner öffnen bleiben nach Bestätigung verfügbar.

Zum Beenden in beiden Terminals **Control + C** drücken. Wenn die Prüfung nicht bereit meldet, zuerst die Meldung im KI-Terminal lesen. Eine gewählte Einstellung oder ein gestarteter Prozess allein bestätigt noch keine erfolgreiche Modellantwort.
