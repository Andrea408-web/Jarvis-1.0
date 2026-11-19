"""Validated local primitive assemblies. Model output is data, never executable code."""
import copy,json,math,re
SHAPES={'box','cylinder','sphere','torus','tube','shade','extrude','lathe'}
MATERIALS={'wood','metal','plastic','diffuser','light'}
def assembly(raw,stored=False):
 if not isinstance(raw,dict)or set(raw)!={'title','parts','steps','features'}:raise ValueError('Die lokale KI hat keinen vollständigen 3D-Entwurf geliefert. Der bisherige Entwurf bleibt erhalten.')
 for key,cap in [('title',90)]:
  if not isinstance(raw[key],str)or not 1<=len(raw[key].strip())<=cap:raise ValueError('Ungültiger Entwurfstitel.')
 if not isinstance(raw['parts'],list)or not 1<=len(raw['parts'])<=16:raise ValueError('Der Entwurf benötigt 1 bis 16 prüfbare Bauteile.')
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
 decorate(data);data['decisions']=['Eigener Entwurf der vorhandenen lokalen Text-KI; kein Rückfall auf die bisherige Box.','Die Maße der dargestellten Bauteile werden in der Liste angegeben.','Gewünschte Oberfläche: '+data['finish']+'. Die Vorschau bleibt grau.'];return data

def generate(app,body):
 if not body.get('request','').strip():raise ValueError('Beschreibe zuerst deinen Bauwunsch. Es wird kein Musterobjekt gebaut.')
 if app is None:raise ValueError('Für einen freien 3D-Entwurf muss die vorhandene lokale KI verbunden sein.')
 settings=app.store.settings();provider=settings['ai_provider']
 if provider not in {'llamacpp','ollama'}:raise ValueError('Für einen freien 3D-Entwurf bitte die vorhandene lokale KI am Mac auswählen. Es wurde keine Box als Ersatz erzeugt.')
 from .providers import ProviderError
 previous=body.get('previous');context=''
 if previous is not None and not isinstance(previous,dict):raise ValueError('Ungültiger bisheriger Entwurf.')
 if previous:
  checked=assembly({k:previous[k]for k in ['title','parts','steps','features']},stored=True);context=' Ausgangswunsch: '+str(previous.get('brief',''))[:700]+' Bisherige Bauteile zur Orientierung: '+json.dumps([{'name':p['name'],'shape':p['shape'],'size':p['size'],'position':p['position']}for p in checked['parts'][:8]],ensure_ascii=False)
 prompt=('Du entwirfst einen kleinen deutschen 3D-Bauprototyp. Gib ausschließlich JSON zurück: {"title":"Name","parts":[{"name":"Bauteil","shape":"cylinder","size":[200,15,120],"position":[0,7.5,0],"rotation":[0,0,0],"material":"wood"}],"steps":["Vorschlag"],"features":["Nutzen"]}. '
 'Du darfst keine fertige Bauvorlage auswählen. Beschreibe nur den Wunsch des Nutzers; bei notwendigen fehlenden Angaben antworte stattdessen mit JSON {"questions":["konkrete Rückfrage"]}. Verwende bevorzugt eigene Konturen: shape extrude mit outline:[[x,y],...], optional smooth:true für eine geschlossene weiche Konturkurve, und holes:[Konturen] für echte durchgehende Ausschnitte, oder shape lathe mit profile:[[Radius,Y],...] für Drehkörper. Konturkoordinaten normiert von -0.5 bis 0.5; Profilradius 0 bis 0.5, Y von -0.5 bis 0.5 von unten nach oben. Größen sind Außenmaße in mm. 1 bis 12 Teile. shape darf auch box,cylinder,sphere,torus,tube,shade sein, wenn genau passend. Alle Maße in Millimeter. Y ist Höhe, Z Tiefe. size sind äußere X/Y/Z-Maße; position ist der Mittelpunkt. rotation sind Euler-XYZ-Grad. torus liegt in XY mit Stärke Z, cylinder/tube/shade sind entlang Y. tube braucht wall als Wandstärke. '
 'material nur wood,metal,plastic,diffuser,light. Verwende runde Formen, wenn gewünscht; keine ungefragte Box. Anleitung nur als ungeprüfter, kleiner Prototyp; keine Tragfähigkeit, funktionierenden Fahrzeuge oder bestandenen Tests behaupten. Keine Netzspannungsverdrahtung. Keine ungefragten Farbvorgaben; Farbe/Oberfläche werden getrennt festgelegt. Keine Dateipfade, Programme oder Befehle. Entwurfsmaße als Startwerte (keine Bauvorlage): '+json.dumps({k:v for k,v in body['spec'].items()if k not in {'template','variant'}})+('. Die eingestellten Maße sind verbindliche Nutzervorgaben.'if body.get('automatic')is False else'. Nur ausdrücklich genannte Vorgaben im Auftrag sind zwingend; sonst passende Maße selbst begründen.')+context)
 if not app.chat_lock.acquire(blocking=False):raise ProviderError('Die lokale KI arbeitet gerade. Bitte den aktuellen Auftrag abwarten.',409)
 try:
  reply=app.code_room._generate({'model':'llamacpp'if provider=='llamacpp'else'ollama:'+settings['local_model']},[{'role':'system','content':prompt},{'role':'user','content':body['request']}],1536,structured=True)
  try:raw=json.loads(reply)
  except (ValueError,TypeError):raise ValueError('Die kleine lokale KI hat keine gültigen 3D-Bauteile geliefert. Der bisherige Entwurf bleibt erhalten; es wurde keine Standardbox eingesetzt.')from None
  if isinstance(raw,dict)and set(raw)=={'questions'}:
   q=raw['questions']
   if not isinstance(q,list)or not 1<=len(q)<=3 or any(not isinstance(t,str)or not 1<=len(t)<=240 for t in q):raise ValueError('Ungültige Rückfrage der lokalen KI.')
   return {'needs_details':True,'questions':q}
  from .workshop import requested_finish
  materials=[key for pattern,key in [(r'holz|sperrholz','wood'),(r'metall|alu|stahl','metal'),(r'kunststoff|acryl|plastik','plastic')]if re.search(pattern,body['request'],re.I)]
  proposed=assembly(raw)
  if len(materials)==1:
   for part in proposed['parts']:
    if part['material']in {'wood','metal','plastic'}:part['material']=materials[0]
  data=result(proposed,{**body['spec'],**({'material':materials[0]}if len(materials)==1 else{}),'finish':requested_finish(body['request'],body['spec'].get('finish','unspecified'))});data['brief']=body['request'][:1000]
  if data['spec']['finish']=='unspecified':data['reply']+=' Welche Farbe oder Oberfläche möchtest du für den Bau? Die Vorschau bleibt grau.'
  return data
 finally:app.chat_lock.release()

def revise(app,body):
 from .workshop import validate,requested_finish
 previous=body.get('previous')
 if not isinstance(previous,dict):raise ValueError('Der freie Entwurf fehlt. Bitte einen neuen Bauwunsch beschreiben.')
 checked=assembly({k:previous.get(k)for k in ['title','parts','steps','features']},stored=True)
 old=validate(previous.get('spec'));new=validate(body['spec']);text=body['request'].lower()
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
