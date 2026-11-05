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

Der Installer verändert die gewählte Stimme nicht mehr automatisch und lädt keine neue Stimme. Ein Browseraufruf des TikTok- und Instagram-Profils am 5. November 2026 endete jeweils mit ERR_TUNNEL_CONNECTION_FAILED. Der Inhalt wurde nicht gesehen. Netzfreigaben für www.tiktok.com und www.instagram.com sind als Cloud-Konfigurationsentwurf gespeichert; erst Prüfung/Speichern und Veröffentlichen in den Umgebungseinstellungen aktiviert sie.

## Audiohinweis im Stimmfenster

Der Audiohinweis wird in den aktiven Dialog verschoben, damit die Browser-Dialogebene seine Knöpfe nicht blockiert. **Audiohinweis schließen** blendet ihn für diese Sitzung aus; erneute Fehler öffnen ihn nicht sofort wieder. Der Aktivierungsknopf zeigt Fortschritt und wird bei einem Fehler wieder freigegeben. Ein nicht antwortender Wiedergabestart meldet nach vier Sekunden einen Fehler. Die Stimmwahl bleibt unverändert.

## Notizen ohne altes 3D-/Spielthema

**„Erstelle eine Notiz: Morgen Milch kaufen“** ist ein deterministischer Notes-Auftrag. Der Inhalt nach dem Doppelpunkt wird unverändert als Text behandelt, auch wenn er Wörter wie 3D oder Videospiel enthält. Ohne Inhalt wird danach gefragt. Auf dem Mac startet der ausdrückliche vollständige Auftrag automatisch. Eine feste AppleScript-Funktion legt eine neue Notiz im Ordner **Jarvis** in Apple Notizen an. Erfolg wird nur mit der von Notizen bestätigten Kennung gemeldet. Keine KI entscheidet über den Inhalt oder führt generierten Code aus.

macOS kann zuerst die Freigabe **Datenschutz & Sicherheit → Automation → Terminal/Python → Notizen** verlangen. Ein verfügbarer Standardaccount in Notizen wird benötigt. Bei verweigerter Freigabe, Timeout oder fehlender Kennung meldet Jarvis einen Fehler, keine erfolgreiche Ausführung. Diese native Mac-Ausführung wurde in der Linux-Cloud nicht live geprüft; Parser, Prozessaufruf, Fehlermeldungen und Ablauf sind kontrolliert getestet.

Neue eigenständige Arbeitsaufträge erhalten keinen alten Gesprächsverlauf als Modellkontext. Der sichtbare Verlauf und gespeicherte Namen bleiben erhalten. Ein ausdrücklich fortgesetzter Auftrag mit „weiter“, „dazu“ oder „darauf“ kann weiter Kontext nutzen.

## Chat löschen und Rückfragen

„Chat löschen“ entfernt alle Chatverläufe, den gemerkten Namen und offene Rückfragen. Gespeicherte Dateien, bereits erstellte Notizen und Einstellungen bleiben erhalten. Eine verspätete KI-Antwort darf den gelöschten Kontext nicht zurückschreiben.

„Erstelle eine Notiz“ fragt nach dem Inhalt. Antworte einfach „morgen Milch kaufen“; der nächste Schritt erstellt diese Notiz. „Abbrechen“ verwirft die Rückfrage. Ebenso: „Öffne eine App“ → „Spotify“ oder „Öffne eine Webseite“ → „youtube.com“. „Tippe Hallo“ fragt nach der Ziel-App. Auf dem Mac benötigen native Aktionen die entsprechenden macOS-Berechtigungen.
