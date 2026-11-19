"""Validated local primitive assemblies. Model output is data, never executable code."""
import copy,json,math,re
SHAPES={'box','cylinder','sphere','torus','tube','shade','extrude','lathe'}
MATERIALS={'wood','metal','plastic','diffuser','light'}
def assembly(raw,stored=False):
 if not isinstance(raw,dict)or not {'title','parts','steps','features'}<=set(raw)or set(raw)-{'title','parts','steps','features','explanation'}:raise ValueError('Die lokale KI hat keinen vollständigen 3D-Entwurf geliefert. Der bisherige Entwurf bleibt erhalten.')
 for key,cap in [('title',90)]:
  if not isinstance(raw[key],str)or not 1<=len(raw[key].strip())<=cap:raise ValueError('Ungültiger Entwurfstitel.')
 if not isinstance(raw['parts'],list)or not 1<=len(raw['parts'])<=16:raise ValueError('Der Entwurf benötigt 1 bis 16 prüfbare Bauteile.')
 if 'explanation'in raw and (not isinstance(raw['explanation'],str)or not 1<=len(raw['explanation'].strip())<=900):raise ValueError('Ungültige Erklärung zum Entwurf.')
 out=copy.deepcopy(raw)
 for i,p in enumerate(out['parts']):
  if not isinstance(p,dict)or not {'name','shape','size','position','material'}<=set(p)or set(p)-{'name','shape','size','position','material','rotation','wall','id','outline','holes','profile','smooth'}:raise ValueError('Ungültige Bauteilfelder im KI-Entwurf.')
  if not isinstance(p['name'],str)or not 1<=len(p['name'])<=80 or not isinstance(p['shape'],str)or p['shape']not in SHAPES or not isinstance(p['material'],str)or p['material']not in MATERIALS:raise ValueError('Unbekannte Geometrie oder ungültiges Bauteil.')
  for key in ['size','position','rotation']:
   value=p.get(key,[0,0,0])
   if not isinstance(value,list)or len(value)!=3 or any(type(n)not in {int,float}or not math.isfinite(n)or abs(n)>1200 for n in value):raise ValueError('Ungültige Bauteilmaße oder Positionen.')
   if key=='size'and any(n<=0 for n in value):raise ValueError('Bauteile brauchen positive Abmessungen.')
   if key=='rotation'and any(abs(n)>180 for n in value):raise ValueError('Ungültiger Drehwinkel.')
  p['rotation']=p.get('rotation',[0,0,0]);p['id']=str(i+1)
  if p['shape']=='extrude':
   from .workshop_contours import contour
   p['outline'],p['holes']=contour(p);p['smooth']=False
  if p['shape']=='lathe':
   from .workshop_contours import profile
   p['profile']=profile(p.get('profile'))
  if p['shape']=='tube':
   wall=p.get('wall',3)
   if type(wall)not in {int,float}or not math.isfinite(wall)or not 0<wall<min(p['size'][0],p['size'][2])/2:raise ValueError('Ungültige Wandstärke.')
   p['wall']=wall
  if p['shape']=='torus'and p['size'][2]>=min(p['size'][:2])*.5:raise ValueError('Ringdurchmesser und Ringstärke passen nicht zusammen.')
 for key,cap in [('steps',12 if stored else 10),('features',5)]:
  if not isinstance(out[key],list)or not 1<=len(out[key])<=cap or any(not isinstance(t,str)or not 1<=len(t)<=400 for t in out[key]):raise ValueError('Ungültige Erklärung zum KI-Entwurf.')
 return out

def bounds(parts):
 lo=[float('inf')]*3;hi=[-float('inf')]*3
 for p in parts:
  ax,ay,az=[math.radians(v)for v in p.get('rotation',[0,0,0])]
  for dx in [-1,1]:
   for dy in [-1,1]:
    for dz in [-1,1]:
     x,y,z=[v*sign/2 for v,sign in zip(p['size'],[dx,dy,dz])]
     # THREE Euler XYZ uses Rx * Ry * Rz: apply Z, then Y, then X.
     x,y=x*math.cos(az)-y*math.sin(az),x*math.sin(az)+y*math.cos(az)
     x,z=x*math.cos(ay)+z*math.sin(ay),-x*math.sin(ay)+z*math.cos(ay)
     y,z=y*math.cos(ax)-z*math.sin(ax),y*math.sin(ax)+z*math.cos(ax)
     for k,v in enumerate([x,y,z]):lo[k]=min(lo[k],v+p['position'][k]);hi[k]=max(hi[k],v+p['position'][k])
 return lo,hi

