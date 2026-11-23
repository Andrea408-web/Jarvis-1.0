# Anrufe und Gesprächsmenü

Öffne „Anrufen“ in Jarvis am Mac, iPad oder Handy. Für normale Telefonnummern wählst du einen Kontakt oder gibst eine Nummer ein und bestätigst die Übergabe an Telefon/FaceTime. Jarvis behauptet dabei keine bestehende Verbindung. Die Web-App kann normale Apple-Telefonate weder abhören noch ihren Ton ersetzen. Apple kann eigene Anruflisten führen.

## Web-Anruf mit Jarvis

Im Anrufmenü führt „Web-Anruf mit Jarvis · Gesprächsmodi öffnen“ zu `/web-call`. Dies ist ein eigener Anruf zwischen zwei Browsern, kein Anruf zu einer Telefonnummer. Beide müssen diese Seite öffnen können. Kamera oder Kontakte sind dafür nicht nötig. Das Mikrofon wird erst nach deiner Freigabe angefragt.

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

Anrufcodes, das kurze Textprotokoll und Anweisungen werden in dieser Funktion nicht dauerhaft gespeichert. Audio wird live übertragen und nicht als Aufnahme angelegt. Die Browser-Spracherkennung kann den Sprachdienst des Browserherstellers mit Internetzugriff nutzen; dafür gibt es eine eigene Freigabe. Die KI verarbeitet die freigegebenen Sätze beim eingestellten Jarvis-Anbieter. Ein bereits extern konfigurierter Anbieter ist dadurch nicht automatisch lokal. Gesprächsdaten sind im Browser während der Sitzung sichtbar. Beim Beenden werden Mikrofon, Verbindung und Sitzungsprotokoll verworfen. Der jeweilige Serverzugang und Browser können unabhängig davon technische Zugriffsprotokolle führen.

Das Menü und die echte WebAudio-Tonmischung wurden mit einer kontrollierten Peer-Verbindung getestet. Die verwaltete Cloud-Testumgebung blockiert direkte WebRTC-Netzwerkverbindungen; ein echter Netzwerk-Anruf und physische iPhone-/iPad-Geräte wurden dort nicht verifiziert.
