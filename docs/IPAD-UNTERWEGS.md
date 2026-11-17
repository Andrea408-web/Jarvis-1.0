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
- **Kontakte und Nachrichtenentwürfe:** Namen, Telefonnummern und Mailadressen speichern; Entwürfe schreiben, kopieren und wieder öffnen. Telefon-/SMS-/Mail-Links öffnen ausschließlich den Editor bzw. die Telefonfunktion des Geräts. Verfügbarkeit hängt von den dort eingerichteten Apps und Konten ab. Anruf-App und alternative Mail-/SMS-Links werden selbst bestätigt. Der direkte Versand über Jarvis benötigt die unten beschriebene Versandbestätigung. Kontaktdaten werden dafür nicht an eine KI geschickt. Jarvis kann den Nutzer aus dieser Web-App noch nicht eigenständig anrufen.
- **Termine:** Datum, Uhrzeit, Dauer und Notiz lokal speichern. Als ICS-Datei exportieren und ausdrücklich in die eigene Kalender-App übernehmen. Termine verwenden die Geräte-Ortszeit. Die Kalender-App verwaltet spätere Erinnerungen, die Web-App ruft nicht im Hintergrund an.
- **Sicherungen:** Unter Ablage → Speicher & Sicherung eine JSON-Datei exportieren. Beim Import ergänzt Jarvis Einträge, statt bestehende abweichende Versionen zu überschreiben. Auch Kontakte und zugehörige Entwürfe bleiben bei Versionskonflikten richtig zugeordnet. „Private Sicherung“ unter Gerät enthält jetzt zusätzlich die Ablage. Ältere Sicherungen ohne Ablage bleiben lesbar. Ein Vollimport ersetzt wie bisher Notizen, Aufgaben, Marken und Skizze; die enthaltene Ablage wird ergänzt. Browser und Betriebssystem können lokale Webdaten entfernen; wichtige Daten als Datei sichern.

Die Offline-KI bleibt unverändert: vorhandenes kleines GGUF plus ungefähr 30 MB Laufzeit, keine Cloud-Inferenz. Die neuen Werkzeuge brauchen keinen weiteren Modelldownload. Thorsten braucht weiterhin den Mac. 3D-Kameratracking braucht die schon vorhandene Mac-Anbindung; die neue Optik ersetzt kein Tracking-Modell.

`python tests/browser/hud_and_desk.py` prüft echte Projektzähler, Textimport und automatisches Speichern, Kontakte und Entwürfe ohne Versand, ICS-Export, Sicherungskonflikte und einen Neustart ohne Netz. Screenshots aus der echten Anwendung: `artifacts/aeris-kontrollzentrum.png`, `artifacts/ipad-astra.png`, `artifacts/ipad-ablage.png`, `artifacts/handy-jarvis-hud.png`. Keine physische iPad-/iPhone-Prüfung in der Cloud.


## Business & Prompts

Im **Markenstudio → Business & Prompts** die aktive Marke übernehmen oder Name, Idee, Zielgruppe, Ziel und Testbudget eingeben. „Angebot & Testplan erstellen“ erzeugt einen bearbeitbaren Vorlagenentwurf, drei mögliche Testformen und einen konkreten 7-Tage-Plan. Es wird nichts veröffentlicht und kein Kunde automatisch kontaktiert.

Der Preis-/Kostenrechner verwendet ausschließlich deine Zahlen: Preis minus variable Stückkosten ergibt den Beitrag je Verkauf; Fixkosten geteilt durch positiven Stückbeitrag ergibt die aufgerundete Verkaufszahl zur Kostendeckung. Beträge werden in ganzen Cent berechnet. Das Monatsergebnis ist Stückbeitrag mal angenommene Verkäufe minus Fixkosten, vor weiteren Kosten und Steuern. Diese Rechnung prognostiziert keine Nachfrage.

