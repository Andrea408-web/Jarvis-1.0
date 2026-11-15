/* WebXR joint poses only; no camera, face data or network. */
'use strict';
(()=>{const states=new Map(),dist=(a,b)=>Math.hypot(...a.map((x,i)=>x-b[i]));
 const chains=[['wrist','thumb-metacarpal','thumb-phalanx-proximal','thumb-phalanx-distal','thumb-tip'],...['index','middle','ring','pinky'].map(f=>['wrist',f+'-finger-metacarpal',f+'-finger-phalanx-proximal',f+'-finger-phalanx-intermediate',f+'-finger-phalanx-distal',f+'-finger-tip'])];
 function update(source,frame,space,time){let state=states.get(source);if(!state){state={closed:false,joints:{},gesture:null,since:time,last:-Infinity};states.set(source,state);}const raw={},joints={};for(const name of new Set(chains.flat())){const joint=source.hand?.get(name);if(!joint)continue;const pose=frame.getJointPose(joint,space);if(!pose)continue;const p=pose.transform.position,v=[p.x,p.y,p.z];if(v.some(n=>!Number.isFinite(n)))continue;raw[name]=v;joints[name]=state.joints[name]?v.map((n,i)=>state.joints[name][i]*.55+n*.45):v;}
 const thumb=raw['thumb-tip'],index=raw['index-finger-tip'],wrist=raw.wrist;let point=null,gesture=null;
 if(thumb&&index&&wrist){const gap=dist(thumb,index);state.closed=gap<(state.closed?.045:.028);point=thumb.map((n,i)=>(joints['thumb-tip'][i]+joints['index-finger-tip'][i])/2);
  const tips=['index','middle','ring','pinky'].map(f=>raw[f+'-finger-tip']),bases=['index','middle','ring','pinky'].map(f=>raw[f+'-finger-phalanx-proximal']);const extended=tips.map((t,i)=>!!(t&&bases[i]&&dist(t,wrist)>dist(bases[i],wrist)*1.4));
  if(extended.every(Boolean)&&!state.closed)gesture='palm';
  if(tips.every(Boolean)&&extended.every(v=>!v)&&thumb[1]>wrist[1]+.055&&dist(thumb,wrist)>.075)gesture='thumb-up';
  if(raw['middle-finger-tip']&&dist(thumb,raw['middle-finger-tip'])<.027&&gap>.045)gesture='mute';
 }else{state.closed=false;state.gesture=null;state.since=time;}
 if(gesture!==state.gesture){state.gesture=gesture;state.since=time;}let fired=null;if(gesture&&time-state.since>650&&time-state.last>1800){fired=gesture;state.last=time;state.since=time+100000;}
 state.joints=joints;return {point,closed:state.closed,joints:Object.values(joints),named:joints,bones:chains.flatMap(chain=>chain.slice(1).map((name,i)=>joints[name]&&joints[chain[i]]?{a:joints[chain[i]],b:joints[name],thumb:chain[1]==='thumb-metacarpal'}:null).filter(Boolean)),gesture:fired,wrist:joints.wrist||null};}
 window.QuestHands={update,forget:source=>states.delete(source),clear:()=>states.clear()};
})();
