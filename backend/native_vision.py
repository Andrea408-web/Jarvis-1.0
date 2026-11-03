"""Explicit macOS Vision classification/OCR using installed system frameworks.

No image is sent to an Internet service. This is not a general vision-language
model and does not infer gameplay, moving actions, or guaranteed object identity.
"""
import ctypes
import platform


def analyze(image):
    if platform.system()!='Darwin':
        return {'available':False,'labels':[],'text':'','note':'Lokale Apple-Vision-Analyse benötigt den Mac. Das Bild kann als Gestaltungsmaterial verwendet werden.'}
    if not isinstance(image,bytes) or not 1<=len(image)<=4*1024*1024:raise ValueError('Ungültiges Bild für die lokale Analyse.')
    ident=ctypes.c_void_p
    runtime=ctypes.CDLL('/usr/lib/libobjc.A.dylib')
    ctypes.CDLL('/System/Library/Frameworks/Foundation.framework/Foundation')
    ctypes.CDLL('/System/Library/Frameworks/Vision.framework/Vision')
    runtime.objc_getClass.argtypes=[ctypes.c_char_p];runtime.objc_getClass.restype=ident
    runtime.sel_registerName.argtypes=[ctypes.c_char_p];runtime.sel_registerName.restype=ident
    address=ctypes.cast(runtime.objc_msgSend,ident).value
    def cls(name):
        value=runtime.objc_getClass(name.encode())
        if not value:raise ValueError('Eine benötigte Apple-Vision-Klasse fehlt.')
        return value
    def call(receiver,name,*args,ret=ident,types=()):
        selector=runtime.sel_registerName(name.encode())
        function=ctypes.CFUNCTYPE(ret,ident,ident,*types)(address)
        return function(receiver,selector,*args)
    def string(value):
        if not value:return ''
        raw=call(value,'UTF8String',ret=ctypes.c_char_p)
        return raw.decode('utf-8',errors='replace') if raw else ''
    def items(array,maximum):
        if not array:return []
        count=call(array,'count',ret=ctypes.c_ulong)
        return [call(array,'objectAtIndex:',i,types=(ctypes.c_ulong,)) for i in range(min(count,maximum))]
    pool=call(cls('NSAutoreleasePool'),'new')
    try:
        buffer=ctypes.create_string_buffer(image)
        data=call(cls('NSData'),'dataWithBytes:length:',ctypes.cast(buffer,ident),len(image),types=(ident,ctypes.c_ulong))
        options=call(cls('NSDictionary'),'dictionary')
        handler=call(call(cls('VNImageRequestHandler'),'alloc'),'initWithData:options:',data,options,types=(ident,ident))
        classification=call(call(cls('VNClassifyImageRequest'),'alloc'),'init')
        ocr=call(call(cls('VNRecognizeTextRequest'),'alloc'),'init')
        call(ocr,'setRecognitionLevel:',0,ret=None,types=(ctypes.c_long,))
        call(ocr,'setUsesLanguageCorrection:',True,ret=None,types=(ctypes.c_bool,))
        languages=[]
        for name in [b'de-DE',b'en-US']:
            languages.append(call(cls('NSString'),'stringWithUTF8String:',name,types=(ctypes.c_char_p,)))
        language_array=(ident*2)(*languages)
        language_list=call(cls('NSArray'),'arrayWithObjects:count:',language_array,2,types=(ctypes.POINTER(ident),ctypes.c_ulong))
        call(ocr,'setRecognitionLanguages:',language_list,ret=None,types=(ident,))
        requests=(ident*2)(classification,ocr)
        request_list=call(cls('NSArray'),'arrayWithObjects:count:',requests,2,types=(ctypes.POINTER(ident),ctypes.c_ulong))
        error=ident()
        try:
            ok=call(handler,'performRequests:error:',request_list,ctypes.byref(error),ret=ctypes.c_bool,types=(ident,ctypes.POINTER(ident)))
            if not ok:raise ValueError('Apple Vision konnte das Bild nicht auswerten. Es wird keine Bildanalyse behauptet.')
            labels=[]
            for observation in items(call(classification,'results'),10):
                confidence=float(call(observation,'confidence',ret=ctypes.c_float))
                if confidence>=.08:labels.append({'label':string(call(observation,'identifier'))[:160],'confidence':round(confidence,3)})
            text=[]
            for observation in items(call(ocr,'results'),40):
                candidates=items(call(observation,'topCandidates:',1,types=(ctypes.c_ulong,)),1)
                if candidates:text.append(string(call(candidates[0],'string'))[:300])
            return {'available':True,'labels':labels,'text':'\n'.join(text)[:4000],'note':'Lokale Apple-Vision-Klassifikation und Texterkennung. Unsichere Befunde; kein vollständiges Bildverständnis oder Gameplay-Analyse.'}
        finally:
            for value in [handler,classification,ocr]:
                if value:call(value,'release',ret=None)
    finally:call(pool,'drain',ret=None)
