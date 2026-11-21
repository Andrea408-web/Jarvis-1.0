"""Requirement handling without substituting invented parts or machine capabilities."""
import copy,math,re

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


def form_request(request,previous=None):
    """Only explicit form wishes constrain geometry; rounded edges may stay boxes.

    A short follow-up keeps the original form requirement. A new complete object
    request, or a positive square/rectangular wish, replaces it.
    """
    text=request.casefold()
    no_boxes=re.search(r'(?:nicht|kein(?:e[snmr]?)?|ohne).{0,28}(?:eckig|viereck|kasten|kästen|quader|box)|(?:nur|immer).{0,18}(?:viereck|kasten|kästen|box)',text)
    if re.search(r'geschwungen|organisch|freiform|fließend|fliessend|eigene[nrms]? kontur',text) or no_boxes:return 'custom'
    if re.search(r'\brund(?:e[snmr]?)?\b|kreisförmig|kreisfoermig|kreisrund|oval|kugelförmig|kugelfoermig|zylindrisch',text):return 'round'
    if re.search(r'eckig|rechteck|viereck|quader|würfel|wuerfel|kasten|\bbox\b',text):return None
    if previous and not re.search(r'^(?:baue?|entwirf|erstell|plane|ich (?:will|möchte))\b',text):
        return form_request(str(previous.get('brief','')))
    return None

def unpack_form(raw,required):
    raw=copy.deepcopy(raw)
    if isinstance(raw,dict)and 'form'in raw:
        if not required or not isinstance(raw['form'],dict)or not isinstance(raw.get('parts'),list):raise ValueError('Ungültiges separat modelliertes Formbauteil.')
        raw['parts']=[raw.pop('form')]+raw['parts']
    return raw

def form_error(parts,required,source=None):
    """Test real geometry, not names: an ornamental sphere cannot fix a box body."""
    if not required:return ''
    solid=[p for p in parts if p['material']!='light']
    if not solid:return 'Der gewünschte Körper fehlt; ein Lichtmodul allein erfüllt den Formwunsch nicht.'
    volume=lambda p:math.prod(p['size'])
    main=max(volume(p)for p in solid)
    def authored(p,index):
        if p['shape']=='lathe':
            profile=p['profile']
            # End caps at radius zero do not make a cylinder a free profile.
            radii=[v[0]for v in profile if v[0]>.005]
            return len(profile)>=4 and len(radii)>=2 and max(radii)-min(radii)>.03
        if p['shape']=='extrude':
            # A four-corner rectangle with an edge bevel is still a rectangle.
            outline=p['outline'];original=(source or parts)[index].get('outline',[])
            area=abs(sum(a[0]*b[1]-b[0]*a[1]for a,b in zip(outline,outline[1:]+outline[:1]))/2)
            return len(original)>=5 and area<.9 and any(abs(x)<.48 and abs(y)<.48 for x,y in outline)
        return False
    curved={'cylinder','sphere','torus','tube','shade','lathe','extrude'}
    for index,p in enumerate(parts):
        if p['material']=='light' or volume(p)<main*.25:continue
        if required=='custom' and authored(p,index):return ''
        if required=='round' and (p['shape']in curved-{'extrude'} or authored(p,index)):return ''
    return ('Die ausdrücklich gewünschte eigene geschwungene Form fehlt. Liefere ein deutliches Hauptbauteil mit eigener nichtrechteckiger extrude-Kontur oder einem variierenden lathe-Profil; ein abgerundeter Kasten oder eine kleine Zierkugel reicht nicht.' if required=='custom' else 'Die ausdrücklich gewünschte runde Form fehlt am Hauptkörper. Liefere ein ausreichend großes rundes Hauptbauteil statt nur Kästen oder einer kleinen Zierkugel.')


def camera_request(request,previous=None):
    text=request.casefold()
    if re.search(r'(?:ohne|keine?)\s+(?:eine?\s+)?(?:kamera|camera|webcam|handtracking|gestensteuerung)',text):return False
    if re.search(r'kamera|camera|webcam|handtracking|gestensteuerung|handgest',text):return True
    if previous and not re.search(r'^(?:baue?|entwirf|erstell|plane|ich (?:will|möchte))\b',text):return camera_request(str(previous.get('brief','')))
    return False

def camera_error(parts,required):
    if required and not any(re.search(r'kamera|camera|webcam',p['name'],re.I)and p['material']!='light'for p in parts):
        return 'Die für Kamera-/Handgestenbedienung benötigte Kamera fehlt als eigenes benanntes Bauteil. Zeige ihr vorgesehenes Modul im Entwurf; behaupte keine bereits funktionierende Bildanalyse.'
    return ''


def normalize_dimensions(raw):
    """Decode fractional-mm text from the constrained generation contract only.

    Never invent, abs(), clamp or fill dimensions. Saved geometry stays numeric;
    assembly still rejects zero/negative numbers from nonconforming runtimes.
    """
    from .workshop_schema import DIMENSION_PATTERN
    raw=copy.deepcopy(raw);notes=[]
    if not isinstance(raw,dict)or not isinstance(raw.get('parts'),list):return raw,notes
    for p in raw['parts']:
        if not isinstance(p,dict)or not isinstance(p.get('size'),list):continue
        for i,value in enumerate(p['size']):
            if not isinstance(value,str):continue
            if re.fullmatch(DIMENSION_PATTERN,value) is None:raise ValueError('Ungültige Millimeterangabe. Bruchmaße müssen zwischen 0.1 und 1200 mm liegen, ohne Einheit oder Vorzeichen.')
            p['size'][i]=float(value)
    return raw,notes


def reference_request(request):
    """Keep web excerpts separate from the user's geometry requirements.

    This is text evidence only. No pixels, model download, vision or code execution.
    An unfinished imported block is not interpreted as a user's instruction.
    """
    sources=[]
    def take(match):
        if len(sources)<3:sources.append(match.group(1).strip()[:500])
        return '\n'
    wish=re.sub(r'\[WEBREFERENZ\](.*?)\[/WEBREFERENZ\]',take,request,flags=re.S)
    wish=wish.split('[WEBREFERENZ]',1)[0].strip()
    return wish,sources


def reference_detail_error(parts,request,references):
    """Check an explicit ring count against generated geometry, not its title."""
    if not references:return ''
    match=re.search(r'\b(2|3|4|5|6|zwei|drei|vier|fünf|fuenf|sechs)\s+(?:(?:konzentrische[nr]?|sichtbare[nr]?|getrennte[nr]?|verschiedene[nr]?)\s+)?ringe[n]?\b',request,re.I)
    if not match:return ''
    counts={'zwei':2,'drei':3,'vier':4,'fünf':5,'fuenf':5,'sechs':6}
    count=counts.get(match[1].casefold())or int(match[1])
    actual=sum(p['shape']in {'torus','tube'}or p['shape']=='extrude'and bool(p.get('holes'))for p in parts)
    if actual<count:return 'Die ausdrücklich gewünschten '+str(count)+' getrennten Ringe fehlen als echte Ringgeometrie (torus, tube oder Kontur mit Loch). Bezeichnungen allein reichen nicht.'
    return ''
