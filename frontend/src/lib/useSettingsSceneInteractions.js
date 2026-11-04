import {useEffect} from 'react';
import {attachSceneActions} from './settingsSceneActions.js';
import {cloudStep,fallStep} from './scenePhysics.js';

export default function useSettingsSceneInteractions(ref,kind){
 useEffect(()=>{
  const root=ref.current;if(!root)return;
  const cleanup=[],timers=[];let frame=0,velocity=0,angle=0,last=0,settling=null;
  const listen=(node,type,handler)=>{node.addEventListener(type,handler);cleanup.push(()=>node.removeEventListener(type,handler));};
  const stop=event=>{event.preventDefault();event.stopPropagation();};
  const reduced=()=>matchMedia('(prefers-reduced-motion: reduce)').matches||document.documentElement.dataset.motion==='off';
  if(kind==='compass'){
   const face=root.querySelector('.scene-compass>circle'),needle=root.querySelector('.compass-needle');
   face.style.pointerEvents='all';face.style.cursor='pointer';face.dataset.sceneInteractive='compass';
   const resume=()=>{needle.style.removeProperty('animation');needle.style.removeProperty('transform');delete root.dataset.interacting;delete needle.dataset.spinSpeed;};
   const tick=now=>{
    const seconds=Math.min(.05,(now-last)/1000);last=now;angle+=velocity*seconds;velocity*=Math.exp(-1.8*seconds);
    needle.style.transform=`rotate(${angle}deg)`;needle.dataset.spinSpeed=String(velocity);
    if(velocity>4){frame=requestAnimationFrame(tick);return;}
    frame=0;const target=Math.round((angle+15)/360)*360-15;
    settling=needle.animate([{transform:`rotate(${angle}deg)`},{transform:`rotate(${target}deg)`}],{duration:450,easing:'ease-out',fill:'forwards'});
    settling.finished.then(()=>{resume();settling?.cancel();settling=null;}).catch(()=>{});
   };
   listen(face,'click',event=>{
    stop(event);settling?.cancel();settling=null;
    if(!frame){const m=new DOMMatrixReadOnly(getComputedStyle(needle).transform);angle=Math.atan2(m.b,m.a)*180/Math.PI;}
    needle.style.animation='none';root.dataset.interacting='spin';
    if(reduced()){angle+=90;needle.style.transform=`rotate(${angle}deg)`;timers.push(setTimeout(resume,180));return;}
    velocity=Math.min(4000,velocity+1000);needle.dataset.spinSpeed=String(velocity);
    if(!frame){last=performance.now();frame=requestAnimationFrame(tick);}
   });
   cleanup.push(()=>{settling?.cancel();resume();});
  }
  if(kind==='cloud'||kind==='dino'){
   const nodes=root.querySelectorAll(kind==='cloud'?'.cloud-flight':'.dino-traveler');
   for(const [index,node] of [...nodes].entries()){
    let drag=null,motion=0,body=null,stamp=0,deadUntil=0;
    node.dataset.sceneInteractive=kind;node.style.cursor='grab';node.style.touchAction='none';
    node.querySelectorAll('path,circle,ellipse').forEach(shape=>{shape.style.pointerEvents='all';});
    const paint=()=>{node.style.left=body.x+'px';node.style.top=body.y+'px';node.style.transform=kind==='dino'?`scaleX(${body.direction})`:'';};
    const respawn=(stage)=>{const direction=Math.random()<.5?1:-1;body={...body,x:direction>0?-body.width:stage.width,y:Math.max(0,stage.height-body.height-10),vx:direction*(26+Math.random()*18),vy:0,direction,landed:true};node.style.opacity='1';delete node.dataset.dead;node.dataset.sceneState='walking';};
    const tick=now=>{
     if(!body)return;const stage=root.getBoundingClientRect(),dt=Math.min(.05,(now-stamp)/1000);stamp=now;
     if(kind==='cloud'){body=cloudStep(body,dt,stage.width,Math.max(0,stage.height-body.height));node.dataset.sceneState='drifting';paint();}
     else if(deadUntil){if(now>=deadUntil){deadUntil=0;respawn(stage);paint();}}
     else if(!body.landed){
      body=fallStep(body,dt,Math.max(0,stage.height-body.height-10));paint();node.dataset.sceneState='falling';
      if(body.landed){
       const lethal=Math.sqrt(2*1200*Math.max(75,stage.height*.3));
       if(body.impactSpeed>lethal){node.dataset.dead='true';node.dataset.sceneState='dead';deadUntil=now+650;node.animate([{transform:`scaleX(${body.direction}) rotate(0deg)`,opacity:1},{transform:`scaleX(${body.direction}) rotate(${body.direction*85}deg) scaleY(.65)`,opacity:0}],{duration:550,easing:'ease-out'});node.style.opacity='0';}
       else{node.dataset.sceneState='walking';body.vx=body.direction*34;}
      }
     }else{body.x+=body.vx*dt;if(body.x>stage.width+body.width||body.x< -body.width*1.5)respawn(stage);paint();}
     motion=requestAnimationFrame(tick);
    };
    listen(node,'click',stop);
    listen(node,'pointerdown',event=>{
     if(event.button!==0||deadUntil)return;stop(event);cancelAnimationFrame(motion);
     const stage=root.getBoundingClientRect(),box=node.getBoundingClientRect();
     drag={pointer:event.pointerId,x:event.clientX,y:event.clientY,left:box.left-stage.left,top:box.top-stage.top,maxX:Math.max(0,stage.width-box.width),maxY:Math.max(0,stage.height-box.height),style:node.getAttribute('style'),lastX:event.clientX,lastY:event.clientY,lastAt:event.timeStamp,vx:0,vy:0};
     body={x:drag.left,y:drag.top,vx:0,vy:0,width:box.width,height:box.height,wind:index%2?-16:20,direction:body?.direction||1};
     node.style.animation='none';const model=node.querySelector('.dino-model');if(model){model.style.animation='none';model.style.transform='none';}node.style.bottom='auto';node.style.opacity='1';node.style.cursor='grabbing';node.dataset.dragging='true';node.dataset.sceneState='held';paint();node.setPointerCapture(event.pointerId);
    });
    listen(node,'pointermove',event=>{
     if(!drag||event.pointerId!==drag.pointer)return;stop(event);const dt=Math.max(.008,(event.timeStamp-drag.lastAt)/1000);
     drag.vx=drag.vx*.4+(event.clientX-drag.lastX)/dt*.6;drag.vy=drag.vy*.4+(event.clientY-drag.lastY)/dt*.6;drag.lastX=event.clientX;drag.lastY=event.clientY;drag.lastAt=event.timeStamp;
     body.x=Math.max(0,Math.min(drag.maxX,drag.left+event.clientX-drag.x));body.y=Math.max(0,Math.min(drag.maxY,drag.top+event.clientY-drag.y));paint();
    });
    const release=event=>{if(!drag||event.pointerId!==drag.pointer)return;stop(event);const recent=event.timeStamp-drag.lastAt<100;body.vx=recent?Math.max(-280,Math.min(280,drag.vx)):0;body.vy=recent?Math.max(-360,Math.min(360,drag.vy)):0;if(kind==='dino'&&Math.abs(body.vx)>10)body.direction=body.vx>0?1:-1;body.landed=false;drag=null;delete node.dataset.dragging;node.style.cursor='grab';try{node.releasePointerCapture(event.pointerId);}catch{}if(reduced()){body.y=kind==='dino'?Math.max(0,root.clientHeight-body.height-10):body.y;body.landed=true;paint();}else{stamp=performance.now();motion=requestAnimationFrame(tick);}};
    listen(node,'pointerup',release);listen(node,'pointercancel',release);cleanup.push(()=>cancelAnimationFrame(motion));
   }
  }
  cleanup.push(attachSceneActions(root,kind));
  return()=>{cancelAnimationFrame(frame);timers.forEach(clearTimeout);cleanup.forEach(fn=>fn());};
 },[kind,ref]);
}
