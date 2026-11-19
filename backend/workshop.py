"""Dimensioned, non-load-rated modular workshop prototypes. No model-generated code."""
import math,re
DEFAULT={'template':'light','material':'wood','width':240,'height':180,'depth':100,'thickness':12,'days':3}
NAMES={'light':'Leuchtobjekt','box':'Offene Aufbewahrungsbox','shelf':'Tischablage','stand':'Geräteständer'}
FINISHES={'unspecified':'noch nicht festgelegt','natur':'naturbelassen','black':'schwarz','white':'weiß','gray':'grau','blue':'blau','red':'rot'}
VARIANTS={'panel','desk','ring','round','classic'}
MATERIALS={'wood':'Holz / Sperrholz','metal':'Metallblech','plastic':'Kunststoffplatte'}
def validate(spec):
 if not isinstance(spec,dict)or not set(DEFAULT)<=set(spec)or set(spec)-set(DEFAULT)-{'finish','variant'}:raise ValueError('Ungültiger Bauentwurf.')
 spec={**spec,'finish':spec.get('finish','unspecified'if spec.get('template')=='custom'else'natur'),'variant':spec.get('variant','panel'if spec.get('template')=='light'else'classic')}
 if not isinstance(spec['finish'],str)or spec['finish']not in FINISHES or not isinstance(spec['variant'],str)or spec['variant']not in VARIANTS:raise ValueError('Ungültige Oberfläche oder Bauform.')
 if not isinstance(spec['template'],str)or spec['template']not in NAMES|{'custom':'Freier Entwurf'} or not isinstance(spec['material'],str)or spec['material']not in MATERIALS:raise ValueError('Bitte eine verfügbare Konstruktion und ein Material auswählen.')
 allowed={'light':{'panel','desk','ring'},'box':{'classic','round'},'shelf':{'classic'},'stand':{'classic'},'custom':{'classic'}}[spec['template']]
 if spec['variant']not in allowed:spec['variant']='panel'if spec['template']=='light'else'classic'
 for k,a,b in [('width',80,1000),('height',60,1000),('depth',50,600),('thickness',1,30),('days',1,30)]:
  if spec['template']=='custom'and k in {'width','height','depth'}:a,b=.1,1200
  v=spec[k]
  if type(v)not in {int,float}or not math.isfinite(v)or not a<=v<=b or k=='days'and int(v)!=v:raise ValueError('Ungültiges Maß oder Zeitfenster: '+k)
 if spec['template']=='light'and spec['variant']=='ring'and spec['height']<=spec['width']+spec['thickness']:raise ValueError('Für das Ringlicht muss die Höhe größer als Ringdurchmesser plus Sockelstärke sein.')
 if spec['template']=='light'and spec['width']<=4*spec['thickness']:raise ValueError('Das Leuchtobjekt ist für diese Materialstärke zu schmal.')
 if spec['template']!='custom'and spec['thickness']*3>=min(spec['width'],spec['height'],spec['depth']):raise ValueError('Die Materialstärke ist für diese Maße zu groß.')
 return dict(spec)
