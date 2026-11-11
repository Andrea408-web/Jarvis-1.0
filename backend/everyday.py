"""Conversation helpers for arithmetic, film ideas and country-filtered news."""
import re
from decimal import Decimal,InvalidOperation
from .hub import COUNTRIES

FILMS=[
 ('Paddington 2',0,'Warmherzig und lustig: Ein kleiner Bär versucht, ein besonderes Geschenk zu besorgen.','komödie familie lustig'),
 ('Die Unglaublichen',6,'Superhelden-Abenteuer mit einer Familie, die zusammenhalten muss.','action abenteuer familie'),
 ('Spider-Man: A New Universe',6,'Ein außergewöhnlich animiertes Abenteuer mit Miles Morales.','animation action abenteuer'),
 ('Interstellar',12,'Ein großes Weltraum-Abenteuer über Zeit, Familie und die Suche nach einer Zukunft.','science fiction weltraum spannend'),
 ('Knives Out',12,'Ein unterhaltsamer Krimi voller überraschender Wendungen.','krimi rätsel spannend'),
]

def arithmetic(text):
 words={'null':'0','eins':'1','ein':'1','zwei':'2','drei':'3','vier':'4','fünf':'5','sechs':'6','sieben':'7','acht':'8','neun':'9','zehn':'10','elf':'11','zwölf':'12'}
 value=text.strip().casefold().rstrip('?.! ');value=re.sub(r'\s+bitte$','',value)
 value=re.sub(r'^(?:(?:was|wie viel|wieviel) (?:ist|sind|ergibt)|rechne(?: bitte)?|berechne)\s+','',value)
 value=re.sub(r'\b('+ '|'.join(words)+r')\b',lambda m:words[m[0]],value)
 for source,target in [('geteilt durch','/'),('dividiert durch','/'),('multipliziert mit','*'),('plus','+'),('minus','-'),('mal','*')]:value=value.replace(source,target)
 match=re.fullmatch(r'\s*(-?\d{1,12}(?:[.,]\d{1,8})?)\s*([+*/−-])\s*(-?\d{1,12}(?:[.,]\d{1,8})?)\s*',value)
 if not match:return None
 a,b=Decimal(match[1].replace(',','.')),Decimal(match[3].replace(',','.'));op=match[2]
 if op=='/' and not b:return 'Durch null kann man nicht teilen, Sir.'
 try:result={'+':lambda:a+b,'-':lambda:a-b,'−':lambda:a-b,'*':lambda:a*b,'/':lambda:a/b}[op]()
 except InvalidOperation:return None
 shown=format(result,'f').rstrip('0').rstrip('.') if '.' in format(result,'f') else format(result,'f')
 if len(shown)>40:shown=format(result,'.12g')
 return f'{match[1]} {op} {match[3]} = {shown.replace(".",",")}, Sir.'


def film_ideas(text):
 if not re.search(r'\bfilm\w*\b',text,re.I) or re.search(r'kino|cineplex|spielzeit|kinoprogramm|laufen|nachricht',text,re.I):return None
 if not re.search(r'angucken|anschauen|ansehen|schauen|gucken|empfiehl|empfehl|filmtipp|lust|welche filme',text,re.I):return None
 age_match=re.search(r'(?:ab|für|bin)\s*(\d{1,2})',text,re.I);age=int(age_match[1]) if age_match else None
 available=[f for f in FILMS if age is None or f[1]<=age]
 preferred=[f for f in available if any(w in text.casefold() for w in f[3].split())]
 picks=(preferred+[f for f in available if f not in preferred])[:3]
 if not picks:return {'reply':'Sir, für dieses Alter habe ich gerade keinen passenden Filmtipp parat. Soll es eher lustig oder spannend sein?','proposals':[]}
 cards=[{'title':f[0],'age':f[1],'description':f[2]} for f in picks]
 reply='Sir, für einen Filmabend hätte ich diese Ideen: '+ ' · '.join(f'{f[0]} (FSK {f[1]})' for f in picks)+'. '+'Zu jedem Tipp findest du die Beschreibung und Altersfreigabe im Filmfenster.'
 reply+=' Das sind Filmtipps, keine bestätigten aktuellen Kino- oder Streaming-Angebote.'
 return {'reply':reply,'proposals':[],'view':'discover','category':'films','title':'Dein Filmabend','cards':cards,'sources':[],'pending':None}


def news_request(text):
 if re.search(r'whatsapp|sms|e-?mail|meine nachrichten',text,re.I):return None
 if not re.search(r'nachrichten|neuigkeiten|was passiert.*(?:deutschland|welt)',text,re.I):return None
 country=next((code for code,(name,*_) in COUNTRIES.items() if name.casefold() in text.casefold()),'ALL')
 return {'country':country,'read':bool(re.search(r'vorlesen|lies|sag|erzähl|erzähle|hör|hoer',text,re.I))}


def news_answer(app,request):
 feed=app.hub.news();country=request['country'];name=COUNTRIES[country][0] if country!='ALL' else 'der Welt'
 articles=[i for i in feed.get('items',[]) if country=='ALL' or country in i.get('countries',[])][:5]
 if not articles:reply=f'Sir, zu {name} sind im aktuellen Feed gerade keine Meldungen verfügbar.'
 else:reply=f'Sir, hier sind die Meldungen zu {name}:\n'+'\n'.join(str(i+1)+'. '+a['title']+'. '+a.get('summary','')[:180] for i,a in enumerate(articles[:3]))
 if feed.get('stale'):reply='Sir, der Abruf ist gerade nicht frisch. Ich zeige den gespeicherten Stand.\n'+reply
 if feed.get('error') and not articles:reply+=' Die Nachrichtenquelle ist derzeit nicht erreichbar.'
 return {'reply':reply[:1700],'proposals':[],'view':'news','country':country,'articles':articles,'news_feed':feed,'speak_requested':request['read'],'pending':None}
