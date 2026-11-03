/* Local voice facade. Background exports are not cancelled by conversational mute. */
'use strict';
(() => {
  let worker=null,sequence=0;const pending=new Map(),naturalRequests=new Set();
  function fail(error){for(const request of pending.values()){clearTimeout(request.timer);request.reject(error);}pending.clear();worker?.terminate();worker=null;}
  function engine(){if(worker)return worker;worker=new Worker('/voice-worker.js');worker.onmessage=event=>{const request=pending.get(event.data.id);if(!request)return;pending.delete(event.data.id);clearTimeout(request.timer);if(event.data.error)request.reject(new Error(event.data.error));else request.resolve(event.data.wav);};worker.onerror=()=>fail(new Error('Die mitgelieferte Sprachengine konnte nicht geladen werden. Keine Systemstimme wurde gestartet.'));return worker;}
  window.JarvisVoice={
    render(text,preset='jarvis',options={}){
      const background=options.background===true;
      if(window.JarvisBridge?.getSettings().voice_engine==='natural'){
        const request={controller:new AbortController(),background};naturalRequests.add(request);
        return window.JarvisBridge.api('/api/natural-voice/speak',{method:'POST',body:JSON.stringify({text:text.slice(0,1800),preset}),signal:request.controller.signal}).then(blob=>blob.arrayBuffer()).finally(()=>naturalRequests.delete(request));
      }
      return new Promise((resolve,reject)=>{const id=++sequence;const timer=setTimeout(()=>{pending.delete(id);reject(new Error('Die Offline-Spracherzeugung braucht zu lange.'));},25000);pending.set(id,{resolve,reject,timer,background});try{engine().postMessage({id,text:text.slice(0,1800),preset});}catch(error){clearTimeout(timer);pending.delete(id);reject(error);}});
    },
    cancel(){
      for(const request of naturalRequests){if(!request.background){request.controller.abort();naturalRequests.delete(request);}}
      for(const [id,request] of pending){if(!request.background){clearTimeout(request.timer);request.reject(new DOMException('Gestoppt','AbortError'));pending.delete(id);}}
    },
    destroy(){for(const request of naturalRequests)request.controller.abort();naturalRequests.clear();fail(new DOMException('Beendet','AbortError'));}
  };
})();
