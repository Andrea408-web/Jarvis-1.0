"""Small, private invention concepts with validated functional diagrams, not CAD."""
import json
import re
from .local_ai import validate_model

def validate(raw):
    fields={'title','purpose','how','components','links','tests','limits'}
    if not isinstance(raw,dict) or set(raw)!=fields:raise ValueError('Die KI hat kein vollständiges Erfindungskonzept geliefert.')
    for key,cap in [('title',90),('purpose',400),('how',900),('limits',600)]:
        if not isinstance(raw[key],str) or not 1<=len(raw[key].strip())<=cap:raise ValueError('Ungültiger Konzepttext: '+key)
    if not isinstance(raw['components'],list) or not 2<=len(raw['components'])<=6 or not isinstance(raw['links'],list) or not 1<=len(raw['links'])<=8 or not isinstance(raw['tests'],list) or not 1<=len(raw['tests'])<=4:raise ValueError('Bitte ein kleines Konzept mit 2–6 Bausteinen erzeugen lassen.')
    ids=set()
    for c in raw['components']:
        if not isinstance(c,dict) or set(c)!={'id','name','purpose'} or not isinstance(c['id'],str) or not re.fullmatch(r'[a-z][a-z0-9_]{0,15}',c['id']) or c['id'] in ids or not isinstance(c['name'],str) or not 1<=len(c['name'])<=40 or not isinstance(c['purpose'],str) or not 1<=len(c['purpose'])<=200:raise ValueError('Ungültiger Baustein in der Funktionsskizze.')
        ids.add(c['id'])
    for edge in raw['links']:
        if not isinstance(edge,dict) or set(edge)!={'from','to','label'} or not isinstance(edge['from'],str) or edge['from'] not in ids or not isinstance(edge['to'],str) or edge['to'] not in ids or edge['from']==edge['to'] or not isinstance(edge['label'],str) or not 1<=len(edge['label'])<=50:raise ValueError('Eine Verbindung verweist auf keinen gültigen Baustein.')
    if any(not isinstance(t,str) or not 1<=len(t)<=200 for t in raw['tests']):raise ValueError('Ungültiger Vorschlag für einen Konzepttest.')
    return raw

def design(app,body):
    if not isinstance(body,dict) or set(body)!={'idea','revision','previous'} or not isinstance(body['idea'],str) or not 1<=len(body['idea'].strip())<=1000 or not isinstance(body['revision'],str) or len(body['revision'])>600:raise ValueError('Bitte eine Idee bis 1.000 Zeichen und optional einen Änderungswunsch bis 600 Zeichen eingeben.')
    previous=validate(body['previous']) if body['previous'] is not None else None
    settings=app.store.settings();provider=settings['ai_provider']
    if provider not in {'llamacpp','ollama'}:raise ValueError('Das Erfinder-Labor nutzt nur deine bereits eingerichtete lokale KI am Mac. Es gibt keinen Cloud-Ausweichdienst.')
    if provider=='ollama':validate_model(settings['local_model'])
    instruction=('Du bist JARVIS, ein deutscher Erfindungshelfer. Entwickle ein kleines, verständliches KONZEPT, keine geprüfte Bauanleitung. Trenne Wunsch und Machbarkeit. Erfinde keine Messwerte oder bestandenen Tests. Antworte nur mit JSON: '
      '{"title":"Name","purpose":"Welches Problem?","how":"So könnte es funktionieren","components":[{"id":"a","name":"Baustein","purpose":"Aufgabe"},{"id":"b","name":"Ausgabe","purpose":"Aufgabe"}],"links":[{"from":"a","to":"b","label":"Was wird übertragen?"}],"tests":["Was müsste man testen?"],"limits":"Offene Fragen und Grenzen"}. '
      '2 bis 6 Bausteine, 1 bis 8 Verbindungen, 1 bis 4 Testideen. Kurz und konkret. Keine fertige Konstruktion behaupten.')
    prompt='Idee: '+body['idea'].strip()
    if previous:prompt+='\nBisheriges Konzept: '+json.dumps(previous,ensure_ascii=False)
    if body['revision'].strip():prompt+='\nBitte überarbeiten: '+body['revision'].strip()
    reply=app.code_room._generate({'model':'llamacpp' if provider=='llamacpp' else 'ollama:'+settings['local_model']},[{'role':'system','content':instruction},{'role':'user','content':prompt}],1280,structured=True)
    try:raw=json.loads(reply)
    except ValueError:raise ValueError('Die lokale KI hat keine gültige Konzeptskizze geliefert. Bitte die Idee kleiner oder konkreter beschreiben.') from None
    return {'concept':validate(raw),'message':'KI-Konzept mit schematischer Funktionsskizze. Nicht technisch geprüft.'}
