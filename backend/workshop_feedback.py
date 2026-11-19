"""Revision intent and geometry comparisons independent of names, colors and file order."""
import json,re

def keep_design(text):
 return bool(re.search(r'kein(?:en|e)?\s+(?:neue[rsnm]?|andere[rsnm]?|komplett neue[rsnm]?)\s+(?:entwurf|design|modell)|nicht\s+(?:alles\s+)?neu|behalte\s+(?:den|das)\s+(?:entwurf|design|modell)',text,re.I))

def wants_new_design(text):
 text=text.lower()
 if keep_design(text):return False
 explicit=bool(re.search(r'(?:neu(?:e[rsnm]?)?|ander(?:e[rsnm]?)?)\s+(?:entwurf|design|modell|variante)|(?:entwurf|design|modell)\s*(?:bitte\s*)?(?:neu|anders)|ganz\s+anders|von\s+vorne|neu\s+anfangen|noch\s*(?:ein)?mal\s+neu',text))
 negative=bool(re.search(r'(?:gefällt|gefaellt|gef[aä]llt).{0,35}nicht|nicht.{0,25}(?:gefällt|gefaellt)|nicht\s+(?:so\s+)?schön|sieht.{0,30}nicht\s+gut|\bso\s+nicht\b|langweilig|gefällt.{0,20}gar\s+nicht',text))
 concrete=bool(re.search(r'breiter|schmaler|höher|hoeher|tiefer|flacher|kleiner|größer|groesser|\d+(?:[.,]\d+)?\s*(?:mm|cm)|schwarz|weiß|weiss|grau|blau|\brot\b|aus\s+(?:holz|metall|kunststoff)',text))
 return explicit or negative and not concrete

def strip_preserve_phrase(text):
 return re.sub(r'kein(?:en|e)?\s+(?:neue[rsnm]?|andere[rsnm]?|komplett neue[rsnm]?)\s+(?:entwurf|design|modell)|nicht\s+(?:alles\s+)?neu','',text,flags=re.I)

def lighting_request(text):
 text=text.lower()
 if re.search(r'(?:ohne|keine?|nicht\s+mit)\s+(?:leds?|beleuchtung|licht)|nicht\s+beleuchtet',text):return False
 if re.search(r'\bleds?\b|led[- ]?(?:streifen|ring|modul)|beleucht',text):return True
 return None

def geometry_signature(parts):
 from .workshop_free import bounds
 lo,hi=bounds(parts);extent=[max(hi[i]-lo[i],1e-9)for i in range(3)]
 def number(n):return round(n,5)
 def poly(points):
  q=[tuple(number(n)for n in p)for p in points]
  if not q:return []
  variants=[q[i:]+q[:i]for i in range(len(q))];rev=list(reversed(q));variants +=[rev[i:]+rev[:i]for i in range(len(q))]
  return min(variants)
 result=[]
 for p in parts:
  d={'shape':p['shape'],'size':[number(p['size'][i]/extent[i])for i in range(3)],'position':[number((p['position'][i]-lo[i])/extent[i])for i in range(3)],'rotation':[number(n)for n in p.get('rotation',[0,0,0])],'light':p['material']=='light'}
  if p.get('outline'):d['outline']=poly(p['outline']);d['holes']=sorted(poly(h)for h in p.get('holes',[]))
  if p.get('profile'):d['profile']=[[number(n)for n in v]for v in p['profile']]
  if 'wall'in p:d['wall']=number(p['wall']/p['size'][0])
  result.append(json.dumps(d,sort_keys=True,separators=(',',':')))
 return sorted(result)
