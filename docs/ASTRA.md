# Astra und Welt

Das kleine **JARVIS-Astra-Update.zip** aktualisiert den vorhandenen Jarvis-Ordner. ZIP entpacken, `JARVIS-Astra-aktualisieren.command` öffnen und bei Bedarf den vorhandenen Ordner wählen. Danach Jarvis mit Control+C beenden und im selben Ordner mit `python3 -m backend --easy-local` neu starten. Textmodell, Stimme, Einstellungen und persönliche Daten bleiben erhalten. Das Astra-Update lädt kein KI-Modell und keine neue Stimme. Unbekannte veränderte Programmdateien werden nicht überschrieben; vor Änderungen wird eine Sicherung angelegt.

## Identität ohne Astra-Schalter

Sage oder schreibe **„Jarvis, werde zu Astra“**. Blaue Partikel bilden einen leuchtenden rotierenden Kern mit ASTRA-Schriftzug, inspiriert von deiner Referenz. **„Werde wieder zu Jarvis“** bringt die goldene Ansicht zurück. Reduzierte Bewegung wird berücksichtigt. Die Auswahl bleibt in diesem Browser gespeichert.

Der Mini-Hub ist entfernt. **Welt** zeigt den lokalen drehbaren Globus, auswählbare Länder und zugeordnete öffentliche Nachrichten. Die Quelle ist tagesschau.de; wenn RSS nicht funktioniert, wird die öffentliche Nachrichten-JSON-Schnittstelle versucht. Auch dieser Abruf kann gesperrt oder nicht erreichbar sein. Es werden keine Nachrichten erfunden. Fehlender Abruf und ältere Stände sind sichtbar. Es gibt keine Kamera-Streams. Manche Länder haben im aktuellen Feed keine Meldung.

## Tatsächliche Desktop-Eingaben

In Astra zum Beispiel **„Astra, öffne Notizen und schreibe eine Einkaufsliste“** sagen. Ein Ablauf wird lokal vorbereitet und zur Prüfung angezeigt. Die kleine KI liefert nicht immer brauchbares JSON; dann wird nichts ausgeführt. „Ablauf selbst bearbeiten“ bietet ein lauffähiges Notizen-Beispiel und unterstützt App öffnen, warten, Tasten, Text sowie selbst angegebene Mauspositionen. Mauskoordinaten sind Anteile des Hauptbildschirms von 0 bis 1. Keine Shell- oder Skriptausführung.

**Geprüften Ablauf starten** führt die Schritte tatsächlich aus; nach drei Sekunden startet die App. Halte den Ablauf im Blick. Falls die Ziel-App nicht im Vordergrund ist, werden Eingaben gestoppt. Unter macOS müssen Terminal bzw. Python unter **Systemeinstellungen → Datenschutz & Sicherheit → Bedienungshilfen** erlaubt sein. Jarvis umgeht diese Freigabe nicht. Über die Handy-Kopplung sind Desktop-Aufträge nicht verfügbar.

Beim Start eines geprüften Ablaufs wird das schwebende Fenster automatisch angefordert. **Schwebendes Fenster** fordert ein natives macOS-Fenster über AppKit/WebKit an. Es zeigt eine blaue räumliche Gehirnstruktur aus vielen verbundenen Punkten und winzige weiße Funken bei tatsächlichen Desktop-/Agentenaufträgen. Es bleibt über anderen normalen App-Fenstern; Vollbild-Spaces sind davon abhängig. **Reden stoppen** schaltet nur die Ausgabe stumm. **Wieder reden** erlaubt künftige Antworten. **Aktionen stoppen** beendet die weiteren Desktop-Schritte; bereits erfolgte Klicks oder Eingaben werden dadurch nicht rückgängig gemacht. Lass das Hauptfenster mit Jarvis geöffnet. Ein ausdrücklich gestartetes Gespräch darf während eines laufenden Astra-Desktopauftrags auch beim App-Wechsel weiterlaufen. Nach Ende des Auftrags wird ein im Hintergrund gebliebenes Gespräch gestoppt. Manche Browser pausieren Spracherkennung im Hintergrund trotzdem; das schwebende Fenster hat keine eigene garantierte Spracherkennung.

### Was damit noch nicht geht

Es ist kein allgemeiner Computer-Agent mit Bildschirmverständnis. Kein autonomer Nachbau von Bildern und keine verlässlich selbst lernende Bedienung beliebiger Apps. Vereinfachte geometrische 3D-Modelle sind möglich; siehe Korrekturabschnitt unten. Das bestehende kleine Textmodell wird durch einen Prompt nicht größer. Bilder kannst du weiterhin Agenten anhängen; lokale Apple-Vision-Befunde sind keine vollständige Bildanalyse und steuern keine Desktop-Abläufe. Ein abgeschlossener Eingabeablauf meldet nur seine ausgeführten Schritte, nicht ein angeblich überprüftes fertiges Modell.

Native Maus-/Tastaturereignisse, macOS-Berechtigungen und das schwebende AppKit-Fenster müssen auf einem echten Mac geprüft werden. Linux-Cloud-Tests mit einem kontrollierten Eingabetreiber belegen diese Mac-Ausführung nicht.

