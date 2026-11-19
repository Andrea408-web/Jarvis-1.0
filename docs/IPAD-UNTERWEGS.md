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

E-Mail wird über das in Apple Mail eingerichtete Konto übergeben. Apple Nachrichten wählt einen verfügbaren SMS-/iMessage-Dienst; SMS benötigt gegebenenfalls die eingerichtete iPhone-Weiterleitung. Nicht verfügbare Konten, Dienste und macOS-Freigaben werden als Fehler gemeldet. Es erfolgt kein Versand über OpenAI oder einen zusätzlichen KI-Dienst. Der SMS-/iMessage-Versand über Jarvis ist für Text ausgelegt. Audio kann über die unten beschriebene gesonderte Bestätigung per Apple Mail oder über das Geräte-Teilen-Menü weitergegeben werden. Telefonate bleiben der nativen Geräte-App überlassen.

Offene Versandvorlagen liegen nur im Arbeitsspeicher des lokalen Mac-Servers und werden nach Abbrechen, Übernahme oder Ablauf aus der Warteschlange entfernt. Die Ablaufbereinigung läuft auch ohne weitere Anfragen. Kurzzeitige Statusbelege enthalten keine Adresse und keinen Nachrichtentext. Kontaktbefehle werden im Geräte-Chat nicht dauerhaft als Verlauf gespeichert. Früher selbst gespeicherte Kontakte/Entwürfe werden dadurch nicht gelöscht. **Mail/Nachrichten können versendete Nachrichten entsprechend ihren Kontoeinstellungen im Verlauf/Gesendet speichern** – das gehört zur tatsächlichen Kommunikation, nicht zu einer Jarvis-Kontaktsicherung.

`tests/test_confirmed_send.py` prüft unveränderliche Vorlagen, Sitzung, Ablauf, Abbrechen, gleichzeitige Bestätigungen, Wiederholungsschutz und ehrliche Fehlerzustände. `tests/browser/confirmed_send.py` prüft den echten UI-/API-Ablauf mit einem reinen Testsender, ohne echte Mail oder SMS. Der native macOS-Versand kann auf dem Linux-Cloudrechner nicht ausgeführt werden; Apple-Mail-/Nachrichten-Freigaben und die echte Zustellung müssen am Mac geprüft werden. Bild mit Beispielkontakt: `artifacts/versand-bestaetigen.png`.


## Sprachnachricht aufnehmen und verschicken

Unter Ablage → Kontakte & Entwürfe eine **eigene Stimme aufnehmen** oder mit **Jarvis / Thorsten** aus dem Text eine Vorschau erstellen. Danach **Stoppen → Audio per E-Mail senden …**. Falls kein E-Mail-Empfänger gewählt ist, öffnet sich die Kontaktliste. Anschließend zeigt die Bestätigung den Empfänger, Dateinamen, Größe und einen Audioplayer zum Vorhören. Erst **Jetzt senden** übergibt die ausgewählte Aufnahme an Apple Mail auf dem verbundenen Mac. Es gibt keinen Versand vor der Bestätigung und keinen automatischen Neuversuch.

Die Browseraufnahme bleibt im Arbeitsspeicher und wird nicht als Stimme/Profil oder im Jarvis-Verlauf gespeichert. **Aufnahme verwerfen** entfernt sie. Nach Annahme durch Apple Mail wird auch die lokale Vorschau entfernt. Abbrechen vor der Bestätigung lässt die Vorschau noch zum Korrigieren bereit; beim Verlassen der Seite wird sie verworfen. Einzelaufnahmen dürfen maximal 4 MB groß sein (WAV, M4A, WebM oder Ogg). Der Bestätigungsserver hält nur die konkrete Aufnahme vorübergehend im RAM; die Audiodaten erscheinen nicht in Sicherungen oder KI-Anfragen.

Mit der ausdrücklich erlaubten Bestätigung wird am Mac genau eine private Arbeitsdatei angelegt (temporärer Ordner, Dateirechte nur für den Benutzer). Nach nativer Übergabe oder Fehler wird diese Arbeitskopie wieder gelöscht. **Apple Mail und der Empfänger können die versendete Audiodatei speichern**; es wird keine vollständige Löschung außerhalb von Jarvis versprochen. Bei einem unklaren Versandstatus zuerst in Apple Mail prüfen. Für die echte native Anhangsübergabe und die macOS-Freigabe ist ein Test auf dem Mac erforderlich; die Cloud-Prüfung verwendet einen Testsender.

**Ohne Mac am Handy/iPad:** eigene Aufnahme und ausdrückliches **Audio teilen** sind weiterhin möglich, sofern der Browser die Aufnahme unterstützt. Der direkte Versand über Apple Mail benötigt den Mac. Ein echtes KI-Telefonat über normale Telefonnummern – mit Zuhören, Antworten und Eingreifen – wurde hier nicht vorgetäuscht: Dafür fehlen weiterhin eine Telefonie-Anbindung und eine passende Sprachverarbeitung. Ohne zusätzliche Anbindung kann die Web-App den normalen Telefonanruf nicht übernehmen. Es wurde kein kostenpflichtiger Dienst eingerichtet und kein neues Stimmenmodell heruntergeladen.

Prüfung: `tests/test_audio_send.py` prüft Audioformat/Größe, unveränderte Vorschau und private temporäre Dateien samt Löschung bei Erfolg und Fehler. `tests/browser/audio_message_send.py` prüft den realen Aufnahme-/Vorschau-/Bestätigungsablauf mit einem Testsender ohne echte Nachrichten. Screenshot mit Beispielkontakt: `artifacts/sprachnachricht-senden.png`.


## Schnellhilfe auf Mac, iPhone, iPad und Aeris

