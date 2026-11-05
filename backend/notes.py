"""Deterministic note requests and a fixed Notes AppleScript; no model-generated code."""
import html
import platform
import re
import subprocess

SCRIPT='''on run argv
 set noteTitle to item 1 of argv
 set noteHTML to item 2 of argv
 tell application "Notes"
  activate
  set targetAccount to default account
  if not (exists folder "Jarvis" of targetAccount) then
   make new folder at targetAccount with properties {name:"Jarvis"}
  end if
  set createdNote to make new note at folder "Jarvis" of targetAccount with properties {name:noteTitle, body:noteHTML}
  try
   show createdNote
  end try
  return id of createdNote
 end tell
end run'''

def request(text):
    if not isinstance(text,str):return None
    text=re.sub(r'^(?:jarvis|astra|asta|astda|astrid|asuka)[,: ]+','',text.strip(),flags=re.I)
    if not re.search(r'\bnotiz(?:en)?\b',text,re.I) or not re.search(r'\b(?:erstell\w*|schreib\w*|mach\w*|notier\w*|speicher\w*|leg\w*)\b',text,re.I):return None
    body=None
    if ':' in text:body=text.split(':',1)[1].strip()
    if not body:
        match=re.search(r'\b(?:mit (?:dem )?(?:text|inhalt)|in(?:halt)? lautet)\s+(.+)',text,re.I|re.S)
        if match:body=match[1].strip()
    if not body:
        match=re.fullmatch(r'(?:schreib\w*|tippe|notiere)\s+(.+?)\s+in\s+(?:die\s+)?notizen[.!?]?',text,re.I|re.S)
        if match:body=match[1].strip()
    if not body:
        match=re.search(r'\bnotizen\b.*?\bund\s+(?:schreib\w*|tippe)\s+(.+)$',text,re.I|re.S)
        if match:body=match[1].strip()
    if not body:return {'title':None,'body':None}
    body=body.strip('“”" ')
    if len(body)>2000:raise ValueError('Bitte eine Notiz mit höchstens 2.000 Zeichen eingeben.')
    title=body.splitlines()[0][:60] or 'Notiz'
    return {'title':title,'body':body}

def create(title,body):
    if platform.system()!='Darwin':raise ValueError('Apple Notizen kann nur auf deinem Mac gesteuert werden.')
    if not isinstance(title,str) or not isinstance(body,str) or not 1<=len(body)<=2000 or not 1<=len(title)<=60:raise ValueError('Ungültige Notiz.')
    markup='<h1>'+html.escape(title)+'</h1><p>'+html.escape(body).replace('\n','<br>')+'</p>'
    try:result=subprocess.run(['/usr/bin/osascript','-e',SCRIPT,title,markup],capture_output=True,text=True,timeout=30)
    except (OSError,subprocess.SubprocessError):raise ValueError('Notizen antwortet nicht. Es wurde keine erstellte Notiz bestätigt.') from None
    if result.returncode or not result.stdout.strip():raise ValueError('Notizen hat keine Erstellung bestätigt. Prüfe macOS → Datenschutz & Sicherheit → Automation → Terminal/Python → Notizen. Ein eingerichteter Notizen-Account wird benötigt.')
    ident=result.stdout.strip()
    if not ident.startswith('x-coredata://') or len(ident)>500:raise ValueError('Notizen hat keine gültige Notizkennung bestätigt.')
    return {'id':ident,'message':'Notiz in Apple Notizen im Ordner Jarvis angelegt und von Notizen bestätigt.'}