## Prompt für die vorhandene Text-KI

Diesen Text kannst du als erste Nachricht in einem neuen Chat senden. Er gilt nur, solange er im begrenzten Gesprächskontext vorhanden ist; er ist kein dauerhaftes Gedächtnis:

> Du bist Jarvis, mein ruhiger deutschsprachiger Assistent. Antworte konkret und kurz. Sprich mich gelegentlich mit Sir an. Bearbeite meinen aktuellen Auftrag und schleppe alte Themen wie Minecraft nicht in neue Fragen hinein. Frage bei einer entscheidenden fehlenden Angabe gezielt nach. Unterscheide Vorschlag, gestarteten Auftrag und überprüftes Ergebnis. Behaupte nie, eine App bedient, ein Bild vollständig verstanden oder eine Aufgabe erledigt zu haben, wenn dir dafür kein echtes Ergebnis vorliegt. Die Oberfläche schaltet mit „Jarvis, werde zu Astra“ um. Astra kann geprüfte lokale Eingabeschritte ausführen, sieht aber den Bildschirm nicht zuverlässig. Bei unlösbaren Aufgaben sage ehrlich, welche Information oder Fähigkeit fehlt. Erfinde keine Nachrichten, Werkzeuge oder Erfolge.


## Korrektur für Apps, Pop-up und Modelle

- **„Astra, öffne Spotify“** startet das Öffnen der nativen App direkt. Ein einzelner eindeutiger App-/Webseitenbefehl benötigt keinen zusätzlichen Startklick. Mehrstufige Eingabeabläufe und Modellierung zeigen weiterhin eine Vorschau vor dem Start. Fehlt sie, wird die Spotify-Web-App in Safari versucht. **„Öffne youtube.com“** oder **„Astra, öffne https://example.com/app“** öffnen Webseiten. Auch installierte Mac-Apps in den üblichen Programmeordnern werden erkannt. Apps/Webseiten öffnen benötigt keine Bedienungshilfen-Freigabe; Maus/Tastatur weiterhin schon.
- **„Astra, erstelle ein 3D-Auto in Blender“** baut ein echtes, vereinfachtes Modell aus Grundkörpern. Zuverlässige Vorlagen: Auto, Haus, Tisch, Stuhl, Roboter, Rakete, Schneemann, Würfel, Kugel, Zylinder. Andere Beschreibungen versucht die kleine lokale KI als begrenzten Grundkörper-Entwurf; ungültige Entwürfe werden abgewiesen. Kein neuer Modelldownload. Blender muss bereits installiert sein.
- Nach dem geprüften Start öffnet ein eigener Blender-Prozess eine neue Szene und fügt die Objekte schrittweise hinzu. Dazu dient Blenders Datenschnittstelle, nicht eine vorgetäuschte Mausanimation. Bestehende Blender-Dateien werden nicht überschrieben. Ein Erfolg wird erst nach der gespeicherten `.blend`-Datei gemeldet; sie lässt sich im Auftrag herunterladen. Die Vorlagen sind einfache Block-/Low-Poly-Modelle, keine professionell detaillierten Nachbildungen.
- **„Astra, stopp“**, **„Hör auf“** oder **Aktionen stoppen** beendet weitere Eingabeschritte und weitere Modellobjekte. Ein bereits hinzugefügtes Objekt wird nicht rückgängig gemacht; Blender bleibt geöffnet. **„Reden stoppen“** schaltet nur die Stimme leise, **„Wieder reden“** erlaubt neue Antworten.
- Das native Pop-up verarbeitet jetzt AppKit-Mausereignisse, bestätigt seine Web-Oberfläche und meldet Absturz bzw. Ladefehler. Diagnose steht privat in `astra-panel.log`. **Browser-Pop-up** ist ein zusätzlicher Weg ohne native AppKit-Brücke. Dieses Browserfenster ist nicht garantiert über anderen Apps angeheftet.
- Der Name Astra wird nun auch gespeichert und dem Sprachmodell übergeben, nicht nur angezeigt. Die Gesprächsanweisung wurde verkürzt und auf natürliche Antworten, aktuelle Aufträge und Umgang mit Scherzen ausgerichtet. Ein Prompt macht das kleine Textmodell nicht so leistungsfähig wie ChatGPT.

Echte Blender-Modelldateien für Auto, Haus und Roboter wurden in der Linux-Cloud erstellt, erneut geladen und auf Mesh-Objekte geprüft; auch Abbruch vor dem ersten Objekt wurde mit echtem Blender geprüft. Das bestätigt die Geometrieerzeugung, nicht die macOS-Fenstersteuerung. Native Mac-Ereignisse und das AppKit-Pop-up können hier weiterhin nicht auf echter Mac-Hardware geprüft werden. Vollständiges Bildschirmverständnis und präziser 3D-Fotonachbau sind nicht enthalten.

## Blender wurde heruntergeladen, wird aber nicht gefunden

Die Erkennung berücksichtigt jetzt auch Downloads, den Schreibtisch und geöffnete Installationslaufwerke. Versionierte App-Namen wie `Blender 4.5.app` werden zusätzlich über ihren internen Namen erkannt. Wenn macOS die App noch nicht registriert hat, versucht Jarvis den tatsächlichen App-Pfad. Für die Modellierung wird auch dort nach Blenders Programmdatei gesucht.

