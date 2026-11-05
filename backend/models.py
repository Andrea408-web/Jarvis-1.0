"""Bounded geometric scenes, built locally and handed to Blender as data."""
import json
import math
import re
from pathlib import Path

SHAPES={'cube','sphere','cylinder','cone','torus','wedge'}

def part(name,shape='cube',location=(0,0,0),scale=(1,1,1),color=(.18,.5,.8),rotation=(0,0,0)):
    return dict(name=name,shape=shape,location=list(location),scale=list(scale),color=list(color),rotation=list(rotation))

def recipe(goal):
    s=goal.casefold()
    if not re.search(r'blender|3d|modell|model[l]?ier|skulptur',s):return None
    if re.search(r'\b(tisch|schreibtisch|desk|table)\b',s):
        parts=[part('Tischplatte',location=(0,0,2),scale=(2,1,.15))]+[part('Tischbein',location=(x,y,1),scale=(.13,.13,1),color=(.15,.18,.23)) for x in [-1.7,1.7] for y in [-.7,.7]]
    elif re.search(r'\b(stuhl|chair)\b',s):
        parts=[part('Sitz',location=(0,0,1.5),scale=(1,1,.15)),part('Lehne',location=(0,.9,2.3),scale=(1,.12,.8))]+[part('Bein',location=(x,y,.7),scale=(.1,.1,.7)) for x in [-.8,.8] for y in [-.8,.8]]
    elif re.search(r'\b(haus|house)\b',s):
        parts=[part('Haus',location=(0,0,1.5),scale=(2,1.5,1.5),color=(.85,.75,.5)),part('Dach','cone',(0,0,3.6),(2.6,2.1,1.1),(.55,.13,.08)),part('Tür',location=(0,-1.52,.8),scale=(.4,.04,.8),color=(.2,.12,.06))]+[part('Fenster',location=(x,-1.53,1.9),scale=(.4,.04,.45),color=(.2,.7,.9)) for x in [-1.2,1.2]]
    elif re.search(r'\b(auto|car|fahrzeug|lamborghini|sportwagen)\b',s):
        parts=[part('Karosserie',location=(0,0,.8),scale=(2,1,.4),color=(.1,.35,.8)),part('Kabine',location=(.1,0,1.4),scale=(1.05,.85,.45),color=(.2,.65,.85))]+[part('Rad','cylinder',(x,y,.4),(.45,.45,.23),(.06,.07,.08),(math.pi/2,0,0)) for x in [-1.3,1.3] for y in [-1.03,1.03]]
        if re.search(r'lamborghini|sportwagen',s):
            parts[0]['shape']='wedge';parts[1]['shape']='wedge';parts[0]['name']='Sportwagen-Karosserie';parts[0]['color']=[.95,.65,.04];parts[1]['location']=[.15,0,1.3];parts[1]['scale']=[.9,.8,.35]
            parts.extend([part('Motorhaube',location=(-1.3,0,1),scale=(.65,.92,.12),color=(.95,.65,.04)),part('Heckspoiler',location=(1.65,0,1.3),scale=(.15,1.05,.08),color=(.12,.13,.16))])
            for x in [-1.3,1.3]:
                for y in [-1.28,1.28]:parts.append(part('Felge','cylinder',(x,y,.4),(.29,.29,.035),(.6,.63,.67),(math.pi/2,0,0)))
            for y in [-.65,.65]:parts.append(part('Scheinwerfer',location=(-2.02,y,.9),scale=(.03,.22,.08),color=(.9,.95,1)))
    elif re.search(r'\b(roboter|robot)\b',s):
        parts=[part('Rumpf',location=(0,0,2.5),scale=(.8,.45,.9)),part('Kopf',location=(0,0,3.8),scale=(.65,.5,.5)),part('Auge',location=(-.25,-.51,3.9),scale=(.12,.03,.12),color=(.9,.95,1)),part('Auge',location=(.25,-.51,3.9),scale=(.12,.03,.12),color=(.9,.95,1))]+[part('Bein',location=(x,0,.8),scale=(.25,.35,.8)) for x in [-.45,.45]]+[part('Arm',location=(x,0,2.5),scale=(.2,.3,.8)) for x in [-1.1,1.1]]
    elif re.search(r'\b(rakete|rocket)\b',s):
        parts=[part('Rumpf','cylinder',(0,0,2),(.7,.7,2),(.8,.85,.9)),part('Spitze','cone',(0,0,4.6),(.7,.7,.8),(.8,.15,.1)),part('Triebwerk','cone',(0,0,-.2),(.5,.5,.5),(.3,.35,.4))]+[part('Flosse',location=(x,y,.4),scale=(.18,.6,.7),color=(.8,.15,.1),rotation=(0,0,r)) for x,y,r in [(0,.9,0),(0,-.9,0),(.9,0,math.pi/2),(-.9,0,math.pi/2)]]
    elif re.search(r'\b(schneemann|snowman)\b',s):
        parts=[part('Schneekugel','sphere',(0,0,z),(r,r,r),(.9,.95,1)) for z,r in [(1.2,1.2),(2.8,.85),(4,.6)]]+[part('Nase','cone',(0,-.7,4),(.15,.15,.5),(1,.4,.05),(math.pi/2,0,0))]
    elif re.search(r'\b(kugel|sphere)\b',s):parts=[part('Kugel','sphere')]
    elif re.search(r'\b(zylinder|cylinder)\b',s):parts=[part('Zylinder','cylinder')]
    elif re.search(r'\b(würfel|wuerfel|cube)\b',s):parts=[part('Würfel')]
    else:return None
    return validate_scene({'name':goal[:120],'parts':parts})

def validate_scene(scene):
    if not isinstance(scene,dict) or set(scene)!={'name','parts'} or not isinstance(scene['name'],str) or not 1<=len(scene['name'])<=120:raise ValueError('Ungültiger Szenenname.')
    parts=scene['parts']
    if not isinstance(parts,list) or not 1<=len(parts)<=80:raise ValueError('Eine Szene braucht 1–80 Grundkörper.')
    clean=[]
    for item in parts:
        if not isinstance(item,dict) or set(item)!={'name','shape','location','scale','color','rotation'}:raise ValueError('Ungültiger 3D-Grundkörper.')
        if not isinstance(item['shape'],str) or item['shape'] not in SHAPES or not isinstance(item['name'],str) or not 1<=len(item['name'])<=80:raise ValueError('Nicht unterstützter Grundkörper.')
        for key,low,high in [('location',-100,100),('scale',.01,30),('color',0,1),('rotation',-math.tau,math.tau)]:
            vector=item[key]
            if not isinstance(vector,list) or len(vector)!=3 or any(type(v) not in {int,float} or not math.isfinite(v) or not low<=v<=high for v in vector):raise ValueError('Ungültige 3D-Abmessungen.')
        clean.append({**item,**{k:list(item[k]) for k in ['location','scale','color','rotation']}})
    return {'name':scene['name'],'parts':clean}

def write_scene(folder,scene):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=False,mode=0o700)
    path=folder/'scene.json';path.write_text(json.dumps(validate_scene(scene),ensure_ascii=False));path.chmod(0o600);return path