Oben **✦ Schnellhilfe** öffnen. „Mein Tag“ zeigt die hier gespeicherten Aufgaben und heutige Einträge aus dem Geräteplaner und der Ablage desselben Browsers. „Text → Aufgaben“ zerlegt Zeilen bzw. „und dann“/„danach“ in bearbeitbare Punkte; erst ausdrücklich bestätigte Aufgaben werden lokal gespeichert. Abhaken und Entfernen sind direkt möglich. „Gesprächshilfe“ erstellt aus Ziel und Angaben einen Gesprächsleitfaden. „Guter Prompt“ baut einen kopierbaren Auftrag mit Rahmen und Qualitätsprüfung. Diese Hilfen arbeiten ohne Modell, Konto oder Netzwerk; sie behaupten keine echte KI-Analyse oder erledigte Telefonate. Gesprächs- und Prompt-Entwürfe werden beim Schließen verworfen. Aufgaben sind lokal in diesem Browser gespeichert, werden nicht geräteübergreifend synchronisiert und können unter „Aufgaben sichern“ separat exportiert werden.


### Fokus, Ideenvergleich und Aufgabensicherung

In der Schnellhilfe gibt es drei weitere Bereiche. **Fokus** speichert nach „Fokus starten“ Ziel und absoluten Endzeitpunkt lokal; Pausieren und Fortsetzen sind möglich. Die Anzeige wird beim Öffnen mit der aktuellen Uhrzeit abgeglichen. Bei geschlossener App oder im Ruhezustand ist kein Alarm garantiert. **Ideenvergleich** gewichtet die selbst vergebenen Bewertungen für Nutzen, leichte Umsetzung und Budgetpassung; das Ergebnis ist eine transparente Rechnung, keine Marktanalyse. Vergleichsentwürfe werden beim Schließen gelöscht. **Aufgaben sichern** exportiert nur Schnellhilfe-Aufgaben und importiert erst nach Vorschau und ausdrücklicher Bestätigung. Vorhandene Einträge bleiben erhalten, identische werden nicht verdoppelt, Konflikte werden als Kopie ergänzt. Fokusdaten, Kontakte, Audio und Gesprächsentwürfe sind nicht im Export enthalten.


### Sichtbare Werkzeugleiste und Sprachnachrichten-Befehl

Direkt unter der Überschrift liegt jetzt eine eigene grün-gelbe Werkzeugleiste: Mein Tag, Aufgaben, Fokus, Ideen, Prompts, Gespräch, Sichern und Sprachnachricht. Jeder Knopf öffnet unmittelbar den passenden Bereich. Handy und iPad haben eine eigene aufgeräumte Darstellung; am iPad stehen Energiekern und Dialog nebeneinander, am Handy bleiben die Navigation und alle Werkzeuge mit Touch erreichbar.

**„Jarvis, sende eine Sprachnachricht an Lea“** wird als Werkzeugbefehl erkannt und nicht an das Sprachmodell geschickt. Bei eindeutigem vollständigem Kontaktnamen wird die Person ausgewählt, sonst öffnet sich die Kontaktliste. Danach erscheint die Aufnahme mit Anleitung. **„Wie sende ich eine Sprachnachricht?“** und der Knopf **Sprachnachricht** führen ebenfalls dorthin. Eine neue Anfrage startet keine Aufnahme und sendet nichts. Die eigene Stimme ist vorausgewählt; mit „Thorsten“ bzw. „deiner Stimme“ im Befehl wird Thorsten ausgewählt. Am Handy ohne Mac ist die eigene Aufnahme mit Audio teilen möglich; direkte Apple-Mail-Übergabe und Thorsten benötigen den verbundenen Mac. Der normale Chat-/Stimmenerkennungszugang muss weiterhin funktionieren, damit gesprochene Befehle als Text ankommen.


### Kontakte in den Papierkorb ziehen

Unter Ablage → Kontakte & Entwürfe können gespeicherte Jarvis-Kontaktkarten in den sichtbaren Papierkorb gezogen werden. Alternativ direkt auf den Papierkorb neben dem Namen tippen, oder den Kontakt auswählen und den großen Papierkorb anklicken. Erst die Bestätigung mit dem Kontaktnamen löscht ihn lokal aus Jarvis. Abbrechen verändert nichts. Nachrichtenentwürfe bleiben bestehen und verlieren nur ihre Empfängerverknüpfung. Apple Kontakte, temporäre Apple-Auswahlen und bereits exportierte Sicherungsdateien werden nicht verändert. Auf dem Mac gilt derselbe Ablauf im eingebetteten Kontaktfenster; zum Verwalten „Kontakt hinzufügen / bearbeiten“ in der Auswahl öffnen.


## 3D-Objekte mit der Kamera zerlegen

In der normalen Jarvis-Werkzeugleiste **⬡ Objekte zerlegen** anklicken. „Getriebe“ lädt das überprüfte öffentliche Gearbox-Assy-Beispiel aus dem Khronos-Archiv (rund 5 MB, erst nach deinem Klick; Quellenhinweis in der Ansicht). Eigene vollständig eingebettete GLB-2.0-Dateien bis 20 MB können ausgewählt werden. Direkte HTTPS-GLB-Links von raw.githubusercontent.com, modelviewer.dev und threejs.org werden unterstützt, außerdem GitHub-Dateilinks über /blob/. Webseiten-/Shop-Links und normale Fotos sind keine zerlegbaren 3D-Dateien. Namenssuche durchsucht vorerst nur die kleine tatsächlich geprüfte Bibliothek und ist keine allgemeine Internet-Suchmaschine.

Der Qualitätsfilter verlangt räumliche Geometrie, Materialien, 2–180 getrennte Modellteile und begrenzte Geometrie-/Texturgrößen. Externe Texturen, komprimierte Spezialformate, Skelettmodelle und zyklische Hierarchien werden abgelehnt. Nicht jedes optisch gute Modell enthält Einzelteile; solche Teile werden nicht erfunden. Die Kriterien können subjektive Schönheit nicht garantieren. Das Modell behält seine echten Materialien, wird räumlich beleuchtet und lässt sich drehen, zoomen und auseinanderziehen.