Eine heruntergeladene ZIP-/DMG-Datei allein ist noch keine startbare App. Auf dem Mac die Blender-DMG öffnen, `Blender.app` nach **Programme** ziehen und Blender einmal normal öffnen. Keine erneute Jarvis- oder KI-Installation erforderlich; macOS-Sicherheitsprüfungen werden nicht umgangen.

„Astrid“ wird als Spracherkennungsvariante von „Astra“ akzeptiert. Der Nutzername ist davon getrennt: **„Ich heiße Maxine“** speichert diesen Namen lokal dauerhaft; **„Wie heiße ich?“** liest ihn ohne KI-Raten aus. Der öffentliche Programmcode enthält keinen persönlichen Standardnamen.

## Stimme, Companion und Rendering

Antworten haben **Antwort anhören**. Gespräch beenden blockiert spätere Antworten nicht mehr dauerhaft. Explizites Stummschalten bleibt davon getrennt. Abgebrochene neuronale Spracherzeugung wird gezielt beendet; Filmexport-Ton wird davon nicht abgebrochen. Browser können Audio weiterhin blockieren; ein Klick auf Antwort anhören entsperrt es.

Das Begleitfenster hat Gespräch starten/beenden sowie ein Texteingabefeld. Die Bedienung wird an das geöffnete Hauptfenster übertragen. Dort müssen Mikrofon und Audio zuerst freigegeben sein. Das Gespräch darf weiterlaufen, solange das Begleitfenster aktiv meldet; Browser können Hintergrund-Spracherkennung trotzdem pausieren. Kein eigener nativer Spracherkenner wird behauptet.

**Vorschaubild rendern** vor dem Modellstart aktivieren: Blender erzeugt mit Kamera, Licht und CPU-Rendering eine PNG-Vorschau. **Renderbild anzeigen** zeigt das echte Ergebnis. Aktionen stoppen beendet den separaten Renderprozess. Sichtbare Mausbewegungen vorhandener move/click-Schritte verlaufen jetzt tatsächlich gleichmäßig und sind abbrechbar. Das ist weiterhin keine allgemeine autonome Bildschirmbedienung.

In der Werkstatt gibt es **Teamauftrag** mit 1–40 tatsächlichen Teilaufträgen. Ein lokales Modell verarbeitet sie nacheinander. Dies erzeugt Textentwürfe mit getrenntem Status; es sind keine 40 gleichzeitig rechnenden Modelle. Vollständige autonome Filmproduktion, allgemeiner Videoschnitt und vollständiger 3D-Fotonachbau sind in diesem Update nicht enthalten. Für den gewünschten Filmstil liegt bisher nur der Kanal @moritz.maaker vor; seine Videos wurden hier nicht überprüft.

Die gewünschte Anrede ist jetzt Master. Es werden keine neuen Modellgewichte heruntergeladen.

## Bildvorlagen: Arbeitsplatz-Inseln und Low-Poly-Filme

Die Werkstatt zeigt fünf farbige Inseln um einen zentralen Kern mit jeweils sechs anklickbaren Arbeitsplätzen. Ein unbesetzter Platz schläft. Belegte Plätze zeigen echte Auftragszustände; Anklicken öffnet Auftrag, aktuellen Schritt und Ergebnis. Bis zu 40 Teilaufträge bleiben im Verlauf sichtbar; es werden keine gleichzeitig arbeitenden Modelle erfunden.

STUDIO bietet im fertigen Auftrag **Filmstil → Low-Poly · animierte 3D-Bühne**. Die Bühne zeigt einen stilisierten Charakter, einen orangefarbenen Würfel und eine violette Terminal-Figur, mit Bewegung und Kamerafahrt. Szenentexte können geändert, Vorschau und echtes Video mit optionalem Sprecher exportiert werden. Mit angehängtem Produktfoto bleibt der Fotostil voreingestellt. Alles wird lokal ohne weitere Modelle gerendert. Das ist eine feste prozedurale Szene aus 3D-Grundkörpern, kein frei aus beliebigen Prompts generierter KI-Film und kein Nachbau der konkreten Figuren aus der Referenz.

Automatisches Vorlesen: Audio wird jetzt während des tatsächlichen Klicks bzw. Tastendrucks auf der Seite freigegeben, bevor die KI-Antwort abgewartet wird. Wenn der Browser Ton blockiert, gibt es eine einmalige Schaltfläche **Automatisches Vorlesen aktivieren** statt eines erforderlichen Klicks pro Nachricht. Diese aktiviert die automatische Ausgabe und hebt explizite Stummschaltung auf. Ein im Betrieb geschlossener oder unterbrochener Audiokontext wird neu gestartet. Das ersetzt keine Prüfung des Mac-Ausgabegeräts oder einer beschädigten Sprachinstallation.

## Gezielte Audio- und Bedienkorrektur