In der **Promptwerkstatt** Positionierung, Angebot, Inhalte, Kundeninterview, Website, Ideenprüfung oder eine eigene Aufgabe wählen. Ein kurzer Prompt wird aus dem Briefing und Zusatzwunsch zusammengestellt; er ist bearbeitbar und kopierbar. „Jetzt lokale KI fragen“ übergibt ausdrücklich eine Anfrage an die vorhandene Geräte-KI oder lokale Mac-KI. KI-Prompts dürfen hier höchstens 1.400 Zeichen haben. Auch **„Gib mir einen Prompt für …“** im Geräte-Dialog öffnet die Promptwerkstatt mit einem passenden Entwurf. Längere aktuelle Fragen werden nicht mehr wie zuvor nach 700 Zeichen abgeschnitten.

Business-Eingaben, Rechnungsannahmen und bearbeitete Entwürfe werden auf diesem Gerät gespeichert und funktionieren ohne Mac. Ein Business-Entwurf kann separat als JSON-Datei gesichert/importiert werden. Die private Gerätesicherung enthält den Business-Bereich zusätzlich. Ein ausgewählter Business-Import ersetzt den aktuellen Business-Entwurf; ältere Gesamtsicherungen ohne Business-Daten lassen ihn bestehen. Für die neuen Vorlagen, Berechnungen und Prompts ist kein weiterer Modelldownload nötig. Individuelle KI-Ausarbeitungen benötigen weiterhin eine eingerichtete lokale KI.

Anrufe/Mail/SMS: Unter Ablage gespeicherte Kontakte lassen sich auswählen, native Telefon-/Mail-/SMS-Entwürfe öffnen und selbst bestätigen. **Kontaktbefehle öffnen die Auswahl oder bei eindeutigem Namen plus Nachrichtentext die Versandbestätigung.** Ohne diese Bestätigung wird nichts versendet; Jarvis ruft den Nutzer nicht eigenständig an.

`python tests/browser/business_lab.py` prüft Markenübernahme, Vorlagen, centgenaue Kostendeckung, Nullmarge, Prompt-Übergabe an einen ausdrücklich simulierten lokalen Testtransport, Datei-/Gesamtsicherung und Offline-Neustart. Bilder aus dem echten UI: `artifacts/business-angebot.png`, `artifacts/business-zahlen-prompts.png`, `artifacts/business-handy.png`.


## MacBook-Ansicht und mobile Ansichten

„MacBook-Modus“ unter Gerät bzw. oben in der iPad-Ansicht öffnet wieder das ursprüngliche Kontrollzentrum unter `/index.html` mit Jarvis/Astra. Die Handy-/iPad-Arbeitsräume bleiben unter `/tablet`; ihre bisherigen Werkzeuge bleiben erhalten. Aeris hat einen gelben Energiekern mit geschwungenen Lichtbändern im Astra-Stil.


## Kontaktmenü und Sprachnachrichten

„Ruf … an“, „Schreib eine E-Mail an …“ und „Schick eine SMS an …“ öffnen nun eine Kontaktliste. Das funktioniert im klassischen Mac-Dialog und in den mobilen Geräte-Ansichten. Es wird ausschließlich in den **in Jarvis gespeicherten Kontakten** gesucht, nicht ungefragt im iPhone-Adressbuch. Der erkannte Satz wird angezeigt; die Suche beginnt leer, damit ein falsch verstandener Name die richtige Person nicht ausblendet. Erst selbst einen Kontakt wählen und Adresse/Text prüfen. Der anschließende Telefon-/SMS-/Mail-Link öffnet die Geräte-App; es gibt weiterhin keinen automatischen Versand.

Unter Ablage → Kontakte & Entwürfe kann eine Sprachnachricht vorbereitet werden: **Jarvis / Thorsten** erzeugt aus dem eingegebenen Text eine WAV-Datei auf dem verbundenen Mac. **Meine eigene Stimme aufnehmen** nimmt mit Mikrofonfreigabe auf dem aktuellen Gerät auf (maximal zwei Minuten pro Aufnahme). Die Vorschau kann angehört und ausdrücklich als Audiodatei gespeichert bzw. über das Geräte-Teilen-Menü geteilt werden. Bei Verlassen des Bereichs oder Ausblenden der Seite wird eine Aufnahme gestoppt. Audio bleibt bis dahin im Arbeitsspeicher und wird nicht automatisch in der Ablage gespeichert.