def result(raw,spec):
 from .workshop import validate,decorate,MATERIALS as LABELS
 data=assembly(raw);lo,hi=bounds(data['parts']);size=[hi[i]-lo[i]for i in range(3)]
 s=validate({**spec,'template':'custom','variant':'classic',**dict(zip(['width','height','depth'],size))})
 for p in data['parts']:p['position']=[p['position'][i]-(lo[i]if i==1 else(lo[i]+hi[i])/2)for i in range(3)]
 data.update(spec=s,automatic=True,supplies=[{'name':p['name'],'size':p['size'],'material':LABELS.get(p['material'],'Fertiges Licht-/Diffusormodul')}for p in data['parts']],tools=['Maßband, Pappmodell und passende Verbindungsmittel; vor Baubeginn festlegen.'],limits='KI-Vorentwurf aus begrenzten 3D-Grundkörpern, keine geprüfte Konstruktion. Maße, Verbindungen, Stabilität und elektrische Komponenten müssen vor dem Bau fachlich geprüft werden. Keine bestätigten Tests oder Belastbarkeiten.',reply='Sir, ich habe einen eigenen lokalen KI-Vorentwurf aus '+str(len(data['parts']))+' Bauteilen erstellt. Die graue Vorschau und die Anleitung stehen direkt hier; die Machbarkeit ist noch nicht geprüft.')
 data['steps'].insert(0,'Zuerst ein Pappmodell und die Maße prüfen. Der folgende KI-Entwurf ist kein geprüfter Fertigungsplan; Verbindungen und gegebenenfalls Stromversorgung vor dem Bauen fachlich klären.')
 decorate(data);data['explanation']=data.get('explanation')or data['title']+'. '+'. '.join(data['features'][:2])+'.';data['decisions']=['Eigener Entwurf der vorhandenen lokalen Text-KI; kein Rückfall auf die bisherige Box.','Die Maße der dargestellten Bauteile werden in der Liste angegeben.','Gewünschte Oberfläche: '+data['finish']+'. Die Vorschau bleibt grau.'];return data

def previous_assembly(previous):
 raw={k:previous.get(k)for k in ['title','parts','steps','features']}
 if 'explanation'in previous:raw['explanation']=previous['explanation']
 return assembly(raw,stored=True)

