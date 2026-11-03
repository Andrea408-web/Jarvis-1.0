"""Public news/channel reader for the local hub. No sign-in, posting or AI service."""
import html
import json
import re
import subprocess
import sys
import threading
import urllib.request
from urllib.parse import quote,urlsplit
from xml.etree import ElementTree as ET
from html.parser import HTMLParser
from datetime import datetime,timezone
from pathlib import Path

from .providers import ProviderError,_NoRedirect

NEWS_URL='https://www.tagesschau.de/infoservices/alle-meldungen-100~rss2.xml'
COUNTRIES={
    'DE':('Deutschland',51.16,10.45,['deutschland','deutsche','bundestag','berlin']),
    'UA':('Ukraine',49.0,31.0,['ukraine','ukrainisch']),
    'US':('USA',39.0,-98.0,['usa','vereinigten staaten','us-amerikanisch']),
    'FR':('Frankreich',46.6,2.4,['frankreich','französisch']),
    'GB':('Großbritannien',54.5,-2.5,['großbritannien','britisch']),
    'RU':('Russland',61.5,100.0,['russland','russisch']),
    'CN':('China',35.0,103.0,['china','chinesisch']),
    'IL':('Israel',31.5,34.8,['israel']),
    'IR':('Iran',32.0,54.0,['iran']),
    'IT':('Italien',42.8,12.8,['italien','italienisch']),
    'ES':('Spanien',40.3,-3.7,['spanien','spanisch']),
}

class PlainText(HTMLParser):
    def __init__(self):super().__init__();self.parts=[];self.images=[]
    def handle_data(self,data):self.parts.append(data)
    def handle_starttag(self,tag,attrs):
        if tag=='img':self.images.extend(value for key,value in attrs if key=='src' and value)


def plain(value,maximum=500):
    parser=PlainText();parser.feed(value or '')
    return ' '.join(html.unescape(' '.join(parser.parts)).split())[:maximum]


def https_url(value,hosts):
    try:
        parsed=urlsplit(value)
        return isinstance(value,str) and parsed.scheme=='https' and parsed.hostname in hosts and parsed.port in {None,443} and not parsed.username and not parsed.password
    except (ValueError,TypeError):return False


def normalize_handle(value,provider):
    if not isinstance(value,str) or len(value)>250:raise ValueError('Bitte einen gültigen Kanalnamen oder Kanallink eingeben.')
    value=value.strip()
    if not value:return ''
    if '://' in value:
        allowed={'youtube.com','www.youtube.com'} if provider=='youtube' else {'tiktok.com','www.tiktok.com'}
        if not https_url(value,allowed):raise ValueError('Bitte den offiziellen YouTube- oder TikTok-Kanallink verwenden.')
        path=urlsplit(value).path.strip('/')
        if provider=='youtube' and path.startswith('channel/'):value=path[8:]
        elif path.startswith('@'):value=path[1:].split('/')[0]
        else:raise ValueError('Bitte einen Kanalnamen mit @ oder einen Kanallink verwenden.')
    value=value.lstrip('@')
    if provider=='youtube' and re.fullmatch(r'UC[A-Za-z0-9_-]{22}',value):return value
    pattern=r'[\w.-]{1,100}' if provider=='youtube' else r'[A-Za-z0-9_.]{1,32}'
    if not re.fullmatch(pattern,value):raise ValueError('Der Kanalname enthält nicht unterstützte Zeichen.')
    return '@'+value


def public_bytes(url,maximum=2000000):
    """Fixed public sources, verified TLS, bounded bytes; no cookies or credentials."""
    if not https_url(url,{'www.tagesschau.de','www.youtube.com','www.tiktok.com'}):raise ValueError('Nicht freigegebene öffentliche Quelle.')
    if sys.platform=='darwin':
        command=['/usr/bin/curl','--disable','--fail','--silent','--show-error','--location','--proto','=https','--proto-redir','=https','--connect-timeout','5','--max-time','12','--user-agent','JARVIS-PublicHub/1.0',url]
        process=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
        try:
            raw=process.stdout.read(maximum+1)
            if len(raw)>maximum:raise ValueError('Die öffentliche Quelle ist zu groß.')
            if process.wait(timeout=3):raise ValueError('Die öffentliche Quelle ist nicht frei erreichbar.')
            return raw
        finally:
            if process.poll() is None:process.kill();process.wait()
            process.stdout.close()
    request=urllib.request.Request(url,headers={'User-Agent':'JARVIS-PublicHub/1.0'})
    with urllib.request.build_opener(_NoRedirect()).open(request,timeout=12) as response:raw=response.read(maximum+1)
    if len(raw)>maximum:raise ValueError('Die öffentliche Quelle ist zu groß.')
    return raw


