"""Reviewed starter-game blueprints; no arbitrary generated script execution."""
import math,re

def wants_studio(task,target='auto'):
    if target=='auto' and re.search(r'website|webseite|homepage|landingpage',task,re.I):return False
    return target=='studio' or target=='auto' and bool(re.search(r'roblox|\bblock[ -]?studi[oe]\b|miles\s*morales|spider[- ]?man',task,re.I))

def from_task(task):
    hero=bool(re.search(r'miles|morales|spider|superheld|schwing|stadtheld',task,re.I))
    if hero:
        return city({'name':'Neonläufer · Stadt-Prototyp','buildings':16})
    if re.search(r'\b(?:rennspiel|shooter|tycoon|horrorspiel)\b',task,re.I):raise ValueError('Dieser direkte Spieltyp ist noch nicht eingebaut. Unterstützt sind Parcours und Superhelden-Stadt. Es wird kein anderes Spiel als erledigt ausgegeben.')
    from .studio_bridge import scene
    number=re.search(r'\b(\d{1,2})\s*(?:plattform|platform)',task,re.I)
    plan=scene({'name':'Jarvis · Parcours','platforms':max(3,min(20,int(number[1]))) if number else 10,'coins':not bool(re.search(r'ohne (?:münzen|coins)',task,re.I))})
    plan.update(features=['Spawn, Plattformen und Ziel','Münzen und Punktestand, falls gewählt'],limits=['Ein Starter-Parcours, kein beliebiges frei programmiertes Roblox-Spiel.','Play-Test und Speichern erfolgen in Roblox Studio.'])
    return plan

def city(body):
    if not isinstance(body,dict) or set(body)!={'name','buildings'} or not isinstance(body['name'],str) or not 1<=len(body['name'].strip())<=80 or type(body['buildings']) is not int or not 8<=body['buildings']<=24:raise ValueError('Bitte Stadtname und 8–24 Gebäude angeben.')
    parts=[]
    def add(kind,pos,size,color):parts.append({'kind':kind,'position':pos,'size':size,'color':color})
    add('ground',[0,-1,0],[360,2,360],[30,38,43]);add('spawn',[0,1,140],[14,1,14],[77,167,161])
    for z in [-100,0,100]:add('road',[0,.05,z],[340,.2,20],[45,49,55])
    for x in [-100,0,100]:add('road',[x,.07,0],[20,.2,340],[45,49,55])
    sites=[(x,z) for z in [-145,-55,45,140] for x in [-145,-55,45,140]][:body['buildings']]
    if body['buildings']>16:sites += [(x,z) for x,z in [(-110,-135),(-40,-125),(35,-125),(115,-135),(-135,95),(-45,95),(40,95),(125,95)]][:body['buildings']-16]
    for i,(x,z) in enumerate(sites):
        height=30+(i*17)%67;size=28 if i<16 else 18
        add('building',[x,height/2+.2,z],[size,height,size],[47+(i%3)*13,62+(i%4)*8,80+(i%3)*10])
        add('roof',[x,height+1,z],[size+2,1.5,size+2],[83,165,157])
        for level in range(8,height-3,12):
            add('window',[x,height-level,z+size/2+.12],[size*.7,2,.25],[124,206,205])
    for i in range(8):
        x,z=sites[i%len(sites)];height=30+((i%len(sites))*17)%67
        add('checkpoint',[x,height+5,z],[5,5,5],[246,210,92])
    return {'name':body['name'].strip(),'kind':'hero-city','requires_version':2,'parts':parts,'features':['Eigenes kleines Stadtviertel mit Dächern und markierten Schwingpunkten','Schwingen: Q halten / Touch-Schaltfläche','Wandlauf: an der Wand W + Leertaste halten','Doppelsprung, Energie-Dash, Rücksetzen nach einem Sturz','8 Dach-Checkpoints als Zeitrennen mit HUD'],'limits':['Originaler Starter-Prototyp. Nur die angezeigten Bausteine werden umgesetzt; zusätzliche Promptwünsche sind nicht automatisch abgedeckt.','Noch keine Kämpfe, Gegner-KI, Tarnung, Story oder fertigen Animationen.','Gebaut wird direkt in Studio; Physik, Steuerung und Spielbalance müssen dort mit Play getestet werden.']}