def generate(app,body):
 if not body.get('request','').strip():raise ValueError('Beschreibe zuerst deinen Bauwunsch. Es wird kein Musterobjekt gebaut.')
 if app is None:raise ValueError('Für einen freien 3D-Entwurf muss die vorhandene lokale KI verbunden sein.')
 settings=app.store.settings();provider=settings['ai_provider']
 if provider not in {'llamacpp','ollama'}:raise ValueError('Für einen freien 3D-Entwurf bitte die vorhandene lokale KI am Mac auswählen. Es wurde keine Box als Ersatz erzeugt.')
 from .providers import ProviderError
 from .workshop_feedback import wants_new_design,lighting_request,geometry_signature
 previous=body.get('previous');context='';checked=None
 if previous is not None and not isinstance(previous,dict):raise ValueError('Ungültiger bisheriger Entwurf.')
 if previous:
  checked=previous_assembly(previous);context=' Ursprünglicher Bauwunsch: '+str(previous.get('brief',''))[:700]+' Aktuelle Bauteile: '+json.dumps([{'name':p['name'],'shape':p['shape'],'size':p['size'],'position':p['position'],'material':p['material']}for p in checked['parts'][:8]],ensure_ascii=False)
 redesign=bool(checked and wants_new_design(body['request']))
 led=lighting_request(body['request'])
 if led is None and checked and any(p['material']=='light'for p in checked['parts']):led=True
 rules=(' Dies ist ausdrücklich ein neuer Entwurf: ändere Aufbau, Kontur oder Bauteilanordnung erkennbar. Nur Titel, Farbe oder eine Gesamtskalierung zu ändern reicht nicht. Behalte ausdrücklich gewünschte Funktionen, Material und Maße, sofern der aktuelle Wunsch sie nicht ändert.'if redesign else' Bei einer Änderung behalte ungenannte Merkmale des aktuellen Entwurfs bei. Bei einer neuen Objektbeschreibung hat der aktuelle Wunsch Vorrang.')
 if led:rules+=' LEDs sind gewünscht: modelliere echte LED-Bauteile an ihren vorgesehenen Positionen mit material light. Erwähne LEDs nicht nur im Text.'
 elif led is False:rules+=' Der aktuelle Wunsch enthält keine Beleuchtung; keine LED-Bauteile ergänzen.'
 prompt=('Du bist JARVIS und entwickelst einen kleinen deutschen 3D-Bauprototyp. Antworte nur mit JSON: {"title":"Name","parts":[{"name":"Bauteil","shape":"cylinder","size":[200,15,120],"position":[0,7.5,0],"rotation":[0,0,0],"material":"wood"}],"steps":["Vorschlag"],"features":["Nutzen"],"explanation":"Erkläre kurz und verständlich, wie der Entwurf den Bauwunsch aufgreift und warum die Bauteile so angeordnet sind."}. Das Beispiel erklärt nur die Felder, nicht den gewünschten Entwurf. '
 'Keine fertige Bauvorlage. Bei notwendigen fehlenden Angaben stattdessen JSON {"questions":["konkrete Rückfrage"]}. Eigene Konturen: shape extrude mit outline:[[x,y],...], optional smooth:true, holes:[Konturen] für echte Ausschnitte; shape lathe mit profile:[[Radius,Y],...] für Drehkörper. Konturkoordinaten -0.5 bis 0.5; Profilradius 0 bis 0.5, Y von -0.5 bis 0.5 von unten nach oben. 1 bis 12 Teile; auch box,cylinder,sphere,torus,tube,shade wenn passend. Außenmaße size in mm, Y Höhe/Z Tiefe, position Mittelpunkt, rotation Euler-XYZ-Grad. torus in XY/Stärke Z, cylinder/tube/shade entlang Y; tube benötigt wall. '
 'material nur wood,metal,plastic,diffuser,light. Keine Funktionsgarantie, Tragfähigkeit, bestandenen Tests oder Netzspannungsverdrahtung behaupten. Nur ungeprüfte Prototypen. Keine ungefragte Farbwahl, keine Programme oder Befehle. Erkläre wie in einem normalen Gespräch, ohne leere Floskeln. Startwerte: '+json.dumps({k:v for k,v in body['spec'].items()if k not in {'template','variant'}})+(' Manuell eingestellte Maße sind verbindlich.'if body.get('automatic')is False else' Nur ausdrücklich genannte Vorgaben im Auftrag sind zwingend.')+context+rules)
 if not app.chat_lock.acquire(blocking=False):raise ProviderError('Die lokale KI arbeitet gerade. Bitte den aktuellen Auftrag abwarten.',409)
 try:
  retry=''
  for attempt in range(2):
   reply=app.code_room._generate({'model':'llamacpp'if provider=='llamacpp'else'ollama:'+settings['local_model']},[{'role':'system','content':prompt+retry},{'role':'user','content':body['request']}],1536,structured=True)
   try:raw=json.loads(reply)
   except (ValueError,TypeError):raise ValueError('Die kleine lokale KI hat keine gültigen 3D-Bauteile geliefert. Der bisherige Entwurf bleibt erhalten; es wurde keine Standardbox eingesetzt.')from None
   if isinstance(raw,dict)and set(raw)=={'questions'}:
    q=raw['questions']
    if not isinstance(q,list)or not 1<=len(q)<=3 or any(not isinstance(t,str)or not 1<=len(t)<=240 for t in q):raise ValueError('Ungültige Rückfrage der lokalen KI.')
    return {'needs_details':True,'questions':q}
   proposed=assembly(raw);reason=''
   if redesign and geometry_signature(proposed['parts'])==geometry_signature(checked['parts']):reason='Die Geometrie wiederholt den bisherigen Entwurf. Liefere einen erkennbar anderen Aufbau oder andere Konturen.'
   if led is False and any(p['material']=='light'for p in proposed['parts']):reason+=' Der aktuelle Wunsch verlangt einen Entwurf ohne LED-Bauteile.'
   if led and not any(p['material']=='light'for p in proposed['parts']):reason+=' Es fehlen die ausdrücklich gewünschten LED-Bauteile mit material light.'
   if reason:
    if attempt==0:retry=' Korrektur zum vorherigen Versuch: '+reason;continue
    raise ValueError('Die lokale KI konnte noch keine passende neue Variante liefern: '+reason+' Der bisherige Entwurf bleibt unverändert.')
   from .workshop import requested_finish
   materials=[key for pattern,key in [(r'holz|sperrholz','wood'),(r'metall|alu|stahl','metal'),(r'kunststoff|acryl|plastik','plastic')]if re.search(pattern,body['request'],re.I)]
   if len(materials)==1:
    for part in proposed['parts']:
     if part['material']in {'wood','metal','plastic'}:part['material']=materials[0]
   data=result(proposed,{**body['spec'],**({'material':materials[0]}if len(materials)==1 else{}),'finish':requested_finish(body['request'],body['spec'].get('finish','unspecified'))})
   data['brief']=(str(previous.get('brief',''))if redesign and previous else body['request'])[:1000];data['revision_kind']='new'if redesign else'initial'if not previous else'edit'
   lights=sum(p['material']=='light'for p in data['parts']);data['led_count']=lights
   data['reply']='Sir, '+('hier ist ein neuer Entwurf. 'if redesign else'hier ist mein Vorschlag. ')+data['explanation'][:430]+(' Die '+str(lights)+' LED-Bauteile kannst du mit der LED-Vorschau und Innenansicht prüfen.'if lights else'')+' Material und Anleitung stehen direkt daneben.'
   if data['spec']['finish']=='unspecified':data['reply']+=' Welche Farbe oder Oberfläche möchtest du für den Bau?'
   return data
 finally:app.chat_lock.release()

