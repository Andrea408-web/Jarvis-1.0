/* Declarative mini-apps and locally rendered text-video, never executable model code. */
'use strict';
window.JarvisArtifacts={
  lines(job){return job.result.split('\n').map(line=>line.replace(/^\s*(?:[-*#]|\d+[.)])\s*/, '').trim()).filter(Boolean).slice(0,8);},
  checklist(parent,job){const section=document.createElement('section');section.className='artifact';const heading=document.createElement('h4');heading.textContent='Anklickbare Mini-App · Checkliste';section.append(heading);const savedKey='jarvis-checklist-'+job.id;let saved=[];try{saved=JSON.parse(localStorage.getItem(savedKey)||'[]');if(!Array.isArray(saved))saved=[];}catch(_){}this.lines(job).forEach((text,index)=>{const label=document.createElement('label');const input=document.createElement('input');input.type='checkbox';input.checked=saved.includes(index);input.onchange=()=>{try{localStorage.setItem(savedKey,JSON.stringify([...section.querySelectorAll('input')].flatMap((box,i)=>box.checked?[i]:[])));}catch(_){}};label.append(input,document.createTextNode(' '+text));section.append(label);});parent.append(section);},
  video(parent,job){
    const section=document.createElement('section');section.className='artifact';
    const title=document.createElement('h4');title.textContent=job.image_mime?'Produktfilm · dein Foto und KI-Skript':'Werbeclip · KI-Skript';section.append(title);
    const note=document.createElement('p');note.textContent='Lokal gerenderter Clip mit animierter Kamera, deinem optionalen Produktfoto und mitgelieferter JARVIS-Stimme. Die Low-Poly-Bühne wird aus festen 3D-Grundkörpern animiert; das ist kein frei generiertes KI-Filmmodell.';section.append(note);
    const voiceLabel=document.createElement('label'),voice=document.createElement('input');voice.type='checkbox';voice.checked=true;voiceLabel.append(voice,document.createTextNode(' JARVIS-Sprecher beim Export hinzufügen'));section.append(voiceLabel);
    const styleLabel=document.createElement('label');styleLabel.textContent='Filmstil ';const style=document.createElement('select');for(const [value,text] of [['lowpoly','Low-Poly · animierte 3D-Bühne'],['photo','Produktfoto / klassische Szene']]){const option=document.createElement('option');option.value=value;option.textContent=text;style.append(option);}style.value=job.image_mime?'photo':'lowpoly';styleLabel.append(style);section.append(styleLabel);
    const canvas=document.createElement('canvas');canvas.width=720;canvas.height=720;canvas.style.width='100%';canvas.style.maxWidth='420px';section.append(canvas);
    const status=document.createElement('p');status.setAttribute('role','status');section.append(status);
    const context=canvas.getContext('2d'),lines=this.lines(job).slice(0,3).map(line=>line.replace(/^szene\s*\d+\s*[:.-]\s*/i,'').slice(0,120));let animation=0,recording=false,photo=null,duration=9000;
    const edit=document.createElement('details');const editTitle=document.createElement('summary');editTitle.textContent='Szenentexte bearbeiten';edit.append(editTitle);const editors=[];
    for(let i=0;i<3;i++){const label=document.createElement('label');label.textContent='Szene '+(i+1);const field=document.createElement('textarea');field.rows=2;field.maxLength=120;field.value=lines[i]||'';field.oninput=()=>{lines[i]=field.value;draw(0);};editors.push(field);label.append(field);edit.append(label);}section.insertBefore(edit,canvas);
    function draw(time){canvas.dataset.frame=String(Math.round(time));
      const scene=Math.min(2,Math.floor(time/(duration/3))),phase=(time%(duration/3))/(duration/3);
      const gradient=context.createLinearGradient(0,0,720,720);gradient.addColorStop(0,['#123a3c','#302247','#3c3518'][scene]);gradient.addColorStop(1,'#080d0f');context.fillStyle=gradient;context.fillRect(0,0,720,720);
      const lowpoly=style.value==='lowpoly';if(lowpoly)window.JarvisLowPoly.draw(context,time,720,720);
      if(photo&&!lowpoly){const scale=Math.max(720/photo.width,720/photo.height)*(1+phase*.12),w=photo.width*scale,h=photo.height*scale;context.drawImage(photo,(720-w)/2+(phase-.5)*20,(720-h)/2,w,h);const shade=context.createLinearGradient(0,80,0,720);shade.addColorStop(0,'#00000018');shade.addColorStop(1,'#000000ee');context.fillStyle=shade;context.fillRect(0,0,720,720);}
      context.strokeStyle=lowpoly?'#ffffff44':'#ead783';context.lineWidth=2;context.strokeRect(35+phase*8,35+phase*8,650-phase*16,650-phase*16);
      context.fillStyle='#ead783';context.font='18px sans-serif';context.fillText('JARVIS / STUDIO',65,100);context.fillStyle='#fff6d8';context.font=lowpoly?'bold 27px sans-serif':'bold 36px sans-serif';
      const words=(lines[scene]||lines[0]||job.task).split(/\s+/);let row='',y=lowpoly?570:photo?450:270;
      for(const word of words){if(context.measureText(row+word).width>565){if(y<620)context.fillText(row,70,y);row='';y+=46;}row+=word+' ';}if(y<620)context.fillText(row,70,y);
      context.fillStyle='#ead783';context.fillRect(65,645,590*Math.min(1,time/duration),4);
    }
    const photoReady=job.image_mime?window.JarvisBridge.api('/api/agents/'+job.id+'/image').then(blob=>createImageBitmap(blob)).then(image=>{photo=image;canvas.dataset.photo='true';draw(0);}):Promise.resolve();
    style.onchange=()=>draw(0);photoReady.catch(error=>{status.textContent='Produktbild konnte nicht geladen werden: '+error.message;});draw(0);
    function run(){cancelAnimationFrame(animation);const start=performance.now();const tick=now=>{if(!canvas.isConnected||document.hidden){cancelAnimationFrame(animation);return;}const elapsed=Math.min(duration,now-start);draw(elapsed);if(elapsed<duration)animation=requestAnimationFrame(tick);};animation=requestAnimationFrame(tick);}
    const play=document.createElement('button');play.type='button';play.className='secondary-button';play.textContent='Vorschau abspielen';play.onclick=async()=>{try{await photoReady;run();}catch(error){status.textContent=error.message;}};section.append(play);
    const exportButton=document.createElement('button');exportButton.type='button';exportButton.className='secondary-button';exportButton.textContent='Video exportieren';
    exportButton.onclick=async()=>{
      if(recording)return;if(!canvas.captureStream||!window.MediaRecorder){status.textContent='Dieser Browser unterstützt keinen lokalen Videoexport.';return;}
      const mime=['video/webm;codecs=vp9,opus','video/webm','video/mp4'].find(type=>MediaRecorder.isTypeSupported(type));if(!mime){status.textContent='Kein unterstütztes Videoformat verfügbar.';return;}
      recording=true;style.disabled=true;exportButton.disabled=true;play.disabled=true;for(const field of editors)field.disabled=true;let stream=null,source=null,destination=null,recorder=null,aborted=false;
      const cleanup=()=>{cancelAnimationFrame(animation);try{source?.stop();}catch(_){}source?.disconnect();destination?.disconnect();stream?.getTracks().forEach(track=>track.stop());recording=false;style.disabled=false;exportButton.disabled=false;play.disabled=false;for(const field of editors)field.disabled=false;};
      try{
        await photoReady;let soundContext=null,sound=null;
        if(voice.checked){window.JarvisConversation?.stop();status.textContent='Die mitgelieferte Stimme erzeugt den Sprechertext …';soundContext=await window.JarvisBridge.prepareAudio();if(!soundContext)throw Error('Audioausgabe nicht unterstützt. Stimme für den Export abschalten.');const wav=await window.JarvisVoice.render(lines.join('. '),'jarvis',{background:true});sound=await soundContext.decodeAudioData(wav);if(sound.duration>30)throw Error('Sprechertext ist zu lang. Bitte den Auftrag mit kürzerem Text wiederholen oder ohne Sprecher exportieren.');}
        duration=sound?Math.max(9000,Math.ceil(sound.duration*1000)+500):9000;
        stream=canvas.captureStream(24);
        if(sound){destination=soundContext.createMediaStreamDestination();source=soundContext.createBufferSource();source.buffer=sound;source.connect(destination);for(const track of destination.stream.getAudioTracks())stream.addTrack(track);}
        recorder=new MediaRecorder(stream,{mimeType:mime});const chunks=[];
        recorder.ondataavailable=event=>{if(event.data.size)chunks.push(event.data);};
        recorder.onerror=()=>{aborted=true;cleanup();status.textContent='Videoexport fehlgeschlagen.';};
        const visibility=()=>{if(document.hidden&&recorder.state!=='inactive'){aborted=true;recorder.stop();}};document.addEventListener('visibilitychange',visibility);
        recorder.onstop=()=>{document.removeEventListener('visibilitychange',visibility);cleanup();if(aborted||!canvas.isConnected){status.textContent='Export unterbrochen. Bitte sichtbar geöffnet lassen und erneut starten.';return;}if(!chunks.length){status.textContent='Kein Video erzeugt.';return;}const blob=new Blob(chunks,{type:mime});if(blob.size<1024){status.textContent='Der Browser hat keine verwertbaren Videobilder aufgezeichnet. Bitte erneut exportieren.';return;}const url=URL.createObjectURL(blob);const link=document.createElement('a');link.href=url;link.download='Jarvis-Werbeclip.'+(mime.includes('mp4')?'mp4':'webm');link.textContent='Fertiges Video herunterladen';section.append(link);status.textContent='Video fertig'+(sound?' · mit JARVIS-Sprecher.':' · ohne Ton.');setTimeout(()=>URL.revokeObjectURL(url),120000);};
        recorder.start(250);draw(0);stream.getVideoTracks()[0]?.requestFrame?.();source?.start();run();status.textContent='Video wird lokal gerendert · etwa '+Math.ceil(duration/1000)+' Sekunden. Bitte sichtbar geöffnet lassen.';
        setTimeout(()=>{if(recorder.state!=='inactive')recorder.stop();},duration+250);
      }catch(error){cleanup();status.textContent=error.message;}
    };
    section.append(exportButton);parent.append(section);
  }
};