Die WAV-Stimme wird jetzt über einen sichtbaren normalen HTML-Audioplayer ohne Web-Audio-Filterkette abgespielt. Erzeugung und laufende Wiedergabe werden ausdrücklich unterschieden. Ein direkter Wechselknopf ergänzt die Sprachbefehle zu Astra/Jarvis; auch Asuka ist eine erkannte Anrede. Ältere Statusantworten können einen frisch vorbereiteten Ablauf nicht mehr deaktivieren. Mac-Lautsprecherausgabe und native Maussteuerung müssen weiterhin am Gerät geprüft werden.

## Kombinierte Modellaufträge und Wiederherstellung von Thorsten

„Öffne Blender und mach mir einen Lamborghini“ wird als Modellierungsauftrag erkannt, ebenso „Mach mir einen Lamborghini in Blender“. Der konkrete Entwurf ist ein vereinfachter Sportwagen mit vierzehn echten Bauteilen, keilförmiger Karosserie und Felgen; kein originalgetreuer Lamborghini. Bekannte Vorlagen starten nach dem ausdrücklichen Auftrag auf dem Mac direkt. Unbekannte KI-Entwürfe bleiben zur Prüfung offen. Erfolg zählt erst nach einer tatsächlich gespeicherten Blender-Datei. Die Desktop-Befehle funktionieren in Jarvis- und Astra-Modus.

**Maussteuerung testen** öffnet Finder und bewegt den echten Zeiger ohne Klicks oder Dateiveränderungen. Eine fehlende Bedienungshilfen-Freigabe erscheint als Fehler. Das ist ein Funktionstest, keine allgemeine visuelle App-Steuerung. Blender-Modelle entstehen über die Datenschnittstelle, nicht durch eine vorgetäuschte Mausbewegung.

Dieses Reparaturpaket wählt die vorhandene gültige natürliche Thorsten-Stimme wieder aus. Fehlt sie, bleibt die Ausgabe aus statt einer Ersatzstimme; neue Modelle werden nicht geladen.

## Drehbare 3D-Werkstatt und konkrete Eingabebefehle

Die neue perspektivische 3D-Werkstatt lässt sich mit Ziehen drehen und mit dem Mausrad zoomen. Figuren sind über ihre projizierte Position anklickbar und zeigen echte Aufträge; die Listenansicht bleibt zugänglich. Es werden lokale Polygone gerendert, keine Grafikpakete oder Modelle heruntergeladen.

„Bewege die Maus nach links in Finder“ und „Tippe Hallo Master in Notizen“ erzeugen konkrete geprüfte Eingabeabläufe. Die Richtung ist ein Anteil des Hauptbildschirms; es ist kein Erkennen von Schaltflächen. Für Notizen wird zuerst eine neue Notiz begonnen. Andere Apps erhalten Text in das aktive Eingabefeld der ausdrücklich genannten App. Native Maus/Tastatur benötigt Bedienungshilfen. Die Voransicht zeigt alle Schritte, bevor sie ausgeführt werden.

Das Update lädt keine neue Stimme automatisch. Auf den aktuellen ausdrücklichen Wunsch bleibt Thorsten fest ausgewählt; bei fehlendem Paket erscheint eine Einrichtungshilfe. Ein Browseraufruf des TikTok- und Instagram-Profils am 5. November 2026 endete jeweils mit ERR_TUNNEL_CONNECTION_FAILED. Der Inhalt wurde nicht gesehen. Netzfreigaben für www.tiktok.com und www.instagram.com sind als Cloud-Konfigurationsentwurf gespeichert; erst Prüfung/Speichern und Veröffentlichen in den Umgebungseinstellungen aktiviert sie.

## Audiohinweis im Stimmfenster

Der Audiohinweis wird in den aktiven Dialog verschoben, damit die Browser-Dialogebene seine Knöpfe nicht blockiert. **Audiohinweis schließen** blendet ihn für diese Sitzung aus; erneute Fehler öffnen ihn nicht sofort wieder. Der Aktivierungsknopf zeigt Fortschritt und wird bei einem Fehler wieder freigegeben. Ein nicht antwortender Wiedergabestart meldet nach vier Sekunden einen Fehler. Die Stimmwahl bleibt unverändert.

## Notizen ohne altes 3D-/Spielthema

**„Erstelle eine Notiz: Morgen Milch kaufen“** ist ein deterministischer Notes-Auftrag. Der Inhalt nach dem Doppelpunkt wird unverändert als Text behandelt, auch wenn er Wörter wie 3D oder Videospiel enthält. Ohne Inhalt wird danach gefragt. Auf dem Mac startet der ausdrückliche vollständige Auftrag automatisch. Eine feste AppleScript-Funktion legt eine neue Notiz im Ordner **Jarvis** in Apple Notizen an. Erfolg wird nur mit der von Notizen bestätigten Kennung gemeldet. Keine KI entscheidet über den Inhalt oder führt generierten Code aus.

macOS kann zuerst die Freigabe **Datenschutz & Sicherheit → Automation → Terminal/Python → Notizen** verlangen. Ein verfügbarer Standardaccount in Notizen wird benötigt. Bei verweigerter Freigabe, Timeout oder fehlender Kennung meldet Jarvis einen Fehler, keine erfolgreiche Ausführung. Diese native Mac-Ausführung wurde in der Linux-Cloud nicht live geprüft; Parser, Prozessaufruf, Fehlermeldungen und Ablauf sind kontrolliert getestet.