**Kamera-Geste starten**: Ein verbundener Mac mit macOS 11 oder neuer erkennt die Finger lokal über Apple Vision. Daumen und Zeigefinger kurz geschlossen halten, bis die Kalibrierung bestätigt wird; dann vor der Kamera öffnen zum Auseinanderziehen und schließen zum Zusammensetzen. Unzuverlässige oder fehlende Handpunkte halten die aktuelle Ansicht an; zum erneuten Aktivieren wieder kurz schließen. Der Schieberegler und „Zusammensetzen“ dienen außerdem zur manuellen Kontrolle. Die Web-App startet keine Kamera beim Laden der Seite oder eines Modells. Auf iPhone/iPad sind eine vertrauenswürdige HTTPS-Verbindung und der verbundene Mac erforderlich; ohne Mac gibt es hier keine versprochene Offline-Handerkennung.

Die Kamera nimmt keinen Ton auf. Kleine JPEG-Bilder werden nur im RAM auf dem eigenen Mac ausgewertet, ohne Datenbank, Gesichtsspeicher oder externen KI-Dienst. Schließen, Kamera aus und Wechsel in den Hintergrund stoppen die Kamera und laufende Anfragen. 3D-Dateien werden nicht automatisch als persönliche Bibliothek gespeichert.

Three.js 0.160.1 ist als kleine lokale Grafikbibliothek mit MIT-Lizenz und Quellenangabe beigefügt; keine KI-Gewichte und keine 3D-Modelldateien sind im Update enthalten. Das Update wird dadurch größer. Modell-Downloads erfolgen getrennt und ausdrücklich bei Bedarf.

Prüfung: tests/test_object_models.py prüft erlaubte Quellen, Größen, GLB-Kopf und abgelehnte Weiterleitungen. tests/browser/object_viewer.py nutzt eine kleine selbst erzeugte Testgeometrie oder optional ein öffentliches Referenz-GLB als Argument und prüft die echte WebGL-Darstellung, echte getrennte Geometrie, Filterfehler, kalibrierte Gesten und vollständiges Kamera-Stoppen. Cloud-Kamera und Handpunkte sind Testdaten; physische Apple-Vision-Erkennung ist hier nicht testbar. Beispielbilder: artifacts/objekt-zusammen.png und artifacts/objekt-einzelteile.png.


## Schachraum

In der Jarvis-Leiste **♟ Schach** öffnen oder „Jarvis, spiele Schach mit mir“ sagen/schreiben. Memory, Reaktion und Zahlenrätsel wurden entfernt. Das Brett hat eigene schattierte SVG-Figuren, einen dunklen Rahmen und Anzeigen für beide Spieler. Drei lokale Spielstärken, Weiß/Schwarz, legale Zielfelder, Zurücknehmen und alle üblichen Spezialzüge bleiben erhalten. Die lokale Browser-Suche ist ein Freizeitgegner, kein versprochener Großmeister. Es wird kein Schachmodell oder externer Dienst benötigt. Die Partie liegt im Arbeitsspeicher und wird beim Schließen verworfen.

Lockere Sprüche und Thorsten-Ausgabe bleiben freiwillig. „Reden stoppen“ stoppt Stimme und Spracheingabe, nicht die Partie. Thorsten und freie KI-Gespräche nutzen den verbundenen Mac und die bereits eingerichtete lokale KI, ohne SQLite-Gesprächsarchiv. Die Schachfunktion verwendet keine Systemstimme. Browser-Spracheingabe kann je nach Browser online verarbeitet werden und startet nur nach gesonderter Freigabe. Schließen und Wechsel in den Hintergrund beenden Mikrofon und Ausgabe.

chess.js ist mit BSD-2-Clause-Lizenz und Quellenhinweis lokal beigefügt. `node tests/chess_rules.mjs` prüft Schachregeln und lokale Züge. `python tests/browser/chess.py` prüft Bedienung, tatsächlichen Browser-Gegner und freiwillige Sprachfunktionen mit Testdaten; physische Mac-Audioausgabe und echte Spracherkennung können in der Cloud nicht geprüft werden.

## Projektboard und Textwerkstatt

Die neuen Knöpfe **▦ Projekte** und **✎ Texte** stehen außerhalb von Schach in der normalen Jarvis-Werkzeugleiste, auch am Handy/iPad. „Öffne mein Projektboard“ und „Öffne die Textwerkstatt“ führen ebenfalls dorthin.

Im Projektboard unter „Neues Projekt“ eine Karte mit Titel, nächstem Schritt und Farbe anlegen. Karten lassen sich zwischen Ideen, In Arbeit und Erledigt ziehen. Am Handy kann der Status direkt ausgewählt werden. Der Fortschritt zählt nur tatsächlich als erledigt markierte Karten. Titel/Details bearbeiten, Karten löschen und während der Ansicht rückgängig machen ist möglich. Änderungen werden ausdrücklich in diesem Browser gespeichert, nicht automatisch zwischen Geräten synchronisiert. „Projekte als Datei sichern“ exportiert ausschließlich die Projektkarten. Nach Schließen ist die letzte Lösch-Rücknahme nicht mehr verfügbar.

Die Textwerkstatt zählt Wörter/Zeichen und schätzt Lesezeit, räumt Abstände/Absätze auf oder macht vorhandene Zeilen zu Listenpunkten. Diese Formatwerkzeuge sind keine KI-Zusammenfassung und funktionieren offline. Ergebnisse bleiben editierbar und können kopiert oder als TXT gespeichert werden. Die zusätzliche KI-Überarbeitung nutzt ausschließlich die vorhandene lokale KI am verbundenen Mac. Bei langen Texten einen Abschnitt bis 1.500 Zeichen markieren; es erfolgt kein stilles Kürzen. Änderungen am Eingabe-/Ergebnistext und Schließen stoppen verspätete Antworten. Texte werden nur im RAM gehalten und beim Schließen verworfen; kein automatisches Speichern im Gesprächsarchiv.


