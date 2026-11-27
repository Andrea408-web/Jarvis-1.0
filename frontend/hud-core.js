/* Procedural local HUD; all geometry is original, no images or model download. */
'use strict';
window.HUDCore={draw(canvas,time=0,{mode='jarvis',working=false,speaking=false}={}){
 const c=canvas.getContext('2d');if(!c)return;const w=canvas.width,h=canvas.height,s=Math.min(w,h)/800,t=matchMedia('(prefers-reduced-motion:reduce)').matches?0:time;
 const rgb=mode==='astra'?'100,202,255':mode==='aeris'?'92,225,155':'255,212,78';const ink=(a=1)=>`rgba(${rgb},${a})`;
 c.clearRect(0,0,w,h);c.save();c.translate(w/2,h/2);c.scale(s,s);
 const halo=c.createRadialGradient(0,0,10,0,0,380);halo.addColorStop(0,ink(.18));halo.addColorStop(.55,ink(.035));halo.addColorStop(1,ink(0));c.fillStyle=halo;c.fillRect(-400,-400,800,800);
 function ring(r,a,b,line=1,alpha=.5){c.beginPath();c.arc(0,0,r,a,b);c.strokeStyle=ink(alpha);c.lineWidth=line;c.stroke();}
 c.strokeStyle=ink(.09);c.lineWidth=1;for(const q of [-1,1]){c.beginPath();c.moveTo(-380,q*190);c.lineTo(380,q*190);c.moveTo(q*190,-380);c.lineTo(q*190,380);c.stroke();}ring(334,0,Math.PI*2,1,.3);
 for(let i=0;i<144;i++){const a=i*Math.PI/72,r=i%6===0?313:322;c.beginPath();c.moveTo(Math.cos(a)*r,Math.sin(a)*r);c.lineTo(Math.cos(a)*330,Math.sin(a)*330);c.strokeStyle=ink(i%6===0?.8:.27);c.lineWidth=i%6===0?2:1;c.stroke();}
 for(let i=0;i<4;i++){const a=i*Math.PI/2+t*.00006;ring(295,a,a+1.02,5,.65);ring(277,-a,-a+.72,1,.5);ring(251,a*1.7,a*1.7+.42,9,i%2?.3:.9);}ring(230,0,Math.PI*2,1,.36);
 if(mode==='aeris'){
  // Aether: three green orbital ribbons around a bright energy seed.
  for(let k=0;k<3;k++){c.save();c.rotate(k*Math.PI/3+t*.00012);c.scale(1,.37);c.strokeStyle=ink(.72);c.lineWidth=4;c.shadowColor=ink();c.shadowBlur=15;c.beginPath();c.arc(0,0,153,0,Math.PI*2);c.stroke();c.strokeStyle=ink(.26);c.lineWidth=1;c.beginPath();c.arc(0,0,175,0,Math.PI*2);c.stroke();const a=t*.0008+k*2;c.fillStyle='#fff5ce';c.beginPath();c.ellipse(Math.cos(a)*153,Math.sin(a)*153,4,9,0,0,Math.PI*2);c.fill();c.restore();}ring(58,0,Math.PI*2,1,.55);
 }else if(mode==='astra'){
  for(let k=0;k<3;k++){c.save();c.rotate(k*Math.PI*2/3+t*.0002);c.strokeStyle=ink(.8);c.lineWidth=3;c.shadowColor=ink();c.shadowBlur=15;c.beginPath();c.moveTo(0,-18);c.bezierCurveTo(170,-150,160,80,25,16);c.stroke();c.restore();}
 }else{for(let i=0;i<120;i++){const a=i*Math.PI/60,r=i%5===0?197:202;c.beginPath();c.moveTo(Math.cos(a)*r,Math.sin(a)*r);c.lineTo(Math.cos(a)*209,Math.sin(a)*209);c.strokeStyle=ink(i%5===0?.85:.37);c.lineWidth=i%5===0?2:1;c.stroke();}ring(216,0,Math.PI*2,1,.35);ring(125,0,Math.PI*2,1,.55);for(let k=0;k<6;k++){const a=k*Math.PI/3+t*.00004;ring(88,a,a+.72,4,.7);ring(65,-a,-a+.6,1,.4);}c.beginPath();for(let k=0;k<7;k++){const a=k*Math.PI/3-Math.PI/2;const x=Math.cos(a)*113,y=Math.sin(a)*113;k?c.lineTo(x,y):c.moveTo(x,y);}c.strokeStyle=ink(.35);c.lineWidth=1;c.stroke();for(let i=0;i<6;i++){const a=i*Math.PI/3+t*.00009;ring(176,a,a+.82,2,.7);ring(148,-a,-a+.56,6,.5);}ring(103,0,Math.PI*2,1,.6);}
 c.shadowBlur=0;const pulse=working?Math.sin(t*.008)*4:Math.sin(t*.0015)*2;c.fillStyle='#fff9df';c.shadowColor=ink();c.shadowBlur=25;c.beginPath();c.arc(0,0,(mode==='aeris'?9:mode==='astra'?13:28)+pulse+(speaking?Math.abs(Math.sin(t*.012))*7:0),0,7);c.fill();c.shadowBlur=0;
 for(let i=0;i<(working?38:12);i++){const a=i*2.399+t*.00008,r=185+(i*31%138);c.fillStyle=ink(i%3===0?.9:.3);c.fillRect(Math.cos(a)*r,Math.sin(a)*r,working?2.5:1.2,working?2.5:1.2);}
 c.font='10px monospace';c.textAlign='center';c.fillStyle=ink(.65);c.fillText(mode.toUpperCase()+' / CORE',0,372);c.restore();
}};
