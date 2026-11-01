import {useEffect} from 'react';

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
   for(const node of nodes){
    let drag=null;
    node.dataset.sceneInteractive=kind;node.style.cursor='grab';node.style.touchAction='none';
    node.querySelectorAll('path,circle,ellipse').forEach(shape=>{shape.style.pointerEvents='all';});
    listen(node,'click',stop);
    listen(node,'pointerdown',event=>{
     if(event.button!==0)return;stop(event);
     const stage=root.getBoundingClientRect(),box=node.getBoundingClientRect();
     drag={pointer:event.pointerId,x:event.clientX,y:event.clientY,left:box.left-stage.left,top:box.top-stage.top,
      maxX:Math.max(0,stage.width-box.width),maxY:Math.max(0,stage.height-box.height),style:node.getAttribute('style')};
     node.style.animation='none';node.style.transform='none';node.style.bottom='auto';node.style.opacity='.85';node.style.left=drag.left+'px';node.style.top=drag.top+'px';node.style.cursor='grabbing';
     node.dataset.dragging='true';node.setPointerCapture(event.pointerId);
    });
    listen(node,'pointermove',event=>{
     if(!drag||event.pointerId!==drag.pointer)return;stop(event);
     node.style.left=Math.max(0,Math.min(drag.maxX,drag.left+event.clientX-drag.x))+'px';
     node.style.top=Math.max(0,Math.min(drag.maxY,drag.top+event.clientY-drag.y))+'px';
    });
    const release=event=>{if(!drag||event.pointerId!==drag.pointer)return;stop(event);drag=null;delete node.dataset.dragging;node.style.cursor='grab';try{node.releasePointerCapture(event.pointerId);}catch{}};
    listen(node,'pointerup',release);
    listen(node,'pointercancel',event=>{if(drag){const style=drag.style;release(event);if(style==null)node.removeAttribute('style');else node.setAttribute('style',style);}});
   }
  }
  if(kind==='balloon'){
   const balloon=root.querySelector('.balloon-flight'),head=balloon.querySelector('ellipse');
   head.style.pointerEvents='all';head.style.cursor='pointer';head.dataset.sceneInteractive='balloon';
   listen(head,'click',event=>{
    stop(event);if(balloon.dataset.popped==='true')return;
    balloon.dataset.popped='true';balloon.style.animationPlayState='paused';
    const children=[...balloon.children];children.forEach(child=>{child.style.visibility='hidden';});
    const burst=document.createElementNS('http://www.w3.org/2000/svg','g');burst.classList.add('balloon-pop-burst');
    for(let i=0;i<10;i++){
     const line=document.createElementNS(burst.namespaceURI,'path'),a=i*Math.PI/5;
     line.setAttribute('d',`M${45+Math.cos(a)*13} ${42+Math.sin(a)*15}l${Math.cos(a)*17} ${Math.sin(a)*19}`);
     line.setAttribute('vector-effect','non-scaling-stroke');burst.append(line);
    }
    balloon.append(burst);if(!reduced())burst.animate([{opacity:1},{opacity:0}],{duration:400,fill:'forwards'});
    timers.push(setTimeout(()=>{burst.remove();children.forEach(child=>{child.style.removeProperty('visibility');});balloon.style.removeProperty('animation-play-state');delete balloon.dataset.popped;},700));
   });
  }
  return()=>{cancelAnimationFrame(frame);timers.forEach(clearTimeout);cleanup.forEach(fn=>fn());};
 },[kind,ref]);
}
