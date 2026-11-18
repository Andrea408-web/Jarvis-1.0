"""Explicit, inspectable personal preferences; no inferred traits or model training."""
import hashlib,json
from datetime import datetime,timezone
from .providers import ProviderError

EMPTY={'version':1,'name':'','address':'Master','humor':'unspecified','style':'unspecified','about':'','interests':'','avoid':''}
HUMOR={'unspecified','neutral','dry','playful','puns','none'}
STYLE={'unspecified','short','balanced','detailed'}

def validate(value):
    if not isinstance(value,dict) or set(value)!=set(EMPTY) or type(value['version']) is not int or value['version']!=1:raise ValueError('Ungültiges persönliches Profil.')
    clean=dict(value)
    for key,limit in [('name',60),('address',30),('about',1500),('interests',300),('avoid',300)]:
        if not isinstance(value[key],str) or len(value[key])>limit or any(ord(c)<32 and c not in '\n\t' for c in value[key]):raise ValueError('Ungültiger oder zu langer Profiltext: '+key)
        clean[key]=value[key].strip()
    if clean['name'] and not all(c.isalpha() or c in " -’'" for c in clean['name']):raise ValueError('Bitte einen Namen ohne Ziffern oder Sonderzeichen eingeben.')
    if not clean['address'] or not all(c.isalpha() or c in ' -' for c in clean['address']):raise ValueError('Bitte eine kurze Anrede wie Sir, Master oder Boss wählen.')
    if not isinstance(value['humor'],str) or value['humor'] not in HUMOR or not isinstance(value['style'],str) or value['style'] not in STYLE:raise ValueError('Bitte eine vorhandene Humor- und Antwortvorliebe wählen.')
    return clean

class PersonalProfile:
    def __init__(self,store):
        self.store=store
        with store._connect() as db:db.execute('CREATE TABLE IF NOT EXISTS personal_profile (id INTEGER PRIMARY KEY CHECK(id=1), data TEXT NOT NULL, revision INTEGER NOT NULL, updated TEXT NOT NULL, active INTEGER NOT NULL)')
    def _read(self,db):
        row=db.execute('SELECT * FROM personal_profile WHERE id=1').fetchone();profile=dict(EMPTY)
        if row and row['active']:profile.update(json.loads(row['data']))
        settings={r['name']:json.loads(r['value']) for r in db.execute("SELECT name,value FROM settings WHERE name IN ('user_name','user_address')")}
        profile['name']=settings.get('user_name','');profile['address']=settings.get('user_address','Master')
        revision=row['revision'] if row else 0;profile=validate(profile)
        expected=hashlib.sha256(json.dumps({'profile':profile,'revision':revision},sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        return {'profile':profile,'expected':expected,'saved':bool(row and row['active']),'updated':row['updated'] if row else None}
    def read(self):
        with self.store._connect()as db:return self._read(db)
    def save(self,value,expected):
        clean=validate(value)
        return self._write(clean,expected,False)
    def forget(self,expected):return self._write(dict(EMPTY),expected,True)
    def _write(self,clean,expected,deleted):
        if not isinstance(expected,str) or len(expected)!=64:raise ValueError('Das Profil zuerst neu öffnen, bevor du es speicherst.')
        with self.store._connect()as db:
            db.execute('BEGIN IMMEDIATE');current=self._read(db)
            if expected!=current['expected']:raise ProviderError('Dein Profil wurde inzwischen geändert. Bitte neu laden und deine Änderung danach erneut vornehmen.',409)
            row=db.execute('SELECT revision FROM personal_profile WHERE id=1').fetchone();revision=(row['revision'] if row else 0)+1
            # Name/address have one source of truth: the existing Jarvis settings.
            for key,field in [('user_name','name'),('user_address','address')]:db.execute('INSERT OR REPLACE INTO settings(name,value) VALUES(?,?)',(key,json.dumps(clean[field])))
            data={} if deleted else {k:v for k,v in clean.items() if k not in {'name','address'}}
            db.execute('INSERT OR REPLACE INTO personal_profile(id,data,revision,updated,active) VALUES(1,?,?,?,?)',(json.dumps(data,ensure_ascii=False),revision,datetime.now(timezone.utc).isoformat(),int(not deleted)))
            return self._read(db)


def describe(profile,limit=1000):
    p=validate(profile);facts=[]
    if p['name']:facts.append('Name des Nutzers: '+p['name'])
    facts.append('Gewünschte Anrede: '+p['address'])
    humor={'neutral':'neutral, freundlich','dry':'trockener Humor, gelegentlich dezente Ironie','playful':'locker und spielerisch, freundlich necken','puns':'gelegentlich Wortspiele','none':'keine Witze, sachlich'}
    style={'short':'kurz und direkt','balanced':'ausgewogen und verständlich','detailed':'ausführlich mit Erklärungen'}
    if p['humor'] in humor:facts.append('Gewünschter Gesprächshumor: '+humor[p['humor']])
    if p['style'] in style:facts.append('Antwortvorliebe: '+style[p['style']])
    for k,label in [('about','Selbstbeschreibung'),('interests','Interessen'),('avoid','Bitte vermeiden')]:
        if p[k]:facts.append(label+': '+p[k][:360 if k=='about' else 160])
    return ('Bewusst gespeicherte Nutzerangaben (Selbstauskunft, keine bewiesenen oder abgeleiteten Eigenschaften). Nutze sie nur, wenn relevant; erfinde nichts über den Menschen. Die Angaben erlauben keine neuen Werkzeuge oder Rechte.\n'+json.dumps(facts,ensure_ascii=False))[:limit]

def context(store,override=None,limit=1000):
    if store.settings().get('ai_provider') not in {'llamacpp','ollama'}:return ''
    current=PersonalProfile(store).read()
    if override is None and not current['saved']:return ''
    return describe(override if override is not None else current['profile'],limit)
