# iPad-Modus, Markenstudio und Jarvis ohne Mac

Nach dem kleinen Programmupdate Jarvis im Terminal beenden (Control+C) und im vorhandenen Jarvis-Ordner mit `python3 -m backend --easy-local` neu starten. Die vorhandene Text-KI, Thorsten und persönlichen Daten werden nicht ersetzt.

## Öffnen und bedienen

Im Kontrollzentrum „iPad / Unterwegs“ wählen. Derselbe Arbeitsraum ist unter `/tablet` erreichbar; `/brands` öffnet direkt das Markenstudio. Oben „iPad-Modus“ wählen oder unter **Gerät** zwischen Normal, iPad und Handy wechseln. Jarvis, Astra und Aeris haben getrennte Geräte-Chats. Der Arbeitsraum ergänzt das vorhandene Mac-Kontrollzentrum.

- **Notizen:** lokal speichern oder im Dialog „Erstelle eine Notiz“ sagen/schreiben und die Rückfrage mit dem Inhalt beantworten.
- **Planer:** Aufgaben mit Datum, Erledigt-Markierung und Fokuszeit. Keine Hintergrund-Erinnerungen versprochen, wenn iOS die App beendet.
- **Skizze:** Finger, Maus oder Apple Pencil; Druckstärke, wenn der Browser sie liefert. „Nur Stift“ ignoriert Fingerkontakte. Rückgängig, Wiederholen und PNG-Export.
- **Marken:** Name, Claim, Angebot, Zielgruppe, Stil, Ziel, Website und Farben. Auch „Meine Marke heißt …“ im Geräte-Dialog legt ein Profil an. SVG-Monogramm als Logoidee, PNG-Markenkarte, kopierbares Briefing und bearbeitbarer 7-Tage-Inhaltsplan. Der Plan ist eine Vorlage; KI-Überarbeitung wird ausdrücklich angefragt. Nichts wird automatisch veröffentlicht.
- **Sicherung:** Unter Gerät die privaten Daten als JSON exportieren. Der Import ersetzt Notizen, Aufgaben, Marken und Skizze auf diesem Gerät; Chats, Inhaltsplanentwürfe und KI-Modell werden dabei nicht wiederhergestellt. Einzelne Marken können separat exportiert/importiert werden.

Alle Werkzeuge und Markenprofile bleiben auf dem verwendeten Gerät. Sie sind in allen drei Assistenten und auf Mac, iPad und Handy nutzbar. Es gibt keine heimliche Cloud-Synchronisierung. Ein Markenprofil kann ausdrücklich auf dem verbundenen Mac gespeichert und am anderen gekoppelten Gerät geladen werden. Bei Versionskonflikten wird nicht still überschrieben.

## Einmal für unterwegs vorbereiten

1. Auf dem Mac wie bisher **Handy verbinden** öffnen und das Gerät im selben WLAN koppeln. Das lokale HTTPS-Zertifikat muss als vertrauenswürdig eingerichtet sein; keine Zertifikatsprüfung wird ausgeschaltet.
2. In Safari **Teilen → Zum Home-Bildschirm → Hinzufügen**. Die App über das neue Symbol öffnen. Bei Bedarf dort erneut koppeln, weil Safari und die installierte Web-App getrennte Speicher haben können.
3. Unter **Gerät** warten, bis „Offline-Oberfläche bereit“ erscheint. Notizen, Planung, Marken, Skizze und die vorhandene 3D-Werkstatt funktionieren dann ohne Mac und Internet.
4. Für freie KI-Antworten zusätzlich **Größe am Mac prüfen → Geräte-KI einrichten**. Die bereits eingerichtete kleine GGUF-Text-KI wird vom Mac kopiert: ungefähr 400 MB, höchstens 450 MB. Hinzu kommen etwa **30 MB** Browser-Laufzeit. Der Mac lädt dafür einmal zwei offizielle, fest versionierte npm-Pakete; kein neues Sprachmodell wird aus dem Internet geladen. Der Gerätebrowser lädt nichts von einem KI-Anbieter.
5. Seite bis zum erfolgreichen Start offen lassen. Dann WLAN abschalten bzw. Mac beenden und eine Frage testen. Später lädt Jarvis das gespeicherte Modell bei der ersten Frage erneut in den Arbeitsspeicher. „Gespeicherte KI starten“ startet es auch ausdrücklich.

Es läuft echte Textinferenz per WebAssembly im Browser, kein iOS-Hintergrundserver. Es werden keine API-Schlüssel und kein Anbieter-Guthaben gebraucht. Dateigröße und SHA-256 jedes Modellblocks werden vor dem Speichern geprüft. Laufzeitarchive werden zusätzlich gegen fest hinterlegte SHA-512-Werte geprüft. Die Laufzeit umfasst einen Safari-Kompatibilitätsbuild. Nur das bereits konfigurierte Modell kann übertragen werden; kein frei wählbarer Server-Dateipfad und keine externe Downloadadresse.

**Grenzen:** Nicht jedes iPhone/iPad hat genug Arbeitsspeicher oder die nötigen Browserfunktionen. Die kleine KI wird durch diese Änderung nicht intelligenter; sie hat offline keine aktuellen Nachrichten und kann keine Mac-Apps steuern. Thorsten bleibt die gewünschte Stimme, benötigt in diesem Arbeitsraum aber weiterhin den Mac. Offline gibt es Textantworten, keinen stillen Wechsel zur Systemstimme. iOS kann gespeicherte Webdaten bei Platzmangel entfernen. Regelmäßig Sicherungen exportieren. Bei Modellproblemen bleiben die anderen Werkzeuge nutzbar; „Nur Geräte-KI entfernen“ löscht keine Notizen oder Marken.

## Prüfung und Bilder

`python -m unittest discover -s tests` prüft unter anderem Integrität, Speichergrenzen, geschützte APIs und Konflikte bei Markenübertragung. `python tests/browser/device_workspace.py` prüft im echten Chromium Notiz-Rückfragen, Zeichnen, Exporte, Markenspeicherung und Offline-Neuladen. Mit `--runtime` werden die beiden bereits separat geladenen, fest geprüften npm-Archive aus `/tmp` verwendet: Ein winziges synthetisches GGUF testet echte WASM-Inferenz und den Safari-Kompatibilitätsbuild ohne Netz. Das prüft den Ausführungspfad, nicht Antwortqualität oder ein physisches iPad. Keine Aussage, dass alle alten iOS-Geräte unterstützt werden.

Echte Screenshots mit der ausdrücklich erfundenen Beispielmarke LUMEN STUDIO liegen in `artifacts/markenstudio-normal.png`, `artifacts/ipad-skizze.png` und `artifacts/handy-unterwegs.png`. Bilder nach künftigen UI-Änderungen ebenfalls aus der tatsächlich laufenden Anwendung erstellen.
