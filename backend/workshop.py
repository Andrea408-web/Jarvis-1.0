"""Dimensioned, non-load-rated modular workshop prototypes. No model-generated code."""
import math,re
DEFAULT={'template':'light','material':'wood','width':240,'height':180,'depth':100,'thickness':12,'days':3}
NAMES={'light':'Leuchtobjekt','box':'Offene Aufbewahrungsbox','shelf':'Tischablage','stand':'Geräteständer'}
MATERIALS={'wood':'Holz / Sperrholz','metal':'Metallblech','plastic':'Kunststoffplatte'}
def validate(spec):
 if not isinstance(spec,dict)or set(spec)!=set(DEFAULT):raise ValueError('Ungültiger Bauentwurf.')
 if not isinstance(spec['template'],str)or spec['template']not in NAMES or not isinstance(spec['material'],str)or spec['material']not in MATERIALS:raise ValueError('Bitte eine verfügbare Konstruktion und ein Material auswählen.')
 for k,a,b in [('width',80,1000),('height',60,1000),('depth',50,600),('thickness',1,30),('days',1,30)]:
  v=spec[k]
  if type(v)not in {int,float}or not math.isfinite(v)or not a<=v<=b or k=='days'and int(v)!=v:raise ValueError('Ungültiges Maß oder Zeitfenster: '+k)
 if spec['template']=='light'and spec['width']<=4*spec['thickness']:raise ValueError('Das Leuchtobjekt ist für diese Materialstärke zu schmal.')
 if spec['thickness']*3>=min(spec['width'],spec['height'],spec['depth']):raise ValueError('Die Materialstärke ist für diese Maße zu groß.')
 return dict(spec)
def design(body):
 if not isinstance(body,dict)or set(body)!={'spec','request'}or not isinstance(body['request'],str)or len(body['request'])>1000:raise ValueError('Bitte einen kurzen Bauwunsch eingeben.')
 s=validate(body['spec']);text=body['request'].lower().strip();recognized=not text
 numbers={'ein':1,'eine':1,'einen':1,'einem':1,'zwei':2,'drei':3,'vier':4,'fünf':5,'sechs':6,'sieben':7,'acht':8,'neun':9,'zehn':10,'elf':11,'zwölf':12,'dreizehn':13,'vierzehn':14,'fünfzehn':15,'sechzehn':16,'siebzehn':17,'achtzehn':18,'neunzehn':19,'zwanzig':20,'dreißig':30}
 for word,n in numbers.items():text=re.sub(r'\b'+word+r'(?=\s*(?:tag|cm|mm|zentimeter|millimeter))',str(n),text)
 for pattern,key in [(r'leucht|lampe|licht','light'),(r'box|kiste|kasten','box'),(r'ablage|regal','shelf'),(r'ständer|staender|halter','stand')]:
  if re.search(pattern,text):s['template']=key;recognized=True;break
 if re.search(r'^(?:ich (?:will|möchte)|baue?(?: mir)?|erstell)',text) and not re.search(r'leucht|lampe|licht|box|kiste|kasten|ablage|regal|ständer|staender|halter',text) and not re.search(r'\b(?:es|das|entwurf|modell)\b',text):raise ValueError('Für diese neue Bauidee gibt es noch keine passende Standardkonstruktion. Bitte Leuchtobjekt, Box, Tischablage oder Ständer wählen; es wurde nichts ersetzt.')
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
 if text and not recognized:raise ValueError('Diesen Bauwunsch kann die Werkstatt noch nicht sicher in Bauteile übersetzen. Wähle Leuchtobjekt, Box, Tischablage oder Ständer und gib Maße/Material an. Zum Beispiel: „Aus Holz, 30 cm breit, in 4 Tagen“.')
 return blueprint(validate(s))