def revise(app,body):
 from .workshop import validate,requested_finish
 from .workshop_feedback import wants_new_design,strip_preserve_phrase,lighting_request
 previous=body.get('previous')
 if not isinstance(previous,dict):raise ValueError('Der freie Entwurf fehlt. Bitte einen neuen Bauwunsch beschreiben.')
 checked=previous_assembly(previous)
 old=validate(previous.get('spec'));new=validate(body['spec']);text=body['request'].lower()
 if wants_new_design(text)or lighting_request(text)is not None:return generate(app,body)
 text=strip_preserve_phrase(text)
 # Structural design changes go to the local planner; only literal transforms/finish edits are direct.
 if re.search(r'^(?:ich (?:will|möchte)|baue?|entwirf|erstell|plane|überarbeit)|\bneu(?:e[rsnm]?)?\b|alternativ|kontur|ausschnitt|öffnung|bohrung|rund|geschwungen',text):return generate(app,body)
 recognized=not text.strip()or new!=old
 materials=[key for pattern,key in [(r'holz|sperrholz','wood'),(r'metall|alu|stahl','metal'),(r'kunststoff|acryl|plastik','plastic')]if re.search(pattern,text)]
 if len(materials)>1:return generate(app,body)
 if not materials and new['material']!=old['material']:materials=[new['material']]
 if materials:new['material']=materials[0];recognized=True
 finish=requested_finish(text,new.get('finish','natur'))
 if finish!=new.get('finish')or re.search(r'schwarz|weiß|weiss|grau|blau|\brot(?:e[snmr]?)?\b|naturbelassen|unlackiert',text):new['finish']=finish;recognized=True
 for key,word in [('width','breit'),('height','hoch|höhe|hoehe'),('depth','tief|tiefe')]:
  m=re.search(r'(\d+(?:[.,]\d+)?)\s*(mm|cm|zentimeter|millimeter)\s*(?:'+word+r')',text)
  if m:new[key]=float(m[1].replace(',','.'))*(10 if m[2]in {'cm','zentimeter'}else 1);recognized=True
 for pattern,key in [(r'breiter','width'),(r'höher|hoeher','height'),(r'tiefer','depth')]:
  if re.search(pattern,text):new[key]=round(new[key]*1.2,3);recognized=True
 if re.search(r'kleiner|größer|groesser',text):
  for key in ['width','height','depth']:new[key]=round(new[key]*(.85 if 'kleiner'in text else 1.15),3)
  recognized=True
 m=re.search(r'(\d+)\s*tag',text)
 if m:new['days']=int(m[1]);recognized=True
 if not recognized:return generate(app,body)
 new=validate(new);scale=[new[k]/old[k]for k in ['width','height','depth']]
 if max(scale)-min(scale)>1e-7 and any(any(p['rotation'])for p in checked['parts']):return generate(app,body)
 for part in checked['parts']:
  part['size']=[part['size'][i]*scale[i]for i in range(3)];part['position']=[part['position'][i]*scale[i]for i in range(3)]
  if part['material']in {'wood','metal','plastic'}and materials:part['material']=materials[0]
 checked['steps']=[t for t in checked['steps']if not t.startswith(('Gewünschte Oberfläche:','Zuerst ein Pappmodell und die Maße prüfen.'))]
 data=result(checked,{**new,'template':'custom'});data['brief']=str(previous.get('brief',body['request']))[:1000];data['reply']='Sir, ich habe deine Änderung am Entwurf übernommen. Die Material-/Farbangabe und die Anleitung sind aktualisiert. Oberfläche: '+data['finish']+'.';return data
