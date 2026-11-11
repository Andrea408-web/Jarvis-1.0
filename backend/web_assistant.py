"""Public web answers with explicit sources and a separate open-site follow-up.
No accounts, AI services, location lookup, cookies or device credentials are sent.
"""
import concurrent.futures
import http.client
import ipaddress
import json
import re
import socket
import ssl
import subprocess
import sys
from datetime import datetime,timedelta
from html.parser import HTMLParser
from urllib.parse import parse_qs, quote_plus, unquote, urljoin, urlsplit
from zoneinfo import ZoneInfo

SEARCH='https://html.duckduckgo.com/html/?q='
CINEMA='https://www.cineplex.de/kinoprogramm/neufahrn/'


def public_url(value):
    try:
        p=urlsplit(value)
        if p.scheme!='https' or not p.hostname or p.username or p.password or p.port not in {None,443} or len(value)>2200:return False
        host=p.hostname.rstrip('.').lower()
        if host=='localhost' or host.endswith(('.local','.localhost','.internal')):return False
        try:return ipaddress.ip_address(host).is_global
        except ValueError:return '.' in host and bool(re.fullmatch(r'[a-z0-9.-]+',host))
    except (ValueError,TypeError):return False


def fetch_public(url):
    """Verified TLS, globally routable DNS addresses pinned for each redirect."""
    for _ in range(4):
        if not public_url(url):raise ValueError('Keine öffentliche HTTPS-Quelle.')
        p=urlsplit(url);addresses={entry[4][0] for entry in socket.getaddrinfo(p.hostname,443,type=socket.SOCK_STREAM)}
        if not addresses or any(not ipaddress.ip_address(address).is_global for address in addresses):raise ValueError('Private Netzwerkziele werden nicht gelesen.')
        address=sorted(addresses,key=lambda v:':' in v)[0]
        if sys.platform=='darwin':
            pinned='['+address+']' if ':' in address else address
            command=['/usr/bin/curl','--disable','--silent','--show-error','--include','--noproxy','*','--proto','=https','--connect-timeout','4','--max-time','8','--max-filesize','1500000','--resolve',p.hostname+':443:'+pinned,'--user-agent','JARVIS-Web/1.0',url]
            process=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
            try:
                raw=process.stdout.read(1500001)
                if len(raw)>1500000 or process.wait(timeout=9):raise ValueError('Webseite nicht frei erreichbar.')
            finally:
                if process.poll() is None:process.kill();process.wait()
                process.stdout.close()
            head,sep,body=raw.partition(b'\r\n\r\n')
            if not sep:raise ValueError('Ungültige Webantwort.')
            status=int(head.split(b' ',2)[1])
            while 100<=status<200:
                head,sep,body=body.partition(b'\r\n\r\n')
                if not sep:raise ValueError('Ungültige Webantwort.')
                status=int(head.split(b' ',2)[1])
            headers={k.lower():v.strip() for line in head.decode('iso-8859-1').splitlines()[1:] if ':' in line for k,v in [line.split(':',1)]}
        else:
            class Pinned(http.client.HTTPSConnection):
                def connect(self):
                    self.sock=ssl.create_default_context().wrap_socket(socket.create_connection((address,443),timeout=8),server_hostname=p.hostname)
            connection=Pinned(p.hostname,timeout=8)
            try:
                connection.request('GET',(p.path or '/')+('?' +p.query if p.query else ''),headers={'User-Agent':'JARVIS-Web/1.0','Accept':'text/html,application/ld+json'})
                response=connection.getresponse();status=response.status;headers={k.lower():v for k,v in response.getheaders()};body=response.read(1500001)
                if len(body)>1500000:raise ValueError('Webseite ist zu groß.')
            finally:connection.close()
        if status in {301,302,303,307,308}:url=urljoin(url,headers.get('location',''));continue
        if status!=200:raise ValueError('Webseite ist nicht frei erreichbar.')
        if not any(m in headers.get('content-type','').lower() for m in ['text/html','application/xhtml','application/ld+json']):raise ValueError('Keine lesbare Webseite.')
        return body.decode('utf-8',errors='replace'),url
    raise ValueError('Zu viele Weiterleitungen.')


