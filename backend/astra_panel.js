/* Native floating macOS panel; WebKit loads only the local Jarvis UI. */
ObjC.import('Cocoa');ObjC.import('WebKit');
function run(args){
  const content=$.NSString.stringWithContentsOfFileEncodingError(args[0],$.NSUTF8StringEncoding,null);
  if(!content)throw Error('Lokale Panel-Adresse fehlt.');
  const app=$.NSApplication.sharedApplication;app.setActivationPolicy($.NSApplicationActivationPolicyAccessory);
  const rect=$.NSMakeRect(70,120,350,470);
  const panel=$.NSPanel.alloc.initWithContentRectStyleMaskBackingDefer(rect,1|2|8|128,$.NSBackingStoreBuffered,false);
  panel.title='ASTRA';panel.becomesKeyOnlyIfNeeded=true;panel.level=$.NSFloatingWindowLevel;panel.hidesOnDeactivate=false;panel.releasedWhenClosed=false;
  const web=$.WKWebView.alloc.initWithFrameConfiguration($.NSMakeRect(0,0,350,470),$.WKWebViewConfiguration.new);
  web.autoresizingMask=2|16;panel.contentView.addSubview(web);
  web.loadRequest($.NSURLRequest.requestWithURL($.NSURL.URLWithString(content)));
  panel.makeKeyAndOrderFront(null);
  while(panel.isVisible){$.NSRunLoop.currentRunLoop.runUntilDate($.NSDate.dateWithTimeIntervalSinceNow(.1));}
}