Das ist kein KI-Telefonat. Browser-Audio kann hier nicht in ein normales iPhone-/Mac-Telefonat eingespeist werden; die Gegenstelle wird nicht automatisch gehört oder beantwortet. Für ein solches echtes, gegenseitiges Gespräch fehlt weiterhin eine Telefonie-Anbindung. Die Auswahl „eigene Stimme“ ist eine Aufnahme, keine Stimmenkopie.

Aether/Äther werden beim Wechsel als Namen des Aeris-Modus verstanden. Sein gelber Orbitalkern unterscheidet sich vom blauen Astra-Kern. Der MacBook-Modus öffnet das ursprüngliche Kontrollzentrum.


## Apple Kontakte vorübergehend verwenden

Im Kontakt-Auswahlfenster **Aus Apple Kontakte wählen – ohne Import** öffnen. Dann:

1. **Apple Kontakte öffnen**. Am verbundenen Mac in der Apple-App genau eine Person auswählen.
2. Zurück in Jarvis **Apple-Auswahl verwenden**. macOS kann beim ersten Zugriff eine Freigabe verlangen. Falls verweigert: Systemeinstellungen → Datenschutz & Sicherheit → Automation → Zugriff des verwendeten Jarvis-Terminals auf Kontakte erlauben.
3. Bei mehreren Nummern/Adressen die gewünschte auswählen. Danach wie bisher Telefon-, Mail- oder SMS-App ausdrücklich öffnen.

Es wird keine komplette Apple-Kontaktliste importiert. Die ausgewählte Person wird auf dem Mac durch ein festes lokales Apple-Events-Skript gelesen und über den bestehenden geschützten Jarvis-Zugang übertragen. Der Server verarbeitet sie nur im Arbeitsspeicher; keine Datenbank-, Protokoll- oder Dateispeicherung und kein KI-Aufruf durch diese Funktion. Im Browser liegen die Daten ausschließlich im vorübergehenden Zustand des Kontaktfensters, nicht in IndexedDB, localStorage, Entwürfen oder Sicherungen. Die manuellen Kontaktfelder werden nicht befüllt, und „Entwurf speichern“ ist für die temporäre Auswahl gesperrt. **Temporären Kontakt entfernen**, Neuladen oder Verlassen der Seite entfernt sie aus dieser Ansicht. Bestehende, früher selbst gespeicherte Jarvis-Kontakte bleiben unverändert.

Die Funktion meldet dich nicht bei Apple an und ändert keine Apple-/iCloud-Einstellungen. Auf iPhone/iPad nutzt diese Lösung den verbundenen Mac; die Web-App hat dafür keinen direkten Zugriff auf das iPhone-Adressbuch. Ohne Mac steht diese Apple-Auswahl nicht bereit. Es gibt weiterhin keine selbstständigen KI-Telefonate.

Prüfung: `python -m unittest tests.test_apple_contacts` prüft Plattformgrenzen und das feste Skript. `python tests/browser/apple_contacts.py` prüft die reale lokale API und Browser-Ansicht mit einer simulierten macOS-Auswahl: ausdrückliche Nummernwahl, kein Kontakt in lokalen Ablagen/Sicherungen/Serverdateien und keine Modell-Anfragen. Die echte Apple-Kontakte-App konnte auf dem Linux-Cloudrechner nicht ausgeführt werden. Screenshot mit Beispielperson: `artifacts/apple-kontakte-voruebergehend.png`.


## Kontakte direkt im Mac-Modus

Kontaktbefehle im ursprünglichen Mac-Kontrollzentrum öffnen jetzt ein eigenes Kontaktfenster über der bestehenden Seite. Es gibt keinen Wechsel zum Tablet-Arbeitsraum. Schließen bringt dich sofort zur unveränderten Mac-Ansicht zurück; das eingebettete Kontaktfenster wird dabei entladen, einschließlich seiner vorübergehenden Apple-Auswahl. Nur die spezielle Kontaktfenster-Seite darf vom eigenen Jarvis-Ursprung eingebettet werden; andere Seiten behalten den bisherigen Schutz gegen Einbettung. Handy-/iPad-Arbeitsräume behalten ihre direkte Kontaktauswahl.


