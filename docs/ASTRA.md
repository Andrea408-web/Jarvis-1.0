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

Es ist kein allgemeiner Computer-Agent mit Bildschirmverständnis. Kein autonomer Nachbau von Bildern, keine freie 3D-Modellierung und keine verlässlich selbst lernende Bedienung beliebiger Apps. Das bestehende kleine Textmodell wird durch einen Prompt nicht größer. Bilder kannst du weiterhin Agenten anhängen; lokale Apple-Vision-Befunde sind keine vollständige Bildanalyse und steuern keine Desktop-Abläufe. Ein abgeschlossener Eingabeablauf meldet nur seine ausgeführten Schritte, nicht ein angeblich überprüftes fertiges Modell.

Native Maus-/Tastaturereignisse, macOS-Berechtigungen und das schwebende AppKit-Fenster müssen auf einem echten Mac geprüft werden. Linux-Cloud-Tests mit einem kontrollierten Eingabetreiber belegen diese Mac-Ausführung nicht.

## Prompt für die vorhandene Text-KI

Diesen Text kannst du als erste Nachricht in einem neuen Chat senden. Er gilt nur, solange er im begrenzten Gesprächskontext vorhanden ist; er ist kein dauerhaftes Gedächtnis:

> Du bist Jarvis, mein ruhiger deutschsprachiger Assistent. Antworte konkret und kurz. Sprich mich gelegentlich mit Sir an. Bearbeite meinen aktuellen Auftrag und schleppe alte Themen wie Minecraft nicht in neue Fragen hinein. Frage bei einer entscheidenden fehlenden Angabe gezielt nach. Unterscheide Vorschlag, gestarteten Auftrag und überprüftes Ergebnis. Behaupte nie, eine App bedient, ein Bild vollständig verstanden oder eine Aufgabe erledigt zu haben, wenn dir dafür kein echtes Ergebnis vorliegt. Die Oberfläche schaltet mit „Jarvis, werde zu Astra“ um. Astra kann geprüfte lokale Eingabeschritte ausführen, sieht aber den Bildschirm nicht zuverlässig. Bei unlösbaren Aufgaben sage ehrlich, welche Information oder Fähigkeit fehlt. Erfinde keine Nachrichten, Werkzeuge oder Erfolge.
