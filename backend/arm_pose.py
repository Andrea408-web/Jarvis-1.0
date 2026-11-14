"""Opt-in 2D arm landmarks from the installed macOS Vision framework.
Frames stay in memory on the user's Mac. No robot commands or external service.
"""
import ctypes,math,platform

class Point(ctypes.Structure):_fields_=[('x',ctypes.c_double),('y',ctypes.c_double)]

def detect(image):
 if platform.system()!='Darwin':raise ValueError('Kameratracking braucht den Jarvis-Server auf einem Mac mit Apple Vision (macOS 11 oder neuer).')
 if not isinstance(image,bytes) or not 1<=len(image)<=300000 or not image.startswith(b'\xff\xd8\xff'):raise ValueError('Bitte ein kleines JPEG-Kamerabild senden.')
 ident=ctypes.c_void_p;runtime=ctypes.CDLL('/usr/lib/libobjc.A.dylib');ctypes.CDLL('/System/Library/Frameworks/Foundation.framework/Foundation');vision=ctypes.CDLL('/System/Library/Frameworks/Vision.framework/Vision')
 runtime.objc_getClass.argtypes=[ctypes.c_char_p];runtime.objc_getClass.restype=ident;runtime.sel_registerName.argtypes=[ctypes.c_char_p];runtime.sel_registerName.restype=ident;address=ctypes.cast(runtime.objc_msgSend,ident).value
 def cls(name):
  found=runtime.objc_getClass(name.encode())
  if not found:raise ValueError('Diese macOS-Version bietet das Körpertracking nicht an.')
  return found
 def call(receiver,name,*args,ret=ident,types=()):return ctypes.CFUNCTYPE(ret,ident,ident,*types)(address)(receiver,runtime.sel_registerName(name.encode()),*args)
 pool=call(cls('NSAutoreleasePool'),'new');handler=request=None
 try:
  buffer=ctypes.create_string_buffer(image);data=call(cls('NSData'),'dataWithBytes:length:',ctypes.cast(buffer,ident),len(image),types=(ident,ctypes.c_ulong));options=call(cls('NSDictionary'),'dictionary');handler=call(call(cls('VNImageRequestHandler'),'alloc'),'initWithData:options:',data,options,types=(ident,ident));request=call(call(cls('VNDetectHumanBodyPoseRequest'),'alloc'),'init');requests=(ident*1)(request);array=call(cls('NSArray'),'arrayWithObjects:count:',requests,1,types=(ctypes.POINTER(ident),ctypes.c_ulong));error=ident()
  if not call(handler,'performRequests:error:',array,ctypes.byref(error),ret=ctypes.c_bool,types=(ident,ctypes.POINTER(ident))):raise ValueError('Das Kamerabild konnte nicht als Körperpose ausgewertet werden.')
  observations=call(request,'results')
  if not call(observations,'count',ret=ctypes.c_ulong):return {'arms':{},'message':'Kein Körper erkannt. Schulter, Ellbogen und Handgelenk ins Kamerabild bringen.'}
  observation=call(observations,'objectAtIndex:',0,types=(ctypes.c_ulong,));group=ident.in_dll(vision,'VNHumanBodyPoseObservationJointsGroupNameAll');points=call(observation,'recognizedPointsForGroupKey:error:',group,ctypes.byref(error),types=(ident,ctypes.POINTER(ident)));arms={}
  for side in ['Left','Right']:
   joints={}
   for part in ['Shoulder','Elbow','Wrist']:
    key=ident.in_dll(vision,'VNHumanBodyPoseObservationJointName'+side+part);point=call(points,'objectForKey:',key,types=(ident,))
    if not point:continue
    confidence=float(call(point,'confidence',ret=ctypes.c_float));location=call(point,'location',ret=Point)
    if confidence>=.4 and all(math.isfinite(v) and 0<=v<=1 for v in [location.x,location.y]):joints[part.lower()]={'x':location.x,'y':1-location.y,'confidence':confidence}
   if len(joints)==3:arms[side.lower()]=joints
  return {'arms':arms,'message':'2D-Armtracking aktiv.' if arms else 'Armgelenke nicht sicher erkannt. Position wird nicht geraten.'}
 except (OSError,ValueError) as e:raise ValueError(str(e)) from None
 finally:
  for value in [handler,request]:
   if value:call(value,'release',ret=None)
  call(pool,'drain',ret=None)
