"""Deterministic task dispatch before model generation, including natural German."""
import re

def task_request(text):
    clean=text.strip()
    from .website import requested
    if requested(clean):return {'role':'builder','task':clean[:3000]}
    if re.match(r'^(?:(?:kannst|könntest) du )?(?:bitte )?(?:erstelle|mach|mache|produziere)\b',clean,re.I) and re.search(r'\b(?:werbeclip|werbung|video)\b',clean,re.I):return {'role':'studio','task':clean[:3000]}
    names=r'atlas|nova|sentinel|planer|autor|prüfer|studio|bauer|agent(?:en)?'
    if not re.search(r'\b(?:'+names+r')\b',clean,re.I):return None
    if not re.search(r'beauftrag|auftrag|\blass\b|\bsoll\b|erstell|mach|bau|schreib|produzier',clean,re.I):return None
    if re.search(r'^(?:jarvis[, ]+)?(?:warum|wieso|was kann|wie funktioniert)\b',clean,re.I) or re.search(r'\b(?:nicht|keinen?|niemals)\b.{0,30}(?:beauftrag|agent)|beauftrag\w*\s+keinen?',clean,re.I):return None
    if re.search(r'^(?:jarvis[, ]+)?(?:was (?:machen|macht|tun|ist|sind|soll)|wie (?:arbeiten|geht)|zeig|zeige|öffne)\b',clean,re.I):return None
    role='planner'
    if re.search(r'video|werbung|werbeclip|studio',clean,re.I):role='studio'
    elif re.search(r'plugin|mini.?app|anklickbar|checkliste|bauer',clean,re.I):role='builder'
    elif re.search(r'sentinel|prüfer|prüf',clean,re.I):role='reviewer'
    elif re.search(r'nova|autor|schreib|text',clean,re.I):role='writer'
    for name,selected in [('atlas','planner'),('nova','writer'),('sentinel','reviewer'),('studio','studio'),('bauer','builder')]:
        if re.search(r'\b'+name+r'\b',clean,re.I):role=selected;break
    patterns=[
        r'beauftrag\w*\s+(?:(?:bitte|doch|mal|den|die|einen|ein|meinen|meine)\s+)*(?:'+names+r')(?:\s+mit\s+(?:dem\s+)?(?:auftrag\s*)?)?\s*[:,;-]?\s*(?:der\s+|die\s+|dass\s+)?(.*)',
        r'lass\s+(?:(?:bitte|den|die|einen|ein)\s+)*(?:'+names+r')\s*[:,;-]?\s*(.*)',
        r'(?:'+names+r')\s+soll\s+(.*)',
    ]
    task=clean
    for pattern in patterns:
        found=re.search(pattern,clean,re.I|re.S)
        if found:task=found.group(1).strip(' ,:.-');break
    task=re.sub(r'^(?:bitte\s+|für\s+mich\s+)+','',task,flags=re.I)
    if len(task)<4:return {'role':role,'task':None}
    return {'role':role,'task':task[:3000]}