def _design_recipe(body):
 if not isinstance(body,dict)or not {'spec','request'}<=set(body)or set(body)-{'spec','request','automatic'}or not isinstance(body['request'],str)or len(body['request'])>1000:raise ValueError('Bitte einen kurzen Bauwunsch eingeben.')
 if type(body.get('automatic',False))is not bool:raise ValueError('Ungültiger Entwurfsmodus.')
 automatic=body.get('automatic',False)
 s=validate(body['spec']);text=body['request'].lower().strip();recognized=not text
 numbers={'ein':1,'eine':1,'einen':1,'einem':1,'zwei':2,'drei':3,'vier':4,'fünf':5,'sechs':6,'sieben':7,'acht':8,'neun':9,'zehn':10,'elf':11,'zwölf':12,'dreizehn':13,'vierzehn':14,'fünfzehn':15,'sechzehn':16,'siebzehn':17,'achtzehn':18,'neunzehn':19,'zwanzig':20,'dreißig':30}
 for word,n in numbers.items():text=re.sub(r'\b'+word+r'(?=\s*(?:tag|cm|mm|zentimeter|millimeter))',str(n),text)
 delegated=bool(re.search(r'übernimm|uebernimm|entscheide|überrasch|ueberrasch|mach.{0,25}(?:schön|schoen|modern|besser|cool)|verbesser|du planst',text))
 generic=bool(re.search(r'(?:etwas|was) (?:cooles|schönes|schoenes|leuchtendes)|deine idee',text))
 if automatic and (delegated or generic):recognized=True
 alternative=bool(re.search(r'alternative|ander(?:er|en)? vorschlag|\banders\b|mach.{0,25}(?:schöner|schoener)|(?:gefällt|gefaellt|sieht).{0,30}nicht',text))
 if automatic and alternative:recognized=True
 new_plan=automatic and (not text or alternative or generic or bool(re.search(r'^(?:ich (?:will|möchte)|baue?(?: mir)?|erstell|entwirf)',text)) and (bool(re.search(r'\b(?:ein|eine|einen|etwas|was)\b',text)) or not bool(re.search(r'\b(?:es|das|entwurf|modell)\b',text))))
 for pattern,key in [(r'leucht|lampe|licht','light'),(r'box|kiste|kasten','box'),(r'ablage|regal','shelf'),(r'ständer|staender|halter|handy|tablet','stand')]:
  if re.search(pattern,text):s['template']=key;recognized=True;break
 old_kind=body['spec']['template']
 if old_kind!=s['template']:s['variant']='panel'if s['template']=='light'else'classic'
 if s['template']=='light':
  if new_plan and not text:s['variant']='desk'
  if re.search(r'ring|kreis',text):s['variant']='ring';recognized=True
  elif re.search(r'tischlampe|tischleuchte|runde? lampe|leuchtenschirm|lampenschirm',text)or new_plan and re.search(r'lampe|leuchte',text)and not re.search(r'platte|paneel|rahmen|box',text):s['variant']='desk';recognized=True
  elif re.search(r'paneel|panel|lichtrahmen',text):s['variant']='panel';recognized=True
 if s['template']=='box'and re.search(r'rund|oval|zylinder',text):s['variant']='round';recognized=True
 if alternative and s['template']=='light':s['variant']='desk'if s.get('variant')=='panel'else'ring'if s.get('variant')=='desk'else'panel'
 if new_plan:
  recommended={'light':(280,180,70),'box':(300,160,200),'shelf':(360,150,220),'stand':(150,160,115)}[s['template']]
  if s['template']=='light'and s['variant']=='desk':recommended=(220,320,145)
  if s['template']=='light'and s['variant']=='ring':recommended=(220,340,145)
  if s['template']=='box'and s['variant']=='round':recommended=(220,130,220)
  if alternative and s.get('variant')=='panel':recommended={'light':(220,240,75),'box':(240,150,240),'shelf':(420,125,210),'stand':(180,140,130)}[s['template']]
  s.update(zip(['width','height','depth'],recommended));s['material']='metal'if re.search(r'robust|industrial',text)else'wood';s['thickness']=2 if s['material']=='metal'else 12
  if re.search(r'einfach|schnell|anfänger|anfaenger',text):s['days']=2
 if re.search(r'^(?:ich (?:will|möchte)|baue?(?: mir)?|erstell)',text) and not re.search(r'leucht|lampe|licht|box|kiste|kasten|ablage|regal|ständer|staender|halter|handy|tablet',text) and not (automatic and generic) and not re.search(r'\b(?:es|das|entwurf|modell)\b',text):raise ValueError('Für diese neue Bauidee gibt es noch keine passende Standardkonstruktion. Bitte Leuchtobjekt, Box, Tischablage oder Ständer wählen; es wurde nichts ersetzt.')
 for pattern,key in [(r'holz|sperrholz','wood'),(r'metall|alu|stahl','metal'),(r'kunststoff|acryl|plastik','plastic')]:
  if re.search(pattern,text):
   if s['material']!=key:s['thickness']={'wood':12,'metal':2,'plastic':5}[key]
   s['material']=key;recognized=True;break
 m=re.search(r'(\d+)\s*tag',text)
 if m:s['days']=int(m[1]);recognized=True
 for k,word in [('width','breit'),('height','hoch|höhe|hoehe'),('depth','tief|tiefe')]:
  m=re.search(r'(\d+(?:[.,]\d+)?)\s*(mm|cm|zentimeter|millimeter)\s*(?:'+word+r')',text)
  if m:s[k]=float(m[1].replace(',','.'))*(10 if m[2]in {'cm','zentimeter'}else 1);recognized=True
 for pattern,key in [(r'breiter','width'),(r'höher|hoeher','height'),(r'tiefer','depth')]:
  if re.search(pattern,text):s[key]=round(s[key]*1.2);recognized=True
 if re.search(r'kleiner|größer|groesser',text):
  factor=.85 if 'kleiner'in text else 1.15
  for k in ['width','height','depth']:s[k]=round(s[k]*factor)
  recognized=True
 next_finish=requested_finish(text,s['finish'])
 if next_finish!=s['finish']or re.search(r'schwarz|weiß|weiss|grau|blau|\brot(?:e[snmr]?)?\b|naturbelassen|unlackiert',text):s['finish']=next_finish;recognized=True
 if re.search(r'runder|rund|weicher|weniger eckig',text)and s['template']=='light'and s.get('variant')=='panel':s['variant']='desk';s['height']=max(s['height'],260);recognized=True
 if text and not recognized:raise ValueError('Diesen Bauwunsch kann die Werkstatt noch nicht sicher in Bauteile übersetzen. Wähle Leuchtobjekt, Box, Tischablage oder Ständer und gib Maße/Material an. Zum Beispiel: „Aus Holz, 30 cm breit, in 4 Tagen“.')
 result=decorate(blueprint(validate(s)))
 result['automatic']=automatic
 reason={'wood':'Holz/Sperrholz für eine warme Oberfläche und gut erhältliche Zuschnitte.','metal':'Metallblech für den gewünschten technischen Look; fertige, entgratete Zuschnitte einplanen.','plastic':'Kunststoffplatte für eine leichte, abwischbare Oberfläche.'}[s['material']]
 result['decisions']=[reason,'Außenmaße '+str(s['width'])+' × '+str(s['height'])+' × '+str(s['depth'])+' mm; direkt am Modell und in der Teileliste übernommen.','Materialstärke '+str(s['thickness'])+' mm. Verbindungsmittel werden vor dem Bauen auf diese Stärke abgestimmt.','Gewünschte Oberfläche: '+FINISHES[s['finish']]+'. Die Modellansicht bleibt bewusst grau.']
 if s['template']=='light':result['decisions'].append('Diffusor und fertiges 5-V-LED-Modul werden automatisch ergänzt; du musst sie nicht einzeln anordnen.')
 if automatic:result['reply']='Sir, ich habe dir diesen '+NAMES[s['template']]+' vorgeschlagen und Material, Maße und Teile zusammengestellt. '+reason+' Du kannst direkt sagen, was ich ändern soll.'
 return result
