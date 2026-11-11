"""Fixed macOS accessibility inspection; no model-written executable script."""
import ctypes,json,platform,subprocess

LABEL_SCRIPT='''function run(argv) {
 var proc=Application('System Events').applicationProcesses.whose({bundleIdentifier:argv[0]})[0];
 var wanted=argv[1].toLocaleLowerCase().trim(), found=[],visited=0;
 function visit(node,depth) {
  if(depth>7||visited++>600)return;
  try {var labels=[];try{labels.push(node.name());}catch(e){}try{labels.push(node.description());}catch(e){}
   var role='';try{role=node.role();}catch(e){}
   if(['AXButton','AXMenuItem','AXCheckBox','AXRadioButton','AXLink','AXPopUpButton','AXMenuButton','AXTextField'].indexOf(role)>=0&&labels.some(function(v){return String(v).toLocaleLowerCase().trim()===wanted;})) {
    var p=node.position(),s=node.size();if(s[0]>0&&s[1]>0)found.push({x:p[0]+s[0]/2,y:p[1]+s[1]/2});
   }
  }catch(e){}
  try{node.uiElements().forEach(function(child){visit(child,depth+1);});}catch(e){}
 }
 visit(proc,0);return JSON.stringify(found);
}'''

def status():
 if platform.system()!='Darwin':return {'supported':False,'trusted':False,'message':'Native Maussteuerung benötigt Jarvis direkt auf deinem Mac.'}
 try:
  lib=ctypes.CDLL('/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices');lib.AXIsProcessTrusted.restype=ctypes.c_bool;trusted=bool(lib.AXIsProcessTrusted())
 except OSError:trusted=False
 return {'supported':True,'trusted':trusted,'message':'Maus- und Tastaturzugriff freigegeben.' if trusted else 'Am Mac: Systemeinstellungen → Datenschutz & Sicherheit → Bedienungshilfen → Terminal bzw. Python erlauben. Danach Jarvis neu starten. Für benannte Schaltflächen kann zusätzlich Automation → System Events nötig sein.'}

def label_point(bundle,label):
 try:result=subprocess.run(['/usr/bin/osascript','-l','JavaScript','-e',LABEL_SCRIPT,'--',bundle,label],capture_output=True,text=True,timeout=12)
 except (OSError,subprocess.SubprocessError):raise ValueError('Die App-Oberfläche konnte nicht gelesen werden.') from None
 if result.returncode:raise ValueError('macOS hat die Oberflächenabfrage abgelehnt. Prüfe Bedienungshilfen und Automation → System Events.')
 try:points=json.loads(result.stdout)
 except ValueError:raise ValueError('Keine lesbare App-Oberfläche erhalten.') from None
 if not isinstance(points,list):raise ValueError('Ungültige Oberflächenantwort.')
 unique={}
 for p in points:
  if isinstance(p,dict) and type(p.get('x')) in {float,int} and type(p.get('y')) in {float,int}:unique[(p['x'],p['y'])]=p
 if len(unique)!=1:raise ValueError('Die Schaltfläche wurde nicht eindeutig gefunden. Es wurde nicht auf eine geratene Position geklickt.')
 return next(iter(unique.values()))


def frontmost(bundle,deadline,cancel_event=None):
 """Wait briefly for a just-opened app; never type into another application."""
 import time
 while True:
  if cancel_event and cancel_event.is_set():return False
  try:
   result=subprocess.run(['/usr/bin/osascript','-l','JavaScript','-e',"ObjC.import('AppKit');ObjC.unwrap($.NSWorkspace.sharedWorkspace.frontmostApplication.bundleIdentifier);"],capture_output=True,text=True,timeout=3)
  except (OSError,subprocess.SubprocessError):raise ValueError('Die Vordergrund-App konnte nicht geprüft werden.') from None
  if not result.returncode and result.stdout.strip()==bundle:return True
  if time.monotonic()>=deadline:raise ValueError('Die Ziel-App ist nicht im Vordergrund. Es wurden keine Eingaben in eine andere App gesendet. Öffne die Ziel-App und starte den Auftrag erneut.')
  if cancel_event:cancel_event.wait(.15)
  else:time.sleep(.15)