Neue eigenständige Arbeitsaufträge erhalten keinen alten Gesprächsverlauf als Modellkontext. Der sichtbare Verlauf und gespeicherte Namen bleiben erhalten. Ein ausdrücklich fortgesetzter Auftrag mit „weiter“, „dazu“ oder „darauf“ kann weiter Kontext nutzen.

## Chat löschen und Rückfragen

„Chat löschen“ entfernt alle Chatverläufe, den gemerkten Namen und offene Rückfragen. Gespeicherte Dateien, bereits erstellte Notizen und Einstellungen bleiben erhalten. Eine verspätete KI-Antwort darf den gelöschten Kontext nicht zurückschreiben.

„Erstelle eine Notiz“ fragt nach dem Inhalt. Antworte einfach „morgen Milch kaufen“; der nächste Schritt erstellt diese Notiz. „Abbrechen“ verwirft die Rückfrage. Ebenso: „Öffne eine App“ → „Spotify“ oder „Öffne eine Webseite“ → „youtube.com“. „Tippe Hallo“ fragt nach der Ziel-App. Auf dem Mac benötigen native Aktionen die entsprechenden macOS-Berechtigungen.

## Start mit einem Klick

„Auftrag starten“ ist auch ohne vorbereiteten Ablauf benutzbar. Gib deinen Auftrag in das Textfeld ein und klicke darauf: Der Auftrag wird validiert, bei Bedarf vorbereitet und gestartet. Ein geänderter Text nach einem fertigen Auftrag aktiviert den Knopf wieder. Leere Eingaben zeigen einen Hinweis; Fehler bleiben sichtbar und können nach Behebung erneut versucht werden. Während Vorbereitung oder Ausführung werden doppelte Starts verhindert.

## Handy und Home-Bildschirm

Am Mac „Handy verbinden“ öffnen und der Anleitung für das eigene HTTPS-Zertifikat folgen. Mac eingeschaltet lassen; beide Geräte brauchen dasselbe WLAN. Nach erfolgreicher Kopplung in Safari: Teilen → Zum Home-Bildschirm → Hinzufügen. Der neue Knopf „App installieren“ erklärt die Schritte für iOS und Android. Dies ist kein öffentlicher Internet-Zugang.

Falls das neue Home-Symbol eine separate Sitzung verwendet, dort einen neuen Kopplungslink vom Mac einfügen und „Mit Mac verbinden“ tippen. Kopplungen bleiben 30 Tage gespeichert, auch bei normalem Jarvis-Neustart; „Verbindung beenden“ am Mac widerruft sie. Nur Hashes der Sitzungsschlüssel liegen im privaten Datenordner. Bei geänderter WLAN-Adresse muss der Link bzw. das Home-Symbol erneuert werden. Mac-Steuerung bleibt auf den direkt am Mac geöffneten Browser beschränkt; auf dem Handy gibt es dafür eine klare Meldung.

## Werbeclips mit eigener Figur und Thorsten

Die Low-Poly-Bühne zeigt eine eigene mechanische Jarvis-Figur mit cyanfarbenem J-Kern, Metallgehäuse, sechseckigem Podest und Lichtbegleitern. Die frühere Dreiergruppe aus Stilvorlagen ist entfernt. Produktfotos werden nur im ausdrücklich ausgewählten Fotostil angezeigt.

„Thorsten-Sprecher“ und „Untertitel“ sind standardmäßig aktiv; Wünsche wie „ohne Ton“ bzw. „ohne Untertitel“ schalten die jeweilige Option zunächst aus. Vorschau und Export verwenden dieselben lokal erzeugten Thorsten-Sätze. Untertitel und Mundlicht folgen den tatsächlichen Satzlängen. Sprechertext lässt sich vor dem Export bearbeiten. Fehlende Sprachdaten werden als Fehler angezeigt; es wird kein stiller Clip als erfolgreicher Sprecher-Export ausgegeben.

## Aktuelle Fragen mit Websites

Fragen zu Kino, Essen, Öffnungszeiten oder aktuellen Preisen verwenden einen öffentlichen Web-Leseweg ohne Konto oder API-Schlüssel. Beispiel: „Welche Filme ab 12 kann ich jetzt im Cineplex Neufahrn ansehen?“ oder „Wo kann ich in München günstig Pizza für drei Personen essen?“ Fehlende Angaben zu Ort, Alter, Personen und Budget werden nacheinander erfragt; normale Antworten wie „zwölf“ oder „München“ genügen. Der Standort wird nicht automatisch ermittelt.

Jarvis zeigt Quellen und fragt, ob die Website geöffnet werden soll. „Ja bitte“ versucht sie zu öffnen; der Link-Knopf „Website öffnen“ funktioniert auch bei blockierten Pop-ups und auf dem Handy. FSK-/Zeitfilter benötigen datierte strukturierte Vorstellungen des Kinos. Restaurantzeiten und Menüpreise werden nur übernommen, soweit die Seite sie lesbar veröffentlicht; tatsächliche Verfügbarkeit, Qualität, Feiertagszeiten oder ein garantiert billigstes Angebot sind damit nicht belegt. Gesperrte oder rein dynamische Seiten ergeben eine ehrliche Auskunft mit Quellenlink.