## Code-Arbeitsraum auf Mac und iPad

In der grün-gelben Jarvis-Leiste auf **⌘ Code** klicken oder „Öffne den Code-Arbeitsraum“ schreiben/sagen. Der Bereich ist im Handy-Modus und auf iPhones ausgeblendet. Auf dem iPad ist er über `/tablet` verfügbar; Mac und lokale KI müssen dafür laufen und das Gerät muss gekoppelt sein. Es gibt hier keine neue Offline-KI und keinen Cloud-Ausweichdienst.

- **Lokale KI:** Die Auswahl zeigt das tatsächlich geladene llama.cpp-Modell und über Ollama vorhandene lokale Modelle. Es werden keine zusätzlichen Modelle heruntergeladen. Modellnamen sind keine garantierte Rangfolge; die kleine bisherige Text-KI bleibt in ihren Fähigkeiten begrenzt.
- **Arbeitsstufe:** Leicht, Mittel und Hoch ändern das Ausgabebudget. Hoch ruft die KI zusätzlich zur Prüfung des Entwurfs auf; diese Hinweise sind kein tatsächlicher Testlauf.
- **Boost:** Kleine Animation beim Einschalten. Nutzt ein kürzeres Ausgabebudget und lässt die zweite KI-Prüfung aus. Beschleunigt die Hardware nicht; weniger Ausgabe kann schneller fertig werden, auf Kosten der Ausführlichkeit.
- **Zugriff:** Nur Entwurf hält Dateien im Arbeitsspeicher. „Vor dem Speichern fragen“ zeigt erst das Ergebnis und verlangt einen bewussten Klick auf **Dateien am Mac speichern**. „Projektzugriff“ speichert automatisch in einem neuen Unterordner von `.jarvis/code-projects` (abhängig vom verwendeten Datenordner). Die tatsächliche Zieladresse steht im Ergebnis. Bestehende Projekte und andere Mac-Dateien werden nicht überschrieben. Die Auswahl gilt jeweils für den nächsten Auftrag.
- **Dateien und Vorschau:** Erzeugte Textdateien lassen sich ansehen und als ZIP herunterladen. HTML-Projekte erhalten eine bewusst gestartete, isolierte Vorschau mit Skripten, ohne Netzwerk oder Zugriff auf den Mac. Lokale CSS-/JS-Dateien werden für diese Vorschau eingebettet. Externe Pakete funktionieren dort nicht. Python-/JSON-Syntax wird geprüft; sonstige Funktion muss selbst getestet werden. Code wird nicht automatisch auf dem Mac ausgeführt.
- **Weiterarbeiten:** Kurze erzeugte Dateien können als Referenzen in den nächsten Auftrag übernommen werden. Alternativ kleine Textdateien auswählen (zusammen höchstens 3.500 Zeichen); große Projekte werden nicht still gekürzt. Ein Auftrag enthält höchstens 1.800 Zeichen und erzeugt höchstens zwölf Textdateien mit zusammen 80 KB.
- **Beispiele:** Kleine Websites und interaktive HTML-Animationen, Lua/Luau-Skripte für Roblox Studio, Python-Skripte oder andere Textdateien. Ein Skript ist noch kein fertig getestetes oder veröffentlichtes Roblox-Spiel; eine HTML-Animation ist noch keine gerenderte Filmdatei. Es gibt keine Behauptung einer Gleichwertigkeit mit Codex.
- **Aufträge und Stoppen:** Die letzten zwanzig Aufträge lassen sich während derselben Serverlaufzeit wieder öffnen. Fenster schließen lässt einen gestarteten Auftrag weiterlaufen. **Stoppen** verwirft das Ergebnis; eine bereits laufende lokale Modellberechnung kann noch auslaufen. Beim Serverneustart gehen ungespeicherte Entwürfe verloren. Gespeicherte Projektdateien und bewusst exportierte ZIPs bleiben erhalten. Aufträge werden weder an Cloud-KI noch in den normalen Chatverlauf geschrieben.

Der Projektzugriff ist ausdrücklich **kein Vollzugriff auf den Mac**: keine Terminalbefehle, keine App-Steuerung, kein Zugriff auf Kontakte oder beliebige vorhandene Dateien. Dafür bestehen die gesonderten Astra-Werkzeuge mit eigenen Freigaben. Dieses Update enthält außerdem den neuen Schachraum, das Projektboard und die Textwerkstatt; das vorherige Update muss nicht zuerst installiert werden.


### Mit Jarvis im Code-Arbeitsraum sprechen

Im Code-Arbeitsraum gibt es den Reiter **Gespräch**. Vor dem Auftrag kannst du mit der ausgewählten lokalen KI planen. Bei laufender Erzeugung liefert Jarvis auf Nachfrage den tatsächlichen Stand; für freie Antworten ist die einzelne KI erst nach ihrer laufenden Berechnung wieder verfügbar. Über **Änderung einarbeiten** kannst du bis zu sechs kurze Zusatzwünsche einreichen. Die laufende Modellantwort wird nicht mitten im Token abgebrochen: Anschließend folgen höchstens zwei Überarbeitungsrunden. Der Ablauf zeigt empfangene und noch nicht eingearbeitete Wünsche ausdrücklich an. Spätere Wünsche lassen sich im nächsten Auftrag übernehmen.

