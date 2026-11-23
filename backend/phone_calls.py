"""Explicit native call handoff. No audio access, call history or contact storage."""
import platform,re,subprocess,unicodedata


def normalize_number(value):
    if not isinstance(value,str) or not 1<=len(value)<=80:
        raise ValueError('Bitte eine Telefonnummer mit 3 bis 15 Ziffern angeben.')
    value=unicodedata.normalize('NFKC',value).strip()
    if not re.fullmatch(r'\+?[0-9 ()/.-]+',value):
        raise ValueError('Bitte nur Telefonnummer, Ländervorwahl und übliche Trennzeichen verwenden. Durchwahlen oder Steuerzeichen sind hier nicht vorgesehen.')
    number=re.sub(r'[ ()/.-]','',value)
    if not re.fullmatch(r'\+?[0-9]{3,15}',number):
        raise ValueError('Bitte eine Telefonnummer mit 3 bis 15 Ziffern angeben.')
    return number


def start(body):
    if not isinstance(body,dict) or set(body)-{'number','method'} or 'number' not in body:
        raise ValueError('Bitte Telefonnummer und die gewünschte Anrufart angeben.')
    number=normalize_number(body['number'])
    method=body.get('method','phone')
    if not isinstance(method,str) or method not in {'phone','facetime'}:
        raise ValueError('Bitte Telefon oder FaceTime Audio auswählen.')
    if platform.system()!='Darwin':
        raise ValueError('Der native Mac-Anrufstart benötigt macOS. Auf iPhone/iPad den Anrufknopf in diesem Browser verwenden; er öffnet die Telefon-App.')
    uri=('tel:' if method=='phone' else 'facetime-audio:')+number
    try:
        result=subprocess.run(['/usr/bin/open',uri],capture_output=True,timeout=10)
    except (OSError,subprocess.TimeoutExpired):
        raise ValueError('Die Telefon-/FaceTime-App konnte nicht geöffnet werden. Prüfe die macOS-Anrufeinrichtung und versuche es erneut.') from None
    if result.returncode:
        raise ValueError('macOS hat den Anrufstart nicht übernommen. Prüfe FaceTime und „Anrufe vom iPhone“ auf deinem Mac.')
    return {'state':'handoff','method':method,'message':'An die Telefon-/FaceTime-App übergeben. Bestätige gegebenenfalls dort den Anruf. Ob die Verbindung zustande kommt, zeigt die Telefon-App; Jarvis erhält daraus keinen Gesprächsstatus.'}
