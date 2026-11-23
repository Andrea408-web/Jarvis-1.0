# Anrufe und Gesprächsmenü

Öffne „Jarvis Apps“ und dann „Telefon“ in Jarvis am Mac, iPad oder Handy. Im selben App-Menü findest du Techniklabor und Aeris. Für normale Telefonnummern wählst du einen Kontakt oder gibst eine Nummer ein und bestätigst die Übergabe an Telefon/FaceTime. Es wird kein Anruflink benötigt. Der Browser öffnet direkt den lokalen Telefon-Link; die gewählte Nummer wird dabei nicht an den Jarvis-Server oder die KI geschickt. Kontaktauswahl aus Apple Kontakte ist eine gesonderte, ausdrücklich ausgelöste Abfrage am Mac. Jarvis behauptet dabei keine bestehende Verbindung. Die Web-App kann normale Apple-Telefonate weder abhören noch ihren Ton ersetzen. Apple kann eigene Anruflisten führen.

## Gespräch mit KI vorbereiten

Schreibe in „Was möchtest du sagen?“ kurz dein Ziel und tippe „Formulierung mit KI vorbereiten“. Nur dieser Text wird an die bereits eingerichtete KI übergeben; Kontaktname und Nummer aus den Kontaktfeldern werden nicht mitgesendet. Ein neuer Gesprächsverlauf wird dafür nicht gespeichert. Der Entwurf bleibt editierbar im Telefonfenster und wird beim Schließen verworfen. Diese Vorbereitung ist kein autonomer Telefonanruf: Beim normalen Telefonat sprichst du selbst. Für diesen Weg wird nur die vorhandene lokale llama.cpp-/Ollama-KI angefragt; externe KI-Anbieter werden zurückgewiesen.

## Web-Anruf mit Jarvis

Unter „Einrichtung & optionale Web-Gespräche“ führt der optionale Browser-Anruf zu `/web-call`. Dies ist ein eigener Anruf zwischen zwei Browsern, kein Anruf zu einer Telefonnummer. Beide müssen diese Seite öffnen können. Kamera oder Kontakte sind dafür nicht nötig. Das Mikrofon wird erst nach deiner Freigabe angefragt.

1. Mikrofon erlauben und Einladung erstellen. Code oder Einladungslink nur an die gewünschte Person geben.
2. Die andere Person öffnet denselben erreichbaren Jarvis-Zugang, erlaubt ihr Mikrofon und übernimmt den Einladungscode. Sie schickt ihren Antwortcode zurück.
3. Den Antwortcode im ersten Browser übernehmen. Erst eine gemeldete Audioverbindung bedeutet, dass Ton übertragen wird.

Auf Handy/iPad ist ein vertrauenswürdiger HTTPS-Zugang nötig. Eine lokale HTTP-IP-Adresse reicht für Mikrofonzugriff gewöhnlich nicht. Eine localhost-Adresse auf deinem Mac ist vom Handy aus nicht erreichbar. Es gibt keinen automatisch eingerichteten öffentlichen Server oder Tunnel. Ohne externe Vermittlungsserver ist dies vor allem fürs gleiche Heimnetz gedacht; unterschiedliche Router, Mobilfunk oder verwaltete Browser können die Verbindung verhindern. Du brauchst kein neues Konto. Direkte Verbindungen müssen vom Browser und Netzwerk erlaubt sein.

## Gespräch steuern

Im einladenden Browser:

- „Du schreibst“: Text eingeben und „Mit Thorsten sagen“ bestätigen.
- „Vorschläge“: Jarvis formuliert Antworten; du bearbeitest und bestätigst jede Ansage.
- „KI-Modus“: Jarvis antwortet automatisch auf freigegebene, übertragene Sätze. Ziele und Grenzen kannst du vorher eingeben. Laufende Antworten werden nicht parallel erzeugt.
- „Ich spreche“ gedrückt halten: Jarvis stoppt, dein Mikrofon sendet kurz. Alternativ dein Mikrofon dauerhaft einschalten.
- „Jarvis stoppen“: KI-Antwort und Ton stoppen, auf manuelle Steuerung wechseln.
- „Blockieren“: diese Verbindung beenden. Dies sperrt keine Telefonnummer im Betriebssystem und identifiziert keinen Teilnehmer dauerhaft.

Jeder Teilnehmer muss seine eigene Spracherkennung ausdrücklich einschalten, wenn Gesprochenes als Text übertragen werden soll. Jarvis erkennt nicht heimlich den entfernten Audiostream. Getippte Nachrichten funktionieren auch ohne Spracherkennung. Vor der KI-Verarbeitung muss der einladende Mensch bestätigen, dass das Gegenüber einverstanden ist. Die erste Jarvis-Ansage weist auf den KI-Assistenten hin. „Stopp“ des Gegenübers beendet automatische KI-Antworten ebenfalls.

Thorsten und die vorhandene KI müssen vom steuernden Gerät erreichbar oder dort schon eingerichtet sein. Der Web-Anruf selbst braucht keinen Mac; die mitgelieferte Thorsten-Ausgabe benötigt aber weiterhin den eingerichteten Jarvis-Sprachserver. Das Update installiert kein zusätzliches Modell und verspricht keine lokale Thorsten-Ausgabe auf einem iPhone ohne Sprachserver.

## Daten und Grenzen