def blueprint(s):
 w,h,d,t=[s[k]for k in ['width','height','depth','thickness']];parts=[]
 def part(name,size,pos,material=None,shape='box',rotation=None,wall=None):
  p={'id':str(len(parts)+1),'name':name,'size':size,'position':pos,'material':material or s['material'],'shape':shape}
  if rotation:p['rotation']=rotation
  if wall:p['wall']=wall
  parts.append(p)
 if s['template']=='light'and s.get('variant')=='desk':
  shade_h=h*.24;shade_d=min(w*.36,d*.9);arm_y=h-shade_h/2
  part('Ovaler Holz-/Plattensockel',[w,t,d],[0,t/2,0],shape='cylinder')
  part('Senkrechter Rundstab',[t,arm_y-t,t],[0,(arm_y+t)/2,0],shape='cylinder')
  part('Waagerechter Rundstab',[t,w*.28,t],[w*.14,arm_y,0],shape='cylinder',rotation=[0,0,-90])
  part('Fertiger Leuchtenschirm',[shade_d,shade_h,shade_d],[w*.28,h-shade_h/2,0],'diffuser',shape='shade')
  part('Fertiges 5-V-LED-Modul',[shade_d*.7,5,shade_d*.7],[w*.28,h-shade_h+5,0],'light',shape='cylinder')
 elif s['template']=='light'and s.get('variant')=='ring':
  part('Ovaler Sockel',[w,t,d],[0,t/2,0],shape='cylinder')
  part('Rundstab',[t,h-w-t,t],[0,(h-w+t)/2,0],shape='cylinder')
  part('Fertiger 5-V-LED-Ring',[w,w,10],[0,h-w/2,0],'light',shape='torus')
 elif s['template']=='box'and s.get('variant')=='round':
  part('Runde / ovale Bodenplatte',[w,t,d],[0,t/2,0],shape='cylinder')
  part('Vorgefertigte zylindrische Seitenwand',[w,h-t,d],[0,(h+t)/2,0],shape='tube',wall=t)
 elif s['template']=='light':
  part('Boden',[w,t,d],[0,t/2,0]);part('Linke Seitenwand',[t,h-2*t,d],[-(w-t)/2,h/2,0]);part('Rechte Seitenwand',[t,h-2*t,d],[(w-t)/2,h/2,0]);part('Deckel',[w,t,d],[0,h-t/2,0]);part('Rückwand',[w-2*t,h-2*t,t],[0,h/2,-(d-t)/2]);part('Diffusor',[w-2*t,h-2*t,2],[0,h/2,(d-2)/2],'diffuser');part('5-V-LED-Modul',[w-4*t,6,6],[0,h/2,-d/2+t+8],'light')
 elif s['template']=='box':
  part('Boden',[w,t,d],[0,t/2,0]);part('Linke Seitenwand',[t,h-t,d],[-(w-t)/2,(h+t)/2,0]);part('Rechte Seitenwand',[t,h-t,d],[(w-t)/2,(h+t)/2,0]);part('Vorderwand',[w-2*t,h-t,t],[0,(h+t)/2,(d-t)/2]);part('Rückwand',[w-2*t,h-t,t],[0,(h+t)/2,-(d-t)/2])
 elif s['template']=='shelf':
  part('Linke Stütze',[t,h-t,d],[-(w-t)/2,(h-t)/2,0]);part('Rechte Stütze',[t,h-t,d],[(w-t)/2,(h-t)/2,0]);part('Ablageplatte',[w,t,d],[0,h-t/2,0]);part('Hintere Querstrebe',[w-2*t,t,t],[0,h/2,-(d-t)/2])
 else:
  part('Grundplatte',[w,t,d],[0,t/2,0]);part('Senkrechte Stütze',[w,h-t,t],[0,(h+t)/2,-d/4]);part('Vordere Anschlagleiste',[w,t,t],[0,t*1.5,d/4])
 steps=['Maße am geplanten Standort prüfen. Zuerst ein Pappmodell in Originalgröße testen.','Platten nach der Zuschnittliste im Fachhandel zuschneiden lassen. Alle Kanten glätten; Metall fertig entgraten lassen.','Bauteile trocken aufstellen, Maße und rechte Winkel prüfen. Verbindungen anzeichnen.','Holz: passende Winkel verschrauben oder nach Herstellerangabe verleimen. Metall/Kunststoff: passende vorgebohrte Winkel und Schrauben vom Fachhandel verwenden. Schraubenlängen an die Materialstärke anpassen.']
 if s.get('variant')in {'desk','ring','round'}:steps[1]='Rundstäbe, Scheiben und gegebenenfalls Hohlzylinder als fertige Bauteile oder Zuschnitt im Fachhandel beschaffen. Schirme und LED-Ringe als fertige passende Module wählen; gebogene Holzbauteile nicht aus einer flachen Platte ableiten.'
 if s['template']=='light':steps+=['Nur ein fertiges 5-V-USB- oder Batterie-LED-Modul nach Herstellerangabe befestigen. Keine Netzspannungsverdrahtung. Kabel nicht einklemmen; Leitungsweg vor der Montage prüfen.','Diffusor lösbar mit dafür geeignetem Montageband befestigen. Wärmeentwicklung beobachten und Lüftungsbedarf des LED-Herstellers einhalten.']
 steps+=['Standsicherheit, Verbindungen und scharfe Kanten prüfen. Erst dann vorsichtig im vorgesehenen kleinen Anwendungsbereich ausprobieren.']
 schedule=[{'day':min(s['days'],1+i*(s['days']-1)//(len(steps)-1)),'task':step}for i,step in enumerate(steps)]
 supplies=[{'name':p['name'],'material':MATERIALS.get(p['material'],{'diffuser':'Transluzente Kunststoffplatte','light':'Fertiges 5-V-LED-Modul'}.get(p['material'])),'size':p['size']}for p in parts]
 return {'spec':s,'title':NAMES[s['template']],'parts':parts,'supplies':supplies,'steps':steps,'schedule':schedule,'tools':['Maßband, Bleistift, Winkel','Schleifpapier / fertig entgratete Zuschnitte','Passende Montagewinkel und Schrauben','Schraubendreher, Klemmen'],'features':(['Diffuses Licht mit austauschbarem LED-Modul','Abnehmbarer Diffusor']if s['template']=='light'else ['Modulare Plattenkonstruktion','Maße und Material lassen sich ändern']),'limits':'Maßhaltiger Vorentwurf aus Standardbauteilen, keine geprüfte Statik oder Fertigungsfreigabe. Verbindungsmittel, Toleranzen und Kabeldurchführung müssen vor dem Bauen passend festgelegt werden. Nicht für tragende oder sicherheitskritische Konstruktionen.','reply':'Sir, dein '+NAMES[s['template']]+' ist als 3D-Vorentwurf mit '+str(len(parts))+' Bauteilen vorbereitet. Die Maße, Einkaufsliste und ein Vorschlag für '+str(s['days'])+' Tage stehen daneben.'}


def decorate(result):
 s=result['spec'];finish=s.get('finish','natur');label=FINISHES[finish]
 result['finish']=label
 if finish not in {'natur','unspecified'}:
  result['steps'].insert(2,'Gewünschte Oberfläche: '+label+'. Holz dafür passend beizen oder mit geeignetem Holzlack behandeln; Metall/Kunststoff nur mit dafür geeignetem Produkt. Herstellerhinweise beachten, vollständig trocknen lassen und Leuchtmittel nicht überstreichen.')
 for p,stock in zip(result['parts'],result['supplies']):
  stock['shape']=p.get('shape','box')
  if p['material']in MATERIALS:stock['material']+=' · '+label
 result['schedule']=[{'day':min(s['days'],1+i*(s['days']-1)//max(1,len(result['steps'])-1)),'task':step}for i,step in enumerate(result['steps'])]
 if s.get('variant')=='desk':result['title']='Tischleuchte mit Rundstäben'
 if s.get('variant')=='ring':result['title']='Ringlicht auf Rundstab'
 if s.get('variant')=='round'and s['template']=='box':result['title']='Runde / ovale Aufbewahrungsbox'
 return result


def design(body,app=None):
 if not isinstance(body,dict):raise ValueError('Ungültiger Bauwunsch.')
 clean={k:v for k,v in body.items()if k not in {'previous','free_design','regenerate'}}
 if set(body)-{'spec','request','automatic','previous','free_design','regenerate'}:raise ValueError('Unbekannte Werkstattfelder.')
 # Validate dimensions before considering any local model request.
 validate(clean.get('spec'));request=clean.get('request')
 if not isinstance(request,str)or len(request)>(2400 if body.get('free_design')else 1000):raise ValueError('Bauwunsch oder Rückfrage-Antwort ist zu lang. Bitte kürzer formulieren.')
 if type(body.get('automatic',False))is not bool or type(body.get('regenerate',False))is not bool:raise ValueError('Ungültiger Entwurfsmodus.')
 if type(body.get('free_design',False))is not bool:raise ValueError('Ungültiger Entwurfsmodus.')
 if body.get('free_design')and (body['spec'].get('template')!='custom'or not body.get('previous')or body.get('regenerate')):
  from .workshop_free import generate
  return generate(app,body)
 if body['spec'].get('template')=='custom':
  from .workshop_free import revise
  return revise(app,body)
 try:return _design_recipe(clean)
 except ValueError as error:
  if app is None or not str(error).startswith(('Für diese neue Bauidee','Diesen Bauwunsch')):raise
  from .workshop_free import generate
  return generate(app,body)


def requested_finish(text,default='natur'):
 text=text.lower()
 for pattern,key in [(r'\bschwarz\w*','black'),(r'\b(?:weiß|weiss)\w*','white'),(r'\bgrau\w*','gray'),(r'\bblau\w*','blue'),(r'\brot(?:e[snmr]?)?\b','red'),(r'naturbelassen|unlackiert','natur')]:
  if re.search(pattern,text):return key
 return default