## Nachrichten nach einmaliger Bestätigung selbst verschicken

Im Kontaktbereich **E-Mail mit Jarvis senden …** bzw. **Nachricht mit Jarvis senden …** verwenden. Jarvis zeigt Empfängername, die konkrete Adresse/Nummer, Kanal, Betreff und vollständigen Text in einem Bestätigungsfenster. Erst **Jetzt senden** übergibt genau diese Vorlage an Apple Mail bzw. Apple Nachrichten auf dem verbundenen Mac. Die nativen Apps müssen eingerichtet sein; beim ersten Mal muss macOS gegebenenfalls den Zugriff des Jarvis-Terminals unter Datenschutz & Sicherheit → Automation erlauben.

Beispiel: **„Schreibe eine E-Mail an Lea mit dem Text: Hallo Lea, morgen passt es.“** Hat genau ein gespeicherter Kontakt den vollständigen Namen „Lea“, öffnet sich direkt die Versandbestätigung. Bei keinem eindeutigen Treffer wird zuerst die Kontaktliste gezeigt. Ein ausgewählter Kontakt plus erkannter Text führt danach ebenfalls zur Bestätigung. „Empfänger ändern“ geht zurück zur Auswahl. Ohne erkannten Nachrichtentext den Text im Kontaktfenster schreiben oder diktieren und den Versandknopf wählen. Kurze Namensfragmente und ähnlich klingende Namen werden nicht still automatisch zugeordnet.

Die Bestätigung ist zwei Minuten gültig, gehört zur anfragenden Sitzung und kann nur einmal einen Versand starten. Doppelte Bestätigungen liefern nur den bisherigen Status zurück. Es gibt keine automatischen Neuversuche. Nach Zeitüberschreitung oder unklarer App-Antwort steht ausdrücklich „Versandstatus unklar“; dann zuerst in der nativen App nachsehen. Nach Annahme heißt es **„Mac-App hat den Versandauftrag angenommen“**, nicht „beim Empfänger zugestellt“.

E-Mail wird über das in Apple Mail eingerichtete Konto übergeben. Apple Nachrichten wählt einen verfügbaren SMS-/iMessage-Dienst; SMS benötigt gegebenenfalls die eingerichtete iPhone-Weiterleitung. Nicht verfügbare Konten, Dienste und macOS-Freigaben werden als Fehler gemeldet. Es erfolgt kein Versand über OpenAI oder einen zusätzlichen KI-Dienst. Die Funktionen versenden nur Text, keine Audiodatei-Anhänge. Telefonate bleiben der nativen Geräte-App überlassen.

Offene Versandvorlagen liegen nur im Arbeitsspeicher des lokalen Mac-Servers und werden nach Abbrechen, Übernahme oder Ablauf aus der Warteschlange entfernt. Die Ablaufbereinigung läuft auch ohne weitere Anfragen. Kurzzeitige Statusbelege enthalten keine Adresse und keinen Nachrichtentext. Kontaktbefehle werden im Geräte-Chat nicht dauerhaft als Verlauf gespeichert. Früher selbst gespeicherte Kontakte/Entwürfe werden dadurch nicht gelöscht. **Mail/Nachrichten können versendete Nachrichten entsprechend ihren Kontoeinstellungen im Verlauf/Gesendet speichern** – das gehört zur tatsächlichen Kommunikation, nicht zu einer Jarvis-Kontaktsicherung.

`tests/test_confirmed_send.py` prüft unveränderliche Vorlagen, Sitzung, Ablauf, Abbrechen, gleichzeitige Bestätigungen, Wiederholungsschutz und ehrliche Fehlerzustände. `tests/browser/confirmed_send.py` prüft den echten UI-/API-Ablauf mit einem reinen Testsender, ohne echte Mail oder SMS. Der native macOS-Versand kann auf dem Linux-Cloudrechner nicht ausgeführt werden; Apple-Mail-/Nachrichten-Freigaben und die echte Zustellung müssen am Mac geprüft werden. Bild mit Beispielkontakt: `artifacts/versand-bestaetigen.png`.
