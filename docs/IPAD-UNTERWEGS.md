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


## Neues HUD und zusätzliche Offline-Ablage (17. November 2026)

Aeris hat jetzt einen eigenen gelben geometrischen Energiekern mit Projektname, tatsächlicher Bauteilanzahl und gespeicherten Projekten. Die mobile Oberfläche folgt dem dunklen HUD-Stil von Jarvis/Astra. Die bisherige Hauptansicht am Mac bleibt erhalten. Auch „Iris“ wird beim Wechsel als Aeris verstanden. Bei einem Wechsel aus der 3D-Werkstatt ohne erreichbaren Mac öffnet sich der entsprechende Assistent im Geräte-Arbeitsraum.

Unter **Ablage** funktionieren ohne Mac und ohne zusätzlichen Modelldownload:

- **Textablage:** mehrere TXT-/MD-Dateien importieren, durchsuchen, bearbeiten und als TXT speichern. Änderungen an bestehenden Dokumenten werden automatisch lokal gespeichert. Neue Dokumente ausdrücklich speichern. Es werden Kopien importiert; die Originaldateien bleiben erhalten. Maximal 100 Dokumente mit je 200.000 Zeichen, zusammen fünf Millionen Zeichen. „Mit KI überarbeiten“ öffnet eine gesonderte Chat-Anfrage mit höchstens den ersten 1.200 Zeichen. Dafür braucht es weiterhin die eingerichtete Geräte-KI oder die vorhandene Mac-KI.
- **Kontakte und Nachrichtenentwürfe:** Namen, Telefonnummern und Mailadressen speichern; Entwürfe schreiben, kopieren und wieder öffnen. Telefon-/SMS-/Mail-Links öffnen ausschließlich den Editor bzw. die Telefonfunktion des Geräts. Verfügbarkeit hängt von den dort eingerichteten Apps und Konten ab. Der Nutzer bestätigt Anruf und Versand selbst. Kein Versand erfolgt im Hintergrund, kein Kontakt wird an einen Anbieter geschickt. Jarvis kann den Nutzer aus dieser Web-App noch nicht eigenständig anrufen.
- **Termine:** Datum, Uhrzeit, Dauer und Notiz lokal speichern. Als ICS-Datei exportieren und ausdrücklich in die eigene Kalender-App übernehmen. Termine verwenden die Geräte-Ortszeit. Die Kalender-App verwaltet spätere Erinnerungen, die Web-App ruft nicht im Hintergrund an.
- **Sicherungen:** Unter Ablage → Speicher & Sicherung eine JSON-Datei exportieren. Beim Import ergänzt Jarvis Einträge, statt bestehende abweichende Versionen zu überschreiben. Auch Kontakte und zugehörige Entwürfe bleiben bei Versionskonflikten richtig zugeordnet. „Private Sicherung“ unter Gerät enthält jetzt zusätzlich die Ablage. Ältere Sicherungen ohne Ablage bleiben lesbar. Ein Vollimport ersetzt wie bisher Notizen, Aufgaben, Marken und Skizze; die enthaltene Ablage wird ergänzt. Browser und Betriebssystem können lokale Webdaten entfernen; wichtige Daten als Datei sichern.

Die Offline-KI bleibt unverändert: vorhandenes kleines GGUF plus ungefähr 30 MB Laufzeit, keine Cloud-Inferenz. Die neuen Werkzeuge brauchen keinen weiteren Modelldownload. Thorsten braucht weiterhin den Mac. 3D-Kameratracking braucht die schon vorhandene Mac-Anbindung; die neue Optik ersetzt kein Tracking-Modell.

`python tests/browser/hud_and_desk.py` prüft echte Projektzähler, Textimport und automatisches Speichern, Kontakte und Entwürfe ohne Versand, ICS-Export, Sicherungskonflikte und einen Neustart ohne Netz. Screenshots aus der echten Anwendung: `artifacts/aeris-kontrollzentrum.png`, `artifacts/ipad-astra.png`, `artifacts/ipad-ablage.png`, `artifacts/handy-jarvis-hud.png`. Keine physische iPad-/iPhone-Prüfung in der Cloud.


## Business & Prompts

Im **Markenstudio → Business & Prompts** die aktive Marke übernehmen oder Name, Idee, Zielgruppe, Ziel und Testbudget eingeben. „Angebot & Testplan erstellen“ erzeugt einen bearbeitbaren Vorlagenentwurf, drei mögliche Testformen und einen konkreten 7-Tage-Plan. Es wird nichts veröffentlicht und kein Kunde automatisch kontaktiert.

Der Preis-/Kostenrechner verwendet ausschließlich deine Zahlen: Preis minus variable Stückkosten ergibt den Beitrag je Verkauf; Fixkosten geteilt durch positiven Stückbeitrag ergibt die aufgerundete Verkaufszahl zur Kostendeckung. Beträge werden in ganzen Cent berechnet. Das Monatsergebnis ist Stückbeitrag mal angenommene Verkäufe minus Fixkosten, vor weiteren Kosten und Steuern. Diese Rechnung prognostiziert keine Nachfrage.

In der **Promptwerkstatt** Positionierung, Angebot, Inhalte, Kundeninterview, Website, Ideenprüfung oder eine eigene Aufgabe wählen. Ein kurzer Prompt wird aus dem Briefing und Zusatzwunsch zusammengestellt; er ist bearbeitbar und kopierbar. „Jetzt lokale KI fragen“ übergibt ausdrücklich eine Anfrage an die vorhandene Geräte-KI oder lokale Mac-KI. KI-Prompts dürfen hier höchstens 1.400 Zeichen haben. Auch **„Gib mir einen Prompt für …“** im Geräte-Dialog öffnet die Promptwerkstatt mit einem passenden Entwurf. Längere aktuelle Fragen werden nicht mehr wie zuvor nach 700 Zeichen abgeschnitten.

Business-Eingaben, Rechnungsannahmen und bearbeitete Entwürfe werden auf diesem Gerät gespeichert und funktionieren ohne Mac. Ein Business-Entwurf kann separat als JSON-Datei gesichert/importiert werden. Die private Gerätesicherung enthält den Business-Bereich zusätzlich. Ein ausgewählter Business-Import ersetzt den aktuellen Business-Entwurf; ältere Gesamtsicherungen ohne Business-Daten lassen ihn bestehen. Für die neuen Vorlagen, Berechnungen und Prompts ist kein weiterer Modelldownload nötig. Individuelle KI-Ausarbeitungen benötigen weiterhin eine eingerichtete lokale KI.

Anrufe/Mail/SMS: Unter Ablage gespeicherte Kontakte lassen sich auswählen, native Telefon-/Mail-/SMS-Entwürfe öffnen und selbst bestätigen. **Sprachbefehle wie „Schick eine Mail an Lea“ werden derzeit nicht automatisch anhand der Kontaktliste ausgeführt.** Es gibt keinen Hintergrundversand und Jarvis ruft den Nutzer nicht eigenständig an.

`python tests/browser/business_lab.py` prüft Markenübernahme, Vorlagen, centgenaue Kostendeckung, Nullmarge, Prompt-Übergabe an einen ausdrücklich simulierten lokalen Testtransport, Datei-/Gesamtsicherung und Offline-Neustart. Bilder aus dem echten UI: `artifacts/business-angebot.png`, `artifacts/business-zahlen-prompts.png`, `artifacts/business-handy.png`.
