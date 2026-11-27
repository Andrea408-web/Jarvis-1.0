# Techniklabor und Aeris

Dieses gemeinsame Update ersetzt den sichtbaren Einstieg ins alte Baulabor durch das Techniklabor und gestaltet den bisherigen dritten Assistenten als Aeris neu. Vorhandene gespeicherte Projekte werden nicht gelöscht. Es wird kein neues KI-Modell geladen.

## Techniklabor

Öffne „Techniklabor“ in Jarvis oder sage „Öffne das Techniklabor“. Drei bereitgestellte Startprojekte sind ein Papp-Handyständer, ein mechanischer Pappgreifer und eine Halterung/Diffusor-Idee für ein bereits fertig aufgebautes USB-Lichtmodul. Jede Anleitung zeigt Material, Werkzeug und jeweils einen Bauschritt. „Schritt erledigt“ ist deine eigene Markierung, keine Prüfung durch Kamera oder KI.

Über „Weiter“, „Zurück“ und die Schrittleiste navigierst du. Fragen werden mit dem aktuellen Projekt und Schritt an die vorhandene lokale KI gestellt. Du kannst auch eine eigene Idee besprechen. Dafür wird nicht automatisch eine beliebige, fertig geprüfte Bauanleitung oder ein 3D-Modell erzeugt. Die bereitgestellten Entwürfe sind Prototypen und müssen vor Ort geprüft werden.

## Aeris

Öffne „Aeris“ in Jarvis oder auf derselben Jarvis-Adresse den Pfad `/aeris`. Alte Verknüpfungen mit `/iris` bleiben kompatibel. Die alte VR-Ansicht unter `/quest` bleibt separat erhalten.

Aeris hat einen eigenen Energiekern, normales Gespräch, Thorsten-Ausgabe, ausdrückliche lokale Notizen und einen Zugang zum Techniklabor. Die normale Ansicht startet keine 3D-Werkstatt, Kamera oder Spracherkennung. Jarvis und Astra erreichst du oben über die Modustasten.

## Sprechen und Daten

Aktiviere die Freigabe für Browser-Spracherkennung und tippe auf „Mit Aeris sprechen“ beziehungsweise „Mit Jarvis sprechen“. Erkannte Sprache wird dann automatisch als Nachricht gesendet. Der Sprachdienst des Browsers kann Internet verwenden. Thorsten benötigt die vorhandene Einrichtung auf dem verbundenen Rechner; es wird keine Roboter-Ersatzstimme gewählt.

Gespräche in diesen beiden neuen Bereichen bleiben im Arbeitsspeicher. „Chat löschen“, Stoppen und Schließen beenden die entsprechenden laufenden Anfragen beziehungsweise Spracheingaben. Nur ausdrücklich gespeicherte Aeris-Notizen bleiben in diesem Browser erhalten und können dort gelöscht werden. Die neue Oberfläche verbessert nicht automatisch die Leistungsfähigkeit des vorhandenen kleinen Sprachmodells.

## Aeris Handtracking wieder erreichbar

Aeris hat einen eigenen Handtracking-Knopf und versteht „Öffne Handtracking“. Die bestehende räumliche Kamera-/Gestenansicht öffnet sich darin, ohne den laufenden Aeris-Chat zu verwerfen. Kamera und Tracking werden erst über ihre ausdrücklichen Startknöpfe eingeschaltet. Beim Schließen wird die Unteransicht entladen und gibt Kamera/Tracking frei. Die Erkennung nutzt die vorhandene Mac-Vision-Anbindung; ohne erreichbaren geeigneten Mac ist diese Fingererkennung nicht verfügbar.

Verbundenes Aeris sowie Handy-/iPad-Chat können allgemeine Web-Recherche und den schreibgeschützten Systemcheck jetzt direkt über ihre bisherige Chat-Schnittstelle anfordern. Es werden keine Mac-Steuerungsrechte erweitert und keine Geräte-Chatverläufe am Server neu gespeichert. Quellen sind in der Antwort anklickbar. Ohne Mac-Verbindung steht dieser Rechercheweg nicht zur Verfügung.

## Farbmodi und Holokern

Jarvis ist gelb, Astra bleibt blau und Aeris ist grün. Im eingebetteten Aeris-Handtracking ist „Holokern steuern“ eingeschaltet: offene Hand vergrößert den Kern, geschlossene Hand/Pinch verkleinert ihn. Näher an die Kamera gehaltene offene Hände vergrößern ihn weiter. Die Größe ist geglättet und begrenzt; bei verlorener oder zu unsicherer Handerkennung verschwindet die Steuerung. Zum Verwenden der bisherigen Handgesten (Dialog/Schnee/Studio) den Holokern-Schalter ausschalten. Es werden ausschließlich virtuelle Inhalte gesteuert.

Die bestehende Mac-Vision-Erkennung bleibt erhalten, kein weiteres Modell wird geladen. Kleine Landmarken-Schwankungen werden gedämpft; Handdetektionen mit einer gemeldeten Konfidenz unter 0,4 werden nicht verwendet. Die echte Erkennungsqualität hängt weiterhin von Licht, Sichtbarkeit der Finger und der Mac-Kamera ab.

Recherche: Die allgemeine Websuche wurde hier vom Netzwerk mit HTTP 403 blockiert. Als direkt zugängliche offizielle Quelle wurde die [HandLandmarker-Implementierung von Google](https://github.com/google-ai-edge/mediapipe/blob/master/mediapipe/tasks/web/vision/hand_landmarker/hand_landmarker.ts) gelesen (Erkennungs-, Anwesenheits- und Tracking-Schwellen). MediaPipe wird nicht installiert; die Quelle ist keine Bestätigung der Qualität der vorhandenen Apple-Vision-Erkennung.
