"""Bounded ISO BMFF metadata reader; seeks over media, never decodes or loads it."""
import struct
from pathlib import Path

def probe(path):
 with Path(path).open('rb') as file:
  size=file.seek(0,2);count=0
  def boxes(start,end):
   nonlocal count
   while start+8<=end:
    count+=1
    if count>100000:raise ValueError('Zu viele Metadatenblöcke.')
    file.seek(start);length,kind=struct.unpack('>I4s',file.read(8));header=8
    if length==1:
     raw=file.read(8)
     if len(raw)!=8:raise ValueError('Unvollständiger Videokopf.')
     length=struct.unpack('>Q',raw)[0];header=16
    elif length==0:length=end-start
    if length<header or start+length>end:raise ValueError('Unvollständige Videodatei. Datei vollständig lokal herunterladen.')
    yield kind,start+header,start+length
    start+=length
  def read(start,end):
   if end-start>1048576:raise ValueError('Metadatenblock zu groß.')
   file.seek(start);return file.read(end-start)
  def duration(raw):
   if not raw or raw[0] not in {0,1}:raise ValueError('Ungültige Videodauer.')
   offset=20 if raw[0]==1 else 12;width=8 if raw[0]==1 else 4
   if len(raw)<offset+4+width:raise ValueError('Videodauer fehlt.')
   scale=int.from_bytes(raw[offset:offset+4],'big');value=int.from_bytes(raw[offset+4:offset+4+width],'big')
   if not scale:raise ValueError('Ungültige Videozeitskala.')
   return 0 if value==(1<<(8*width))-1 else value/scale
  movie=next(((a,b) for k,a,b in boxes(0,size) if k==b'moov'),None)
  if not movie:raise ValueError('Kein MP4/MOV-Videokopf gefunden.')
  tracks=[];fallback=0;defaults={}
  for kind,a,b in boxes(*movie):
   if kind==b'mvhd':fallback=duration(read(a,b))
   if kind==b'mvex':
    for key,c,d in boxes(a,b):
     if key==b'trex':
      raw=read(c,d)
      if len(raw)>=16:defaults[int.from_bytes(raw[4:8],'big')]=int.from_bytes(raw[12:16],'big')
   if kind!=b'trak':continue
   track={}
   for key,c,d in boxes(a,b):
    if key==b'tkhd':
     raw=read(c,d)
     if len(raw)<32:raise ValueError('Unvollständiger Videospurkopf.')
     track['id']=int.from_bytes(raw[20:24] if raw[0]==1 else raw[12:16],'big')
     if len(raw)>=8:track['width'],track['height']=[round(v/65536) for v in struct.unpack('>II',raw[-8:])]
    elif key==b'mdia':
     for key2,e,f in boxes(c,d):
      if key2==b'hdlr':track['kind']=read(e,min(f,e+12))[8:12]
      elif key2==b'mdhd':
       raw=read(e,f);track['duration']=duration(raw);offset=20 if raw[0]==1 else 12;track['scale']=int.from_bytes(raw[offset:offset+4],'big')
   tracks.append(track)
  video=next((t for t in tracks if t.get('kind')==b'vide' and t.get('width',0)>0 and t.get('height',0)>0),None)
  if not video:raise ValueError('Keine lesbare Videospur gefunden.')
  length=video.get('duration') or fallback
  if not length:
   ends={}
   for key,a,b in boxes(0,size):
    if key!=b'moof':continue
    for key2,c,d in boxes(a,b):
     if key2!=b'traf':continue
     ident=None;base=None;default=0;runs=[]
     for key3,e,f in boxes(c,d):
      if key3==b'tfhd':
       raw=read(e,f);flags=int.from_bytes(raw[1:4],'big');ident=int.from_bytes(raw[4:8],'big');pos=8+(8 if flags&1 else 0)+(4 if flags&2 else 0);default=int.from_bytes(raw[pos:pos+4],'big') if flags&8 else defaults.get(ident,0)
      elif key3==b'tfdt':
       raw=read(e,f);base=int.from_bytes(raw[4:12] if raw[0]==1 else raw[4:8],'big')
      elif key3==b'trun':runs.append(read(e,f))
     total=0
     for raw in runs:
      flags=int.from_bytes(raw[1:4],'big');samples=int.from_bytes(raw[4:8],'big');pos=8+(4 if flags&1 else 0)+(4 if flags&4 else 0);stride=4*sum(bool(flags&bit) for bit in [256,512,1024,2048])
      if len(raw)<pos+samples*stride:raise ValueError('Unvollständige Videofragmente.')
      if flags&256:total+=sum(int.from_bytes(raw[pos+i*stride:pos+i*stride+4],'big') for i in range(samples))
      else:total+=samples*default
     if ident is not None:ends[ident]=max(ends.get(ident,0),(base if base is not None else ends.get(ident,0))+total)
   length=ends.get(video.get('id'),0)/video.get('scale',1)
  return {'duration':length,'width':video['width'],'height':video['height'],'audio':any(t.get('kind')==b'soun' for t in tracks)}