Unter Einstellungen → „Öffentliche Websuche erlauben“ lässt sich die Funktion abschalten. Bei aktivierter Suche verlassen Suchbegriffe und mitgeteilte Ortsangaben den Mac in Richtung öffentlicher Webseiten; Schlüssel und Chatverlauf werden nicht mitgeschickt. Allgemeine Fragen bleiben beim gewählten Sprachmodell, mit natürlicherer Gesprächsanweisung und der eingestellten Anrede. Die kleine lokale KI wird dadurch nicht zu ChatGPT.

## 11. November: mobile Ansicht, Auftragstafel und Websites

Gekoppelte Handys und Tablets erhalten unter `/` eine eigenständige, schlanke Ansicht ohne 3D-Canvas oder Worker. Sie bietet Chat, Thorsten-Wiedergabe, Sprachaufnahme soweit Safari sie unterstützt, Quellenlinks und eine Live-Auftragsliste. `/mobile` ist auch am Mac ein Ausweichweg; `/index.html` öffnet die vollständige Ansicht. Ein unabhängiger Start-Hinweis bietet den Ausweichweg an, wenn das Haupt-JavaScript nicht startet. Ein weißer Bildschirm am konkreten iPhone ist dadurch nicht vor Ort diagnostiziert; TLS-Zertifikatsvertrauen und lokale Netzwerkfreigaben bleiben erforderlich.

Ein zuvor eingeschalteter oder gültig gekoppelter Heimnetz-Zugang wird beim normalen Serverstart wieder gestartet. Der Link nutzt nach Möglichkeit den lokalen Mac-Namen (`.local`), zusätzlich gibt es einen IP-Ersatzlink. „Verbindung beenden“ widerruft Kopplungen und deaktiviert den automatischen Start. Mac und Geräte müssen weiter im selben WLAN sein, der Mac muss laufen.

„Erstelle eine Website für …“ startet nun ohne Agentennamen einen tatsächlichen Auftrag. Es wird eine eigenständige HTML-Datei erstellt, in einer Sandbox angezeigt und zum Download angeboten. Bei fehlerhafter JSON-Antwort gibt es einen ausdrücklich bezeichneten einfachen Grundentwurf aus dem gelieferten Text. Keine automatische Veröffentlichung, kein beliebiger KI-Programmcode. Die Auftragstafel zeigt gespeicherte Phasen und Ergebnisse, keine simulierten Prozentzahlen. „Erstelle einen Werbeclip …“ ist ebenfalls ohne Agentennamen möglich.

Astra: „Mauszugriff prüfen“ zeigt die echte Bedienungshilfen-Freigabe. Sie wird vor Maus-/Tastaturstarts geprüft. „Klicke auf Speichern in Notizen“ sucht die exakt benannte Schaltfläche über die macOS-Oberfläche und bewegt/klickt nur bei eindeutigem Treffer. System Events kann eine zusätzliche Automation-Freigabe brauchen. Das Ausführungsprotokoll zeigt gestartete und bestätigte Eingabeschritte. Ein sichtbarer Klick ist keine Bestätigung, dass eine beliebige komplexe Aufgabe fertig ist. Native Mac-Maussteuerung und iOS-Hardware bleiben hier ungeprüft.

## Filmfenster, Nachrichten und selbstständiges Mini-Fenster

Allgemeine Filmtipps öffnen eine lokale Kartenansicht mit Beschreibungen und FSK. Das sind kuratierte Empfehlungen, keine bestätigten aktuellen Kino- oder Streaming-Angebote. Kino-/Webantworten erscheinen in einer lesbaren Ergebnisansicht statt als unbeschriftete Suchlinks im Chat. Die Originalseite ist über einen benannten externen Link erreichbar; fremde Webseiten werden wegen ihrer Einbettungsregeln nicht als angeblich vollständige Browseransicht eingebunden. Einfache Rechnungen wie „eins plus eins“ lösen offene Web-Rückfragen ab und werden direkt berechnet.

„Lies mir Nachrichten aus Deutschland vor“ filtert sowohl Anzeige als auch Sprechertext nach Deutschland. Im Weltfenster gibt es „Meldung vorlesen“ und „Ausgewählte Nachrichten vorlesen“. Fehlende bzw. ältere Quellen bleiben erkennbar. Eine ausdrückliche Vorlese-Anfrage funktioniert auch bei ansonsten ausgeschalteter automatischer Stimme.

Das Browser-Pop-up unter Astra sendet Text und Sprache selbst an Jarvis und spielt Thorsten selbst ab. Der große Jarvis-Tab kann geschlossen werden; der Python-Server muss weiterlaufen. „Gespräch starten“ startet die Spracherkennung dieses Fensters. Der Browser kann Mikrofonberechtigungen verlangen und Hintergrundaufnahme einschränken. Das native schwebende WKWebView-Fenster bietet auf manchen macOS-Versionen keine Web-Spracherkennung: Dann ist Schreiben mit eigener Thorsten-Ausgabe möglich; zum Sprechen das Browser-Pop-up verwenden. Diese Grenze wird im Fenster angezeigt. „Stopp“ bzw. „Aktionen stoppen“ stoppt den Desktopablauf, „Reden stoppen“ nur die Stimme.

