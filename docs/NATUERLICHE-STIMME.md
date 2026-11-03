# Mini-Hub und natürlichere Stimme nachrüsten – vorhandenes Jarvis behalten

Du brauchst nur das kleine **JARVIS-Stimme-Nachruestung.zip** mit **JARVIS-Stimme-nachruesten.command**, nicht das komplette Projekt und nicht deine Text-KI noch einmal.

1. Lade das kleine Nachrüst-ZIP herunter und entpacke es. Du kannst ihn in deinen vorhandenen Jarvis-Ordner legen und öffnen. Liegt er daneben, sucht er passende JARVIS-Ordner; bei mehreren oder keinem Treffer öffnet sich die Mac-Ordnerauswahl.
2. Der Helfer prüft, ob die Programmdateien zur zuletzt bereitgestellten Version **232ba23** passen. Eigene unbekannte Änderungen werden nicht überschrieben. Die wenigen ersetzten Programmdateien werden vorher gesichert.
3. Er lädt die passende Mac-Sprachengine und das deutsche **Thorsten-medium**-Stimmenmodell von offiziellen sherpa-onnx-Releases, prüft feste SHA256-Prüfsummen und die Mac-Architektur und erzeugt eine echte Sprachprobe. Keine API, kein Sprachkonto, keine Systemstimme, kein Compiler und keine Python-Fremdpakete.
4. Nach erfolgreicher Prüfung wird die natürliche Stimme ausgewählt. Beende dein bisheriges Jarvis-Terminal mit **Control+C** und starte wie gewohnt **2-JARVIS-starten.command**. Lade bei Bedarf die Browserseite neu. **Die Text-KI wird nicht neu heruntergeladen.**

Download: ungefähr **100 MB auf Apple Silicon**, ungefähr **104 MB auf Intel**. Nach dem Entpacken und Entfernen der Downloadarchive bleiben ungefähr **160–180 MB** für die Stimme. Während der Einrichtung sollten vorsichtshalber **500 MB frei** sein. Die Downloadarchive werden bei Erfolg entfernt. Bei einem Abbruch können geprüfte Downloads für den nächsten Versuch wiederverwendet werden.

Die Stimme wird getrennt im privaten JARVIS-Datenordner unter `natural-voice` gespeichert. Gespräche, Schlüssel, Bilder, dein Textmodell und andere Einstellungen werden nicht ersetzt. Die Sicherung der wenigen aktualisierten Programmdateien liegt unter `.jarvis/voice-update-backups` im Projektordner. Schlägt die Installation fehl, werden diese Programmdateien zurückgesetzt; die natürliche Stimme wird nicht fälschlich aktiviert.

Unter **Stimme → Natürliche Stimme verwenden** kannst du sie erneut auswählen und testen. Standard/Zügig/Ruhig ändern nur das Tempo; die künstlichen Formant-/Tonhöhenänderungen der bisherigen Roboterstimme entfallen. Eine fehlende oder beschädigte natürliche Stimme löst einen sichtbaren Fehler aus, keinen stillen Wechsel zur alten Stimme.

Die natürliche Ausgabe wird auf dem JARVIS-Mac erzeugt, auch wenn du Jarvis auf deinem Handy öffnest. Deine Texte gehen dafür an deinen eigenen JARVIS-Server, nicht an einen externen Sprachanbieter. Die bestehende Browser-Spracherkennung ist davon getrennt und bleibt browserabhängig.

## Quellen und Prüfgrenzen

