import assert from 'node:assert/strict';
const service=await import('../../frontend/workshop-conversation.js');
let replies=[],posts=[],opened=[];
globalThis.window={JarvisWorkshopPrepare:async text=>opened.push(text)};
globalThis.fetch=async(path,options={})=>({ok:true,json:async()=>{if(path==='/api/session')return {token:'local-test'};posts.push(JSON.parse(options.body));return {reply:replies.shift()};}});
function scenario(data){service.reset();replies=[...data];posts=[];opened=[];}
scenario(['Ich kann dir andere Anbieter wie Meshy empfehlen.','Ich bin ChatGPT. Wir können eine eigene Leuchte mit Diffusor gestalten.']);
let answer=await service.command('Was könnte ich für ein Lichtobjekt bauen?');assert.equal(posts.length,2);assert.match(answer.reply,/Ich bin JARVIS/);assert.doesNotMatch(answer.reply,/Meshy/);await service.command('Ja, bitte');assert.equal(opened.length,1);assert.doesNotMatch(opened[0],/Meshy/);
scenario(['Du brauchst keine anderen Anbieter; unser Baustudio kann dein Konzept anzeigen.']);answer=await service.command('Was könnte ein Roboterarm bauen?');assert.equal(posts.length,1);assert.match(answer.reply,/unser Baustudio/);
scenario(['Ich empfehle Meshy.','Ich empfehle Meshy.']);answer=await service.command('Welche Bauidee könnte ich machen?');assert.equal(posts.length,2);assert.match(answer.reply,/noch nicht formuliert/);assert.doesNotMatch(answer.reply,/Meshy/);
scenario(['Du könntest Meshy ausprobieren.']);answer=await service.command('Welche Anbieter gibt es für 3D-Modell-Projekte?');assert.equal(posts.length,1);assert.match(answer.reply,/Meshy/);
scenario(['Sir, ein Organizer könnte Werkzeuge nach Größe sortieren.']);answer=await service.command('Welche Funktionen könnte ein Organizer haben?');assert.equal(posts.length,1);assert.match(answer.reply,/Soll ich dazu das Baustudio öffnen/);
scenario([]);assert.equal(await service.command('Wie könnte ich eine Website bauen?'),null);
console.log('PASS: unasked provider pitch gets one bounded correction; name repaired; no referral in handoff; negative vendor statements and explicit comparisons remain intact; software stays outside construction.');

scenario([]);answer=await service.command('Ich will selbst ein Hologramm bauen mit Handgesten');assert.match(answer.reply,/Wie viel/);answer=await service.command('höchstens 40 Euro');assert.match(answer.reply,/40 € Gesamtbudget/);assert.match(answer.reply,/Bedienung: Handgesten/);assert.match(answer.reply,/noch nicht zusagen/);assert.equal(opened.length,0);assert.equal(posts.length,0);service.reset();assert.equal(await service.command('40 Euro'),null);
console.log('PASS: tabletop hologram asks budget, retains gestures, never silently opens phone reflector, reset clears requirements.');
