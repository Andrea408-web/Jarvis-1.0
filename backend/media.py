"""Public YouTube result discovery. No model, account, stream extraction or playback log."""
import re
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


def search(body,reader=None):
    if not isinstance(body,dict)or set(body)!={'query'}or not isinstance(body['query'],str):raise ValueError('Bitte einen Videotitel angeben.')
    query=' '.join(body['query'].split())
    if not 2<=len(query)<=180:raise ValueError('Bitte einen Suchbegriff mit 2 bis 180 Zeichen eingeben.')
    url=SEARCH+quote_plus('site:youtube.com/watch '+query)
    try:
        html,_=(reader or fetch_public)(url);page=Page();page.feed(html)
    except (ValueError,OSError,TimeoutError):
        return {'items':[],'available':False,'message':'Die öffentliche Videosuche ist gerade nicht erreichbar. Du kannst einen YouTube-Link einfügen oder eigene Dateien abspielen.','search_url':'https://www.youtube.com/results?search_query='+quote_plus(query)}
    items=[];seen=set()
    for row in page.links[:50]:
        key=video_id(row['url'])
        if not key or key in seen:continue
        seen.add(key);items.append({'id':key,'title':' '.join(row['title'].split())[:200]or'YouTube-Video','url':'https://www.youtube.com/watch?v='+key,'description':row.get('snippet','')[:240]})
        if len(items)>=5:break
    return {'items':items,'available':True,'message':'Wähle einen Treffer, um ihn direkt in Jarvis abzuspielen.'if items else'Keine passenden frei auffindbaren Videos gefunden. Füge einen YouTube-Link ein.','search_url':'https://www.youtube.com/results?search_query='+quote_plus(query)}