Anrufcodes, das kurze Textprotokoll und Anweisungen werden in dieser Funktion nicht dauerhaft gespeichert. Audio wird live übertragen und nicht als Aufnahme angelegt. Die Browser-Spracherkennung kann den Sprachdienst des Browserherstellers mit Internetzugriff nutzen; dafür gibt es eine eigene Freigabe. Die Gesprächs-KI verarbeitet freigegebene Sätze ausschließlich mit der eingerichteten lokalen llama.cpp-/Ollama-Anbindung. Ein konfigurierter externer Anbieter wird für diesen Weg zurückgewiesen; es wird kein externer KI-Dienst angefragt. Gesprächsdaten sind im Browser während der Sitzung sichtbar. Beim Beenden werden Mikrofon, Verbindung und Sitzungsprotokoll verworfen. Der jeweilige Serverzugang und Browser können unabhängig davon technische Zugriffsprotokolle führen.

Das Menü und die echte WebAudio-Tonmischung wurden mit einer kontrollierten Peer-Verbindung getestet. Die verwaltete Cloud-Testumgebung blockiert direkte WebRTC-Netzwerkverbindungen; ein echter Netzwerk-Anruf und physische iPhone-/iPad-Geräte wurden dort nicht verifiziert.

## Live-Gespräch ohne Anruflink

Öffne „Jarvis Apps → Live-Gespräch“ oder im Telefonfenster „Live-Gespräch · Jarvis denkt mit“. Du brauchst dafür keinen Gesprächspartner-Link und keine Telefonnummer. Dieser Modus ist ein Gespräch mit Jarvis beziehungsweise eine Begleitung für Personen im Raum, kein Ersatz für eine Telefonie-Anbindung.

„Mit Jarvis reden“ lässt dich direkt mit ihm sprechen. „Ein Gespräch im Raum begleiten“ erfordert zusätzlich, dass alle Beteiligten über den KI-Assistenten informiert und mit Erkennung und KI-Verarbeitung einverstanden sind. Es wird ausschließlich die Browser-Spracherkennung am Mikrofon dieses Geräts genutzt; keine Telefon-/FaceTime-Audiospur wird ausgelesen. Ein Gespräch auf einem anderen Gerät könnte nur akustisch über dessen Lautsprecher im Raum hörbar sein. Ob das verständlich erkannt wird, hängt von Umgebung und Browser ab und ist nicht zugesichert. Ein Anruf und diese Erkennung auf demselben Handy können sich beim Mikrofonzugriff gegenseitig blockieren.

Aktiviere die Browser-Spracherkennung ausdrücklich und starte das Gespräch. Erkannte vollständige Sätze werden automatisch an die eingerichtete KI geschickt. Jarvis formuliert eigene Antworten und Rückfragen, die Thorsten am Gerät vorliest. Während Antwortgenerierung und Vorlesen pausiert seine Erkennung, damit er sich nicht selbst beantwortet. Die Qualität hängt vom vorhandenen Modell ab; das Update lädt kein neues Modell herunter.

Unter „Antworten mitsteuern“ kannst du Ziel, Ton und Grenzen eingeben und die letzte Antwort anders formulieren lassen. „Jede Ansage erst von mir freigeben“ zeigt zunächst einen editierbaren Vorschlag. „Diese Antwort vorlesen“ bestätigt die Ausgabe. „Pause / ich übernehme“ stoppt Erkennung, KI-Anfrage und Sprache. Ein erkanntes „Stopp“ oder „Pause“ stoppt ebenfalls. Beim Wechsel in einen unsichtbaren Tab pausiert der Modus.

Der Live-Verlauf und seine Ziele bleiben im Arbeitsspeicher. „Gespräch verwerfen“ und Schließen löschen die Sitzungsinhalte, beenden Erkennung und Sprachausgabe und ignorieren verspätete Antworten. Es gibt keine Audioaufnahme und keinen neuen gespeicherten Jarvis-Chat. Browser-Spracherkennung kann über einen Internetdienst laufen; freigegebene Texte werden ausschließlich bei der eingerichteten lokalen llama.cpp-/Ollama-KI verarbeitet. Thorsten benötigt weiterhin den vorhandenen Jarvis-Sprachserver. Das Update richtet keine Telefonie und keinen externen KI-Dienst ein.

## Vor dem Wählen informieren und eigenen Hinweis aufnehmen

Nach „Anruf prüfen“ siehst du „Bevor du anrufst“. „Vorher mit Jarvis besprechen“ öffnet den Live-Gesprächsmodus über dem Telefonfenster. Du kannst dort dein Ziel besprechen; die Auswahl des Empfängers bleibt währenddessen nur im offenen Telefonfenster erhalten. Schließe das Gespräch, um zur Anrufbestätigung zurückzukehren.

„Vorher informieren & eigenen Hinweis aufnehmen“ enthält zwei editierbare Hinweistexte: Du stellst Jarvis vor, oder Jarvis stellt sich ausdrücklich als KI vor. Die eigene Aufnahme startet nur mit „Meinen Hinweis aufnehmen“ und einer Mikrofonfreigabe. Sie ist auf 45 Sekunden und 4 MB begrenzt, wird nicht hochgeladen und existiert nur als Blob im Arbeitsspeicher. Stoppen gibt das Mikrofon frei. Anhören geht wiederholt, bis du die Aufnahme löschst oder das Telefonfenster schließt. Es wird kein Stimmprofil erstellt. Eine Wiederverwendung nach dem Schließen benötigt eine gesondert gewünschte lokale Speicherung; diese ist nicht eingeschaltet.

„Mit Thorsten als Vorschau erstellen“ übermittelt ausschließlich den Hinweistext an den eingerichteten Sprachserver und zeigt einen Audioplayer. Diese Vorschau wird ebenso beim Schließen verworfen. Alle Vorschauen laufen nur auf diesem Gerät. Sie werden nicht automatisch an einen normalen Telefonanruf übertragen. Der Start eines normalen Anrufs stoppt die Aufnahme, bevor die Telefon-App geöffnet wird.