class Page(HTMLParser):
    def __init__(self):super().__init__();self.text=[];self.schemas=[];self.links=[];self.hidden=0;self.ld=None;self.anchor=None;self.snippet=None
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag in {'script','style','noscript'}:
            self.hidden+=1
            if tag=='script' and a.get('type','').lower()=='application/ld+json':self.ld=[]
        if tag=='a' and 'result__a' in a.get('class','').split():self.anchor={'url':a.get('href',''),'title':'','snippet':''}
        if 'result__snippet' in a.get('class','').split():self.snippet=[]
    def handle_data(self,data):
        if self.ld is not None:self.ld.append(data)
        if not self.hidden:self.text.append(data)
        if self.anchor:self.anchor['title']+=data
        if self.snippet is not None:self.snippet.append(data)
    def handle_endtag(self,tag):
        if tag=='script' and self.ld is not None:
            try:self.schemas.append(json.loads(''.join(self.ld)))
            except (ValueError,TypeError,RecursionError):pass
            self.ld=None
        if tag in {'script','style','noscript'}:self.hidden=max(0,self.hidden-1)
        if tag=='a' and self.anchor:
            url=self.anchor['url']
            if 'uddg=' in url:url=parse_qs(urlsplit(url).query).get('uddg',[''])[0]
            elif url.startswith('//'):url='https:'+url
            if public_url(url):self.anchor['url']=url;self.links.append(self.anchor)
            self.anchor=None
        if tag in {'a','div','span'} and self.snippet is not None:
            if self.links:self.links[-1]['snippet']=' '.join(''.join(self.snippet).split())[:400]
            self.snippet=None


def nodes(value,depth=0):
    if depth>12:return
    if isinstance(value,list):
        for child in value:yield from nodes(child,depth+1)
    elif isinstance(value,dict):
        yield value
        for child in value.values():
            if isinstance(child,(dict,list)):yield from nodes(child,depth+1)


def screenings(schemas,now,age,on_date=None,place=None):
    found=[]
    for item in nodes(schemas):
        types=item.get('@type',[]);types=[types] if isinstance(types,str) else types
        if 'ScreeningEvent' not in types:continue
        location=item.get('location')
        if place and location and place.casefold() not in json.dumps(location,ensure_ascii=False).casefold():continue
        movie=item.get('workPresented',{});movie=movie if isinstance(movie,dict) else {}
        title=movie.get('name') or item.get('name');rating=str(movie.get('contentRating',item.get('contentRating','')))
        match=re.search(r'(?:FSK\s*(?:ab\s*)?|^)(0|6|12|16|18)\b',rating,re.I)
        if not title or not match or int(match[1])>age:continue
        try:
            start=datetime.fromisoformat(item['startDate'].replace('Z','+00:00'))
            if start.tzinfo is None:start=start.replace(tzinfo=now.tzinfo)
            start=start.astimezone(now.tzinfo)
        except (KeyError,ValueError,TypeError,AttributeError):continue
        if start.date()!=(on_date or now.date()) or start<now:continue
        found.append((start,str(title)[:140],int(match[1])))
    return sorted(set(found))[:8]


def restaurant_rows(schemas,now,people,budget):
    """Only explicit structured business hours/menu prices; no quality claims."""
    rows=[];days=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    for business in nodes(schemas):
        types=business.get('@type',[]);types=[types] if isinstance(types,str) else types
        if not any(t in types for t in ['Restaurant','FastFoodRestaurant','FoodEstablishment','CafeOrCoffeeShop','Bakery']):continue
        name=business.get('name')
        if not isinstance(name,str):continue
        specs=business.get('openingHoursSpecification',[]);specs=[specs] if isinstance(specs,dict) else specs
        opened=None
        for spec in specs if isinstance(specs,list) else []:
            if not isinstance(spec,dict):continue
            weekdays=spec.get('dayOfWeek',[]);weekdays=[weekdays] if isinstance(weekdays,str) else weekdays
            if not isinstance(weekdays,list):continue
            day_names=[str(d).rsplit('/',1)[-1] for d in weekdays]
            try:
                if spec.get('validFrom') and now.date()<datetime.fromisoformat(spec['validFrom']).date():continue
                if spec.get('validThrough') and now.date()>datetime.fromisoformat(spec['validThrough']).date():continue
                begin=datetime.strptime(spec['opens'],'%H:%M').time();end=datetime.strptime(spec['closes'],'%H:%M').time()
                minute=now.time().replace(tzinfo=None)
                if begin==end:continue # 00:00/00:00 is ambiguous across publishers.
                if begin<end:inside=days[now.weekday()] in day_names and begin<=minute<end
                else:inside=(days[now.weekday()] in day_names and minute>=begin) or (days[(now.weekday()-1)%7] in day_names and minute<end)
                opened=bool(opened or inside)
            except (ValueError,KeyError,TypeError):continue
        offers=[]
        for offer in nodes(business.get('hasOfferCatalog',business.get('hasMenu',{}))):
            if offer.get('@type')!='Offer' or offer.get('priceCurrency')!='EUR':continue
            item=offer.get('itemOffered',{});label=item.get('name') if isinstance(item,dict) else None;label=label or offer.get('name')
            try:price=float(str(offer['price']).replace(',','.'))
            except (ValueError,KeyError,TypeError):continue
            if isinstance(label,str) and 1<=price<=1000 and not re.search(r'wasser|getränk|cola|bier|kaffee',label,re.I):offers.append((price,label[:80]))
        detail='laut regulären Web-Öffnungszeiten jetzt geöffnet' if opened else 'laut regulären Web-Öffnungszeiten jetzt geschlossen' if opened is False else 'aktuelle Öffnung nicht bestätigt'
        if offers:
            price,label=min(offers);total=price*people;detail+=f"; Menüangabe: {label} {price:.2f} €; {people} × ≈ {total:.2f} €"
            amount=re.search(r'(\d+(?:[,.]\d+)?)',budget)
            if amount:
                limit=float(amount[1].replace(',','.'));cost=price if re.search('pro person|je person|jeder',budget,re.I) else total
                if cost>limit:detail+=' (über eurem genannten Budget)'
        else:detail+='; kein verlässlicher Menüpreis auslesbar'
        rows.append((opened,name[:120]+' – '+detail))
    return rows[:3]