def parse_news(raw):
    if b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():raise ValueError('Unzulässige RSS-Struktur.')
    document=ET.fromstring(raw);items=[]
    for index,item in enumerate(document.findall('.//item')[:24]):
        title=plain(item.findtext('title'),220);url=(item.findtext('link') or '').strip()
        if not title or not https_url(url,{'www.tagesschau.de','tagesschau.de'}):continue
        description=plain(item.findtext('description'),450)
        candidates=[]
        for element in item.iter():
            if element.tag.rsplit('}',1)[-1] in {'content','thumbnail','enclosure'}:
                if element.attrib.get('url'):candidates.append(element.attrib['url'])
            if element.text and '<img' in element.text:
                parser=PlainText();parser.feed(element.text);candidates.extend(parser.images)
        image=next((value for value in candidates if https_url(value,{'images.tagesschau.de','www.tagesschau.de','tagesschau.de'})),None)
        text=(title+' '+description).casefold()
        countries=[code for code,(_,_,_,names) in COUNTRIES.items() if any(re.search(r'\b'+re.escape(name),text) for name in names)]
        items.append({'id':str(index),'title':title,'summary':description,'url':url,'image':image,'countries':countries,'published':plain(item.findtext('pubDate'),100)})
    if not items:raise ValueError('Der RSS-Feed enthält keine lesbaren Meldungen.')
    return items


def json_script(page,identifier):
    match=re.search(r'<script\b[^>]*\bid=["\']'+re.escape(identifier)+r'["\'][^>]*>([\s\S]*?)</script>',page,re.I)
    if not match:return None
    try:return json.loads(html.unescape(match.group(1)))
    except ValueError:return None


def walk(value):
    queue=[value];count=0
    while queue and count<60000:
        current=queue.pop();count+=1
        if isinstance(current,dict):yield current;queue.extend(current.values())
        elif isinstance(current,list):queue.extend(current)


def text_value(value):
    if not isinstance(value,dict):return None
    result=value.get('simpleText') or ''.join(part.get('text','') for part in value.get('runs',[]) if isinstance(part,dict))
    return plain(result,100) if result else None


def youtube_data(handle,reader=public_bytes):
    url='https://www.youtube.com/'+(quote(handle,safe='@') if handle.startswith('@') else 'channel/'+handle)
    result={'handle':handle,'url':url,'subscribers':None,'videos':[],'name':handle,'error':None}
    channel=handle if re.fullmatch(r'UC[A-Za-z0-9_-]{22}',handle) else None
    if channel is None:
        page=reader(url).decode('utf-8',errors='replace')
        match=re.search(r'(?:var\s+)?ytInitialData\s*=\s*',page)
        data=None
        if match:
            try:data=json.JSONDecoder().raw_decode(page[match.end():])[0]
            except ValueError:pass
        for node in walk(data):
            metadata=node.get('channelMetadataRenderer')
            if isinstance(metadata,dict):
                candidate=metadata.get('externalId')
                if isinstance(candidate,str) and re.fullmatch(r'UC[A-Za-z0-9_-]{22}',candidate):channel=candidate
                result['name']=plain(metadata.get('title') or handle,100)
            if 'subscriberCountText' in node:result['subscribers']=text_value(node['subscriberCountText'])
            # Newer public channel headers expose already-formatted text.
            content=node.get('content')
            if isinstance(content,str) and re.search(r'abonnenten|subscribers',content,re.I):result['subscribers']=plain(content,100)
        if not channel:raise ValueError('YouTube liefert keinen öffentlich lesbaren Kanal. Bitte bei Bedarf die UC-Kanal-ID eintragen.')
    feed=reader('https://www.youtube.com/feeds/videos.xml?channel_id='+channel)
    if b'<!DOCTYPE' in feed.upper() or b'<!ENTITY' in feed.upper():raise ValueError('Ungültiger Kanalfeed.')
    document=ET.fromstring(feed);ns={'a':'http://www.w3.org/2005/Atom','yt':'http://www.youtube.com/xml/schemas/2015'}
    for entry in document.findall('a:entry',ns)[:6]:
        video=entry.findtext('yt:videoId',namespaces=ns)
        if video and re.fullmatch(r'[A-Za-z0-9_-]{11}',video):result['videos'].append({'id':video,'title':plain(entry.findtext('a:title',namespaces=ns),180),'url':'https://www.youtube.com/watch?v='+video,'image':'https://i.ytimg.com/vi/'+video+'/hqdefault.jpg'})
    return result