Astra wartet nach dem App-Öffnen kurz auf die tatsächliche Vordergrund-App. Bei einer anderen App wird keine Eingabe gesendet. „Mausfreigabe am Mac öffnen“ öffnet die passende Systemeinstellung; eine Freigabe muss der Nutzer selbst erteilen.

## Aeris – kompaktes Spatial Studio

Unter `/aeris` stehen ein prozedural gezeichneter goldener Energiekern, ein eigener Moduswechsel zu Jarvis/Astra und eine feste Arbeitsfläche ohne langen Seitenlauf zur Verfügung. Die Navigation wechselt zwischen Kern, 3D-Studio und Kamera. Chat, Gesten, Armregler, VR/MR und Einstellungen öffnen durchscheinende Fenster; nur deren Inhalt scrollt bei Bedarf. Kleine Bildschirme und reduzierte Bewegung werden berücksichtigt. Thorsten bleibt die Stimme und wird auf dem Mac erzeugt.

Der virtuelle Manipulator besitzt modellierte Gelenke, Gehäuse, Schienen und Greifer. Ziehen dreht die Ansicht, die Armregler bewegen die Gelenke. Bis zu 30 Würfel lassen sich erstellen, entfernen und als tatsächliche OBJ-Geometrie exportieren. Der Arm ist kein Bestandteil des Exports und nicht mit echter Hardware verbunden.

## Kamera, Fingertracking und einstellbare Gesten

In der Kameraansicht startet „Kamera einschalten“ nur die Vorschau. Erst „Handtracking einschalten“ überträgt kleine JPEG-Frames an den eigenen Mac (höchstens ca. 8 pro Sekunde, langsamer bei längerer Auswertung). Apple Vision erkennt dort bis zu zwei Hände mit je bis zu 21 Fingergelenken sowie optional Schulter, Ellbogen und Handgelenk. Voraussetzung: Mac-Server auf macOS 11 oder neuer; sichere Verbindung und Kamerafreigabe am aufnehmenden Gerät. Kein zusätzliches Modell und kein externer Bilddienst. Frames werden nicht gespeichert. Die native Vision-Erkennung muss auf einem echten Mac überprüft werden; automatisierte Tests verwenden kontrollierte Kamerabilder und Gelenkdaten.

Daumen und Zeigefinger zusammenführen greift einen nahen virtuellen Würfel; die Hand bewegt ihn in einer 2D-Ebene. Finger öffnen legt ihn ab. Bei unsicherer oder verlorener Hand wird der Griff gelöst. Ein Würfel wird beim ersten Trackingstart als greifbares Objekt bereitgestellt. Fingerlinien und ein Greifcursor erscheinen über dem Kamerabild. Das ist kein 3D-Scan und keine Tiefenmessung. Optional erkannte Armgelenke bewegen zusätzlich den virtuellen Arm.

Unter „Gesten“ lassen sich offene Hand, zwei Finger (Zeige-/Mittelfinger) und Faust den Aktionen Dialog öffnen, Studio öffnen, Schnee an/aus, Stimme stoppen oder keiner Aktion zuordnen. Die Zuordnung wird auf dem jeweiligen Gerät gespeichert. Eine Geste muss kurz ruhig gehalten werden; dieselbe gehaltene Geste löst nur einmal aus. Pinch zum Greifen funktioniert unabhängig vom Schalter für zusätzliche Gestenaktionen. Schnee ist ein lokaler dekorativer Effekt, keine Veränderung anderer Apps. Trackingstopp, Kamerastopp, Hintergrundwechsel und Verlassen der Seite stoppen weitere Bildübertragung und lösen den Griff.

## VR und Mixed Reality

Im VR-Fenster startet Aeris auf unterstützten Quest-Browsern WebXR. Bei eingeschaltetem „Umgebung sichtbar lassen“ wird zuerst `immersive-ar` geprüft. Falls verfügbar, wird mit transparentem Hintergrund gerendert; echte Umgebungsdurchsicht hängt zusätzlich vom Blendmodus und der Freigabe der Brille ab. Sonst startet `immersive-vr` mit einer virtuellen Umgebung. Die Fenster und Arbeitsfläche sind in beiden Modi durchscheinende goldene Flächen mit dünnen Kanten. Passthrough ist damit ausdrücklich nicht auf allen Meta-Modellen garantiert.

WebXR-Hand-Pinch oder Controller-Trigger greift nahe virtuelle Würfel, Handbewegung verschiebt sie, Loslassen/Poseverlust legt sie ab. Die sichtbare Armform wird aus Handpositionen konstruiert und ist keine Messung des tatsächlichen menschlichen Ellbogens. Export speichert die VR-Würfel als tatsächliche OBJ-Datei. Die Brille beendet die Sitzung über ihr Systemmenü. Automatisierte Tests prüfen VR- und MR-Sitzungen mit einer kontrollierten Laufzeit; keine physische Brille wurde hier getestet.