**Thorsten antwortet** ist voreingestellt; kein Wechsel zu einer Systemstimme. Einmal Senden oder Gespräch starten antippen, damit der Browser Audio freigibt. Thorsten muss auf dem verbundenen Mac eingerichtet sein. Für freihändiges Sprechen erst **Browser-Spracheingabe erlauben**, dann **Gespräch starten** wählen: erkannte Sätze werden automatisch gesendet, nach der Antwort hört Jarvis wieder zu. Die Browser-Spracherkennung kann ihren eigenen Onlinedienst nutzen. Tippen bleibt möglich. Gespräch beenden, Fenster schließen, Tab-Wechsel oder Hintergrundwechsel stoppen Mikrofon und Stimme; ein laufender Arbeitsauftrag wird dadurch nicht gestoppt. Es wird weder ein Stimmprofil noch eine Aufnahme im Chatverlauf gespeichert.

### Roblox: direkt in Studio bauen statt Skriptdateien

Im Code-Arbeitsraum gibt es jetzt **Ausgabeziel**. Bei **Automatisch** führen Roblox-/Superhelden-Aufträge in den direkten Studio-Ablauf; Websites bleiben Dateientwürfe. **Roblox Studio direkt** wählt diesen Ablauf ausdrücklich, **Nur Dateientwürfe** behält die bisherige Code-Ausgabe. Ein direkter Studio-Auftrag erzeugt keine Ersatz-Skriptdateien und kein Projekt-ZIP. Du siehst einen Studio-Bauplan und danach die tatsächlichen Plugin-Rückmeldungen.

- **Nur Bauplan:** Studio bleibt unverändert.
- **Vor dem Bauen fragen:** erst den Plan prüfen, dann **In Studio bauen** klicken.
- **Projektzugriff:** mit **Auftrag starten** wird der Bauplan direkt an das verbundene Studio übergeben. Gebaut wird aus geprüften Spielbausteinen, ohne frei generierten Lua-Code auszuführen. Arbeitsstufe und Boost betreffen weiterhin die Dateientwürfe, nicht die Studio-Bausteine.

Unterstützt sind ein **Parcours** und ein eigener **Superhelden-Stadtprototyp**. Die Stadt enthält Gebäude, Dächer, markierte Zielpunkte sowie mitgelieferte Server- und Clientsteuerung: Q halten zum Schwingen, E für Dash, Space für Sprung/Doppelsprung und an einer Wand mit W + Space die Wandlauf-Hilfe, R zum Rücksetzen. Touch-Schaltflächen werden im Spiel eingeblendet. Acht Dach-Checkpoints bilden ein Zeitrennen mit Fortschritts- und Energieanzeige. Es gibt noch keine Kämpfe, Gegner-KI, Tarnung, Story, professionellen Figurenanimationen oder ein komplettes Miles-Morales-Spiel. Das Modell ist ein eigener Starter-Prototyp ohne fremde Spielassets. Andere direkte Spieltypen werden nicht einfach als erledigt ausgegeben.

**Einmalig Plugin v2 einrichten:**

1. Jarvis aktualisieren und neu starten. In **⌘ Code → Roblox Studio** auf **Studio-Plugin v2 herunterladen** klicken. Diese Version ist für den Stadt-Prototyp nötig; das bisherige Plugin unterstützt nur den Parcours.
2. Die alte **JarvisStudio.rbxmx** im lokalen Plugins-Ordner von Roblox Studio durch die neue Datei ersetzen. Nicht beide Versionen nebeneinander behalten. Den Ordner findet man abhängig von Studio unter **Plugins → Plugins Folder** oder den erweiterten Dateioptionen. Studio neu starten.
3. Lokale HTTP-Anfragen an **127.0.0.1** und das Einfügen der mitgelieferten Spielskripte erlauben, wenn Studio fragt. Ein neues leeres Projekt im Bearbeitungsmodus öffnen. Play muss beim Bauen gestoppt sein.
4. Jarvis muss **Studio verbunden · Plugin v2** melden. Danach einen Roblox-Auftrag starten oder im Studio-Reiter den Spieltyp auswählen und **In Studio bauen** klicken. Das Plugin zeigt zusätzlich ein eigenes Studio-Statusfenster. Die Objekte und Spielskripte entstehen direkt im geöffneten Studio-Projekt.
5. Nach **Im Studio aufgebaut** in Roblox Studio selbst **Play** starten, Steuerung und Physik testen und das Projekt speichern. Die Fertigmeldung bestätigt nur den Einbau, keinen bestandenen Spieltest und keine Veröffentlichung.

**Danach kein erneuter Plugin-Download bei jedem Jarvis-Neustart:** Die lokale Adresse und die widerrufbare Verbindungskennung werden ausschließlich am Mac in `studio-link.json` im Jarvis-Datenordner gespeichert (Dateirechte 0600). Der Code in dieser Datei ist eine lokale Plugin-Kennung, kein Anbieter-API-Schlüssel. Die Datei nicht teilen. Nach dem Neustart Jarvis und Studio öffnen und gegebenenfalls **Vorhandenes Plugin verbinden** wählen. Das installierte v2-Plugin verwendet dieselbe Kennung und Adresse weiter. Ist der gespeicherte Port von einer anderen App belegt, meldet Jarvis den Konflikt; die Verbindung wird nicht still auf einen anderen Port verschoben.

Die Brücke lauscht nur am Mac auf **127.0.0.1**. Ein gekoppeltes iPad kann über den Mac-Server Bauaufträge auslösen; Studio läuft dabei auf dem Mac. Studio muss mit einem Projekt geöffnet sein und kann während des Baus im Hintergrund liegen. Ohne laufendes Studio oder Plugin gibt es keine falsche Erfolgsmeldung und keinen stillen Rückfall auf Dateien. Die normale Studio-Anmeldung bleibt erforderlich; keine neue KI-Anmeldung und keine zusätzlichen Modelle sind nötig.

