/* Bundled independent German voice. Speech generation never calls speechSynthesis. */
'use strict';
(() => {
  let worker=null,sequence=0;const pending=new Map();
  function fail(error){for(const request of pending.values()){clearTimeout(request.timer);request.reject(error);}pending.clear();worker?.terminate();worker=null;}
  function engine(){if(worker)return worker;worker=new Worker('/voice-worker.js');worker.onmessage=event=>{const request=pending.get(event.data.id);if(!request)return;pending.delete(event.data.id);clearTimeout(request.timer);if(event.data.error)request.reject(new Error(event.data.error));else request.resolve(event.data.wav);};worker.onerror=()=>fail(new Error('Die mitgelieferte Sprachengine konnte nicht geladen werden. Keine Systemstimme wurde gestartet.'));return worker;}
  window.JarvisVoice={render(text,preset='jarvis'){return new Promise((resolve,reject)=>{const id=++sequence;const timer=setTimeout(()=>{pending.delete(id);reject(new Error('Die Offline-Spracherzeugung braucht zu lange.'));},25000);pending.set(id,{resolve,reject,timer});try{engine().postMessage({id,text:text.slice(0,1800),preset});}catch(error){clearTimeout(timer);pending.delete(id);reject(error);}});},cancel(){for(const request of pending.values()){clearTimeout(request.timer);request.reject(new DOMException('Gestoppt','AbortError'));}pending.clear();},destroy(){fail(new DOMException('Beendet','AbortError'));}};
})();
