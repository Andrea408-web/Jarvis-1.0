"""Optional USB-only Quest localhost forward using an already installed adb.
No download, account creation, LAN listener or certificate bypass.
"""
import json,os,shutil,subprocess,urllib.request
from pathlib import Path

def find_adb():
    found=shutil.which('adb')
    if found:return found
    for path in [Path.home()/'Library/Android/sdk/platform-tools/adb',Path.home()/'Downloads/platform-tools/adb']:
        if path.is_file() and os.access(path,os.X_OK):return str(path)
    raise ValueError('Android Platform Tools (adb) fehlen. Offiziell: https://developer.android.com/tools/releases/platform-tools — Mac-Paket laden und platform-tools im Downloads-Ordner lassen. Es wird hier nichts automatisch installiert.')

def connect(disconnect=False):
    adb=find_adb()
    def run(args):
        try:return subprocess.run([adb,*args],capture_output=True,text=True,check=True,timeout=20).stdout
        except (OSError,subprocess.SubprocessError):raise ValueError('USB-Verbindung fehlgeschlagen. Entwickler-Modus, USB-Kabel und USB-Debugging-Freigabe in der Quest prüfen.') from None
    lines=run(['devices']).splitlines()[1:];devices=[line.split()[0] for line in lines if len(line.split())==2 and line.split()[1]=='device']
    if len(devices)!=1:raise ValueError('Bitte genau eine freigegebene Quest per USB anschließen. In der Meta-Horizon-App muss der Entwickler-Modus verfügbar und aktiviert sein; in der Brille USB-Debugging erlauben. Andere Android-Geräte abziehen.')
    serial=devices[0]
    manufacturer=run(['-s',serial,'shell','getprop','ro.product.manufacturer']).strip().lower()
    if manufacturer not in {'oculus','meta'}:raise ValueError('Das angeschlossene Gerät wurde nicht als Meta/Oculus-Gerät erkannt. Andere Android-Geräte abziehen.')
    if disconnect:
        run(['-s',serial,'reverse','--remove','tcp:8765']);return 'USB-Weiterleitung beendet.'
    try:
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open('http://127.0.0.1:8765/api/session',timeout=5) as response:
            data=json.loads(response.read(8192))
        if not isinstance(data.get('token'),str):raise ValueError()
    except Exception:raise ValueError('Jarvis läuft noch nicht auf Port 8765. Zuerst 2-JARVIS-starten.command im Jarvis-Ordner öffnen und das Terminal offen lassen.') from None
    run(['-s',serial,'reverse','tcp:8765','tcp:8765'])
    run(['-s',serial,'shell','am','start','-a','android.intent.action.VIEW','-d','http://localhost:8765/aeris?vr=1','-p','com.oculus.browser'])
    return 'Quest Browser geöffnet: http://localhost:8765/aeris?vr=1\nJetzt VR starten wählen und die Freigabe bestätigen. Das USB-Kabel angeschlossen und Jarvis auf dem Mac geöffnet lassen. Die Brille nutzt den Server auf dem Mac, keinen eigenen KI-Server.'

def main():
    import sys
    try:print(connect('--disconnect' in sys.argv))
    except ValueError as error:print(str(error));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