- Sprachengine: [sherpa-onnx v1.12.34](https://github.com/k2-fsa/sherpa-onnx/releases/tag/v1.12.34), natives Paket für die tatsächliche Mac-Architektur. Es wird keine andere Architektur installiert und keine macOS-Sicherheitsprüfung umgangen.
- Modell: [vits-piper-de_DE-thorsten-medium](https://github.com/k2-fsa/sherpa-onnx/releases/tag/tts-models), neuronale Piper/VITS-Stimme, 22.050 Hz. Das Modell nutzt den [Thorsten-Voice-Datensatz](https://github.com/thorstenMueller/Thorsten-Voice), laut beigefügter Modellkarte CC0. Das ist eine natürliche veröffentlichte Sprecherstimme, keine Filmstimmen-Kopie. Die Modellkarte bleibt im installierten Paket erhalten.
- Dateien und SHA256 sind im Modul `backend/natural_voice.py` fest hinterlegt. TLS bleibt aktiviert. Es werden keine Zugangsdaten als Download-Header verwendet.
- Ein echter deutscher Audiotest mit diesem Modell und der entsprechenden Linux-Engine ist in der Cloud möglich. Native Mac-Ausführung muss beim Nachrüsten auf deinem Gerät bestehen, bevor die Stimme aktiviert wird. Ein Linux-Test wird nicht als erfolgreicher Mac-Test ausgegeben.


## Mini-Hub benutzen

Oben **Mini-Hub** anklicken oder **„Öffne meinen Hub“** sagen. Du kannst auch im geöffneten Hub über die Gesprächsschaltfläche mit Jarvis sprechen.

- **Überblick:** Systemwerte des JARVIS-Servergeräts und ein Gehirn als stilisierte Arbeitsanzeige. Weiße Funken erscheinen bei Antworterzeugung, Sprachausgabe oder tatsächlich laufenden Agentenaufträgen. Es wird keine interne Gedanken- oder Gehirnaktivität gemessen.
- **Nachrichten:** Aktuelle öffentliche RSS-Meldungen von tagesschau.de mit Quelle, Abrufzeitpunkt und – falls geliefert – Vorschaubild. Auf der lokalen Weltkarte kannst du nach erwähnten Ländern filtern. Die Zuordnung anhand genannter Länder/Orte ist keine exakte Geolokalisierung. Ohne erreichbare Quelle bleiben Meldungen ausdrücklich älter oder fehlen; keine erfundenen Nachrichten. „Zeig aktuelle Nachrichten“ liest drei tatsächliche Schlagzeilen vor.
- **Meine Kanäle:** YouTube- und TikTok-Kanalnamen oder offizielle Kanallinks eintragen und **Speichern & öffentlich laden** wählen. Die Namen bleiben lokal gespeichert. Zahlen werden nur angezeigt, wenn die Plattform sie ohne Anmeldung öffentlich liefert; YouTube-Anzeigen können gerundet sein. Verborgene, gesperrte oder nicht abrufbare Zahlen sind „nicht verfügbar“, nicht automatisch null. Öffentliche Videos lassen sich im Hub einbetten, wenn der Anbieter das erlaubt; der offizielle Link bleibt vorhanden. Jarvis sammelt keine Plattform-Passwörter und umgeht keine Anmeldung oder Captchas.
- **Planer:** Termine mit Datum und Uhrzeit speichern und als erledigt markieren. Sie verwenden deinen lokalen JARVIS-Erinnerungsspeicher. Keine garantierten OS-Alarme bei geschlossener App.

Nachrichtenbilder und Videoplayer werden beim jeweiligen öffentlichen Anbieter geladen. Für aktuelle Nachrichten und Videos brauchst du Internet; der lokale Chat und die natürliche Sprachausgabe bleiben davon getrennt.

## Doppelklatschen: schlafen und aufwecken

Die Klatscherkennung zuerst ausdrücklich aktivieren; dafür bleibt das Mikrofon sichtbar an. Doppelklatschen während einer Antwort stoppt die Sprachausgabe und versetzt das Gespräch in den Schlafmodus. Bereits gestartete Agentenaufträge laufen weiter. Erneutes Doppelklatschen oder **Jarvis aufwecken** startet das Gespräch wieder. Der Stop-Knopf schaltet auch die Klatscherkennung aus.

Die Erkennung ist von Mikrofon und Raumgeräuschen abhängig. Die bestehende Browser-Spracherkennung kann einen Dienst des Browseranbieters verwenden; die neue Sprachausgabe selbst benötigt keinen externen Sprachdienst.

Die Stimme ist eine natürliche veröffentlichte deutsche Sprecherstimme, keine identische Kopie des deutschen Film-JARVIS. Die Hörprobe zeigt den tatsächlichen Klang vor dem größeren Download.
