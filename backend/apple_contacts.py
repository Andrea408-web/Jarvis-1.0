"""Read one explicitly selected Apple contact into RAM. Never persist or log it."""
import json,platform,re,subprocess

SCRIPT=r'''function run() {
 const app=Application('com.apple.AddressBook');
 const people=app.selection();
 if (!people || people.length!==1) return JSON.stringify({selection:false});
 const p=people[0];
 return JSON.stringify({selection:true,name:String(p.name()).slice(0,100),phones:p.phones().slice(0,10).map(x=>String(x.value()).slice(0,80)),emails:p.emails().slice(0,10).map(x=>String(x.value()).slice(0,200))});
}'''

def _mac():
 if platform.system()!='Darwin':raise ValueError('Apple Kontakte werden über Jarvis auf deinem Mac geöffnet. Direkter Zugriff auf iPhone-Kontakte ist in Safari nicht verfügbar.')

def open_contacts():
 _mac()
 try:
  result=subprocess.run(['/usr/bin/open','-b','com.apple.AddressBook'],capture_output=True,timeout=8)
  if result.returncode:raise ValueError('Apple Kontakte konnten nicht geöffnet werden.')
 except (OSError,subprocess.TimeoutExpired):raise ValueError('Apple Kontakte konnten nicht geöffnet werden.') from None
 return {'message':'In Apple Kontakte genau eine Person auswählen. Danach in Jarvis auf „Apple-Auswahl verwenden“ tippen. Es wird keine Kontaktliste importiert.'}

def selected():
 _mac()
 try:result=subprocess.run(['/usr/bin/osascript','-l','JavaScript','-'],input=SCRIPT,text=True,capture_output=True,timeout=20)
 except (OSError,subprocess.TimeoutExpired):raise ValueError('Apple-Auswahl nicht verfügbar. Kontakte am Mac öffnen und die macOS-Freigabe für Kontakte/Automation prüfen.') from None
 if result.returncode:raise ValueError('macOS hat den Kontaktzugriff nicht freigegeben. In Systemeinstellungen → Datenschutz & Sicherheit → Automation den Zugriff deines Jarvis-Terminals auf Kontakte erlauben und erneut versuchen.')
 try:
  if len(result.stdout)>20000:raise ValueError()
  raw=json.loads(result.stdout)
 except (ValueError,TypeError):raise ValueError('Die Apple-Auswahl konnte nicht gelesen werden. Es wurde kein Kontakt gespeichert.') from None
 if not isinstance(raw,dict) or raw.get('selection') is not True:raise ValueError('Bitte in Apple Kontakte genau eine Person auswählen und erneut auf „Apple-Auswahl verwenden“ tippen.')
 name=raw.get('name');phones=raw.get('phones');emails=raw.get('emails')
 if not isinstance(name,str) or not name.strip() or len(name)>100 or not isinstance(phones,list) or not isinstance(emails,list) or len(phones)>10 or len(emails)>10:raise ValueError('Die Apple-Auswahl hat ein ungültiges Format.')
 phones=[p.strip() for p in phones if isinstance(p,str) and len(p)<=80 and re.fullmatch(r'\+?[0-9\s()./-]{3,80}',p)]
 emails=[e.strip() for e in emails if isinstance(e,str) and len(e)<=200 and re.fullmatch(r'[^\s@?&=]+@[^\s@?&=]+\.[^\s@?&=]+',e)]
 if not phones and not emails:raise ValueError('Die gewählte Person hat keine hier verwendbare Telefonnummer oder E-Mail-Adresse.')
 return {'name':name.strip(),'phones':phones,'emails':emails,'temporary':True}