**Stoppen** hält einen aktiven direkten Bau beim nächsten Plugin-Kontakt an. Schon erstellte Teile können stehen bleiben. **Brücke trennen** widerruft die aktuelle Freigabe; über **Vorhandenes Plugin verbinden** lässt sie sich ohne neue Datei wieder aktivieren. Bestehende fremde Objekte werden nicht gelöscht. Ist das Einfügen der Spielskripte nicht erlaubt, nimmt das Plugin den gerade neu angelegten Bauentwurf zurück und meldet den Fehler. Für eine neue Stadt ein leeres Projekt verwenden; ein vorhandener Jarvis-Stadtprototyp wird nicht automatisch überschrieben.

Die Tests prüfen echte lokale HTTP-Rückmeldungen, das dauerhafte Wiederverbinden, Syntax mit dem offiziellen Luau-Compiler und den tatsächlichen Plugin-Code gegen ein Studio-API-Testmodell. Dabei wird geprüft, dass Server-Script und LocalScript im richtigen Roblox-Objektbaum landen und dass Abbruch keine Erfolgsmeldung erzeugt. Eine reale Roblox-Studio-Grafik-/Physikprüfung ist in der Linux-Cloud nicht möglich und muss im geöffneten Studio erfolgen.

## Sichtbarer Handy-Modus und Schachgespräch

Oben gibt es jetzt **ANSICHT → MacBook / iPad / Handy**, auch direkt im ursprünglichen Mac-Kontrollzentrum. Du musst keine Adresse ändern. Handy wählt eine kompakte Ansicht mit einer Spalte, größer bedienbaren Inhalten und Navigation am unteren Rand; der Code-Arbeitsraum bleibt dort ausgeblendet. Die Ansicht wird auf dem Gerät gespeichert und lässt sich wieder auf iPad oder MacBook umschalten. Notizen, Marken und Ablage werden dabei nicht in einen zweiten Speicher kopiert. Die bisherigen Adressen bleiben bestehen; es gibt für den Wechsel keinen neu zu tippenden Handy-Pfad.

Beim Schach zuerst **Browser-Spracheingabe erlauben**, dann **Mit Jarvis sprechen** wählen. Das gibt zugleich die Audiowiedergabe frei und aktiviert Thorsten. Erkannte Sätze werden automatisch gesendet. Nach einer Antwort hört Jarvis wieder zu, ohne dass du erneut Senden oder das Mikrofon drücken musst. Beispiel: „von e zwei nach e vier“. Nur erlaubte Züge werden ausgeführt. Zwischen Mikrofonaufnahme und Thorsten-Ausgabe wird gewechselt, damit Jarvis nicht seine eigene Stimme als Nutzereingabe übernimmt. Gespräch beenden, Fenster schließen oder in den Hintergrund gehen stoppt das Mikrofon. Bei verweigerter Freigabe erscheint ein Hinweis; die Aufnahme wird nicht heimlich wieder aktiviert.

Die Browser-Spracheingabe benötigt je nach Browser dessen Onlinedienst und eine freigegebene sichere Verbindung. Es wird keine eigene Aufnahme oder Stimme als Profil gespeichert. Thorsten benötigt den verbundenen Mac; auf einem echten Mac/iPhone muss die Mikrofon- und Audiofreigabe weiterhin einmal erlaubt werden. Ohne Sprachunterstützung bleiben Tippen und das Tastaturmikrofon als Alternative.

Sprüche wechseln jetzt ohne unmittelbare Wiederholung innerhalb ihrer Gruppe und unterscheiden gewöhnliche Züge, Schach, Figurenschlagen und Rochade. Eine Frage nach dem eigenen letzten Zug bekommt dessen tatsächliche Notation statt eines zufälligen Kompliments. Wiederholt die kleine Gesprächs-KI wortgleich ihre letzte Antwort, wird das sichtbar angesprochen; es wird keine sichere Stellungsbewertung behauptet.

## Erfinder-Labor

In der Jarvis-Leiste auf **⚗ Erfinden** klicken oder „Öffne das Erfinder-Labor“ schreiben. Das Werkzeug ist in MacBook-, iPad- und Handy-Ansicht verfügbar. Beschreibe eine Idee, wähle **Konzept entwickeln** und sieh dir die beschrifteten Funktionsbausteine an. Tippe einen Baustein für seine Aufgabe an. Unter **Gemeinsam weiterdenken** kannst du Änderungswünsche eingeben; die lokale KI bekommt das bisherige Konzept mit.

Die Skizze zeigt 2–6 Bausteine und deren Verbindungen. Sie ist ein schematisches Konzept, kein maßhaltiges CAD-Modell, keine technisch geprüfte Konstruktion und keine bereits bewiesene Erfindung. Offene Fragen und vorgeschlagene Tests stehen ausdrücklich dabei. **Skizze als SVG** und **Konzept sichern** exportieren nur den aktuellen Entwurf. Ohne bewussten Export bleibt er im Arbeitsspeicher. Bei einer ungültigen KI-Ausgabe bleibt eine vorhandene Skizze unverändert; sie wird nicht als neue erfolgreiche Überarbeitung ausgegeben. Änderungen während einer Anfrage und Stoppen verwerfen verspätete Antworten.

Das Labor nutzt nur die vorhandene lokale KI am verbundenen Mac und lädt kein Modell nach. Bei belegter KI oder fehlender Verbindung erscheint eine Erklärung; es gibt keine automatische Cloud-Ausweichroute. Die Browserprüfung verwendet Testantworten zur Kontrolle von Bedienung und Datenfluss; die inhaltliche Qualität der Erfindungen hängt vom tatsächlich gewählten Modell ab.


## Reparierter Offline-Start und Handy-Modus

Der normale iPhone-/iPad-Einstieg öffnet jetzt denselben lokalen Arbeitsraum wie die Geräteansicht. Oben steht sichtbar **Offline bereit**, sobald die tatsächlich nötige Oberfläche vollständig gespeichert ist. Die Vorbereitung beginnt unabhängig von Mac-API und KI-Modell; ein langsamer oder ausgeschalteter Mac blockiert das Zeichnen der Oberfläche nicht mehr. Auf Geräteansichten, der alten Mobilseite und dem normalen Mac-Einstieg wird die Offline-Oberfläche vorbereitet.

