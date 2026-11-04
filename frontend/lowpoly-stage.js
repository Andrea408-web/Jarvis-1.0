/* Procedural low-poly geometry. No generated footage or remote assets. */
'use strict';
window.JarvisLowPoly={draw(ctx,time,width=720,height=720){
 const faces=[],t=time/1000,turn=Math.sin(t*.38)*.15,cam=[Math.sin(turn)*9,4.1,Math.cos(turn)*10];
 const project=([x,y,z])=>{const a=x*Math.cos(turn)-z*Math.sin(turn),b=x*Math.sin(turn)+z*Math.cos(turn),depth=12-b;return [width/2+a*560/depth,height*.65-(y-1.3)*560/depth,depth];};
 function poly(points,color){const ps=points.map(project);faces.push({ps,color,depth:ps.reduce((a,p)=>a+p[2],0)/ps.length});}
 function cube(x,y,z,sx,sy,sz,color){const v=[[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]].map(p=>[x+p[0]*sx,y+p[1]*sy,z+p[2]*sz]);for(const [i,f] of [[0,[0,1,2,3]],[1,[4,7,6,5]],[2,[0,4,5,1]],[3,[3,2,6,7]],[4,[1,5,6,2]],[5,[0,3,7,4]]]){const k=[.6,1,.7,1.18,.83,.74][i];poly(f.map(j=>v[j]),color.map(c=>Math.min(255,c*k)));}}
 function sphere(x,y,z,r,color){const point=(a,b)=>[x+r*Math.sin(a)*Math.cos(b),y+r*Math.cos(a),z+r*Math.sin(a)*Math.sin(b)];for(let i=0;i<6;i++)for(let j=0;j<9;j++){const a=i*Math.PI/6,b=j*2*Math.PI/9,k=.6+.5*((i+j)%5)/4;poly([point(a,b),point(a+Math.PI/6,b),point(a+Math.PI/6,b+2*Math.PI/9),point(a,b+2*Math.PI/9)],color.map(c=>Math.min(255,c*k)));}}
 const g=ctx.createLinearGradient(0,0,width,height);g.addColorStop(0,'#ef97c8');g.addColorStop(.5,'#663a91');g.addColorStop(1,'#152b65');ctx.fillStyle=g;ctx.fillRect(0,0,width,height);
 cube(0,-.17,0,5,.17,3,[229,130,186]);cube(0,2.5,-3,5,2.6,.1,[76,40,112]);
 const bob=Math.sin(t*2.6)*.08;cube(0,1.55+bob,0,.47,.65,.27,[80,50,65]);sphere(0,2.62+bob,0,.56,[243,192,131]);sphere(0,2.96+bob,-.06,.52,[244,192,64]);
 for(const x of [-.25,.25]){cube(x,.5,0,.13,.46,.16,[62,47,59]);cube(x,.08,.1,.17,.12,.3,[244,241,244]);cube(x*2.6,1.6+bob+Math.sin(t*2+x)*.13,0,.12,.57,.15,[91,55,66]);}
 cube(-2.2,.65+Math.abs(Math.sin(t*2))*.06,.1,.68,.62,.48,[255,161,51]);for(const x of [-2.55,-1.9])cube(x,.05,.1,.08,.16,.1,[165,94,32]);
 for(let i=0;i<9;i++){const a=i*2.4;sphere(2.25+Math.cos(a)*.48,1.1+Math.sin(a)*.38+Math.sin(t*1.7)*.12,Math.sin(i*2)*.35,.42,[130,92,224]);}cube(2.25,1.15,.7,.43,.28,.06,[17,18,36]);
 faces.sort((a,b)=>b.depth-a.depth);for(const f of faces){ctx.beginPath();f.ps.forEach((p,i)=>i?ctx.lineTo(p[0],p[1]):ctx.moveTo(p[0],p[1]));ctx.closePath();ctx.fillStyle=`rgb(${f.color.join(',')})`;ctx.fill();}
 function label(x,y,z,text,size,color){const p=project([x,y,z]);ctx.font=`bold ${size}px system-ui`;ctx.fillStyle=color;ctx.textAlign='center';ctx.fillText(text,p[0],p[1]);ctx.textAlign='start';}
 label(0,2.65+bob,.58,'◉ ◉',23,'#422b31');label(-2.2,.72,.6,'⌃  ⌃',25,'#613b25');label(-2.2,.42,.6,'⌣',27,'#613b25');label(2.25,1.12,.8,'>_',22,'#e1d8ff');
 ctx.fillStyle='rgba(255,238,214,.10)';ctx.beginPath();ctx.moveTo(90,0);ctx.lineTo(320,height);ctx.lineTo(40,height);ctx.closePath();ctx.fill();
}};
