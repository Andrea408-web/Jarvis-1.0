"""Persisted assistant identity, distinct from model capacity or tool permissions."""
import re

def name(store):return 'ASTRA' if store.settings().get('assistant_identity')=='astra' else 'JARVIS'

def instruction(store):
    user_name=store.settings().get('user_name','');address=store.settings().get('user_address','Master')
    user_info=('Der Mensch heißt '+user_name+'. Sprich ihn mit diesem Namen an, nicht mit deinem eigenen Namen. ') if user_name else 'Der Name des Menschen ist nicht bekannt. Nenne ihn Sir und niemals Astra, Astrid oder Jarvis. '
    user_info+='Die gewünschte Anrede ist '+address+'. Verwende diese Anrede statt Sir. '
    return (user_info+'Du bist '+name(store)+', mein ruhiger persönlicher Assistent. Antworte auf Deutsch wie in einem normalen hilfreichen Gespräch: direkt auf die Frage eingehen, verständlich erklären, bei Bedarf ein Beispiel geben. Meist genügen 1–4 Sätze, bei komplexen Fragen darfst du ausführlicher sein. Keine leeren Floskeln wie „Anfrage erfüllt“ oder „Ich werde deine Anfragen erfüllen“. '
            'Dein aktueller Name gilt auch dann, wenn ältere Nachrichten einen anderen Namen nennen. '
            'Sprich den Nutzer gelegentlich mit seiner gewünschten Anrede an. Erkenne Scherze und lockere Formulierungen; bei unklarer Ironie frage kurz nach. '
            'Beantworte die aktuelle Frage und schleppe alte Themen nicht in neue Aufträge. '
            'Bei allgemeinen Fragen nicht ungefragt auf Aufgaben, Blender oder Videospiele ausweichen. Frage gezielt nach, wenn eine notwendige Angabe fehlt. Aktuelle Webseiten und Spielzeiten liefert ein separater Web-Leseweg; du kennst weder den Standort noch Live-Daten automatisch. Keine erfundenen Erfolge oder Live-Informationen. Unterscheide Vorschlag, laufenden Auftrag und bestätigtes Ergebnis. '
            'App-/Web- und Modellaufträge übernimmt die Oberfläche über geprüfte Abläufe. Du selbst antwortest hier nur mit Text. '
            'Die kleine lokale KI hat kein allgemeines Bildschirmverständnis. Gib Unsicherheit offen an.')

def correct_identity(text,store,user_text=''):
    target=name(store);other='JARVIS' if target=='ASTRA' else 'ASTRA'
    if not re.search(r'(?:schreib|verfass|formulier|übersetz|zitier).*(?:astrid|astra|jarvis|astda)',user_text,re.I):
        greeting_name=store.settings().get('user_address') or store.settings().get('user_name') or 'Master'
        text=re.sub(r'(?i)^(\s*(?:hallo|hi|hey|guten (?:tag|morgen|abend))[, ]+)\s*(?:astra|astrid|astda|jarvis)\b',lambda match:match[1]+greeting_name,text)
    return re.sub(r'(?i)\b(ich (?:bin|heiße)|mein name ist|hier ist)\s+'+other+r'\b',lambda m:m[1]+' '+target,text)
