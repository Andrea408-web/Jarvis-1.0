 'use strict';
(()=>{
 const message=document.getElementById('pair-message'),form=document.getElementById('pair-form'),input=document.getElementById('pair-link');
 async function pair(value){
  let ticket=value.trim();
  try{if(ticket.includes('#'))ticket=new URLSearchParams(new URL(ticket).hash.slice(1)).get('pair')||'';}catch(_){throw Error('Bitte den vollständigen Kopplungslink vom Mac einfügen.');}
  if(!ticket)throw Error('Bitte einen neuen Kopplungslink vom Mac einfügen.');
  const response=await fetch('/api/mobile/pair',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ticket})});
  const data=await response.json();if(!response.ok)throw Error(data.error||'Kopplung fehlgeschlagen.');
  message.textContent='Verbunden. JARVIS wird geöffnet …';location.replace('/');
 }
 form.addEventListener('submit',async event=>{event.preventDefault();const button=form.querySelector('button');button.disabled=true;try{await pair(input.value);}catch(error){message.textContent=error.message;}finally{button.disabled=false;}});
 const ticket=new URLSearchParams(location.hash.slice(1)).get('pair');history.replaceState(null,'',location.pathname);
 if(ticket)pair(ticket).catch(error=>message.textContent=error.message);
})();
