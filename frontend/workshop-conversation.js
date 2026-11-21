/* Build-idea discussion uses the existing local text AI, with a separate open offer. */
let pending=null,epoch=0,active=null;
const clean=text=>text.trim().replace(/^(?:jarvis|astra)[, :]+/i,'').replace(/[.!?]+$/,'');
export function reset(){epoch++;pending=null;active?.abort();active=null;}
function introduction(text){return /^(?:ich (?:will|möchte|plane)|ich habe vor)\b/i.test(text);}
function inquiry(text){if(/web(?:site|seite)|homepage|software|roblox|minecraft|programmier|\bcode\b|\bapp\b/i.test(text)&&!/roboter|robotik|holz|metall|mechanik/i.test(text))return false;if(/^(?:baue?|entwirf|erstell|öffne|starte|zeige)\b/i.test(text))return false;return /roboter[ -]?arm|robotik|\bbauen\b|bau(?:idee|projekt)|werkstatt|erfindung|3d[ -]?(?:modell|projekt)/i.test(text)&&(introduction(text)||/(?:^|\s)(?:was|wofür|welche?|wie|ideen|möglichkeiten)|könnte|koennte/i.test(text));}
async function answer(text,history,signal,address){
 const messages=[{role:'system',content:'Du bist Jarvis. Sprich Deutsch und den Nutzer mit '+address+' an. Besprich den aktuellen Bauwunsch natürlich. Nenne konkrete, zum Objekt passende mögliche Funktionen und warum sie nützlich wären. Unterscheide Ideen von bereits vorhandenen Fähigkeiten. Frage nach dem vorgesehenen Einsatz, wenn nötig. Keine erledigten Bauaufträge oder berechnete Mechanik behaupten.'},...history,{role:'user',content:text}];
 if(window.DeviceAI&&((await window.DeviceAI.record())?.completed)){if(signal.aborted)throw new DOMException('Gestoppt','AbortError');const abort=()=>window.DeviceAI.stop();signal.addEventListener('abort',abort,{once:true});try{return await window.DeviceAI.chat(messages,()=>{},()=>{});}finally{signal.removeEventListener('abort',abort);}}
 const session=await fetch('/api/session',{signal});if(!session.ok)throw Error('Bitte den Mac verbinden oder die bereits vorhandene Geräte-KI verwenden.');
 const token=(await session.json()).token,response=await fetch('/api/device-ai/chat',{method:'POST',headers:{'Content-Type':'application/json','X-Jarvis-Token':token},body:JSON.stringify({text:(messages[0].content+'\nBauwunsch / Frage: '+text).slice(0,2000),history,mode:'jarvis'}),signal});
 const data=await response.json();if(!response.ok)throw Error(data.error||'Die lokale KI konnte den Bauwunsch gerade nicht besprechen.');return data.reply;
}
export async function command(raw,{address='Sir'}={}){
 if(typeof raw!=='string')return null;const text=clean(raw);if(pending&&Date.now()-pending.time>600000)pending=null;
 if(/^(?:chat löschen|vergiss alles|neues gespräch|chat zurücksetzen)\b/i.test(text)){reset();return null;}
 if(pending&&/^(?:ja(?:[, ]+(?:bitte|gerne|mach auf))?|gerne|mach auf|öffne (?:es|das)|(?:das )?baustudio öffnen)$/i.test(text)){const draft=pending;reset();await window.JarvisWorkshopPrepare('Entwickle einen 3D-Konzeptentwurf zu diesem Bauwunsch: '+draft.brief+'\nBesprochene Möglichkeiten: '+draft.answer.slice(0,500));return {reply:address+', das Baustudio ist offen und unser Bauwunsch übernommen. Du kannst den Entwurf dort starten und weiter mit mir sprechen.',proposals:[]};}
 if(pending&&/^(?:nein(?:[, ]+danke)?|später|noch nicht|abbrechen)$/i.test(text)){reset();return {reply:address+', wir bleiben im Gespräch. Das Baustudio bleibt geschlossen.',proposals:[]};}
 const follow=!!pending&&!introduction(text)&&/(?:funktion|könnte|koennte|greif|bewegen|arm|idee|stattdessen|lieber|was noch|weitere|andere|ändern|besser|^was kann (?:er|es|das|der)\b|^und sonst)/i.test(text);
 if(!inquiry(text)&&!follow){if(pending)reset();return null;}
 if(active)return {reply:address+', ich denke gerade über deinen Bauwunsch nach.',proposals:[]};
 const version=epoch,c=new AbortController();active=c;const timer=setTimeout(()=>c.abort(),60000),brief=follow?pending.brief:text,history=follow?[{role:'user',content:pending.brief.slice(0,600)},{role:'assistant',content:pending.answer.slice(0,600)}]:[];
 try{const reply=await answer(text.slice(0,1000),history,c.signal,address);if(version!==epoch)return {cancelled:true};if(typeof reply!=='string'||!reply.trim())throw Error('Die lokale KI hat keine verständliche Bauidee geliefert.');pending={brief:brief.slice(0,1000),answer:reply.slice(0,1000),time:Date.now()};return {reply:reply.trim()+'\n\nSoll ich dazu das Baustudio öffnen, '+address+'?',proposals:[]};}
 catch(e){if(version!==epoch)return {cancelled:true};return {reply:address+', das Besprechen der Bauidee klappt gerade nicht: '+(e.name==='AbortError'?'Die lokale KI braucht zu lange.':e.message),proposals:[]};}
 finally{clearTimeout(timer);if(active===c)active=null;}
}
