# Mini-Hub und natürlichere Stimme nachrüsten – vorhandenes Jarvis behalten

Du brauchst nur das kleine **JARVIS-Stimme-Nachruestung.zip** mit **JARVIS-Stimme-nachruesten.command**, nicht das komplette Projekt und nicht deine Text-KI noch einmal.

1. Lade das kleine Nachrüst-ZIP herunter und entpacke es. Du kannst ihn in deinen vorhandenen Jarvis-Ordner legen und öffnen. Liegt er daneben, sucht er passende JARVIS-Ordner; bei mehreren oder keinem Treffer öffnet sich die Mac-Ordnerauswahl.
2. Der Helfer prüft, ob die Programmdateien zur zuletzt bereitgestellten Version **232ba23** passen. Eigene unbekannte Änderungen werden nicht überschrieben. Die wenigen ersetzten Programmdateien werden vorher gesichert.
3. Er lädt die passende Mac-Sprachengine und das deutsche **Thorsten-medium**-Stimmenmodell von offiziellen sherpa-onnx-Releases, prüft feste SHA256-Prüfsummen und die Mac-Architektur und erzeugt eine echte Sprachprobe. Keine API, kein Sprachkonto, keine Systemstimme, kein Compiler und keine Python-Fremdpakete.
4. Nach erfolgreicher Prüfung wird die natürliche Stimme ausgewählt. Beende dein bisheriges Jarvis-Terminal mit **Control+C** und starte wie gewohnt **2-JARVIS-starten.command**. Lade bei Bedarf die Browserseite neu. **Die Text-KI wird nicht neu heruntergeladen.**

Download: ungefähr **100 MB auf Apple Silicon**, ungefähr **104 MB auf Intel**. Nach dem Entpacken und Entfernen der Downloadarchive bleiben ungefähr **160–180 MB** für die Stimme. Während der Einrichtung sollten vorsichtshalber **500 MB frei** sein. Die Downloadarchive werden bei Erfolg entfernt. Bei einem Abbruch können geprüfte Downloads für den nächsten Versuch wiederverwendet werden.

Die Stimme wird getrennt im privaten JARVIS-Datenordner unter `natural-voice` gespeichert. Gespräche, Schlüssel, Bilder, dein Textmodell und andere Einstellungen werden nicht ersetzt. Die Sicherung der wenigen aktualisierten Programmdateien liegt unter `.jarvis/voice-update-backups` im Projektordner. Schlägt die Installation fehl, werden diese Programmdateien zurückgesetzt; die natürliche Stimme wird nicht fälschlich aktiviert.

Unter **Stimme → Thorsten testen** kannst du sie erneut auswählen und testen. Standard/Zügig/Ruhig ändern nur das Tempo; die künstlichen Formant-/Tonhöhenänderungen der bisherigen Roboterstimme entfallen. Eine fehlende oder beschädigte natürliche Stimme löst einen sichtbaren Fehler aus, keinen stillen Wechsel zur alten Stimme.

Die natürliche Ausgabe wird auf dem JARVIS-Mac erzeugt, auch wenn du Jarvis auf deinem Handy öffnest. Deine Texte gehen dafür an deinen eigenen JARVIS-Server, nicht an einen externen Sprachanbieter. Die bestehende Browser-Spracherkennung ist davon getrennt und bleibt browserabhängig.

## Quellen und Prüfgrenzen

- Sprachengine: [sherpa-onnx v1.12.34](https://github.com/k2-fsa/sherpa-onnx/releases/tag/v1.12.34), natives Paket für die tatsächliche Mac-Architektur. Es wird keine andere Architektur installiert und keine macOS-Sicherheitsprüfung umgangen.
- Modell: [vits-piper-de_DE-thorsten-medium](https://github.com/k2-fsa/sherpa-onnx/releases/tag/tts-models), neuronale Piper/VITS-Stimme, 22.050 Hz. Das Modell nutzt den [Thorsten-Voice-Datensatz](https://github.com/thorstenMueller/Thorsten-Voice), laut beigefügter Modellkarte CC0. Das ist eine natürliche veröffentlichte Sprecherstimme, keine Filmstimmen-Kopie. Die Modellkarte bleibt im installierten Paket erhalten.
- Dateien und SHA256 sind im Modul `backend/natural_voice.py` fest hinterlegt. TLS bleibt aktiviert. Es werden keine Zugangsdaten als Download-Header verwendet.
- Ein echter deutscher Audiotest mit diesem Modell und der entsprechenden Linux-Engine ist in der Cloud möglich. Native Mac-Ausführung muss beim Nachrüsten auf deinem Gerät bestehen, bevor die Stimme aktiviert wird. Ein Linux-Test wird nicht als erfolgreicher Mac-Test ausgegeben.


## Neue Oberfläche

Der frühere Mini-Hub und die öffentlichen Kameralinks wurden auf Wunsch entfernt. Die neue Weltansicht und Astra sind in der [Astra-Anleitung](ASTRA.md) beschrieben. Das separate Astra-Update behält eine vorhandene Stimme und lädt keine neuen Modelle.

## Doppelklatschen: schlafen und aufwecken

Die Klatscherkennung zuerst ausdrücklich aktivieren; dafür bleibt das Mikrofon sichtbar an. Doppelklatschen während einer Antwort stoppt die Sprachausgabe und versetzt das Gespräch in den Schlafmodus. Bereits gestartete Agentenaufträge laufen weiter. Erneutes Doppelklatschen oder **Jarvis aufwecken** startet das Gespräch wieder. Der Stop-Knopf schaltet auch die Klatscherkennung aus.

Die Erkennung ist von Mikrofon und Raumgeräuschen abhängig. Die bestehende Browser-Spracherkennung kann einen Dienst des Browseranbieters verwenden; die neue Sprachausgabe selbst benötigt keinen externen Sprachdienst.

Die Stimme ist eine natürliche veröffentlichte deutsche Sprecherstimme, keine identische Kopie des deutschen Film-JARVIS. Die Hörprobe zeigt den tatsächlichen Klang vor dem größeren Download.

## Feste Auswahl: Thorsten

Auf Wunsch des Nutzers bleibt Thorsten immer die Stimme für Jarvis und Astra. Alte gespeicherte „bundled“-Einstellungen werden als Thorsten gelesen; alte Clients können keine Roboterstimme zurückschalten. Die Tempo-Profile verändern nur Thorsten. Es gibt keinen System- oder Formantstimmen-Fallback.

Unter „Stimme“: „Thorsten testen“ für die Hörprobe. Falls nötig am Mac „Thorsten einrichten / reparieren“ anklicken. Vorhandene, geprüfte Dateien werden wiederverwendet; bei fehlendem Paket beträgt der Download ungefähr 100–104 MB. Die Text-KI muss nicht erneut geladen werden. Der Download startet nur durch diesen Klick oder den ausdrücklich geöffneten Stimmen-Nachrüsthelfer.
