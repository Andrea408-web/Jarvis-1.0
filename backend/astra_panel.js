/* Native macOS panel with a real AppKit event pump, not only an NSRunLoop. */
ObjC.import('Cocoa');ObjC.import('WebKit');
function run(args){
 const content=$.NSString.stringWithContentsOfFileEncodingError(args[0],$.NSUTF8StringEncoding,null);
 if(!content)throw Error('Lokale Panel-Adresse fehlt.');
 const app=$.NSApplication.sharedApplication;app.setActivationPolicy($.NSApplicationActivationPolicyAccessory);app.finishLaunching;
 const rect=$.NSMakeRect(70,120,360,500);
 const panel=$.NSPanel.alloc.initWithContentRectStyleMaskBackingDefer(rect,1|2|8|128,$.NSBackingStoreBuffered,false);
 panel.title='ASTRA';panel.becomesKeyOnlyIfNeeded=true;panel.level=$.NSFloatingWindowLevel;panel.hidesOnDeactivate=false;panel.releasedWhenClosed=false;panel.collectionBehavior=1|256;
 const config=$.WKWebViewConfiguration.new;config.mediaTypesRequiringUserActionForPlayback=0;
 const web=$.WKWebView.alloc.initWithFrameConfiguration($.NSMakeRect(0,0,360,500),config);
 web.autoresizingMask=2|16;panel.contentView.addSubview(web);web.loadRequest($.NSURLRequest.requestWithURL($.NSURL.URLWithString(content)));
 panel.orderFrontRegardless;
 while(panel.isVisible){
   const event=app.nextEventMatchingMaskUntilDateInModeDequeue(0xffffffff,$.NSDate.dateWithTimeIntervalSinceNow(.05),$.NSDefaultRunLoopMode,true);
   if(event)app.sendEvent(event);
   app.updateWindows;
 }
}
