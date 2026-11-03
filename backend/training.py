"""Small, deterministic drills from declared settings. Never image analysis."""
import re

def plan(body):
    if set(body)-{'edition','version','goal','controls'}:raise ValueError('Unbekannte Trainingsangaben.')
    edition=body.get('edition','java');version=body.get('version','');goal=body.get('goal','aim');controls=body.get('controls','keyboard')
    if any(not isinstance(value,str) for value in (edition,goal,controls)):
        raise ValueError('Trainingsoptionen müssen Text sein.')
    if edition not in {'java','bedrock'} or goal not in {'aim','movement','combos','shield','building'} or controls not in {'keyboard','controller','touch'}:raise ValueError('Bitte gültige Trainingsoptionen wählen.')
    if not isinstance(version,str) or len(version)>30 or (version and not re.fullmatch(r'[0-9]+(?:\.[0-9]+){0,3}',version)):raise ValueError('Version bitte als Zahl eingeben, z. B. 1.21.')
    legacy=edition=='java' and bool(re.match(r'^1\.[0-8](?:\.|$)',version))
    timing=('Java bis 1.8: kein Angriffsstärke-Cooldown wie ab 1.9. Treffer-Unverwundbarkeit und Serverregeln beachten.' if legacy else 'Java ab 1.9: Angriffsstärke-Anzeige beachten und Schläge gezielt setzen; Dauer-Klicken schwächt viele Angriffe.') if edition=='java' else 'Bedrock hat nicht den Java-Angriffsstärke-Cooldown. Reichweite, Treffer-Unverwundbarkeit und die Regeln deines Servers beachten.'
    if edition=='java' and not version:timing='Version fehlt: Java bis 1.8 und Java ab 1.9 haben verschiedene Kampfsysteme. Trage deine Version ein.'
    drills={
        'aim':['2 Minuten: Fadenkreuz ruhig auf Brusthöhe halten und ein festes Ziel umkreisen.','4 Minuten: Bewegliches Ziel verfolgen; erst schlagen, wenn es im Fadenkreuz ist.','4 Minuten: Freundliches Duell; Treffer und Versuche zählen, Sensitivität nur in kleinen Schritten ändern.'],
        'movement':['2 Minuten: Seitwärtsbewegung und Zielverfolgung getrennt üben.','4 Minuten: Links/rechts variieren, nicht rhythmisch immer dasselbe machen.','4 Minuten: Kurzes Übungsduell mit Fokus auf Abstand statt Sieg.'],
        'combos':['2 Minuten: Sichere Reichweite und den ersten gezielten Treffer üben.','4 Minuten: Nach dem Treffer Abstand und Sprint kontrollieren; Servermechanik prüfen.','4 Minuten: Freundliches Duell aufnehmen und einen eigenen Fehler notieren.'],
        'shield':['2 Minuten: Schild nur nutzen, falls in Version und Spielmodus verfügbar.','4 Minuten: Blocken, Position wechseln und sicheren Gegenangriff getrennt üben.','4 Minuten: Mit einem Freund Angriffsmuster langsam variieren; Serverregeln berücksichtigen.'],
        'building':['2 Minuten: In einer sicheren Übungswelt einfache Blockreihen setzen.','4 Minuten: Langsam rückwärts bauen und sichere Platzierung vor Tempo üben.','4 Minuten: Einen kurzen Parcours wiederholen und Fehlerstellen vergleichen.']}
    control={'keyboard':'Tastatur/Maus: bequeme Tasten und gleichbleibende Sensitivität wählen.','controller':'Controller: kleine Stickbewegungen und eine niedrige, kontrollierbare Sensitivität üben.','touch':'Touch: HUD so anordnen, dass Sicht und Bewegung gleichzeitig möglich bleiben.'}[controls]
    return {'basis':'Trainingsplan aus deinen Angaben – keine Analyse der Kamerabilder.','edition':edition,'timing':timing,'controls':control,'drills':drills[goal]}
