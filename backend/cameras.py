"""Curated public pages; no discovery of private or unsecured cameras."""
CAMERAS = [
    {'id':'new-york','name':'New York · Times Square','aliases':['new york','times square'], 'lat':40.758,'lon':-73.985,'url':'https://www.earthcam.com/usa/newyork/timessquare/'},
    {'id':'london','name':'London · Abbey Road','aliases':['london','abbey road'],'lat':51.532,'lon':-.178,'url':'https://www.abbeyroad.com/crossing'},
    {'id':'reykjavik','name':'Reykjavík','aliases':['reykjavik','reykjavík','island'],'lat':64.146,'lon':-21.942,'url':'https://www.livefromiceland.is/webcams/reykjavik/'},
    {'id':'venice','name':'Venedig · Rialto','aliases':['venedig','venice','rialto'],'lat':45.438,'lon':12.335,'url':'https://www.skylinewebcams.com/en/webcam/italia/veneto/venezia/rialto-canal-grande.html'},
]

# Public German webcam pages. Embedding remains subject to the operator.
CAMERAS.extend([
    {'id':'zugspitze','name':'Zugspitze · Panorama','aliases':['zugspitze','garmisch','alpen'],'country':'Deutschland','lat':47.421,'lon':10.985,'url':'https://zugspitze.panomax.com/'},
    {'id':'muenchen','name':'München · Webcams','aliases':['münchen','muenchen','munich','marienplatz'],'country':'Deutschland','lat':48.137,'lon':11.576,'url':'https://www.muenchen.de/sehenswuerdigkeiten/webcams'},
    {'id':'berlin','name':'Berlin · Öffentliche Webcams','aliases':['berlin','brandenburger tor'],'country':'Deutschland','lat':52.516,'lon':13.378,'url':'https://www.berlin.de/tourismus/webcams/'},
])
SPORTS = [
    {'name':'Sportschau · Live & Ergebnisse','url':'https://www.sportschau.de/live-und-ergebnisse','note':'Offizielle Übertragungen und Live-Angebote; nicht jedes Spiel hat einen Videostream.'},
    {'name':'ARD · Live-TV','url':'https://www.ardmediathek.de/live','note':'Öffentliche Livekanäle, meist ohne Konto. Fußball nur bei vorhandenen Übertragungsrechten.'},
    {'name':'ZDF · Sport','url':'https://www.zdf.de/sport','note':'Sportübertragungen und frei verfügbare Beiträge. Rechte und Standort können das Angebot begrenzen.'},
]