## Automatischer Oberflächenspeicher

Der störende Vorbereitungsschritt entfällt. Bei sicherer Verbindung speichert Aeris seine kleine Programmoberfläche automatisch im Browser. 3D-Regler und OBJ-Export sind danach ohne Mac nutzbar; Browser können den Cache später entfernen. API-Antworten, Chatverläufe, Kamerabilder und Schlüssel werden nicht zwischengespeichert. Offline-KI, Thorsten direkt auf iOS/iPadOS und Handtracking ohne Mac sind weiterhin nicht eingerichtet.

Ein echter Roboterarm ist nicht angeschlossen. Dafür fehlen Hersteller, Modell, Schnittstelle, Arbeitsraum und Kalibrierung. Kamera und WebXR verändern ausschließlich virtuelle Szenendaten.

## Verbesserte Armsteuerung und Zieltraining

Aeris ordnet im Modus „Automatisch“ den Körperarm anhand der Nähe des Handgelenks zur erkannten Hand zu, statt grundsätzlich rechts zu wählen. In den Armreglern gibt es Spiegelung und einstellbare Glättung. „Arm kalibrieren“ setzt die gerade erkannte Haltung als Ausgangshaltung; weitere Schulter-/Ellbogenbewegungen verändern die Gelenke des virtuellen Studioarms. In der Kameraansicht wird der virtuelle Arm weiterhin an den gemessenen 2D-Körperpunkten ausgerichtet. Fehlen Körperpunkte, folgt der virtuelle Greifer über eine berechnete Zweigelenkbewegung der Handposition. Das ist keine Tiefenmessung und keine echte Motorsteuerung. Die getrennte Anzeige für Hand und Körperarm macht unvollständige Erkennung sichtbar. Tests mit kontrollierten Punkten prüfen Zuordnung und Bewegung; die tatsächliche Erkennungsqualität auf dem Mac bleibt geräteabhängig.

„Zieltraining“ zeigt einen goldenen Ablagekreis. Einen Würfel per Pinch aufnehmen, in den Kreis bewegen und die Finger öffnen zählt einen tatsächlichen Treffer und setzt ein neues Ziel. Bloßer Trackingverlust zählt nicht als Ablage.

## Jarvis-Videoanruf ohne Bildspeicherung

In Jarvis öffnet „Videoanruf“ eine eigene Ansicht mit einem prozedural gezeichneten, fiktiven Android-Avatar und lokaler Kameravorschau. Der Mund bewegt sich nur während tatsächlicher Tonwiedergabe, vereinfacht anhand der Wiedergabezeit; keine phonemgenaue Lippensynchronisation. Thorsten bleibt die Stimme. „Anruf starten“ fragt Kamera und die vorhandene Gesprächsfunktion nach Mikrofonfreigabe. Browser-Spracherkennung kann Audio online verarbeiten; sie ist nicht garantiert lokal. Schreiben funktioniert ebenfalls. Auf der mobilen Seite führt „Videoanruf mit Jarvis öffnen“ zur vollständigen Ansicht mit geöffnetem Anruffenster.

Nur bei einer gestellten Frage und aktiviertem Schalter zur Bildauswertung wird ein kleines JPEG an den eigenen Jarvis-Server geschickt. Keine kontinuierliche Videoübertragung, keine Aufnahme und keine Gesichtserkennung oder Gesichtsvorlage. Apple Vision liefert lokal unsichere Objektkategorien und erkannten Text. Die bestehende lokale Text-KI (llama.cpp/Ollama) erhält ausschließlich diese Hinweise, keine Bildpixel. Sie besitzt dadurch kein allgemeines Bild- oder Videoverständnis. Keine Cloud-Ausweichanfrage und kein neuer Modelldownload. Ohne lokale Text-KI bzw. unterstütztes Apple Vision wird die Einschränkung angezeigt.

Die Schnittstelle `/api/video-call` verwendet ausschließlich den flüchtigen Gesprächskontext der Oberfläche und den lokalen Modelltransport. Sie ruft keinen normalen Chat-/Agenten-Speicherweg auf. Bilder, Analysehinweise und Videoanruf-Dialog werden nicht in SQLite oder Bilddateien gespeichert. Nach Ende werden Kameraspuren, Mikrofon, flüchtiger Anrufkontext und offene Browser-Anfragen beendet; verspätete Antworten werden verworfen. Bereits gestartete lokale Modellberechnung kann serverseitig noch auslaufen. Hintergrundwechsel und Schließen beenden den Anruf ebenfalls. Ein normaler Text-Chat außerhalb des Anrufs behält seine bisherigen Speicherregeln.

Automatisierte Browserprüfungen verwenden künstliche Kamera-, Bildbefund- und Audiodaten und prüfen Aufnahmefreigabe, keine Vorschau-Uploads, Bild pro Frage, tatsächliche Audiowiedergabe, Text ohne Kamera, fehlende Datenbankeinträge sowie Geräte-/Anfrageabbruch. Ein physischer Mac mit Apple Vision wurde hier nicht getestet.