**Nach dem Update einmal mit eingeschaltetem Mac vorbereiten:**

1. Jarvis am Mac aktualisieren und neu starten. Die bisherige HTTPS-Adresse auf dem Handy/iPad öffnen und das Gerät bei Bedarf koppeln.
2. Warten, bis **Offline bereit** erscheint. Die Anzeige prüft den wirklichen Cache und zeigt bei einem Fehler eine Erklärung statt einer Erfolgsmeldung. Bei unvollständiger Vorbereitung auf **Prüfen** tippen, solange der Mac verbunden ist.
3. Wenn du die Home-Bildschirm-App nutzt, diese ebenfalls einmal bei laufendem Mac öffnen und dort auf **Offline bereit** warten. Safari und die Home-Bildschirm-App können unterschiedliche Speicher verwenden.
4. Erst danach den Mac ausschalten. **Ohne Mac · Oberfläche bereit** zeigt den lokalen Betrieb an. Notizen, Ablage, Markenwerkzeuge und andere gespeicherte Browserfunktionen bleiben erreichbar.

Ohne einmalige Speicherung kann Safari eine nicht erreichbare Website nicht selbst herstellen. Vertrauenswürdiges HTTPS ist weiterhin nötig. Browserdaten und vorhandene KI nicht löschen; bei einem Updatefehler bleibt die vorherige funktionierende Oberfläche erhalten. Ein optionales fehlendes 3D-Modul verhindert nicht mehr den Offline-Start der Handy-Oberfläche. Lädt der Server eine Einstiegsseite nicht rechtzeitig, wird nach kurzer Frist die gespeicherte Oberfläche gezeigt. Auch die alten Einstiege `/`, `/mobile`, `/index.html` und Adressen mit Ansichtsparametern bekommen offline den gespeicherten Arbeitsraum. Mac-spezifische Ansichten erhalten einen erklärten Rückweg statt eines leeren Dokuments.

**Handy-Modus:** Die untere Navigation ist nun auch bei breiten Fenstern eine begrenzte horizontale Leiste. Sie wird nicht mehr durch geerbte Desktop-Regeln fast bildschirmhoch. Auf schmalen Handys passt sie ohne seitlichen Überlauf. Die Werkzeugleiste bleibt beim Scrollen nicht über dem Chat hängen. Bei erkannter Bildschirmtastatur wird die untere Navigation vorübergehend ausgeblendet, damit das Eingabefeld frei bleibt. Ohne Mac lassen sich die lokalen Ansichten wechseln, ohne auf eine unerreichbare Mac-Seite geschickt zu werden.

**Offline-Oberfläche und Offline-KI sind getrennt:** Freie KI-Antworten ohne Mac benötigen weiterhin das einmal eingerichtete kleine Gerätemodell unter **Gerät**. Die Reparatur lädt kein Modell automatisch herunter. Thorsten, Roblox Studio und andere Mac-Werkzeuge brauchen weiterhin den Mac. Die neue Speicherung betrifft statische Oberflächendateien, keine API-Antworten oder Aufnahmen; vorhandene Modellteile und persönliche IndexedDB-Daten werden beim Oberflächenupdate nicht gelöscht.

Geprüft wurden echte Browser-Kaltstarts nach vollständigem Abschalten des Testservers (auch bei weiterhin als online gemeldetem Netzwerk), Notizen und Ansichtsparameter, fehlende optionale Dateien, ein fehlgeschlagenes Update ohne Verlust der alten Oberfläche, verschiedene Handy-Breiten sowie lokale WASM-Inferenz mit synthetischen Testgewichten. Der Safari-Kompatibilitätsbinärcode wurde in Chromium ausgeführt; ein physisches iPhone/iPad war hier nicht verfügbar.

### Über mich · dein persönliches Profil

In der grünen Schnellzugriffsleiste auf **„Über mich“** tippen, oder „Was weißt du über mich?“ schreiben. In der Mitte steht eine anatomische 3D-Gehirnoberfläche (fsaverage5-Standardmodell) mit grüner Beleuchtung und sichtbaren Windungen. Mit einem Finger oder der Maus lässt sie sich drehen; die Texte daneben sind Schaltflächen. Name, Anrede, Humor, Antwortstil, Interessen und Dinge, die Jarvis vermeiden soll, lassen sich einzeln ansehen und ändern. Das Standardmodell ist kein Scan von dir. Bei reduzierten Animationen bleibt die automatische Bewegung aus; manuelles Drehen funktioniert weiterhin. Für die räumliche Ansicht wird WebGL benötigt.

Einmal freiwillig von dir erzählen und **„Meine Angaben speichern“** wählen. Es werden nur deine eigenen Angaben und der bereits eingestellte Name/die Anrede angezeigt, keine heimlich abgeleiteten Eigenschaften. Die vorhandene lokale KI erhält passende Profilangaben als Gesprächskontext; das ist kein Training und macht das kleine Modell nicht leistungsfähiger. Diese zusätzliche Profilweitergabe ist bei Internet-KI-Anbietern deaktiviert.

Am verbundenen Mac bleibt das Profil lokal in der vorhandenen Jarvis-Datenbank. Auf Handy und iPad wird eine Kopie im Gerätespeicher gehalten. Nach „Offline bereit“ kann sie auch ohne Mac geöffnet und bearbeitet werden. Wird der Browserspeicher gelöscht, entfällt diese Gerätekopie. Auf anderen Geräten mit dem gleichen Jarvis-Mac muss man sich nicht erneut vorstellen.

