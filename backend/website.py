"""Actual self-contained HTML artifacts from a bounded, non-executable site spec."""
import html
import json
import re
from pathlib import Path

INSTRUCTION=('Erstelle einen konkreten Website-Entwurf für den Auftrag als JSON. Nur diese Struktur: '
 '{"title":"Seitentitel","intro":"Einleitung","sections":[{"title":"Überschrift","text":"Inhalt"}]}. '
 'Drei passende Abschnitte, konkrete deutsche Texte. Kein HTML, JavaScript oder Markdown. Keine erfundenen Kontaktdaten, Zertifikate oder Kundenbewertungen.')

def requested(text):
    if re.search(r'^(?:kannst|könntest|würdest)\s+du\b.*\b(?:website|webseite|homepage|landingpage)\b.*\b(?:erstellen|bauen|gestalten|entwickeln)\b',text,re.I):return True
    if re.search(r'^(?:eine?\s+)?(?:website|webseite|homepage|landingpage)\b.*\b(?:erstellen|bauen|gestalten|entwickeln)\b',text,re.I):return True
    return bool(re.search(r'^(?:(?:kannst|könntest|würdest)\s+du\s+)?(?:bitte\s+)?(?:erstell\w*|bau\w*|mach\w*|gestalt\w*|entwickl\w*)\b.*\b(?:website|webseite|homepage|landingpage)\b',text,re.I))

def specification(reply,task):
    raw=reply.strip()
    if raw.startswith('```'):raw=raw.split('\n',1)[-1].rsplit('```',1)[0].strip()
    try:value=json.loads(raw)
    except (ValueError,TypeError):
        # A small text model may fail JSON. Preserve its actual prose as a clearly
        # labelled basic draft, instead of claiming it generated code.
        return {'title':'Mein Website-Entwurf','intro':task[:240],'sections':[{'title':'Erster Textentwurf','text':reply[:4000]}]},True
    if not isinstance(value,dict) or set(value)!={'title','intro','sections'}:raise ValueError('Die KI hat keine gültige Website-Struktur geliefert.')
    if not isinstance(value['title'],str) or not 1<=len(value['title'])<=150 or not isinstance(value['intro'],str) or not 1<=len(value['intro'])<=800:raise ValueError('Ungültige Website-Überschrift oder Einleitung.')
    if not isinstance(value['sections'],list) or not 1<=len(value['sections'])<=8:raise ValueError('Eine Website braucht 1–8 Abschnitte.')
    for section in value['sections']:
        if not isinstance(section,dict) or set(section)!={'title','text'} or not isinstance(section['title'],str) or not 1<=len(section['title'])<=150 or not isinstance(section['text'],str) or not 1<=len(section['text'])<=4000:raise ValueError('Ungültiger Website-Abschnitt.')
    return value,False


def build(reply,task,path,progress):
    spec,basic=specification(reply,task);path=Path(path);blocks=[]
    style='html{color-scheme:dark;font-family:system-ui,sans-serif;background:#0b1520;color:#edf6fc}body{margin:0}main{max-width:1000px;margin:auto;padding:7vw 24px}header{padding:5vw 0}h1{font-size:clamp(2.2rem,7vw,5rem);line-height:1.05;color:#87e4ef}p{line-height:1.7;max-width:75ch;white-space:pre-wrap}section{padding:28px;border:1px solid #335367;border-radius:18px;background:#112131;margin:22px 0}small{color:#a0b7bf}nav a{color:#87e4ef;display:inline-block;margin:8px}footer{padding:28px;color:#a0b7bf}'
    start='<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(spec['title'])+'</title><style>'+style+'</style></head><body><main><header><small>ERSTELLT MIT JARVIS</small><h1>'+html.escape(spec['title'])+'</h1><p>'+html.escape(spec['intro'])+'</p></header><nav>'+''.join('<a href="#section-'+str(i)+'">'+html.escape(s['title'])+'</a>' for i,s in enumerate(spec['sections']))+'</nav>'
    def save():
        temporary=path.with_suffix('.tmp');temporary.write_text(start+''.join(blocks)+'<footer>Lokaler Entwurf · Inhalte vor Veröffentlichung prüfen.</footer></main></body></html>',encoding='utf-8');temporary.chmod(0o600);temporary.replace(path)
    progress('Website-Grundgerüst schreiben');save()
    for i,section in enumerate(spec['sections']):
        progress('Abschnitt '+str(i+1)+' von '+str(len(spec['sections']))+' schreiben: '+section['title'])
        blocks.append('<section id="section-'+str(i)+'"><h2>'+html.escape(section['title'])+'</h2><p>'+html.escape(section['text'])+'</p></section>');save()
    progress('HTML-Datei gespeichert und geprüft')
    return ('Echte HTML-Datei erstellt: '+spec['title']+'. '+str(len(spec['sections']))+' Abschnitte. '+('Ein einfacher Grundentwurf aus dem KI-Text; kein frei programmierter Webauftritt. ' if basic else '')+'Vorschau und Download stehen bereit. Noch nicht veröffentlicht.')
