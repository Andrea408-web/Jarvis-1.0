"""Public YouTube result discovery. No model, account, stream extraction or playback log."""
import re
import json
from http.client import HTTPException
from urllib.parse import urlsplit,parse_qs,quote_plus
from .web_assistant import Page,fetch_public,SEARCH


def video_id(value):
    if not isinstance(value,str)or len(value)>2200:return None
    try:
        p=urlsplit(value)
        if p.scheme!='https'or p.username or p.password or p.port not in {None,443}:return None
        host=(p.hostname or '').lower()
        if host=='youtu.be':candidate=p.path.strip('/').split('/')[0]
        elif host in {'youtube.com','www.youtube.com','m.youtube.com','music.youtube.com','www.youtube-nocookie.com'}:
            parts=p.path.strip('/').split('/')
            candidate=parse_qs(p.query).get('v',[''])[0] if p.path=='/watch'else parts[1] if len(parts)==2 and parts[0]in {'embed','shorts','live'}else ''
        else:return None
        return candidate if re.fullmatch(r'[A-Za-z0-9_-]{11}',candidate)else None
    except ValueError:return None


def youtube_results(html):
    """Read public ytInitialData JSON, never execute page scripts or extract streams."""
    for match in re.finditer(r'(?:var\s+ytInitialData|window\["ytInitialData"\]|ytInitialData)\s*=\s*',html):
        try:data,_=json.JSONDecoder().raw_decode(html,match.end())
        except (ValueError,RecursionError):continue
        stack=[data];items=[];seen=set();visited=0
        while stack and visited<15000 and len(items)<5:
            node=stack.pop();visited+=1
            if isinstance(node,list):stack.extend(reversed(node[:200]))
            elif isinstance(node,dict):
                value=node.get('videoRenderer')
                if isinstance(value,dict):
                    key=value.get('videoId');title=value.get('title',{});name=title.get('simpleText') or ''.join(r.get('text','') for r in title.get('runs',[]) if isinstance(r,dict))
                    if isinstance(key,str)and re.fullmatch(r'[A-Za-z0-9_-]{11}',key)and key not in seen:
                        seen.add(key);items.append({'id':key,'title':str(name or 'YouTube-Video')[:200],'url':'https://www.youtube.com/watch?v='+key,'description':'Öffentliches YouTube-Suchergebnis'})
                stack.extend(reversed(list(node.values())[:200]))
        if items:return items
    return []


def search(body,reader=None):
    if not isinstance(body,dict)or set(body)!={'query'}or not isinstance(body['query'],str):raise ValueError('Bitte einen Videotitel angeben.')
    query=' '.join(body['query'].split())
    if not 2<=len(query)<=180:raise ValueError('Bitte einen Suchbegriff mit 2 bis 180 Zeichen eingeben.')
    url=SEARCH+quote_plus('site:youtube.com/watch '+query);direct='https://www.youtube.com/results?search_query='+quote_plus(query)
    read=reader or (lambda link:fetch_public(link,max_bytes=5000000));items=[];seen=set();fetched=False
    try:
        html,_=read(url);fetched=True;page=Page();page.feed(html)
        for row in page.links[:50]:
            key=video_id(row['url'])
            if not key or key in seen:continue
            seen.add(key);items.append({'id':key,'title':' '.join(row['title'].split())[:200]or'YouTube-Video','url':'https://www.youtube.com/watch?v='+key,'description':row.get('snippet','')[:240]})
            if len(items)>=5:break
    except (ValueError,OSError,TimeoutError,HTTPException):pass
    source='Öffentliche Websuche'
    if not items:
        try:
            html,_=read(direct);fetched=True;items=youtube_results(html);source='YouTube-Suche'
        except (ValueError,OSError,TimeoutError,HTTPException):pass
    message='Wähle einen Treffer, um ihn direkt in Jarvis abzuspielen.'if items else'Keine Videotreffer verfügbar. Der Suchdienst kann blockieren. Füge einen direkten YouTube-Link ein oder öffne die YouTube-Suche.'
    return {'items':items,'available':fetched,'message':message,'search_url':direct,'source':source}
