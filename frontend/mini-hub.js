/* Compact public-news hub. Remote content is data, never executable HTML. */
'use strict';
(() => {
  const bridge=window.JarvisBridge;
  const el=(tag,text,parent)=>{const node=document.createElement(tag);if(text)node.textContent=text;if(parent)parent.append(node);return node;};
  const button=(text,parent,run)=>{const node=el('button',text,parent);node.type='button';node.className='secondary-button';node.onclick=()=>Promise.resolve().then(run).catch(error=>status.textContent=error.message);return node;};
  const dialog=el('dialog',null,document.body);dialog.id='mini-hub';dialog.className='extras-dialog mini-hub';
  const heading=el('div',null,dialog);heading.className='dialog-heading';const brand=el('div',null,heading);el('small','J.A.R.V.I.S. / PERSONAL HUB',brand);el('h2','Dein Mini-Hub',brand);button('Schließen',heading,()=>dialog.close());
  const tabs=el('nav',null,dialog);tabs.className='hub-tabs';tabs.setAttribute('aria-label','Hub-Bereiche');
  const panels={},tabButtons={};let snapshot=null,timer=null,jobs=0,mapReady=null,country='ALL',brainFrame=0,geo=null;
  for(const [id,title] of [['overview','Überblick'],['news','Nachrichten'],['channels','Meine Kanäle'],['planner','Planer']]){panels[id]=el('section',null,dialog);panels[id].className='hub-panel';panels[id].dataset.panel=id;tabButtons[id]=button(title,tabs,()=>selectTab(id));}
  const status=el('p','',dialog);status.id='hub-status';status.setAttribute('role','status');
  function selectTab(id){for(const [name,panel] of Object.entries(panels)){panel.hidden=name!==id;tabButtons[name].setAttribute('aria-pressed',String(name===id));}if(id!=='channels')document.getElementById('hub-player')?.replaceChildren();if(id==='overview'&&dialog.open){cancelAnimationFrame(brainFrame);brainFrame=requestAnimationFrame(drawBrain);}if(id==='news')loadMap().catch(error=>status.textContent=error.message);}
  const overview=el('div',null,panels.overview);overview.className='hub-overview';
  const brainCard=el('article',null,overview);brainCard.className='hub-card';el('h3','JARVIS · Arbeitsanzeige',brainCard);
  const brain=el('canvas',null,brainCard);brain.id='hub-brain';brain.width=560;brain.height=300;brain.setAttribute('role','img');brain.setAttribute('aria-label','Dreidimensionale Gehirn-Arbeitsanzeige');
  const brainState=el('p','Bereit',brainCard);brainState.id='hub-brain-state';
  const system=el('div',null,brainCard);system.className='hub-system';const systemValues={};
  for(const [id,title] of [['device','Servergerät'],['cpu','CPU'],['ram','RAM'],['disk','Freier Speicher']]){const box=el('div',null,system);el('small',title,box);systemValues[id]=el('strong','—',box);}
  const overviewNews=el('article',null,overview);overviewNews.className='hub-card';el('h3','Was gerade passiert',overviewNews);const highlights=el('div',null,overviewNews);button('Alle Meldungen & Weltkarte',overviewNews,()=>selectTab('news'));
  const newsTools=el('div',null,panels.news);newsTools.className='extras-actions';
  const countryLabel=el('label','Meldungen erwähnen',newsTools);const countrySelect=el('select',null,countryLabel);countrySelect.id='hub-country';
  const newsUpdated=el('p','Noch keine Nachrichten geladen.',panels.news);newsUpdated.id='hub-news-updated';button('Nachrichten aktualisieren',newsTools,refreshNews);
  const newsLayout=el('div',null,panels.news);newsLayout.className='hub-news-layout';const map=el('canvas',null,newsLayout);map.id='hub-map';map.setAttribute('role','img');
  const globe=new window.JarvisGlobe(map,point=>{countrySelect.value=point.id;countrySelect.dispatchEvent(new Event('change'));});const articles=el('div',null,newsLayout);articles.id='hub-articles';
  countrySelect.onchange=async()=>{country=countrySelect.value;renderNews();const point=snapshot?.countries.find(item=>item.id===country);if(point)globe.focus(point);else globe.reset();try{await bridge.api('/api/settings',{method:'PUT',body:JSON.stringify({hub_country:country})});}catch(error){status.textContent=error.message;}};
  function safeLink(url){try{const parsed=new URL(url);return parsed.protocol==='https:'&&['www.tagesschau.de','tagesschau.de','www.youtube.com','www.tiktok.com'].includes(parsed.hostname);}catch(_){return false;}}
  function link(text,url,parent){if(!safeLink(url))return null;const node=el('a',text,parent);node.href=url;node.target='_blank';node.rel='noopener noreferrer';return node;}
  function stamp(value){if(!value)return 'Noch nicht abgerufen';const date=new Date(value);return Number.isNaN(date.getTime())?'Zeitpunkt unbekannt':date.toLocaleString('de-DE');}
  function image(url,parent,title){const fallback=el('div','NACHRICHTEN',parent);fallback.className='hub-thumb';if(!url)return;try{const parsed=new URL(url);if(parsed.protocol!=='https:'||!['images.tagesschau.de','www.tagesschau.de','tagesschau.de','i.ytimg.com'].includes(parsed.hostname))return;}catch(_){return;}const img=el('img',null,fallback);img.alt=title;img.loading='lazy';img.referrerPolicy='no-referrer';img.src=url;img.onerror=()=>img.remove();}
  function renderNews(){
    const feed=snapshot?.news||{items:[]};const all=feed.items||[];const filtered=country==='ALL'?all:all.filter(item=>item.countries?.includes(country));articles.replaceChildren();
    for(const item of filtered){const card=el('article',null,articles);card.className='hub-news-card';image(item.image,card,item.title);const body=el('div',null,card);const names=(item.countries||[]).map(code=>snapshot.countries.find(item=>item.id===code)?.name).filter(Boolean);el('small',names.length?names.join(' · '):'Welt / nicht eindeutig zugeordnet',body);const title=el('h3',null,body);link(item.title,item.url,title);el('p',item.summary||'',body);el('small','Quelle: tagesschau.de',body);}
    if(!filtered.length)el('p',country==='ALL'?'Noch keine verifizierten Meldungen geladen.':'Im aktuellen Feed wurde dieses Land nicht eindeutig erwähnt.',articles);
    newsUpdated.textContent=(feed.stale?'Älterer Stand · ':'Stand: ')+stamp(feed.updated_at)+' · tagesschau.de. Zuordnung anhand erwähnter Länder und Orte.';
    if(feed.error)status.textContent=feed.error;highlights.replaceChildren();
    for(const item of all.slice(0,3)){const card=el('div',null,highlights);card.className='hub-highlight';image(item.image,card,item.title);link(item.title,item.url,card);}
    if(!all.length)el('p','Aktuelle Nachrichten werden nur mit erreichbarer Quelle angezeigt.',highlights);
    if(geo&&snapshot)globe.load(geo,snapshot.countries.filter(point=>all.some(item=>item.countries?.includes(point.id))));
  }
  async function loadMap(){if(!mapReady)mapReady=fetch('/world.geojson').then(response=>{if(!response.ok)throw Error('Lokale Weltkarte konnte nicht geladen werden.');return response.json();}).then(data=>{geo=data;if(snapshot)globe.load(geo,snapshot.countries);}).catch(error=>{mapReady=null;throw error;});await mapReady;}
  async function refreshNews(){status.textContent='Öffentlichen Tagesschau-RSS-Feed laden …';try{const data=await bridge.api('/api/hub/news',{method:'POST',body:'{}'});snapshot.news=data;status.textContent=data.error||'Nachrichten aktualisiert. Vorschaubilder stammen von der Quelle.';renderNews();return data;}catch(error){status.textContent=error.message;return snapshot?.news||{items:[],error:error.message};}}
  el('h3','Deine Kanäle',panels.channels);el('p','Kanalnamen werden lokal gespeichert. Öffentliche Zahlen können verborgen oder gesperrt sein; dann wird keine Zahl erfunden. Kein Login bei Jarvis erforderlich.',panels.channels);
  const profile=el('form',null,panels.channels);const channelFields={};
  for(const [id,title] of [['youtube','YouTube · @Kanalname oder UC-Kanal-ID'],['tiktok','TikTok · @Kanalname']]){const label=el('label',title,profile);const input=el('input',null,label);input.maxLength=250;input.autocomplete='off';input.name=id+'_channel';channelFields[id]=input;}
  const save=el('button','Speichern & öffentlich laden',profile);save.type='submit';save.className='primary-button';button('Öffentliche Zahlen aktualisieren',panels.channels,refreshChannels);
  const channelCards=el('div',null,panels.channels);channelCards.id='hub-channels';const player=el('div',null,panels.channels);player.id='hub-player';
  profile.onsubmit=async event=>{event.preventDefault();save.disabled=true;try{const result=await bridge.api('/api/settings',{method:'PUT',body:JSON.stringify({youtube_channel:channelFields.youtube.value,tiktok_channel:channelFields.tiktok.value})});for(const id of ['youtube','tiktok'])channelFields[id].value=result.settings[id+'_channel'];await bridge.refreshStatus();await refreshChannels();}catch(error){status.textContent=error.message;}finally{save.disabled=false;}};
  function renderChannels(){
    channelCards.replaceChildren();
    for(const provider of ['youtube','tiktok']){
      const data=snapshot?.channels[provider]||{},card=el('article',null,channelCards);card.className='hub-card';el('h3',(provider==='youtube'?'YouTube':'TikTok')+' · '+(data.name||data.handle||'Noch nicht eingerichtet'),card);
      const known=provider==='youtube'?data.subscribers:data.followers;el('strong',known===undefined||known===null?'Zahl nicht verfügbar':typeof known==='number'?known.toLocaleString('de-DE')+' Follower':known,card);el('p','Stand: '+stamp(data.updated_at),card);if(data.error)el('p',data.error,card);
      const handle=data.handle;if(handle){const url=data.url||(provider==='youtube'?'https://www.youtube.com/'+(handle.startsWith('@')?encodeURIComponent(handle):'channel/'+encodeURIComponent(handle)):'https://www.tiktok.com/'+encodeURIComponent(handle));link('Profil beim Anbieter öffnen ↗',url,card);}
      for(const video of data.videos||[]){const row=el('div',null,card);row.className='hub-video-row';if(video.image)image(video.image,row,video.title);el('p',video.title,row);
        button('Im Hub ansehen',row,()=>{player.replaceChildren();const valid=provider==='youtube'?/^[A-Za-z0-9_-]{11}$/.test(video.id):/^[0-9]{10,24}$/.test(video.id);if(!valid)return;const frame=el('iframe',null,player);frame.title=video.title;frame.referrerPolicy='no-referrer';frame.allow='fullscreen; encrypted-media; picture-in-picture';frame.allowFullscreen=true;frame.src=provider==='youtube'?'https://www.youtube-nocookie.com/embed/'+video.id:'https://www.tiktok.com/player/v1/'+video.id;el('p','Wenn der Anbieter die Wiedergabe blockiert, verwende den offiziellen Link.',player);link('Video beim Anbieter öffnen ↗',video.url,player);player.scrollIntoView({block:'nearest'});});
        link('Offizieller Videolink ↗',video.url,row);
      }
    }
  }
  async function refreshChannels(){status.textContent='Öffentliche Kanalseiten werden gelesen. Keine Anmeldung oder Sperre wird umgangen.';try{snapshot.channels=await bridge.api('/api/hub/channels',{method:'POST',body:'{}'});renderChannels();status.textContent='Kanaldaten aktualisiert, soweit öffentlich erreichbar.';}catch(error){status.textContent=error.message;}}
  el('h3','Dein Planer',panels.planner);el('p','Lokal gespeicherte Termine. Kein garantierter Systemalarm bei geschlossenem Jarvis.',panels.planner);
  const planForm=el('form',null,panels.planner);const planTextLabel=el('label','Was steht an?',planForm);const planText=el('input',null,planTextLabel);planText.required=true;planText.maxLength=500;
  const planDateLabel=el('label','Datum und Uhrzeit',planForm);const planDate=el('input',null,planDateLabel);planDate.type='datetime-local';planDate.required=true;
  const planSubmit=el('button','Termin speichern',planForm);planSubmit.type='submit';planSubmit.className='primary-button';const plans=el('div',null,panels.planner);plans.id='hub-plans';
  async function refreshPlanner(){const data=await bridge.api('/api/reminders');plans.replaceChildren();for(const task of data.reminders||[]){const row=el('article',null,plans);row.className='hub-plan';el('strong',task.text,row);el('p',stamp(task.due_at)+(task.status==='done'?' · Erledigt':''),row);if(task.status==='pending')button('Erledigt',row,async()=>{await bridge.api('/api/reminders/'+task.id,{method:'PATCH',body:JSON.stringify({status:'done'})});await refreshPlanner();});}if(!plans.children.length)el('p','Noch keine Termine gespeichert.',plans);}
  planForm.onsubmit=async event=>{event.preventDefault();planSubmit.disabled=true;try{const date=new Date(planDate.value);if(Number.isNaN(date.getTime()))throw Error('Bitte Datum und Uhrzeit wählen.');await bridge.api('/api/reminders',{method:'POST',body:JSON.stringify({text:planText.value,due_at:date.toISOString()})});planText.value='';await refreshPlanner();status.textContent='Termin lokal gespeichert.';}catch(error){status.textContent=error.message;}finally{planSubmit.disabled=false;}};
  function renderSystem(){for(const [id,source] of [['cpu','cpu-value'],['ram','memory-detail'],['disk','disk-detail'],['device','device-name']])systemValues[id].textContent=document.getElementById(source)?.textContent||'—';}
  function drawBrain(time){
    if(!dialog.open||document.hidden||panels.overview.hidden)return;const ctx=brain.getContext('2d'),state=bridge.interaction(),working=state.busy||jobs>0||state.mode==='speaking';brain.dataset.working=String(working);
    brainState.textContent=state.busy?'JARVIS erstellt eine Antwort':jobs?jobs+' laufende Agentenaufträge':state.mode==='speaking'?'JARVIS spricht':state.recording?'JARVIS hört zu':'Bereit';
    ctx.clearRect(0,0,560,300);const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches,motion=reduced?0:time*.00025,points=[];
    function project(side,u,v){const fold=1+.055*Math.sin(u*9+v*5),x=side*42+Math.cos(u)*Math.cos(v)*62*fold,y=Math.sin(u)*94*fold,z=Math.cos(u)*Math.sin(v)*56,a=-.38+Math.sin(motion)*.04;return [280+(x*Math.cos(a)+z*Math.sin(a))*1.65,143+y*1.15-z*.22,z];}
    for(const side of [-1,1]){
      for(let ring=0;ring<12;ring++){ctx.beginPath();for(let i=0;i<=70;i++){const u=-Math.PI/2+Math.PI*i/70,v=ring*Math.PI/6,[x,y,z]=project(side,u,v);if(i)ctx.lineTo(x,y);else ctx.moveTo(x,y);if(i%9===0&&z>0)points.push([x,y]);}ctx.strokeStyle='rgba(204,216,145,'+(.18+ring*.025)+')';ctx.lineWidth=1;ctx.stroke();}
      for(let j=1;j<10;j++){ctx.beginPath();for(let i=0;i<=70;i++){const [x,y]=project(side,-Math.PI/2+j*Math.PI/10,i*Math.PI/35);if(i)ctx.lineTo(x,y);else ctx.moveTo(x,y);}ctx.strokeStyle='#d4d78c44';ctx.stroke();}
    }
    ctx.strokeStyle='#d4d78c88';ctx.beginPath();ctx.moveTo(274,224);ctx.bezierCurveTo(267,248,287,259,280,281);ctx.stroke();
    if(working){for(let i=0;i<points.length;i+=3){const [x,y]=points[i],glow=reduced?0.8:(Math.sin(time*.006+i*1.9)+1)/2;if(glow<.6)continue;ctx.shadowBlur=14;ctx.shadowColor='#ffffff';ctx.fillStyle='rgba(255,255,255,'+glow+')';ctx.beginPath();ctx.arc(x,y,1.5+glow,0,Math.PI*2);ctx.fill();}ctx.shadowBlur=0;}
    if(!reduced)brainFrame=requestAnimationFrame(drawBrain);
  }
  async function poll(){renderSystem();try{const data=await bridge.api('/api/agents');jobs=data.jobs.filter(item=>item.status==='running').length;}catch(_){}}
  async function open(tab='overview',update=true){
    if(!dialog.open)dialog.showModal();status.textContent='Verbinde den Hub …';if(bridge.ready)await bridge.ready;selectTab(tab);snapshot=await bridge.api('/api/hub');country=snapshot.country;countrySelect.replaceChildren();const all=el('option','Alle Länder',countrySelect);all.value='ALL';
    for(const point of snapshot.countries){const option=el('option',point.name,countrySelect);option.value=point.id;}countrySelect.value=country;
    for(const id of ['youtube','tiktok'])channelFields[id].value=snapshot.channels[id]?.handle||'';
    renderNews();renderChannels();renderSystem();await refreshPlanner();await poll();clearInterval(timer);timer=setInterval(()=>{if(!document.hidden)poll();},3000);cancelAnimationFrame(brainFrame);brainFrame=requestAnimationFrame(drawBrain);
    if(update&&(!snapshot.news.items?.length||Date.now()-new Date(snapshot.news.updated_at).getTime()>900000))await refreshNews();
  }
  dialog.addEventListener('close',()=>{if(!dialog.open){clearInterval(timer);cancelAnimationFrame(brainFrame);player.replaceChildren();}});
  window.addEventListener('pagehide',()=>{clearInterval(timer);cancelAnimationFrame(brainFrame);});document.addEventListener('visibilitychange',()=>{if(dialog.open&&!document.hidden){cancelAnimationFrame(brainFrame);brainFrame=requestAnimationFrame(drawBrain);}});
  window.JarvisMiniHub={open,async command(text){
    const lower=text.toLowerCase();
    if(/\b(?:mini.?hub|hub)\b/.test(lower)&&/öffne|zeig|start|hub$/.test(lower)){await open();return {reply:'Sir, dein Mini-Hub ist geöffnet. Hier sind Nachrichten, Kanäle, Planer und Systemstatus.',proposals:[]};}
    if(/^(?:nachrichten|neuigkeiten)[.!?]?$|(?:zeig|lies|aktuell|neuest).*(?:nachrichten|neuigkeiten)|was.*(?:welt.*passiert|gibt es neues|heute passiert)/.test(lower)){await open('news',false);const feed=await refreshNews();if(feed.error)return {reply:'Sir, die Nachrichtenquelle ist gerade nicht erreichbar. Vorhandene Meldungen behalten ihren ursprünglichen Zeitstempel.',proposals:[]};return {reply:'Sir, aktuelle Schlagzeilen von tagesschau.de: '+feed.items.slice(0,3).map(item=>item.title).join(' · '),proposals:[]};}
    if(/(?:öffne|zeig).*(?:planer|termine)/.test(lower)){await open('planner');return {reply:'Sir, dein lokal gespeicherter Planer ist geöffnet.',proposals:[]};}
    if(/(?:öffne|zeig).*(?:meine kanäle|youtube.?kanal|tiktok.?kanal)/.test(lower)){await open('channels');return {reply:'Sir, deine Kanäle sind geöffnet. Nicht öffentlich abrufbare Zahlen bleiben als nicht verfügbar markiert.',proposals:[]};}
    return null;
  }};
  window.addEventListener('DOMContentLoaded',()=>{const nav=document.querySelector('.extras-nav');if(nav)button('Mini-Hub',nav,()=>open());});selectTab('overview');
})();
