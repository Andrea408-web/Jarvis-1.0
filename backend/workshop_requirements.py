"""Requirement handling without substituting invented parts or machine capabilities."""
import copy,re

def complex_goal(request,previous=None):
    if re.search(r'komplex|mechanik|robot|greifer|gelenk|servo|motor|automati|antrieb|sensor|steuerung|beweglich|mechanisch',request,re.I):return True
    return bool(previous and previous.get('concept')and not re.search(r'^(?:baue?|entwirf|erstell|plane|ich (?:will|möchte))\b',request,re.I))

def unpack_lighting(raw,lighting):
    raw=copy.deepcopy(raw)
    if isinstance(raw,dict)and 'lighting'in raw:
        if lighting is not True or not isinstance(raw['lighting'],dict)or not isinstance(raw.get('parts'),list):raise ValueError('Ungültiges separat modelliertes LED-Modul.')
        raw['parts']=[raw.pop('lighting')]+raw['parts']
    return raw

def normalize_emitters(raw,lighting):
    """A clearly named LED module is an emitter, even if its housing is plastic.

    Preserve its generated geometry; never turn a bracket/diffuser into a lamp or
    add a stock part at a guessed location. No correction when LEDs were removed.
    """
    raw=copy.deepcopy(raw);notes=[]
    if lighting is not True or not isinstance(raw,dict)or not isinstance(raw.get('parts'),list):return raw,notes
    for p in raw['parts']:
        if not isinstance(p,dict):continue
        name=p.get('name','')
        if not isinstance(name,str):continue
        if re.search(r'\bleds?\b|led[- ]?(?:modul|streifen|ring|diode|leiste|band|platine|panel|chip)',name,re.I)and not re.search(r'halter|gehäuse|gehaeuse|sockel|diffusor|abdeckung|kanal|aufnahme|schraub|montage|fassung|ausschnitt|kabel|holz|stütz|traeger|träger|rahmen|platte|fuß|fuss|steg',name,re.I)and p.get('material')in {'wood','metal','plastic','diffuser'}:
            p['material']='light';notes.append('Das bereits modellierte Bauteil „'+name[:80]+'“ wird als LED-Lichtmodul angezeigt.')
    return raw,notes

def validate_concept(value):
    if not isinstance(value,dict)or set(value)!={'systems','workflow','unresolved'}:raise ValueError('Das komplexe Konzept braucht Baugruppen, Funktionsablauf und offene Prüfpunkte.')
    systems=value['systems']
    if not isinstance(systems,list)or not 2<=len(systems)<=6:raise ValueError('Ein komplexes Konzept braucht zwei bis sechs Baugruppen.')
    for system in systems:
        if not isinstance(system,dict)or set(system)!={'name','function'}or any(not isinstance(system[k],str)or not 1<=len(system[k].strip())<=cap for k,cap in [('name',80),('function',260)]):raise ValueError('Ungültige Baugruppenbeschreibung.')
    for key in ['workflow','unresolved']:
        if not isinstance(value[key],list)or not 1<=len(value[key])<=6 or any(not isinstance(t,str)or not 1<=len(t.strip())<=300 for t in value[key]):raise ValueError('Ungültiger Funktionsablauf oder Prüfpunkt.')
    return copy.deepcopy(value)
