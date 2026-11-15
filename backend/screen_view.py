"""Explicit, memory-only main-display snapshots. No files, clipboard or external service."""
import ctypes,platform,threading
class Rect(ctypes.Structure):_fields_=[('x',ctypes.c_double),('y',ctypes.c_double),('w',ctypes.c_double),('h',ctypes.c_double)]
class ScreenView:
 def __init__(self):self.enabled=False;self.generation=0;self.lock=threading.Lock()
 def _graphics(self):
  if platform.system()!='Darwin':raise ValueError('Bildschirmaufnahme ist hier nur am Mac verfügbar.')
  return ctypes.CDLL('/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics')
 def start(self):
  with self.lock:self.generation+=1;version=self.generation;self.enabled=False
  try:
   c=self._graphics();c.CGPreflightScreenCaptureAccess.restype=ctypes.c_bool;c.CGRequestScreenCaptureAccess.restype=ctypes.c_bool
   if not c.CGPreflightScreenCaptureAccess():c.CGRequestScreenCaptureAccess()
   granted=bool(c.CGPreflightScreenCaptureAccess())
  except (OSError,AttributeError):raise ValueError('Native Bildschirmfreigabe ist hier nicht verfügbar. Bitte den Browser-Helfer verwenden.') from None
  with self.lock:self.enabled=granted and version==self.generation;active=self.enabled
  return {'active':active,'message':'Hauptbildschirm freigegeben. Ein Bild wird nur bei deinen Fragen lokal ausgewertet; keine Speicherung.' if active else 'macOS hat Bildschirmaufnahme noch nicht freigegeben oder die Anfrage wurde beendet. Unter Systemeinstellungen → Datenschutz & Sicherheit → Bildschirmaufnahme erlauben; gegebenenfalls Jarvis neu starten. Alternativ Bildschirm im Browser-Helfer teilen.'}
 def stop(self):
  with self.lock:self.generation+=1;self.enabled=False
  return {'active':False,'message':'Bildschirmfreigabe beendet.'}
 def capture(self):
  if not self.enabled:raise ValueError('Bildschirm wurde nicht freigegeben.')
  c=self._graphics();c.CGPreflightScreenCaptureAccess.restype=ctypes.c_bool
  if not c.CGPreflightScreenCaptureAccess():self.stop();raise ValueError('macOS-Bildschirmfreigabe wurde entzogen.')
  p=ctypes.c_void_p;size=ctypes.c_size_t;allocated=[];image=scaled=context=space=None
  try:
   f=ctypes.CDLL('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation');io=ctypes.CDLL('/System/Library/Frameworks/ImageIO.framework/ImageIO')
   def setup(lib,name,ret,args):fn=getattr(lib,name);fn.restype=ret;fn.argtypes=args;return fn
   capture=setup(c,'CGDisplayCreateImage',p,[ctypes.c_uint32]);display=setup(c,'CGMainDisplayID',ctypes.c_uint32,[]);image=capture(display())
   if not image:raise ValueError('Diese macOS-Version bietet diese Aufnahme nicht an. Bitte Bildschirm im Browser-Helfer freigeben.')
   width=setup(c,'CGImageGetWidth',size,[p])(image);height=setup(c,'CGImageGetHeight',size,[p])(image)
   if not width or not height:raise ValueError('Kein Bildschirmbild verfügbar.')
   ratio=min(1,1280/max(width,height));w=max(1,int(width*ratio));h=max(1,int(height*ratio));space=setup(c,'CGColorSpaceCreateDeviceRGB',p,[])();context=setup(c,'CGBitmapContextCreate',p,[p,size,size,size,size,p,ctypes.c_uint32])(None,w,h,8,w*4,space,16385)
   if not context:raise ValueError('Bildschirmbild konnte nicht verkleinert werden.')
   setup(c,'CGContextDrawImage',None,[p,Rect,p])(context,Rect(0,0,w,h),image);scaled=setup(c,'CGBitmapContextCreateImage',p,[p])(context)
   data=setup(f,'CFDataCreateMutable',p,[p,ctypes.c_long])(None,0);allocated.append(data);kind=setup(f,'CFStringCreateWithCString',p,[p,ctypes.c_char_p,ctypes.c_uint32])(None,b'public.jpeg',0x08000100);allocated.append(kind);destination=setup(io,'CGImageDestinationCreateWithData',p,[p,p,size,p])(data,kind,1,None);allocated.append(destination)
   if not data or not kind or not destination or not scaled:raise ValueError('Bildschirmbild konnte nicht verarbeitet werden.')
   setup(io,'CGImageDestinationAddImage',None,[p,p,p])(destination,scaled,None)
   if not setup(io,'CGImageDestinationFinalize',ctypes.c_bool,[p])(destination):raise ValueError('Bildschirmbild konnte nicht kodiert werden.')
   length=setup(f,'CFDataGetLength',ctypes.c_long,[p])(data)
   if not 1<=length<=4*1024*1024:raise ValueError('Bildschirmbild ist zu groß.')
   address=setup(f,'CFDataGetBytePtr',p,[p])(data);return ctypes.string_at(address,length)
  except (OSError,AttributeError) as error:raise ValueError('Native Bildschirmaufnahme nicht verfügbar. Bitte den Browser-Helfer verwenden.') from None
  finally:
   for value in reversed(allocated):
    if value:setup(f,'CFRelease',None,[p])(value)
   for value in [image,scaled]:
    if value:setup(c,'CGImageRelease',None,[p])(value)
   if context:setup(c,'CGContextRelease',None,[p])(context)
   if space:setup(c,'CGColorSpaceRelease',None,[p])(space)
