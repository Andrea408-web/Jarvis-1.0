# Musik und Videos direkt in Jarvis

Dieses gemeinsame Update enthält den Player zusammen mit dem neuen Jarvis-HUD, Techniklabor, Aeris und den bisherigen Funktionen. Es lädt keine Sprach- oder KI-Modelle nach.

## Öffnen und sprechen

Öffne „Jarvis Apps → Musik & Video“. Oder sage beziehungsweise schreibe „Spiel Musik“, „Spiel Rock Antenne“, „Spiel ein Lied von …“ oder „Zeig mir ein Video über …“. Ein vorhandener YouTube-Link kann mit „Spiel dieses Video https://…“ geöffnet werden. Diese Befehle funktionieren auch aus dem Live-Gesprächsmodus; dessen Erkennung pausiert beim Öffnen des Players. Für diese Befehle wird kein Sprachmodell angefragt. Die vorhandene freiwillige Browser-Spracherkennung bleibt Voraussetzung, wenn du sprechen möchtest.

„Spiel Musik“ startet einen Verbindungsversuch zu ANTENNE BAYERN. Alternativ ist ROCK ANTENNE auswählbar. Das ist öffentliches Webradio mit dem Programm und gegebenenfalls Werbung des Senders, kein frei wählbarer Streaming-Katalog. Die Verfügbarkeit hängt von Internetverbindung, Sender und Browser ab. Bei gesperrtem Autoplay zeigt Jarvis den Hinweis, einmal „Abspielen“ anzutippen; ein Verbindungsversuch wird nicht als erfolgreiche Wiedergabe ausgegeben.

## Videos und Titelsuche

Ein gültiger YouTube-Link wird im eingebetteten YouTube-Player innerhalb von Jarvis geöffnet. Unterstützt werden normale Video-, Kurz-, Shorts- und Live-Links mit einer Video-ID. YouTube wird erst beim Öffnen eines Videos kontaktiert; es gibt keine automatische Anmeldung und keinen Download der Videodatei. Manche Videos benötigen Anmeldung oder lassen keine Einbettung zu. Dann kannst du ein anderes Video wählen oder den angezeigten YouTube-Link selbst öffnen. Das umgeht keine Zugangsbeschränkungen.

Bei einem Titel sucht der verbundene Jarvis-Server öffentlich auffindbare YouTube-Treffer über eine öffentliche Suchseite und zeigt bis zu fünf Ergebnisse. Wähle den passenden Treffer zum Abspielen. Dafür wird keine KI und kein API-Schlüssel benötigt. Suchbegriffe werden dem Suchdienst übermittelt, aber nicht als neue Wiedergabeliste oder Suchhistorie in Jarvis gespeichert. Ohne erreichbaren Server oder Suchdienst kann weiterhin ein direkter YouTube-Link eingefügt werden. Es werden keine erfundenen Video-IDs oder Titel erzeugt.

## Eigene Dateien und Bedienung

„Eigene Musik oder Videos auswählen“ erlaubt mehrere Dateien oder du ziehst Dateien in den Player. Bis zu 32 ausgewählte Dateien bilden eine Warteschlange im Arbeitsspeicher. Sie werden über lokale Blob-URLs abgespielt, weder an den Jarvis-Server noch an einen Anbieter hochgeladen. Der Browser muss den enthaltenen Audio-/Video-Codec unterstützen; die Dateiendung allein reicht nicht. Bei einem nicht unterstützten Format zeigt der Player eine Fehlermeldung. Ein verdeckter Konvertierungs- oder Downloadvorgang findet nicht statt.

Pause, Abspielen, Stopp und „Nächste Datei“ steuern die Wiedergabe. Der native Video-/YouTube-Player bietet außerdem seine eigenen Regler. Mit „Player verkleinern“ bleibt eine kleine Leiste im Jarvis-Fenster. Über sie kannst du wieder öffnen oder stoppen. Schließen beendet die Wiedergabe und verwirft die Dateiauswahl; ein Seitenwechsel beendet sie ebenfalls. Browser-/Betriebssystemregeln können Hintergrundwiedergabe unterbrechen.

Beim Öffnen pausiert Jarvis seine bisherige Mikrofon- und Klatschsteuerung, damit Musik keine neuen Aufträge auslöst. Im Player gibt es unter „Sprachsteuerung & Hinweise“ eine eigene freiwillige Spracherkennung für jeweils einen Befehl: „Pause“, „Weiter“, „Musik stoppen“ oder eine neue Videosuche. Dabei wird die Medienwiedergabe zuerst angehalten. Die Browser-Spracherkennung kann Audio online verarbeiten. Alle Knöpfe funktionieren auch ohne Sprachfreigabe.

## Prüfung

Lokales Audio und Video, Warteschlange, Pause, Fortsetzen, Verkleinern, Stoppen sowie die Befehlswege werden im echten Browser mit erzeugten Testdateien geprüft. Externe Radio- und YouTube-Antworten sowie Suchergebnisse werden in den Tests kontrolliert simuliert. Eine erfolgreiche echte Senderverbindung oder Wiedergabe jedes YouTube-Videos wird dadurch nicht belegt.