def blueprint(s):
 w,h,d,t=[s[k]for k in ['width','height','depth','thickness']];parts=[]
 def part(name,size,pos,material=None):parts.append({'id':str(len(parts)+1),'name':name,'size':size,'position':pos,'material':material or s['material']})
 if s['template']=='light':
  part('Boden',[w,t,d],[0,t/2,0]);part('Linke Seitenwand',[t,h-2*t,d],[-(w-t)/2,h/2,0]);part('Rechte Seitenwand',[t,h-2*t,d],[(w-t)/2,h/2,0]);part('Deckel',[w,t,d],[0,h-t/2,0]);part('Rückwand',[w-2*t,h-2*t,t],[0,h/2,-(d-t)/2]);part('Diffusor',[w-2*t,h-2*t,2],[0,h/2,(d-2)/2],'diffuser');part('5-V-LED-Modul',[w-4*t,6,6],[0,h/2,-d/2+t+8],'light')
 elif s['template']=='box':
  part('Boden',[w,t,d],[0,t/2,0]);part('Linke Seitenwand',[t,h-t,d],[-(w-t)/2,(h+t)/2,0]);part('Rechte Seitenwand',[t,h-t,d],[(w-t)/2,(h+t)/2,0]);part('Vorderwand',[w-2*t,h-t,t],[0,(h+t)/2,(d-t)/2]);part('Rückwand',[w-2*t,h-t,t],[0,(h+t)/2,-(d-t)/2])
 elif s['template']=='shelf':
  part('Linke Stütze',[t,h-t,d],[-(w-t)/2,(h-t)/2,0]);part('Rechte Stütze',[t,h-t,d],[(w-t)/2,(h-t)/2,0]);part('Ablageplatte',[w,t,d],[0,h-t/2,0]);part('Hintere Querstrebe',[w-2*t,t,t],[0,h/2,-(d-t)/2])
 else:
  part('Grundplatte',[w,t,d],[0,t/2,0]);part('Senkrechte Stütze',[w,h-t,t],[0,(h+t)/2,-d/4]);part('Vordere Anschlagleiste',[w,t,t],[0,t*1.5,d/4])
 steps=['Maße am geplanten Standort prüfen. Zuerst ein Pappmodell in Originalgröße testen.','Platten nach der Zuschnittliste im Fachhandel zuschneiden lassen. Alle Kanten glätten; Metall fertig entgraten lassen.','Bauteile trocken aufstellen, Maße und rechte Winkel prüfen. Verbindungen anzeichnen.','Holz: passende Winkel verschrauben oder nach Herstellerangabe verleimen. Metall/Kunststoff: passende vorgebohrte Winkel und Schrauben vom Fachhandel verwenden. Schraubenlängen an die Materialstärke anpassen.']
 if s['template']=='light':steps+=['Nur ein fertiges 5-V-USB- oder Batterie-LED-Modul nach Herstellerangabe befestigen. Keine Netzspannungsverdrahtung. Kabel nicht einklemmen; Leitungsweg vor der Montage prüfen.','Diffusor lösbar mit dafür geeignetem Montageband befestigen. Wärmeentwicklung beobachten und Lüftungsbedarf des LED-Herstellers einhalten.']
 steps+=['Standsicherheit, Verbindungen und scharfe Kanten prüfen. Erst dann vorsichtig im vorgesehenen kleinen Anwendungsbereich ausprobieren.']
 schedule=[{'day':min(s['days'],1+i*(s['days']-1)//(len(steps)-1)),'task':step}for i,step in enumerate(steps)]
 supplies=[{'name':p['name'],'material':MATERIALS.get(p['material'],{'diffuser':'Transluzente Kunststoffplatte','light':'Fertiges 5-V-LED-Modul'}.get(p['material'])),'size':p['size']}for p in parts]
 return {'spec':s,'title':NAMES[s['template']],'parts':parts,'supplies':supplies,'steps':steps,'schedule':schedule,'tools':['Maßband, Bleistift, Winkel','Schleifpapier / fertig entgratete Zuschnitte','Passende Montagewinkel und Schrauben','Schraubendreher, Klemmen'],'features':(['Diffuses Licht mit austauschbarem LED-Modul','Abnehmbarer Diffusor']if s['template']=='light'else ['Modulare Plattenkonstruktion','Maße und Material lassen sich ändern']),'limits':'Maßhaltiger Vorentwurf aus Standardbauteilen, keine geprüfte Statik oder Fertigungsfreigabe. Verbindungsmittel, Toleranzen und Kabeldurchführung müssen vor dem Bauen passend festgelegt werden. Nicht für tragende oder sicherheitskritische Konstruktionen.','reply':'Sir, dein '+NAMES[s['template']]+' ist als 3D-Vorentwurf mit '+str(len(parts))+' Bauteilen vorbereitet. Die Maße, Einkaufsliste und ein Vorschlag für '+str(s['days'])+' Tage stehen daneben.'}
