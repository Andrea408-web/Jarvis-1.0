/* Thorsten only. No synthetic or system-voice fallback. */
'use strict';
(()=>{
 const requests=new Set();
 window.JarvisVoice={
  render(text,preset='jarvis',options={}){
   const request={controller:new AbortController(),background:options.background===true,id:crypto.randomUUID()};requests.add(request);
   return window.JarvisBridge.api('/api/natural-voice/speak',{method:'POST',body:JSON.stringify({text:text.slice(0,1800),preset,id:request.id,background:request.background}),signal:request.controller.signal}).then(blob=>blob.arrayBuffer()).finally(()=>requests.delete(request));
  },
  cancel(){for(const request of requests){if(!request.background){request.controller.abort();window.JarvisBridge.api('/api/natural-voice/cancel',{method:'POST',body:JSON.stringify({id:request.id})}).catch(()=>{});requests.delete(request);}}},
  destroy(){for(const request of requests)request.controller.abort();requests.clear();}
 };
})();