class WebAssistant:
    def __init__(self,app,reader=None,clock=None):self.app=app;self.reader=reader or fetch_public;self.clock=clock or (lambda:datetime.now(ZoneInfo('Europe/Berlin')))
    def intent(self,text):
        if re.search(r'kino|cineplex|(?:welche|was für).*filme.*(?:heute|jetzt|laufen|angucken|anschauen)',text,re.I):return 'cinema'
        if re.search(r'(?:wo|restaurant|imbiss|in der nähe).*(?:essen|pizza|döner|sushi|burger|restaurant)|(?:essen|pizza|döner|sushi|burger).*(?:wo|jetzt|heute|geöffnet|billig|günstig)',text,re.I):return 'food'
        if re.search(r'(?:wo|welche).*(?:kaufen|bestellen|reservieren|geöffnet|tickets)|was kostet|wie teuer|öffnungszeiten|(?:aktuell|heute|jetzt).*(?:wetter|preis|kostet|veranstaltung|zug|bahn)|(?:webseite|website|im internet|im web).*(?:such|find|inform)|(?:such|find).*(?:im internet|im web|webseite)',text,re.I):return 'web'
        return None
    def slots(self,text,kind,old=None,field=None):
        result=dict(old or {});result.setdefault('kind',kind);result.setdefault('query',text)
        if re.search(r'cineplex',result['query'],re.I):result['cineplex']=True
        numbers={'null':0,'eins':1,'eine':1,'zwei':2,'drei':3,'vier':4,'fünf':5,'sechs':6,'sieben':7,'acht':8,'neun':9,'zehn':10,'elf':11,'zwölf':12,'dreizehn':13,'vierzehn':14,'fünfzehn':15,'sechzehn':16,'siebzehn':17,'achtzehn':18,'neunzehn':19,'zwanzig':20,'dreißig':30,'vierzig':40}
        parsed=re.sub(r'\b('+ '|'.join(numbers)+r')\b',lambda m:str(numbers[m[0].casefold()]),text,flags=re.I)
        if field:
            if field=='place':result['place']=text.strip(' .!?')[:100]
            if field=='age':
                match=re.search(r'\b(\d{1,2})\b',parsed)
                if match and 0<=int(match[1])<=99:result['age']=int(match[1])
            if field=='people':
                match=re.search(r'\b(\d{1,2})\b',parsed)
                if match and 1<=int(match[1])<=40:result['people']=int(match[1])
            if field=='budget':result['budget']='kein festes Budget insgesamt' if re.search(r'egal|flexibel|weiß nicht|weiss nicht|keine? grenze|kein budget',text,re.I) else text[:100]
            if field=='budget_scope':result['budget']=result.get('budget','')+' '+text[:80]
        if re.search(r'neuf[ae]hr?n|neufahrn|neufarhn',text,re.I):result['place']='Neufahrn';result['cineplex']=bool(re.search('cineplex',text,re.I)) or result.get('cineplex',False)
        place=re.search(r'\b(?:ich bin (?:gerade )?in|in|bei)\s+([A-ZÄÖÜ][\wäöüß-]*(?:\s+(?:bei|am|an der)\s+[A-ZÄÖÜ][\wäöüß-]*)?)',text,re.I)
        if place and place[1].casefold() not in {'kino','cineplex','der','meiner','deiner','einem'}:result['place']=place[1]
        if result.get('place','').lower() in {'neufahrn','neufarhn'}:result['place']='Neufahrn'
        age=re.search(r'\b(?:ab|fsk|bin|für)\s*(\d{1,2})(?:\s*jahre)?\b',parsed,re.I)
        if age and (kind=='cinema'):result['age']=int(age[1])
        people=re.search(r'\b(?:für|mit|sind)\s+(\d{1,2})\s*(?:personen|leute|menschen|personenanzahl)',parsed,re.I)
        if people:result['people']=int(people[1])
        budget=re.search(r'(?:bis|maximal|höchstens|unter|budget)\s*(\d+(?:[,.]\d+)?)\s*(?:€|euro)(?:\s*(?:pro person|insgesamt|gesamt))?',parsed,re.I)
        if budget:result['budget']=budget[0]
        return result
    def handle(self,text):
        dialogue=self.app.dialogue
        with dialogue.lock:pending=dict(dialogue.pending) if dialogue.get() else None
        if pending and pending['kind']=='web_open':
            if re.fullmatch(r'(?:ja(?: bitte)?|öffne (?:sie|die (?:webseite|website))|öffnen|mach das)[.! ]*',text,re.I):
                dialogue.clear();return {'reply':'Hier ist die Website, Sir. Falls der Browser das neue Fenster blockiert, tippe auf „Website öffnen“.','proposals':[],'pending':None,'open_url':pending['data']['url'],'sources':pending['data']['sources']}
            if re.fullmatch(r'(?:nein(?: danke)?|lieber nicht|nicht öffnen|passt|danke)[.! ]*',text,re.I):dialogue.clear();return {'reply':'Gerne, Sir. Die Website bleibt geschlossen.','proposals':[],'pending':None}
            dialogue.clear();pending=None
        if pending and pending['kind']!='web_details':return None
        kind=pending['data']['slots']['kind'] if pending else self.intent(text)
        if not kind:return None
        if not self.app.store.settings().get('web_enabled',True):return {'reply':'Die öffentliche Websuche ist ausgeschaltet, Sir. Du kannst sie in den Einstellungen einschalten.','proposals':[]}
        data=self.slots(text,kind,pending['data']['slots'] if pending else None,pending['data'].get('field') if pending else None)
        if kind in {'cinema','food'} and not data.get('place'):return dialogue.ask('web_details','In welchem Ort suchst du, Sir? Deinen Standort kenne ich nicht automatisch.',slots=data,field='place')
        if kind=='cinema' and 'age' not in data:return dialogue.ask('web_details','Wie alt ist die jüngste Person, Sir? Dann berücksichtige ich die FSK.',slots=data,field='age')
        if kind=='food' and not data.get('people'):return dialogue.ask('web_details','Für wie viele Personen suchst du etwas zu essen, Sir?',slots=data,field='people')
        if kind=='food' and not data.get('budget'):return dialogue.ask('web_details','Wie viel möchtet ihr höchstens ausgeben, Sir – pro Person oder insgesamt?',slots=data,field='budget')
        if kind=='food' and not re.search(r'pro person|insgesamt|gesamt|zusammen|je person|jeder',data['budget'],re.I):return dialogue.ask('web_details','Gilt das Budget pro Person oder insgesamt, Sir?',slots=data,field='budget_scope')
        if not self.app.chat_lock.acquire(blocking=False):raise ValueError('Eine Anfrage läuft bereits. Bitte kurz warten.')
        epoch=self.app.store.memory_epoch()
        try:
            result=self.answer(data)
            with dialogue.lock:
                if self.app.store.memory_epoch()!=epoch:raise ValueError('Der Chat wurde inzwischen gelöscht.')
                dialogue.ask('web_open','Soll ich die Website öffnen, Sir?',url=result['sources'][0]['url'],sources=result['sources'])
                result.update(proposals=[],pending=dialogue.get());result['reply']+='\nSoll ich die Website öffnen, Sir?'
                self.app.store.append('user',text,expected_epoch=epoch);self.app.store.append('assistant',result['reply'],expected_epoch=epoch)
            return result
        finally:self.app.chat_lock.release()
    def answer(self,data):
        now=self.clock();kind=data['kind'];query=data['query'];on_date=now.date()+timedelta(days=2 if 'übermorgen' in query.casefold() else 1 if re.search(r'\bmorgen\b',query,re.I) else 0)
        if kind=='cinema':query=f"Kino {data['place']} {'Cineplex' if data.get('cineplex') else ''} Kinoprogramm {on_date:%d.%m.%Y} FSK bis {data['age']}"
        if kind=='food':query=f"{data['query']} {data['place']} für {data['people']} Personen {data['budget']} Speisekarte Öffnungszeiten"
        search_url=SEARCH+quote_plus(query);sources=[];pages=[]
        if kind=='cinema' and data.get('cineplex') and data['place']=='Neufahrn':sources.append({'title':'Cineplex Neufahrn · offizielles Kinoprogramm','url':CINEMA,'snippet':''})
        try:
            html,_=self.reader(search_url);parser=Page();parser.feed(html);sources.extend(row for row in parser.links if not any(row['url']==old['url'] for old in sources))
        except (OSError,ValueError,http.client.HTTPException,subprocess.SubprocessError):pass
        sources=sources[:3]
        if not sources:sources=[{'title':'Öffentliche Websuche','url':search_url,'snippet':''}]
        def read(source):
            try:
                html,final=self.reader(source['url']);page=Page();page.feed(html);return {**source,'url':final},page
            except (OSError,ValueError,http.client.HTTPException,subprocess.SubprocessError):return source,None
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:pages=list(pool.map(read,[source for source in sources if source['url']!=search_url]))
        if kind=='cinema':
            shows=[]
            # FSK/time claims come only from dated structured screening events.
            for source,page in pages:
                if page and urlsplit(source['url']).hostname in {'cineplex.de','www.cineplex.de'} and data['place'].casefold() in unquote(source['url']).casefold():shows.extend(screenings(page.schemas,now,data['age'],on_date,data['place']))
            if shows:
                reply=f"Sir, diese Vorstellungen passen zur angegebenen Altersgrenze {data['age']} und beginnen am {on_date:%d.%m.%Y} (Stand {now:%H:%M}, deutsche Ortszeit):\n"+'\n'.join(f"• {title} – {start:%H:%M}, FSK {rating}" for start,title,rating in sorted(set(shows))[:8])
                reply+='\nFSK ist keine Garantie für den Einlass; Begleitung, Jugendschutz und freie Plätze bitte beim Kino prüfen.'
            else:reply=f"Sir, für {data['place']} kann ich gerade keine Spielzeiten für {on_date:%d.%m.%Y} samt passender FSK bis {data['age']} zuverlässig bestätigen. Ich nenne dir deshalb keine erfundenen Filme oder Uhrzeiten. Das aktuelle Kinoprogramm findest du über die Quelle unten."
        else:
            rows=[]
            for source,page in pages:
                if kind=='food' and page:
                    businesses=restaurant_rows(page.schemas,now,data['people'],data['budget'])
                    if businesses:
                        rows.extend(row for opened,row in businesses if opened is not False)
                        if not any(opened is not False for opened,_ in businesses):rows.append(source['title']+': aktuell laut regulären Webangaben geschlossen.')
                        continue
                excerpt=source.get('snippet','')
                if page:
                    relevant=[p.strip() for p in page.text if re.search(r'€|euro|öffnungs|geöffnet|speisekarte|preis',p,re.I) and 15<len(p.strip())<400]
                    if relevant:excerpt=' '.join(relevant[:2])[:450]
                if excerpt:rows.append(source['title']+': '+excerpt)
            if rows:
                reply='Sir, ich habe dazu folgende öffentlichen Angaben gefunden:\n'+'\n'.join('• '+row for row in rows[:3])
                if kind=='food':reply+=f"\nGesucht für {data['people']} Personen in {data['place']}, Budget: {data['budget']}. Ob gerade geöffnet ist und ihr innerhalb des Budgets satt werdet, ist durch diese Angaben nicht sicher bestätigt."
            else:reply='Sir, die aktuellen Angaben konnte ich nicht zuverlässig aus den öffentlichen Seiten lesen. Ich kann dir die passende Website bzw. Websuche öffnen; Preise und Öffnungszeiten erfinde ich nicht.'
        reply+=f'\nAbruf: {now:%d.%m.%Y %H:%M} (Europe/Berlin).'
        return {'reply':reply,'sources':[{'title':s['title'][:180],'url':s['url']} for s in sources]}
