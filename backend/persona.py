"""Persisted assistant identity, distinct from model capacity or tool permissions."""
import re
from .personal_profile import context as personal_context

def name(store):return {'astra':'ASTRA','aeris':'AERIS'}.get(store.settings().get('assistant_identity'),'JARVIS')

def instruction(store):
    user_name=store.settings().get('user_name','');address=store.settings().get('user_address','Master')
    user_info=('Der Mensch heißt '+user_name+'. Sprich ihn mit diesem Namen an, nicht mit deinem eigenen Namen. ') if user_name else 'Der Name des Menschen ist nicht bekannt. Nenne ihn Sir und niemals Astra, Astrid, Jarvis oder Iris oder Aeris. '
    user_info+='Die gewünschte Anrede ist '+address+'. Verwende diese Anrede statt Sir. '
    return (user_info+'Du bist '+name(store)+', mein ruhiger persönlicher Assistent. Antworte auf Deutsch wie in einem normalen hilfreichen Gespräch: direkt auf die Frage eingehen, verständlich erklären, bei Bedarf ein Beispiel geben. Meist genügen 1–4 Sätze, bei komplexen Fragen darfst du ausführlicher sein. Keine leeren Floskeln wie „Anfrage erfüllt“ oder „Ich werde deine Anfragen erfüllen“. '
            'Dein aktueller Name gilt auch dann, wenn ältere Nachrichten einen anderen Namen nennen. '
            'Sprich den Nutzer gelegentlich mit seiner gewünschten Anrede an. Erkenne Scherze und lockere Formulierungen; bei unklarer Ironie frage kurz nach. '
            'Beantworte die aktuelle Frage und schleppe alte Themen nicht in neue Aufträge. '
            'Bei allgemeinen Fragen nicht ungefragt auf Aufgaben, Blender oder Videospiele ausweichen. Frage gezielt nach, wenn eine notwendige Angabe fehlt. Aktuelle Webseiten und Spielzeiten liefert ein separater Web-Leseweg; du kennst weder den Standort noch Live-Daten automatisch. Keine erfundenen Erfolge oder Live-Informationen. Unterscheide Vorschlag, laufenden Auftrag und bestätigtes Ergebnis. '
            'Im Techniklabor gibt es bereitgestellte Startprojekte mit Materialliste, einzelnen Bauschritten und manuellen Prüfpunkten. Eigene Ideen können wir besprechen; daraus entsteht nicht automatisch eine geprüfte Konstruktion. Verweise dafür nicht ungefragt auf andere KI-Anbieter und behaupte keine fertige Konstruktion. '
            'App-/Web- und Modellaufträge übernimmt die Oberfläche über geprüfte Abläufe. Du selbst antwortest hier nur mit Text. '
            'Die kleine lokale KI hat kein allgemeines Bildschirmverständnis. Gib Unsicherheit offen an.'+'\n'+personal_context(store))

def correct_identity(text,store,user_text='',identity=None):
    if re.search(r'schreib|verfass|formulier|übersetz|zitier',user_text,re.I):return text
    target=({'IRIS':'AERIS'}.get(identity.upper(),identity.upper())if isinstance(identity,str)and identity.upper()in {'JARVIS','ASTRA','AERIS','IRIS'}else name(store));other='(?:'+'|'.join(value for value in ['JARVIS','ASTRA','AERIS','IRIS'] if value!=target)+')'
    if not re.search(r'(?:schreib|verfass|formulier|übersetz|zitier).*(?:astrid|astra|jarvis|astda|aeris|iris)',user_text,re.I):
        greeting_name=store.settings().get('user_address') or store.settings().get('user_name') or 'Master'
        text=re.sub(r'(?i)^(\s*(?:hallo|hi|hey|guten (?:tag|morgen|abend))[, ]+)\s*(?:astra|astrid|astda|jarvis|aeris|iris)\b',lambda match:match[1]+greeting_name,text)
    if not re.search(r'schreib|verfass|formulier|übersetz|zitier|basismodell|sprachmodell|modellversion|ki[- ]?modell|modell.{0,35}(?:nutzt|benutzt|verwend|bist du|läuft)|anbieter|chatgpt|claude|gemini|qwen|llama',user_text,re.I):
        text=re.sub(r'(?i)\b(ich (?:bin|heiße)|mein name ist|hier ist)\s+(?:ChatGPT|Claude|Gemini|Qwen|Llama)(?:[- ](?:Assistent|assistant))?\b',lambda m:m[1]+' '+target,text)
    return re.sub(r'(?i)\b(ich (?:bin|heiße)|mein name ist|hier ist)\s+'+other+r'\b',lambda m:m[1]+' '+target,text)
