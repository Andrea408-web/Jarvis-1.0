"""Opt-in body AND finger landmarks from installed macOS Vision, no model download.
Frames and landmarks stay in memory on the user's Mac. No motor commands.
"""
import ctypes, math, platform

class Point(ctypes.Structure):
 _fields_=[('x',ctypes.c_double),('y',ctypes.c_double)]

HAND_JOINTS=['Wrist','ThumbCMC','ThumbMP','ThumbIP','ThumbTip']+[finger+part for finger in ['Index','Middle','Ring','Little'] for part in ['MCP','PIP','DIP','Tip']]

def detect(image):
 if platform.system()!='Darwin':raise ValueError('Kameratracking braucht den Jarvis-Server auf einem Mac mit Apple Vision (macOS 11 oder neuer).')
 if not isinstance(image,bytes) or not 1<=len(image)<=300000 or not image.startswith(b'\xff\xd8\xff'):raise ValueError('Bitte ein kleines JPEG-Kamerabild senden.')
 ident=ctypes.c_void_p;runtime=ctypes.CDLL('/usr/lib/libobjc.A.dylib');ctypes.CDLL('/System/Library/Frameworks/Foundation.framework/Foundation');vision=ctypes.CDLL('/System/Library/Frameworks/Vision.framework/Vision')
 runtime.objc_getClass.argtypes=[ctypes.c_char_p];runtime.objc_getClass.restype=ident;runtime.sel_registerName.argtypes=[ctypes.c_char_p];runtime.sel_registerName.restype=ident;address=ctypes.cast(runtime.objc_msgSend,ident).value
 def cls(name):
  found=runtime.objc_getClass(name.encode())
  if not found:raise ValueError('Diese macOS-Version bietet das Handtracking nicht an (macOS 11 oder neuer nötig).')
  return found
 def call(receiver,name,*args,ret=ident,types=()):return ctypes.CFUNCTYPE(ret,ident,ident,*types)(address)(receiver,runtime.sel_registerName(name.encode()),*args)
 def landmarks(observation,group_symbol,prefix,names):
  error=ident();group=ident.in_dll(vision,group_symbol);points=call(observation,'recognizedPointsForJointsGroupName:error:',group,ctypes.byref(error),types=(ident,ctypes.POINTER(ident)));out={}
  if not points:return out
  for name in names:
   key=ident.in_dll(vision,prefix+name);point=call(points,'objectForKey:',key,types=(ident,))
   if not point:continue
   confidence=float(call(point,'confidence',ret=ctypes.c_float));location=call(point,'location',ret=Point)
   if confidence>=.35 and all(math.isfinite(v) and 0<=v<=1 for v in [location.x,location.y]):out[name[0].lower()+name[1:]]={'x':location.x,'y':1-location.y,'confidence':confidence}
  return out
 pool=call(cls('NSAutoreleasePool'),'new');allocated=[]
 try:
  buffer=ctypes.create_string_buffer(image);data=call(cls('NSData'),'dataWithBytes:length:',ctypes.cast(buffer,ident),len(image),types=(ident,ctypes.c_ulong));options=call(cls('NSDictionary'),'dictionary');handler=call(call(cls('VNImageRequestHandler'),'alloc'),'initWithData:options:',data,options,types=(ident,ident));allocated.append(handler)
  body=call(call(cls('VNDetectHumanBodyPoseRequest'),'alloc'),'init');allocated.append(body);hand=call(call(cls('VNDetectHumanHandPoseRequest'),'alloc'),'init');allocated.append(hand);call(hand,'setMaximumHandCount:',2,ret=None,types=(ctypes.c_ulong,))
  requests=(ident*2)(body,hand);array=call(cls('NSArray'),'arrayWithObjects:count:',requests,2,types=(ctypes.POINTER(ident),ctypes.c_ulong));error=ident()
  if not call(handler,'performRequests:error:',array,ctypes.byref(error),ret=ctypes.c_bool,types=(ident,ctypes.POINTER(ident))):raise ValueError('Das Kamerabild konnte nicht als Hand-/Körperpose ausgewertet werden.')
  arms={};hands=[];observations=call(body,'results')
  if call(observations,'count',ret=ctypes.c_ulong):
   observation=call(observations,'objectAtIndex:',0,types=(ctypes.c_ulong,))
   for side in ['Left','Right']:
    found=landmarks(observation,'VNHumanBodyPoseObservationJointsGroupNameAll','VNHumanBodyPoseObservationJointName',[side+part for part in ['Shoulder','Elbow','Wrist']]);joints={key[len(side):].lower():value for key,value in found.items()}
    if len(joints)==3:arms[side.lower()]=joints
  observations=call(hand,'results')
  for index in range(min(2,call(observations,'count',ret=ctypes.c_ulong))):
   observation=call(observations,'objectAtIndex:',index,types=(ctypes.c_ulong,));joints=landmarks(observation,'VNHumanHandPoseObservationJointsGroupNameAll','VNHumanHandPoseObservationJointName',HAND_JOINTS)
   if all(key in joints for key in ['wrist','indexTip','thumbTip','middleMCP']):hands.append({'joints':joints,'confidence':sum(p['confidence'] for p in joints.values())/len(joints)})
  return {'arms':arms,'hands':hands,'message':'Handtracking aktiv.' if hands else 'Keine sichere Hand erkannt. Handfläche und Finger gut beleuchten und vollständig ins Bild halten.'}
 except (OSError,ValueError) as e:raise ValueError(str(e)) from None
 finally:
  for value in reversed(allocated):
   if value:call(value,'release',ret=None)
  call(pool,'drain',ret=None)
