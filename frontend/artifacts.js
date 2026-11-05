/* Declarative mini-apps and locally rendered text-video, never executable model code. */
'use strict';
window.JarvisArtifacts={
  lines(job){return job.result.split('\n').map(line=>line.replace(/^\s*(?:[-*#]|\d+[.)])\s*/, '').trim()).filter(Boolean).slice(0,8);},
  checklist(parent,job){const section=document.createElement('section');section.className='artifact';const heading=document.createElement('h4');heading.textContent='Anklickbare Mini-App · Checkliste';section.append(heading);const savedKey='jarvis-checklist-'+job.id;let saved=[];try{saved=JSON.parse(localStorage.getItem(savedKey)||'[]');if(!Array.isArray(saved))saved=[];}catch(_){}this.lines(job).forEach((text,index)=>{const label=document.createElement('label');const input=document.createElement('input');input.type='checkbox';input.checked=saved.includes(index);input.onchange=()=>{try{localStorage.setItem(savedKey,JSON.stringify([...section.querySelectorAll('input')].flatMap((box,i)=>box.checked?[i]:[])));}catch(_){}};label.append(input,document.createTextNode(' '+text));section.append(label);});parent.append(section);},
  video(parent,job){
    const make=(tag,text,parent)=>{const item=document.createElement(tag);if(text)item.textContent=text;parent?.append(item);return item;};
    const section=make('section',null,parent);section.className='artifact';
    make('h4',job.image_mime?'Produktfilm · dein Foto und KI-Skript':'Werbeclip · eigene JARVIS-Figur',section);
    make('p','Eigene lokal animierte Low-Poly-Figur. Thorsten spricht in Vorschau und Export; Untertitel folgen den gesprochenen Sätzen. Kein frei generiertes KI-Filmmodell.',section);
    const option=(text,checked)=>{const label=make('label',null,section),input=make('input',null,label);input.type='checkbox';input.checked=checked;label.append(document.createTextNode(' '+text));return input;};
    const voice=option('Thorsten-Sprecher',!/(?:ohne|kein(?:e[nr]?)?)\s+(?:stimme|sprecher|ton|sprache|sprachausgabe)/i.test(job.task||''));
    const subtitles=option('Untertitel',!/(?:ohne|kein(?:e[nr]?)?)\s+untertitel/i.test(job.task||''));
    const styleLabel=make('label','Filmstil ',section),style=make('select',null,styleLabel);
    for(const [value,text] of [['lowpoly','Low-Poly · eigene JARVIS-Figur'],['photo','Eigenes Produktfoto']]){const item=make('option',text,style);item.value=value;}style.value=job.image_mime?'photo':'lowpoly';
    const canvas=make('canvas',null,section);canvas.width=720;canvas.height=720;canvas.style.width='100%';canvas.style.maxWidth='420px';
    const status=make('p','Vorschau und Export verwenden dieselbe Thorsten-Tonspur.',section);status.setAttribute('role','status');
    const context=canvas.getContext('2d'),lines=this.lines(job).slice(0,3).map(line=>line.replace(/^szene\s*\d+\s*[:.-]\s*/i,'').slice(0,120));
    let animation=0,recording=false,photo=null,duration=9000,cues=[],cachedSpeech=null,previewing=false,previewSource=null,previewGeneration=0;
    const edit=make('details',null,section);make('summary','Sprechertext und Untertitel bearbeiten',edit);const editors=[];
    for(let i=0;i<3;i++){const label=make('label','Satz '+(i+1),edit),field=make('textarea',null,label);field.rows=2;field.maxLength=120;field.value=lines[i]||'';field.oninput=()=>{stopPreview();lines[i]=field.value;cachedSpeech=null;draw(0);};editors.push(field);}section.insertBefore(edit,canvas);
    function caption(time){if(cues.length){const active=cues.find(cue=>time>=cue.start&&time<cue.end);return active||{index:[...cues].reverse().find(cue=>time>=cue.start)?.index||0,speaking:false};}return {index:Math.min(2,Math.floor(time/(duration/3))),speaking:false};}
    function draw(time){
      canvas.dataset.frame=String(Math.round(time));const cue=caption(time),scene=cue.index,phase=Math.min(1,time/duration),lowpoly=style.value==='lowpoly';
      if(lowpoly)window.JarvisLowPoly.draw(context,time,720,720,{speaking:cue.speaking});
      else{const gradient=context.createLinearGradient(0,0,720,720);gradient.addColorStop(0,'#123a3c');gradient.addColorStop(1,'#080d0f');context.fillStyle=gradient;context.fillRect(0,0,720,720);}
      if(photo&&!lowpoly){const scale=Math.max(720/photo.width,720/photo.height)*(1+phase*.12),w=photo.width*scale,h=photo.height*scale;context.drawImage(photo,(720-w)/2+(phase-.5)*20,(720-h)/2,w,h);}
      context.fillStyle='#e8d087';context.font='18px sans-serif';context.fillText('JARVIS / STUDIO',55,70);
      const text=lines[scene]||'';canvas.dataset.caption=subtitles.checked?text:'';canvas.dataset.speaking=String(cue.speaking);
      if(subtitles.checked&&text){
        context.font='bold 28px sans-serif';const rows=[];let row='';for(const word of text.split(/\s+/)){if(row&&context.measureText(row+' '+word).width>570){rows.push(row);row='';}row+=(row?' ':'')+word;}if(row)rows.push(row);
        const visible=rows.slice(0,4),top=630-visible.length*38;context.fillStyle='#030912dd';context.fillRect(48,top-29,624,visible.length*38+18);context.fillStyle='#ffffff';visible.forEach((line,i)=>context.fillText(line,70,top+i*38));
      }
      context.fillStyle='#e8d087';context.fillRect(55,663,610*phase,4);
    }
    const photoReady=job.image_mime?window.JarvisBridge.api('/api/agents/'+job.id+'/image').then(blob=>createImageBitmap(blob)).then(image=>{photo=image;canvas.dataset.photo='true';draw(0);}):Promise.resolve();
    photoReady.catch(error=>status.textContent='Produktbild konnte nicht geladen werden: '+error.message);draw(0);
    async function speech(){
      if(!voice.checked){cues=[];duration=9000;return null;}
      const audio=await window.JarvisBridge.prepareAudio();if(!audio)throw Error('Audio wird von diesem Browser nicht unterstützt.');
      const spokenLines=[...lines],key=JSON.stringify(spokenLines);if(cachedSpeech?.key===key){cues=cachedSpeech.cues;duration=cachedSpeech.duration;return cachedSpeech;}
      status.textContent='Thorsten erzeugt die gesprochenen Sätze und passenden Untertitel …';
      const clips=[];let total=0;const timeline=[];
      for(let i=0;i<3;i++){
        const text=(spokenLines[i]||'').trim();if(!text)continue;
        const wav=await window.JarvisVoice.render(text,'jarvis',{background:true}),buffer=await audio.decodeAudioData(wav);
        timeline.push({index:i,start:total*1000,end:(total+buffer.duration)*1000,speaking:true});clips.push({buffer,offset:total});total+=buffer.duration+.12;
        if(total>30)throw Error('Sprechertext ist zu lang. Bitte die drei Sätze kürzen.');
      }
      if(!clips.length)throw Error('Bitte zuerst mindestens einen Sprechertext eintragen.');
      const sound=audio.createBuffer(1,Math.ceil(total*audio.sampleRate),audio.sampleRate);
      for(const clip of clips){const offset=Math.round(clip.offset*audio.sampleRate),target=sound.getChannelData(0);for(let c=0;c<clip.buffer.numberOfChannels;c++){const input=clip.buffer.getChannelData(c);for(let n=0;n<input.length&&n+offset<target.length;n++)target[n+offset]+=input[n]/clip.buffer.numberOfChannels;}}
      if(key!==JSON.stringify(lines))throw Error('Der Sprechertext wurde geändert. Bitte die Vorschau neu starten.');
      cachedSpeech={key,audio,sound,cues:timeline,duration:Math.ceil(total*1000)+250};cues=timeline;duration=cachedSpeech.duration;return cachedSpeech;
    }
    function run(done){cancelAnimationFrame(animation);const start=performance.now();const tick=now=>{if(!canvas.isConnected||document.hidden){stopPreview();return;}const elapsed=Math.min(duration,now-start);draw(elapsed);if(elapsed<duration)animation=requestAnimationFrame(tick);else done?.();};animation=requestAnimationFrame(tick);}
    const play=make('button','Vorschau abspielen',section);play.type='button';play.className='secondary-button';
    function stopPreview(){previewGeneration++;previewing=false;cancelAnimationFrame(animation);try{previewSource?.stop();}catch(_){}previewSource?.disconnect();previewSource=null;play.textContent='Vorschau abspielen';}
    section.closest('dialog')?.addEventListener('close',stopPreview);
    play.onclick=async()=>{
      if(previewing){stopPreview();status.textContent='Vorschau gestoppt.';return;}
      previewing=true;const generation=++previewGeneration;play.textContent='Vorschau stoppen';
      try{window.JarvisConversation?.stop();window.JarvisBridge.stopAudio();await photoReady;const narration=await speech();if(generation!==previewGeneration)return;
        if(narration){previewSource=narration.audio.createBufferSource();previewSource.buffer=narration.sound;previewSource.connect(narration.audio.destination);previewSource.start();}
        status.textContent=narration?'Vorschau mit Thorsten'+(subtitles.checked?' und Untertiteln.':'.'):'Vorschau ohne Ton.';run(()=>{stopPreview();status.textContent='Vorschau beendet.';});
      }catch(error){if(generation!==previewGeneration)return;stopPreview();status.textContent='Vorschau fehlgeschlagen: '+error.message;}
    };
    for(const input of [style,voice,subtitles])input.onchange=()=>{stopPreview();draw(0);};
    const exportButton=make('button','Video exportieren',section);exportButton.type='button';exportButton.className='secondary-button';
    exportButton.onclick=async()=>{
      if(recording)return;if(!canvas.captureStream||!window.MediaRecorder){status.textContent='Dieser Browser unterstützt keinen lokalen Videoexport.';return;}
      const mime=['video/webm;codecs=vp9,opus','video/webm','video/mp4'].find(type=>MediaRecorder.isTypeSupported(type));if(!mime){status.textContent='Kein unterstütztes Videoformat verfügbar.';return;}
      stopPreview();recording=true;const inputs=[style,voice,subtitles,exportButton,play,...editors];inputs.forEach(input=>input.disabled=true);
      let stream=null,source=null,destination=null,recorder=null,aborted=false,visibility=null;
      const cleanup=()=>{cancelAnimationFrame(animation);try{source?.stop();}catch(_){}source?.disconnect();destination?.disconnect();stream?.getTracks().forEach(track=>track.stop());if(visibility)document.removeEventListener('visibilitychange',visibility);recording=false;inputs.forEach(input=>input.disabled=false);};
      try{
        window.JarvisConversation?.stop();window.JarvisBridge.stopAudio();await photoReady;const narration=await speech();
        stream=canvas.captureStream(24);
        if(narration){destination=narration.audio.createMediaStreamDestination();source=narration.audio.createBufferSource();source.buffer=narration.sound;source.connect(destination);for(const track of destination.stream.getAudioTracks())stream.addTrack(track);}
        recorder=new MediaRecorder(stream,{mimeType:mime});const chunks=[];recorder.ondataavailable=event=>{if(event.data.size)chunks.push(event.data);};
        recorder.onerror=()=>{aborted=true;cleanup();status.textContent='Videoexport fehlgeschlagen.';};
        visibility=()=>{if(document.hidden&&recorder.state!=='inactive'){aborted=true;recorder.stop();}};document.addEventListener('visibilitychange',visibility);
        recorder.onstop=()=>{cleanup();if(aborted||!canvas.isConnected){status.textContent='Export unterbrochen. Bitte sichtbar geöffnet lassen und erneut starten.';return;}const blob=new Blob(chunks,{type:mime});if(blob.size<1024){status.textContent='Keine verwertbare Videodatei erzeugt.';return;}const url=URL.createObjectURL(blob),link=make('a','Fertiges Video herunterladen',section);link.href=url;link.download='Jarvis-Werbeclip.'+(mime.includes('mp4')?'mp4':'webm');status.textContent='Video fertig'+(narration?' · mit Thorsten-Sprecher':' · ohne Ton')+(subtitles.checked?' und eingebrannten Untertiteln.':'.');setTimeout(()=>URL.revokeObjectURL(url),120000);};
        recorder.start(250);draw(0);stream.getVideoTracks()[0]?.requestFrame?.();source?.start();run();status.textContent='Video wird lokal gerendert · etwa '+Math.ceil(duration/1000)+' Sekunden. Bitte sichtbar geöffnet lassen.';
        setTimeout(()=>{if(recorder.state!=='inactive')recorder.stop();},duration+250);
      }catch(error){cleanup();status.textContent='Export fehlgeschlagen: '+error.message;}
    };
  }
};
