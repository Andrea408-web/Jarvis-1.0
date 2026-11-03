/* GPL component adapter; raw PCM generation only, no system/cloud voice. */
var module={exports:{}};
importScripts('/vendor/voice/ESpeak.js');
var Engine=module.exports;
var require=function(name){if(name==='./ESpeak.js')return Engine;throw Error('Unexpected speech dependency');};
module={exports:{}};
importScripts('/vendor/voice/mespeak.js');
var synth=module.exports;
var ready=Promise.all([fetch('/vendor/voice/config.json').then(r=>{if(!r.ok)throw Error('Sprachdaten fehlen');return r.json();}),fetch('/vendor/voice/jarvis-de.json').then(r=>{if(!r.ok)throw Error('Deutsche Stimme fehlt');return r.json();})]).then(data=>{synth.loadConfig(data[0]);synth.loadVoice(data[1]);if(!synth.isConfigLoaded()||!synth.isVoiceLoaded('de/jarvis'))throw Error('Sprachengine nicht bereit');});
self.onmessage=async event=>{const {id,text,preset}=event.data;try{await ready;if(typeof text!=='string'||!text.trim()||text.length>1800)throw Error('Sprachtext zu lang oder leer');const raw=synth.speak(text,{voice:'de/jarvis',amplitude:90,pitch:preset==='clear'?48:preset==='system'?26:35,speed:preset==='clear'?170:preset==='system'?145:155,wordgap:1,rawdata:'array'});if(!raw||raw.length<44)throw Error('Keine Sprachdaten erzeugt');const bytes=new Uint8Array(raw);postMessage({id,wav:bytes.buffer},[bytes.buffer]);}catch(error){postMessage({id,error:error.message||'Spracherzeugung fehlgeschlagen'});}};
