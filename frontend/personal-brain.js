import * as THREE from './vendor/three/three.module.min.js';
import {OrbitControls} from './vendor/three/OrbitControls.js';

// Anatomical fsaverage5 template; see vendor/brain/NOTICE.txt and LICENSE.txt.
export async function createBrain(canvas){
 const response=await fetch('/vendor/brain/fsaverage5.bin');
 if(!response.ok)throw Error('Das 3D-Gehirn konnte nicht geladen werden. Bitte die Seite nach dem Update neu laden.');
 const data=await response.arrayBuffer(),header=new DataView(data);
 if(data.byteLength<12||header.getUint32(0,true)!==0x3152424a)throw Error('Die Gehirnoberfläche ist beschädigt.');
 const count=header.getUint32(4,true),triangles=header.getUint32(8,true);
 if(count!==20484||triangles!==40960||data.byteLength!==12+count*6+triangles*6)throw Error('Ungültige Gehirnoberfläche.');
 const packed=new Int16Array(data,12,count*3),positions=new Float32Array(count*3);
 for(let i=0;i<packed.length;i++)positions[i]=packed[i]/10000;
 const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.BufferAttribute(positions,3));geometry.setIndex(new THREE.BufferAttribute(new Uint16Array(data,12+count*6,triangles*3),1));geometry.computeVertexNormals();
 // Subtle baked cavity shading makes the actual cortical folds readable on small screens.
 const neighbors=new Float32Array(count*3),weights=new Uint16Array(count),index=geometry.index.array,normals=geometry.attributes.normal.array;
 for(let i=0;i<index.length;i+=3)for(let j=0;j<3;j++){const a=index[i+j],b=index[i+(j+1)%3];for(let k=0;k<3;k++){neighbors[a*3+k]+=positions[b*3+k];neighbors[b*3+k]+=positions[a*3+k];}weights[a]++;weights[b]++;}
 const colors=new Float32Array(count*3),base=new THREE.Color('#40996b').toArray();
 for(let i=0;i<count;i++){let curvature=0;for(let k=0;k<3;k++)curvature+=(neighbors[i*3+k]/weights[i]-positions[i*3+k])*normals[i*3+k];const light=THREE.MathUtils.clamp(.87-curvature*19,.28,1);for(let k=0;k<3;k++)colors[i*3+k]=base[k]*light;}
 geometry.setAttribute('color',new THREE.BufferAttribute(colors,3));
 let renderer;try{renderer=new THREE.WebGLRenderer({canvas,alpha:true,antialias:true,powerPreference:'low-power'});}catch(_){geometry.dispose();throw Error('Für das räumliche Gehirn bitte WebGL im Browser aktivieren. Deine Profilangaben bleiben nutzbar.');}
 renderer.setPixelRatio(Math.min(devicePixelRatio||1,1.75));renderer.setSize(480,480,false);renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.05;
 const scene=new THREE.Scene(),camera=new THREE.PerspectiveCamera(34,1,.1,30);camera.position.set(3.5,1.5,4.9);camera.lookAt(0,0,0);
 scene.add(new THREE.HemisphereLight('#b5ffd1','#041b0c',.65));
 for(const[color,power,pos]of [['#e2ffea',3.1,[1.5,3.5,4]],['#36ef91',2.7,[-3,1,-2]],['#4aaa73',.7,[4,-1,-1]]]){const light=new THREE.DirectionalLight(color,power);light.position.set(...pos);scene.add(light);}
 const brain=new THREE.Group();scene.add(brain);const material=new THREE.MeshStandardMaterial({vertexColors:true,metalness:.22,roughness:.5});brain.add(new THREE.Mesh(geometry,material));
 const sparksGeometry=new THREE.BufferGeometry(),sparkPositions=new Float32Array(36*3);
 for(let i=0;i<36;i++){const v=(i*571+61)%count;for(let k=0;k<3;k++)sparkPositions[i*3+k]=positions[v*3+k]*1.009;}
 sparksGeometry.setAttribute('position',new THREE.BufferAttribute(sparkPositions,3));const sparksMaterial=new THREE.PointsMaterial({color:'#d7ffe5',size:.023,transparent:true,opacity:.8,depthWrite:false});brain.add(new THREE.Points(sparksGeometry,sparksMaterial));
 const ringGeometry=new THREE.TorusGeometry(1.59,.004,5,140),ringMaterial=new THREE.MeshBasicMaterial({color:'#369b63',transparent:true,opacity:.55}),ring=new THREE.Mesh(ringGeometry,ringMaterial);ring.rotation.x=Math.PI/2;ring.position.y=-1.12;scene.add(ring);
 const controls=new OrbitControls(camera,canvas);controls.enableZoom=false;controls.enablePan=false;controls.enableDamping=false;controls.target.set(0,0,0);controls.minPolarAngle=.5;controls.maxPolarAngle=2.3;controls.update();
 const reduced=matchMedia('(prefers-reduced-motion: reduce)'),draw=()=>renderer.render(scene,camera);let raf=null,running=false,disposed=false,last=0,elapsed=0;
 function loop(t){if(!running||disposed){raf=null;return;}raf=requestAnimationFrame(loop);if(t-last<40)return;const dt=last?Math.min((t-last)/1000,.1):0;last=t;elapsed+=dt;if(!reduced.matches){brain.rotation.y=.16+Math.sin(elapsed*.23)*.26;brain.rotation.z=Math.sin(elapsed*.18)*.025;sparksMaterial.opacity=.45+Math.sin(elapsed*1.5)*.3;}draw();}
 controls.addEventListener('change',draw);canvas.addEventListener('pointerdown',()=>{canvas.classList.add('brain-dragging');});const up=()=>{canvas.classList.remove('brain-dragging');};canvas.addEventListener('pointerup',up);canvas.addEventListener('pointercancel',up);
 function start(){if(disposed||running)return;running=true;last=0;draw();if(!reduced.matches)raf=requestAnimationFrame(loop);}
 function stop(){running=false;if(raf!==null)cancelAnimationFrame(raf);raf=null;last=0;}
 function motion(){stop();start();}reduced.addEventListener('change',motion);
 canvas.dataset.brainRenderer='webgl';canvas.dataset.brainVertices=String(count);canvas.setAttribute('aria-label','Anatomisches grünes 3D-Gehirn mit Windungen. Mit einem Finger oder der Maus drehen. Standardmodell, kein persönlicher Scan.');draw();
 return{start,stop,dispose(){stop();disposed=true;controls.dispose();geometry.dispose();material.dispose();sparksGeometry.dispose();sparksMaterial.dispose();ringGeometry.dispose();ringMaterial.dispose();renderer.dispose();reduced.removeEventListener('change',motion);}};
}
