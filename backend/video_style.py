"""Bounded declarative video styles and literal subtitle text; never model code."""
import math
DEFAULT={'look':'natural','transition':'cut','zoom':False,'vignette':False,'sharpen':False,'speed':1.0,'subtitle_style':'clean'}
def validate(style=None,captions=None):
 style={} if style is None else style;captions=[] if captions is None else captions
 if not isinstance(style,dict) or set(style)-set(DEFAULT):raise ValueError('Unbekannte Videoeffekte.')
 result={**DEFAULT,**style}
 if result['look'] not in {'natural','cinematic','neon','mono','warm'} or result['transition'] not in {'cut','fade'} or result['subtitle_style'] not in {'clean','gold','pop'}:raise ValueError('Unbekannter Look, Übergang oder Untertitelstil.')
 if any(type(result[k]) is not bool for k in ['zoom','vignette','sharpen']):raise ValueError('Ungültiger Effektschalter.')
 if type(result['speed']) not in {int,float} or not math.isfinite(result['speed']) or not .5<=result['speed']<=2:raise ValueError('Tempo muss zwischen 0,5 und 2 liegen.')
 if not isinstance(captions,list) or len(captions)>600:raise ValueError('Maximal 600 Untertitel pro Export.')
 checked=[]
 for cue in captions:
  if not isinstance(cue,dict) or set(cue)!={'start','end','text'}:raise ValueError('Ungültiger Untertitel.')
  a,b,text=cue['start'],cue['end'],cue['text']
  if any(type(v) not in {float,int} or not math.isfinite(v) for v in [a,b]) or not 0<=a<b<=43200 or not isinstance(text,str) or not 1<=len(text.strip())<=240:raise ValueError('Untertitel benötigen gültige Zeiten und 1 bis 240 Zeichen.')
  checked.append({'start':a,'end':b,'text':text.strip()})
 return result,sorted(checked,key=lambda c:c['start'])
def active(style,captions):return bool(captions) or any(style[k]!=v for k,v in DEFAULT.items() if k!='subtitle_style')

def ass(captions,width,height,style):
 def stamp(value):
  value=round(value*100);return f'{value//360000}:{value//6000%60:02}:{value//100%60:02}.{value%100:02}'
 color='&H007CE5FF' if style=='gold' else '&H00FFFFFF';font=round(min(width*.055,height*.043));margin=round(height*.075)
 lines=['[Script Info]','ScriptType: v4.00+',f'PlayResX: {width}',f'PlayResY: {height}','WrapStyle: 0','[V4+ Styles]','Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding',f'Style: Default,Arial,{font},{color},{color},&H00101010,&H80000000,-1,0,0,0,100,100,0,0,1,3,1,2,50,50,{margin},1','[Events]','Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text']
 for cue in captions:
  text=cue['text'].replace('\\','＼').replace('{','｛').replace('}','｝').replace('\r','').replace('\n',r'\N')
  if style=='pop':text=r'{\fscx90\fscy90\t(0,120,\fscx100\fscy100)}'+text
  lines.append(f"Dialogue: 0,{stamp(cue['start'])},{stamp(cue['end'])},Default,,0,0,0,,{text}")
 return '\n'.join(lines)+'\n'

def filters(style,width,height):
 looks={'natural':[],'cinematic':['eq=contrast=1.12:saturation=0.8:brightness=0.015'],'neon':['eq=contrast=1.15:saturation=1.6'],'mono':['hue=s=0'],'warm':['colorbalance=rs=.10:bs=-.06:rh=.04']}
 out=list(looks[style['look']])
 if style['zoom']:out.append(f"zoompan=z='min(zoom+0.00035,1.12)':d=1:s={width}x{height}:fps=30")
 if style['vignette']:out.append('vignette=PI/5')
 if style['sharpen']:out.append('unsharp=5:5:0.45:5:5:0')
 if style['speed']!=1:out.append('setpts=PTS/'+str(style['speed']))
 return out

def spread(captions,duration):
 if not captions:return []
 if not 0<duration<=43200:raise ValueError('Untertitel-Projekt muss kürzer als 12 Stunden sein.')
 return [{'start':i*duration/len(captions),'end':(i+1)*duration/len(captions),'text':cue['text']} for i,cue in enumerate(captions)]
