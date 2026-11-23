/* Original AERIS aperture portrait. Rendering only; state comes from the assistant. */
const TAU=Math.PI*2;
// Idle and reduced-motion portraits are still images. Keep repeated callers cheap.
const portraits=new WeakMap();
function ring(c,r,start,end,color,width=1){c.beginPath();c.arc(0,0,r,start,end);c.strokeStyle=color;c.lineWidth=width;c.stroke();}
export function drawAeris(canvas,time=0,{working=false,speaking=false,listening=false,reducedMotion}={}){
 const c=canvas?.getContext?.('2d');if(!c)return;
 const box=canvas.getBoundingClientRect(),side=box.width>0&&box.height>0?Math.min(box.width,box.height):0;
 if(!side)return;
 const dpr=Number.isFinite(globalThis.devicePixelRatio)?Math.max(1,Math.min(globalThis.devicePixelRatio,1.5)):1;
 const pixels=Math.max(1,Math.min(1536,Math.round(side*dpr)));
 const resized=canvas.width!==pixels||canvas.height!==pixels;
 if(resized)canvas.width=canvas.height=pixels;
 const reduced=reducedMotion??globalThis.matchMedia?.('(prefers-reduced-motion: reduce)').matches??false,t=reduced?0:Number.isFinite(time)?time:0;
 const state=[pixels,!!working,!!speaking,!!listening,!!reduced].join(':');
 if(!resized&&(reduced||!(working||speaking||listening))&&portraits.get(canvas)===state)return;
 const activity=working||speaking||listening,pulse=speaking?Math.sin(t*.014)*.5+.5:listening?Math.sin(t*.003)*.5+.5:.35;
 c.setTransform(1,0,0,1,0,0);c.clearRect(0,0,canvas.width,canvas.height);c.save();c.translate(canvas.width/2,canvas.height/2);const scale=Math.min(canvas.width,canvas.height)/720;c.scale(scale,scale);c.lineCap='round';
 const haze=c.createRadialGradient(0,0,60,0,0,335);haze.addColorStop(0,activity?'#e1be6236':'#b29a4b22');haze.addColorStop(.55,'#b49a4c17');haze.addColorStop(1,'#b49a4c00');c.fillStyle=haze;c.fillRect(-360,-360,720,720);
 // Orbital rail: deliberately broken arcs, not a progress indicator.
 const spin=working?t*.00012:0;
 for(let i=0;i<3;i++){const a=i*TAU/3+spin;ring(c,266,a+.07,a+1.5,'#c0a66d55',1.5);ring(c,280,a+.25,a+.72,activity?'#ead7a2bd':'#cfbb8790',3);}
 for(let i=0;i<72;i++){const a=i*TAU/72,major=i%6===0,inner=248,outer=major?259:253;c.beginPath();c.moveTo(Math.cos(a)*inner,Math.sin(a)*inner);c.lineTo(Math.cos(a)*outer,Math.sin(a)*outer);c.strokeStyle=major?'#eadfbb9c':'#b9a77755';c.lineWidth=major?2:1;c.stroke();}
 // Dark, shaded housing gives the core depth without pretending to be a 3D editor.
 const shell=c.createRadialGradient(-78,-102,14,18,25,230);shell.addColorStop(0,'#4d4c3b');shell.addColorStop(.34,'#252b24');shell.addColorStop(.76,'#101a16');shell.addColorStop(1,'#070d0b');c.fillStyle=shell;c.beginPath();c.arc(0,0,228,0,TAU);c.fill();
 ring(c,228,0,TAU,'#e4d4a690',1.5);ring(c,219,.15,TAU-.15,'#f8edcd24',1);ring(c,193,0,TAU,'#bcab7650',1);
 const sheen=c.createRadialGradient(-72,-98,4,-55,-80,190);sheen.addColorStop(0,'#fff3cf13');sheen.addColorStop(1,'#fff3cf00');c.fillStyle=sheen;c.beginPath();c.arc(0,0,223,0,TAU);c.fill();
 for(let i=0;i<6;i++){
  c.save();c.rotate(i*TAU/6+(working?t*.000055:0));
  const blade=c.createLinearGradient(-20,-150,110,100);blade.addColorStop(0,'#e5d4a3');blade.addColorStop(.24,'#a18a52');blade.addColorStop(.65,'#4c5039');blade.addColorStop(1,'#1a2720');c.fillStyle=blade;
  c.beginPath();c.moveTo(-18,-165);c.bezierCurveTo(55,-190,135,-114,118,-42);c.bezierCurveTo(112,-12,88,17,65,28);c.bezierCurveTo(58,-8,32,-36,-2,-50);c.bezierCurveTo(31,-69,26,-129,-18,-165);c.closePath();c.fill();c.strokeStyle='#f7e5ab48';c.lineWidth=1;c.stroke();
  c.beginPath();c.moveTo(-9,-157);c.bezierCurveTo(43,-165,100,-114,106,-67);c.strokeStyle='#fff4ce50';c.lineWidth=1.3;c.stroke();c.restore();
 }
 const aperture=57+(speaking?pulse*5:listening?2:0);const inner=c.createRadialGradient(0,0,5,0,0,aperture+27);inner.addColorStop(0,'#fffce9');inner.addColorStop(.3,'#f6e7b8');inner.addColorStop(.58,'#d9c78a');inner.addColorStop(.72,'#907e4740');inner.addColorStop(1,'#d8bf6300');c.fillStyle=inner;c.beginPath();c.arc(0,0,aperture+27,0,TAU);c.fill();
 const seed=c.createRadialGradient(-12,-15,2,0,5,43);seed.addColorStop(0,'#fffef4');seed.addColorStop(.5,'#f4edca');seed.addColorStop(1,'#d1be81');c.fillStyle=seed;c.shadowColor='#f9e6a6';c.shadowBlur=activity?24:15;c.beginPath();c.arc(0,0,39+(speaking?pulse*3:0),0,TAU);c.fill();c.shadowBlur=0;
 ring(c,76,0,TAU,'#f9e9bd77',1);for(let i=0;i<24;i++){const a=i*TAU/24+(working?-t*.0001:0);c.beginPath();c.arc(Math.cos(a)*86,Math.sin(a)*86,i%3===0?1.8:1,0,TAU);c.fillStyle='#f8eac7a0';c.fill();}
 // Listening and speaking have honest, state-driven emphasis only.
 if(listening){ring(c,237,-2.5,-.64,'#fff5d5bd',2.5);ring(c,237,.64,2.5,'#fff5d570',1.5);}
 if(speaking){for(let i=0;i<9;i++){const a=.7+i*.22,r=182,len=3+Math.abs(Math.sin(t*.012+i*.9))*9;c.beginPath();c.moveTo(Math.cos(a)*r,Math.sin(a)*r);c.lineTo(Math.cos(a)*(r+len),Math.sin(a)*(r+len));c.strokeStyle='#fff3cec7';c.lineWidth=2;c.stroke();}}
 if(working){for(let i=0;i<7;i++){const a=i*2.399+t*.00022,r=286+(i%3)*8,fade=.35+.45*(.5+.5*Math.sin(t*.003+i));c.globalAlpha=fade;c.fillStyle='#fffbee';c.beginPath();c.arc(Math.cos(a)*r,Math.sin(a)*r,i%3===0?1.8:1.1,0,TAU);c.fill();}c.globalAlpha=1;}
 c.restore();
 portraits.set(canvas,state);
}

// Legacy import compatibility for already cached callers.
export {drawAeris as drawIris};
