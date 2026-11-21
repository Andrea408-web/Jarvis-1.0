"""Controlled concept data for tests/screenshots, never an application template."""
ARM={'title':'Mini-Roboterarm · Konzeptstudie','parts':[
 {'name':'LED-Statusmodul','shape':'cylinder','size':[12,4,12],'position':[0,23,55],'material':'light'},
 {'name':'Standfuß','shape':'lathe','size':[170,20,150],'position':[0,10,0],'material':'metal','profile':[[0,-.5],[.43,-.5],[.5,-.1],[.5,.2],[.42,.5],[0,.5]]},
 {'name':'Linke Säule','shape':'cylinder','size':[24,135,24],'position':[-40,87.5,0],'material':'metal'},
 {'name':'Rechte Säule','shape':'cylinder','size':[24,135,24],'position':[40,87.5,0],'material':'metal'},
 {'name':'Schultergelenk-Gehäuse','shape':'cylinder','size':[48,110,48],'position':[0,155,0],'rotation':[0,0,90],'material':'metal'},
 {'name':'Oberarm','shape':'extrude','size':[32,110,32],'position':[38.9,193.9,0],'rotation':[0,0,-45],'material':'metal','outline':[[-.25,-.5],[.25,-.5],[.5,-.35],[.35,.35],[.15,.5],[-.15,.5],[-.35,.35],[-.5,-.35]],'smooth':True},
 {'name':'Ellbogengelenk-Gehäuse','shape':'cylinder','size':[44,52,44],'position':[77.8,232.8,0],'rotation':[0,0,90],'material':'metal'},
 {'name':'Unterarm','shape':'extrude','size':[28,110,28],'position':[130.9,247,0],'rotation':[0,0,-75],'material':'metal','outline':[[-.3,-.5],[.3,-.5],[.5,-.3],[.3,.45],[0,.5],[-.3,.45],[-.5,-.3]],'smooth':True},
 {'name':'Handgelenk-Gehäuse','shape':'cylinder','size':[36,42,36],'position':[184,261.2,0],'rotation':[0,0,90],'material':'metal'},
 {'name':'Greifer-Konzept','shape':'extrude','size':[54,44,16],'position':[222,261.2,0],'material':'metal','outline':[[-.5,-.5],[.5,-.5],[.5,-.25],[-.15,-.25],[-.15,.25],[.5,.25],[.5,.5],[-.5,.5]]}],
 'steps':['Den Platz am Tisch und den gewünschten Arbeitsbereich ausmessen.','Zuerst einen unbeweglichen Maßstabsprototyp mit den Baugruppen anfertigen.','Antriebe, Gelenklager, Verkabelung und Greifer erst nach Auslegung zusammenstellen.'],
 'features':['Standfuß mit zwei tragenden Säulen als Konzept','Zwei Armsegmente und Greifer als räumlicher Vorentwurf'],
 'explanation':'Der breite Standfuß und zwei Säulen bilden die Basis. Zwei Armsegmente reichen zum vorgesehenen Arbeitsbereich; die Gelenkgehäuse markieren mögliche Antriebspositionen. Das ist ein Funktionskonzept, noch keine berechnete Maschine.',
 'concept':{'systems':[{'name':'Standfuß & Säulen','function':'Soll die Baugruppen am Tisch tragen; Befestigung und Kippstabilität sind noch auszulegen.'},{'name':'Gelenke & Antrieb','function':'Vorgesehene Armbewegung über zwei Segmente; Motoren, Lager und Gelenkgrenzen sind noch offen.'},{'name':'Greifer','function':'Konzept für die Aufnahme kleiner Teile. Greifkraft und passende Backen hängen vom Werkstück ab.'},{'name':'Steuerung & Versorgung','function':'Soll Bewegung und Statuslicht koordinieren. Hier noch kein Controller oder Steuerprogramm vorhanden.'}],
 'workflow':['Werkstück und erlaubten Arbeitsbereich festlegen.','Geplante Bewegung und Greifposition zunächst ohne Antrieb überprüfen.','Erst nach Auslegung eine begrenzte Bewegung mit geeigneter Steuerung erproben.'],
 'unresolved':['Welche Teile sollen gegriffen werden, wie schwer sind sie und wie weit liegen sie entfernt?','Drehmomente, Lager, Kippstabilität, Kabelwege und mechanische Anschläge berechnen.','Geeignete Antriebe, Versorgung, Abschaltung und Steuerung auswählen.']}}