def tiktok_data(handle,reader=public_bytes):
    url='https://www.tiktok.com/'+quote(handle,safe='@')
    page=reader(url).decode('utf-8',errors='replace')
    data=json_script(page,'__UNIVERSAL_DATA_FOR_REHYDRATION__') or json_script(page,'SIGI_STATE')
    result={'handle':handle,'url':url,'followers':None,'videos':[],'name':handle,'error':None}
    user_id=None
    for node in walk(data):
        pairs=[]
        if isinstance(node.get('user'),dict):pairs.append((node['user'],node.get('stats') or node.get('statsV2')))
        if isinstance(node.get('users'),dict) and isinstance(node.get('stats'),dict):
            pairs.extend((user,node['stats'].get(key)) for key,user in node['users'].items() if isinstance(user,dict))
        for user,stats in pairs:
            if isinstance(stats,dict) and str(user.get('uniqueId','')).casefold()==handle.lstrip('@').casefold():
                count=stats.get('followerCount')
                if isinstance(count,str) and count.isdigit():count=int(count)
                if type(count) is int and 0<=count<=1000000000000:result['followers']=count
                result['name']=plain(user.get('nickname') or handle,100);user_id=str(user.get('id',''))
    for node in walk(data):
        video=node.get('id');author=node.get('author')
        owner=(str(author.get('uniqueId','')).casefold()==handle.lstrip('@').casefold() or bool(user_id and str(author.get('id',''))==user_id)) if isinstance(author,dict) else isinstance(author,str) and (author.casefold()==handle.lstrip('@').casefold() or bool(user_id and author==user_id))
        if owner and isinstance(video,str) and re.fullmatch(r'[0-9]{10,24}',video) and isinstance(node.get('desc'),str):
            if not any(item['id']==video for item in result['videos']):result['videos'].append({'id':video,'title':plain(node['desc'],180),'url':url+'/video/'+video})
    result['videos']=result['videos'][:6]
    if result['followers'] is None:result['error']='TikTok stellt die Followerzahl gerade nicht öffentlich bereit. Es wird keine Zahl erfunden.'
    return result


class MiniHub:
    def __init__(self,store,reader=None):
        self.store=store;self.reader=reader or public_bytes;self.lock=threading.Lock();self.cache={}
        self.path=store.data_dir/'hub-cache.json'
        try:
            if self.path.stat().st_size<2000000:
                cached=json.loads(self.path.read_text())
                if isinstance(cached,dict):self.cache=cached
        except (OSError,ValueError):pass
    def _save(self):
        temporary=self.path.with_suffix('.tmp');temporary.write_text(json.dumps(self.cache,ensure_ascii=False));temporary.chmod(0o600);temporary.replace(self.path)
    def snapshot(self):
        settings=self.store.settings();channels={}
        for provider in ['youtube','tiktok']:
            handle=settings[provider+'_channel'];cached=self.cache.get(provider)
            channels[provider]=cached if isinstance(cached,dict) and cached.get('handle')==handle else {'handle':handle,'subscribers':None,'followers':None,'videos':[]}
        return {'news':self.cache.get('news',{'items':[],'updated_at':None,'error':None}),'channels':channels,'country':settings['hub_country'],'countries':[{'id':code,'name':name,'lat':lat,'lon':lon} for code,(name,lat,lon,_) in COUNTRIES.items()]}
    def news(self):
        if not self.lock.acquire(blocking=False):raise ProviderError('Eine Hub-Aktualisierung läuft bereits.',409)
        try:
            previous=self.cache.get('news',{'items':[],'updated_at':None})
            try:
                result={'items':parse_news(self.reader(NEWS_URL)),'updated_at':datetime.now(timezone.utc).isoformat(),'error':None,'source':'tagesschau.de','stale':False}
                self.cache['news']=result;self._save();return result
            except Exception:
                return {**previous,'stale':True,'error':'Aktuelle Nachrichten konnten nicht geladen werden. Angezeigte ältere Meldungen behalten ihren Zeitstempel; ohne Quelle wird nichts erfunden.'}
        finally:self.lock.release()
    def channels(self):
        if not self.lock.acquire(blocking=False):raise ProviderError('Eine Hub-Aktualisierung läuft bereits.',409)
        try:
            settings=self.store.settings()
            for provider,reader in [('youtube',youtube_data),('tiktok',tiktok_data)]:
                handle=settings[provider+'_channel']
                if not handle:continue
                try:result=reader(handle,self.reader);result['updated_at']=datetime.now(timezone.utc).isoformat()
                except Exception:
                    old=self.cache.get(provider,{})
                    result=old if isinstance(old,dict) and old.get('handle')==handle else {'handle':handle,'subscribers':None,'followers':None,'videos':[]}
                    result={**result,'error':'Öffentliche Kanaldaten momentan nicht abrufbar. Anmeldung, Captcha oder eine Sperre werden nicht umgangen.'}
                self.cache[provider]=result
            self._save();return self.snapshot()['channels']
        finally:self.lock.release()
