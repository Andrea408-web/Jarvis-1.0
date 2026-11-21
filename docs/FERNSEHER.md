# Jarvis auf dem Fernseher und als eigenes HDMI-Gerät

Ein eigenes Jarvis-Gerät ist ein Computer, der Jarvis und die lokale KI selbst ausführt und sein Bild per HDMI an den Fernseher sendet. HDMI ist nur der Bild-/Tonanschluss. Ein Kabel oder USB-Stick allein kann die KI nicht berechnen. Dieses Update enthält die TV-Oberfläche und die Verbindungshilfe; es stellt keine neue Hardware her.

## Direkt mit deinem eingerichteten Mac per HDMI

1. Verbinde den Mac mit einem passenden HDMI-Kabel beziehungsweise seinem vorgesehenen Adapter am Hisense-Fernseher. Wähle dort genau diesen HDMI-Eingang.
2. Installiere das gemeinsame Jarvis-Update in deinem bisherigen Jarvis-Ordner. Die lokale KI muss dort bereits eingerichtet sein.
3. Öffne **Jarvis-TV-starten.command** in diesem Ordner. Das Terminal muss geöffnet bleiben. Wenn Jarvis schon läuft, beende die alte Instanz zuerst mit Strg+C, damit der Port frei ist.
4. Verschiebe das TV-Browserfenster auf den Fernseher. In den macOS-Anzeigeeinstellungen kannst du spiegeln oder den Fernseher als zweiten Bildschirm verwenden. Aktiviere Vollbild über das Browsermenü, falls gewünscht.
5. Wenn kein Ton kommt, wähle in macOS unter Ton die HDMI-/TV-Ausgabe. Lautstärke und Stummschaltung am Fernseher ebenfalls prüfen.

Der Mac führt die KI aus. Es wird keine neue KI auf den Fernseher oder Fire TV Stick kopiert. Der Starter installiert nichts und ist kein allgemeiner Linux-Starter.

## Ein eigenes, unabhängiges HDMI-Gerät vorbereiten

Für ein vom bisherigen Mac unabhängiges Gerät brauchst du einen eigenen geeigneten Computer mit HDMI-Ausgabe, passender Stromversorgung und ausreichend Speicher für Anwendung, Laufzeit und das bereits erlaubte lokale KI-Modell. Eine bereits eingerichtete kompatible Mac-Installation, etwa auf einem eigenen Mac mini, kann die vorhandenen Mac-Funktionen verwenden. Verfügbarkeit, Leistung und Preis einer neuen Hardwarekombination sind hier nicht geprüft.

Ein beliebiger Linux-Mini-PC wird durch dieses Update nicht fertig eingerichtet. Er benötigt ein passendes Betriebssystem, Python und eine kompatible lokale KI-Laufzeit samt Modell. Der vorhandene `--easy-local`-Ablauf setzt macOS-Komponenten voraus und ist deshalb keine funktionierende Installationsanleitung für Linux. Apple Vision, Mac-App-Steuerung und der bisherige Thorsten-Einrichter stehen dort nicht automatisch zur Verfügung.

Für ein eigenes Gehäuse:

1. Erst den vorhandenen, vollständig eingerichteten Computer außerhalb des Gehäuses testen: Bild am TV, Bedienung, lokale KI-Antwort und gegebenenfalls Ton.
2. Außenmaße, Lüftungsöffnungen und Kabelstecker am konkreten Gerät messen. Ein Gehäuse darf die vom Hersteller verlangte Belüftung nicht einschränken.
3. Gerät standsicher aufstellen; vorgesehene HDMI- und Netzkabel mit Platz für Biegungen führen. Ein-/Ausschalter und Anschlüsse zugänglich lassen.
4. Nur vorgesehene unbeschädigte Netzteile nutzen. Keine Netzteile öffnen, keine eigene Netzspannungsverdrahtung bauen und keine Elektronik in das TV-Gehäuse einbauen.
5. Mit offenem Aufbau prüfen, ob Wärmeentwicklung und Verbindung stabil bleiben. Erst ein funktionierendes eigenes System ist ein unabhängiger Jarvis-Rechner; ein externer Mac als benötigter Server erfüllt das noch nicht.

Das ist eine Integrationsanleitung für vorhandene, passende Geräte, keine zugesagte Stückliste oder ein fertig gebauter HDMI-Dongle.

## Mit deinem vorhandenen Fire TV Stick

Der Fire TV Stick steckt bereits im HDMI-Anschluss und kann einen Browser als Anzeige verwenden. Die lokale Jarvis-KI läuft bei dieser Variante weiterhin auf dem Mac.

1. Mac und Fire TV Stick mit demselben vertrauenswürdigen Heimnetz verbinden. Den Mac eingeschaltet lassen.
2. In Jarvis am Mac **Fernseher / HDMI verbinden** öffnen und danach **TV-Verbindung vorbereiten** wählen. Die kurze TV-Adresse und der sechsstellige Kopplungscode werden dort live angezeigt. Der Code ist nur kurz gültig; bei Ablauf einen neuen erzeugen.
3. Am Fire TV über die App-Suche **Amazon Silk** suchen und öffnen beziehungsweise regulär installieren, falls verfügbar. Es wird kein Entwicklerkonto und keine seitlich installierte Android-App benötigt. Falls der Browser für dein Gerät nicht verfügbar ist, funktioniert diese Browservariante nicht; nutze dann die direkte HDMI-Verbindung.
4. Die kurze TV-Adresse vom Mac im Browser eingeben und anschließend den sechsstelligen Code. Die Adresse ist die tatsächliche private Heimnetzadresse; sie ist nicht auf jedem Mac gleich.
5. Die private HTTPS-Verbindung muss im konkreten TV-Browser funktionieren. Bei einem Zertifikatsfehler den Schutz nicht ausschalten. Falls das Gerät das benötigte private Zertifikat nicht nutzen kann, ist HDMI die Ausweichmöglichkeit.

Es wird kein dauerhaft gültiger Code auf einen USB-Stick geschrieben. Kopplung und Gerätezugriff verwenden dieselben Schutzmechanismen wie die vorhandene private Jarvis-Verbindung.

## Was der USB-Ordner tatsächlich macht

Der Ordner **USB-Jarvis** kann auf einen USB-Stick kopiert werden. **START-HIER.html** ist eine Offline-Starthilfe für einen geeigneten Browser an einem Computer. Sie zeigt die Verbindungsschritte und kann selbst ausgewählte lokale Bilder und Videos ohne Upload anzeigen. Sie enthält keine KI und speichert weder Link noch Medienauswahl.

Der normale USB-Medienplayer eines Fernsehers führt diese HTML-Datei meist nicht aus. Er zeigt gegebenenfalls unterstützte Mediendateien. Welche Dateisysteme, Codecs und Auflösungen funktionieren, steht im Handbuch des konkreten Fernsehers. Nicht jedes Video mit der Endung `.mp4` hat denselben Codec. Für Live-Jarvis braucht es weiterhin einen Browser mit erreichbar eingerichtetem Jarvis-Rechner oder das eigene vollständig eingerichtete HDMI-Gerät.
