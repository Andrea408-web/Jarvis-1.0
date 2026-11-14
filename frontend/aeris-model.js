/* Small, bounded project format shared by the normal canvas and WebXR. */
'use strict';
(()=>{
 const TYPES=['box','sphere','cylinder'],COLORS=['#80d6cb','#edce79','#9bb8ef','#e8a6b7'];
 function number(v,fallback,min,max){if(v===undefined)return fallback;if(typeof v!=='number'||!Number.isFinite(v)||v<min||v>max)throw Error('Ungültiger Wert im 3D-Projekt.');return v;}
 function object(raw,i=0){if(!raw||typeof raw!=='object'||Array.isArray(raw))throw Error('Ungültiges Bauteil.');const type=raw.type||'box';if(!TYPES.includes(type))throw Error('Unbekannte Form.');return {id:typeof raw.id==='string'&&/^[a-zA-Z0-9_-]{1,64}$/.test(raw.id)?raw.id:'part_'+i,type,x:number(raw.x,0,-20,20),y:number(raw.y,.4,-20,20),z:number(raw.z,0,-20,20),sx:number(raw.sx,.68,.005,12),sy:number(raw.sy,.68,.005,12),sz:number(raw.sz,.68,.005,12),rotation:number(raw.rotation,0,-360,360),color:/^#[0-9a-f]{6}$/i.test(raw.color||'')?raw.color:COLORS[0]};}
 function parse(raw){if(!raw||raw.version!==1||!Array.isArray(raw.objects)||raw.objects.length>64)throw Error('Bitte ein Aeris-Projekt mit höchstens 64 Bauteilen auswählen.');const objects=raw.objects.map(object);if(new Set(objects.map(o=>o.id)).size!==objects.length)throw Error('Doppelte Bauteil-IDs.');return {version:1,name:typeof raw.name==='string'?raw.name.slice(0,80):'Mein Projekt',objects};}
 function mesh(raw){const o=object(raw);let v=[],f=[];
 if(o.type==='box'){v=[[-.5,-.5,-.5],[.5,-.5,-.5],[.5,.5,-.5],[-.5,.5,-.5],[-.5,-.5,.5],[.5,-.5,.5],[.5,.5,.5],[-.5,.5,.5]];f=[[0,3,2,1],[4,5,6,7],[0,1,5,4],[3,7,6,2],[1,2,6,5],[0,4,7,3]];}
 else if(o.type==='sphere'){for(let i=0;i<=8;i++)for(let j=0;j<=12;j++){const a=i*Math.PI/8,b=j*Math.PI/6;v.push([Math.sin(a)*Math.cos(b)*.5,Math.cos(a)*.5,Math.sin(a)*Math.sin(b)*.5]);}for(let i=0;i<8;i++)for(let j=0;j<12;j++){const a=i*13+j;f.push([a,a+1,a+14,a+13]);}}
 else{for(const y of [-.5,.5])for(let i=0;i<16;i++)v.push([Math.cos(i*Math.PI/8)*.5,y,Math.sin(i*Math.PI/8)*.5]);f.push(Array.from({length:16},(_,i)=>i),Array.from({length:16},(_,i)=>31-i));for(let i=0;i<16;i++)f.push([i,i+16,(i+1)%16+16,(i+1)%16]);}
 const a=o.rotation*Math.PI/180,co=Math.cos(a),si=Math.sin(a);v=v.map(p=>{const x=p[0]*o.sx,z=p[2]*o.sz;return [o.x+x*co-z*si,o.y+p[1]*o.sy,o.z+x*si+z*co];});return {vertices:v,faces:f};}
 function obj(objects){let text='# AERIS project geometry\n',offset=1;objects.forEach((o,i)=>{const m=mesh(o);text+='o '+(o.type||'box')+'_'+i+'\n';for(const p of m.vertices)text+='v '+p.join(' ')+'\n';for(const face of m.faces)text+='f '+face.map(n=>n+offset).join(' ')+'\n';offset+=m.vertices.length;});return text;}
 window.AerisModel={TYPES,COLORS,object,parse,mesh,obj};
})();
