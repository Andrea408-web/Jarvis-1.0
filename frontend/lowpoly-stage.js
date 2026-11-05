/* Original JARVIS robot geometry, drawn locally without reference-image assets. */
'use strict';
window.JarvisLowPoly={draw(ctx,time,width=720,height=720,options={}){
 const faces=[],t=time/1000,turn=Math.sin(t*.38)*.15;
 const project=([x,y,z])=>{const a=x*Math.cos(turn)-z*Math.sin(turn),b=x*Math.sin(turn)+z*Math.cos(turn),depth=12-b;return [width/2+a*1050/depth,height*.58-(y-1.3)*1050/depth,depth];};
 function poly(points,color){const ps=points.map(project);faces.push({ps,color,depth:ps.reduce((a,p)=>a+p[2],0)/ps.length});}
 function cube(x,y,z,sx,sy,sz,color){const v=[[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]].map(p=>[x+p[0]*sx,y+p[1]*sy,z+p[2]*sz]);for(const [i,f] of [[0,[0,1,2,3]],[1,[4,7,6,5]],[2,[0,4,5,1]],[3,[3,2,6,7]],[4,[1,5,6,2]],[5,[0,3,7,4]]]){const k=[.6,1,.7,1.18,.83,.74][i];poly(f.map(j=>v[j]),color.map(c=>Math.min(255,c*k)));}}
 function prism(x,y,z,r,h,color,n=6){const ring=dy=>Array.from({length:n},(_,i)=>[x+Math.cos(i*2*Math.PI/n)*r,y+dy,z+Math.sin(i*2*Math.PI/n)*r]);const a=ring(-h),b=ring(h);poly(b,color.map(c=>Math.min(255,c*1.2)));for(let i=0;i<n;i++)poly([a[i],a[(i+1)%n],b[(i+1)%n],b[i]],color.map(c=>c*(.65+i/n*.45)));}
 const g=ctx.createLinearGradient(0,0,width,height);g.addColorStop(0,'#142d46');g.addColorStop(.55,'#07121f');g.addColorStop(1,'#04090f');ctx.fillStyle=g;ctx.fillRect(0,0,width,height);
 // An observatory floor, one original mechanical host, and orbiting light beacons.
 for(let i=-5;i<=5;i++){ctx.strokeStyle='#366b8130';ctx.beginPath();let a=project([i,-.3,-4]),b=project([i,-.3,4]);ctx.moveTo(a[0],a[1]);ctx.lineTo(b[0],b[1]);a=project([-5,-.3,i]);b=project([5,-.3,i]);ctx.moveTo(a[0],a[1]);ctx.lineTo(b[0],b[1]);ctx.stroke();}
 prism(0,-.1,0,2.25,.16,[29,63,82]);prism(0,.08,0,1.65,.04,[62,175,197]);
 const bob=Math.sin(t*2)*.035,speech=options.speaking?(.5+.5*Math.sin(t*22)):0;
 for(const x of [-.35,.35]){cube(x,.33,.18,.24,.17,.38,[58,77,97]);cube(x,.8,0,.16,.36,.19,[85,107,126]);}
 prism(0,1.6+bob,0,.7,.5,[57,84,105]);cube(0,1.62+bob,.66,.25,.24,.04,[77,220,235]);cube(0,2.24+bob,0,.17,.17,.17,[191,159,86]);
 prism(0,2.82+bob,0,.64,.43,[82,109,132],8);cube(0,2.93+bob,.59,.48,.18,.06,[8,23,36]);
 for(const x of [-.24,.24])cube(x,2.96+bob,.67,.13,.035,.025,[117,239,248]);
 for(let i=-2;i<=2;i++)cube(i*.075,2.62+bob,.64,.023,.025+speech*(.025+Math.abs(Math.sin(i+t*5))*.065),.025,[233,200,114]);
 for(const side of [-1,1]){prism(side*.86,1.98+bob,0,.22,.2,[106,128,143]);cube(side*1.02,1.56+bob+speech*.08,0,.15,.34,.17,[52,77,100]);prism(side*1.08,1.2+bob+speech*.12,.08,.18,.13,[203,170,92]);}
 for(let i=0;i<3;i++){const a=t*.5+i*2.094;prism(Math.cos(a)*2.6,1.5+Math.sin(t+i)*.3,Math.sin(a)*1.6,.15,.16,[91,191,208]);}
 faces.sort((a,b)=>b.depth-a.depth);for(const f of faces){ctx.beginPath();f.ps.forEach((p,i)=>i?ctx.lineTo(p[0],p[1]):ctx.moveTo(p[0],p[1]));ctx.closePath();ctx.fillStyle=`rgb(${f.color.join(',')})`;ctx.fill();}
 const chest=project([0,1.55+bob,.72]);ctx.textAlign='center';ctx.font='bold 20px system-ui';ctx.fillStyle='#092431';ctx.fillText('J',chest[0],chest[1]);ctx.textAlign='start';
}};