Offline-Änderungen werden nicht ungefragt über das Mac-Profil geschrieben. **„Mit Mac abgleichen“** zeigt beide Fassungen, danach wählst du bewusst die gewünschte Fassung. „Profilangaben löschen“ entfernt das Profil und setzt Name/Anrede zurück; Chats, Notizen und weitere Geräte werden dabei nicht gelöscht. Eine Offline-Löschung muss später ebenfalls mit dem Mac abgeglichen werden. Für alte Chats gibt es separat „Chat löschen“.

### Übersicht & 3D-Baustudio

Offline-Verfügbarkeit und Gerätewahl stehen am Mac kompakt in einer Zeile. **Info** blendet die Offline-Erklärung ein; **Weitere Bereiche** öffnet die Links zu Helfer, Videoschnitt, VR und Marken. Die Werkzeugleiste startet klein und lässt sich über **Jarvis-Werkzeuge** aufklappen.

Dort **Baustudio** öffnen, oder Jarvis schreiben: „Ich will ein leuchtendes Objekt aus Holz bauen, 30 cm breit, in 4 Tagen“. Das Studio berechnet einen modularen Vorentwurf und zeigt, wie seine Bauteile im 3D-Modell zusammengesetzt werden. Finger/Maus drehen das Modell; der Regler zieht die Teile auseinander. Ein Teil antippen, um seine Maße zu sehen. Aktuell gibt es Leuchtobjekt, offene Box, Tischablage und Geräteständer mit änderbaren Maßen und den Materialien Holz, Metall oder Kunststoff. Das ist ein Einstieg mit Standardkonstruktionen, keine beliebige automatische CAD-Fertigung.

„Breiter“, „kleiner“, „aus Metall“, konkrete Maße sowie das Zeitfenster können im Studio eingegeben werden. Die Teileliste verwendet dieselben Maße wie das Modell. Bauanleitung, Werkzeuge und eine vorgeschlagene Tagesaufteilung stehen daneben. „Weiter“ und „zurück“ gehen durch die Anleitung. Fragen wie „Was kann es?“ oder „Wo finde ich die Bauteile?“ zeigen die passenden Angaben. Allgemeine Beratung nutzt bei entsprechend formulierten Fragen die vorhandene lokale KI am verbundenen Mac.

Unter **Mit Jarvis sprechen** optional die Browser-Spracherkennung erlauben. Diese kann Audio online verarbeiten. Danach werden Sprachaufträge ohne Senden übernommen; Thorsten antwortet, soweit die Stimme am Mac verfügbar ist. **Reden stoppen** schaltet die Sprachausgabe aus, **Stoppen** unterbricht eine laufende Anfrage/Montageansicht. Beim Schließen endet das Zuhören.

Einkaufslinks sind Suchanfragen, keine Bestands- oder Preiszusagen. Verbindungsmittel, Toleranzen und bei Leuchten der Kabelweg müssen vor dem Bau festgelegt werden; die Anleitung setzt fertige Zuschnitte und fertige 5-V-/Batterie-LED-Module voraus. Die Entwürfe haben keine geprüfte Tragfähigkeit. Ein Zeitfenster ist ein Planungswunsch, keine zugesagte Bauzeit.

**Entwurf auf diesem Gerät sichern** speichert ausdrücklich im Browser; der gesicherte Stand kann nach „Offline bereit“ auch ohne Mac als 3D-Modell samt Anleitung geöffnet werden. Neue Entwürfe und Änderungen brauchen derzeit den verbundenen Mac. **Bauplan als Text herunterladen** sichert Maße, Teile und Anleitung zusätzlich als Datei.


### Jarvis plant mit · schwebendes Gesicht

Im Baustudio ist **„Jarvis plant für mich“** beim Start eingeschaltet. Ein Ziel wie „Ich will eine moderne Lampe bauen“ reicht für einen Vorschlag mit Material, Maßen, Diffusor und LED-Modul. Rechts erklärt Jarvis seine Entscheidungen. Ausdrücklich genannte Materialien und Maße im Auftrag haben Vorrang. **„Alternative entwerfen“** erstellt innerhalb der verfügbaren Bauformen einen anderen Maßvorschlag. Nicht unterstützte Gegenstände werden weiter klar abgelehnt.

Die manuellen Maße liegen unter **„Maße und Material selbst vorgeben“**. Eine Änderung dort schaltet den Automatikmodus aus, damit deine Eingaben erhalten bleiben. „Übernimm“ bzw. die Alternative-Schaltfläche schalten ihn wieder ein. Die weichere Kantendarstellung, Lichtmaterialien, Holzoberflächen, Metallreflexionen und Bodenschatten dienen der Vorschau. Verbindungsmittel und Toleranzen sind weiterhin vor der Fertigung festzulegen.

Das kleine Jarvis-Gesicht schwebt **innerhalb der Browserseite**. Am Griff verschieben, über den Bewegungsschalter stillsetzen oder ausblenden. Das Mikrofonsymbol öffnet dieselbe Sprachsteuerung wie die Werkstatt; die Zustimmung zur Browser-Spracherkennung ist weiterhin erforderlich. Der Mund animiert erst während tatsächlich abgespielter Thorsten-Audiodaten, nicht schon beim Laden. Das Stoppsymbol am Gesicht beendet nur die Sprachausgabe; ein Entwurf kann weiterlaufen. Ausblenden, Schließen der Werkstatt oder Verlassen der sichtbaren Seite beendet das Zuhören. Das Gesicht steuert weder den Browser-Tabbalken noch andere Programme.

Die kompakte Hauptansicht, das 3D-Gehirn und alle vorherigen Änderungen sind im selben Update enthalten. Kein neues KI- oder Stimmenmodell wird geladen.

Während eines laufenden Schritts kann der nächste Wunsch schon gesprochen werden. Der neueste Wunsch wird vorgemerkt und danach angewendet; ein älterer noch wartender Wunsch wird dadurch ersetzt. „Stopp“ verwirft auch den wartenden Wunsch.
