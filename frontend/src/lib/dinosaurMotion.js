import {fallStep} from './scenePhysics.js';

export function attachDinosaur(root){
 const node=root.querySelector('.dino-traveler'),model=node.querySelector('.dino-model'),landscape=root.querySelector('.dino-landscape');
 const clean=[],media=matchMedia('(prefers-reduced-motion: reduce)');let frame=0,stamp=0,drag=null,deadUntil=0,death=null,alive=true;
 const reduced=()=>media.matches||document.documentElement.dataset.motion==='off';
 const listen=(target,type,fn)=>{target.addEventListener(type,fn);clean.push(()=>target.removeEventListener(type,fn));};
 const stop=event=>{event.preventDefault();event.stopPropagation();};
 const stage=root.getBoundingClientRect(),box=node.getBoundingClientRect();
 let body={x:box.left-stage.left,y:box.top-stage.top,width:box.width,vx:34,vy:0,direction:1,landed:true},bounds={width:stage.width,height:stage.height,floor:0};
 node.dataset.sceneInteractive='dino';Object.assign(node.style,{animation:'none',bottom:'auto',cursor:'grab',touchAction:'none'});Object.assign(model.style,{animation:'none',transform:'none'});
 node.querySelectorAll('path,circle').forEach(shape=>shape.style.pointerEvents='all');
 const paint=()=>{node.style.left=body.x+'px';node.style.top=body.y+'px';node.style.transform=`scaleX(${body.direction})`;};
 const measure=()=>{
  const stage=root.getBoundingClientRect(),box=node.getBoundingClientRect(),ground=landscape.getScreenCTM(),feet=model.getScreenCTM();if(!ground||!feet)return;
  // Both positions come from their SVG view boxes, including letterboxing.
  const groundY=new DOMPoint(0,289).matrixTransform(ground).y,footY=new DOMPoint(0,317.5).matrixTransform(feet).y;
  bounds={width:stage.width,height:stage.height,floor:groundY-stage.top-(footY-box.top)};body.width=box.width;
  if(body.landed&&!drag){body.y=bounds.floor;paint();}
 };
 const start=()=>{if(!frame&&!reduced()&&!drag){stamp=performance.now();frame=requestAnimationFrame(tick);}};
 const respawn=()=>{const direction=Math.random()<.5?1:-1;body={...body,x:direction>0?-body.width:bounds.width,y:bounds.floor,vx:direction*34,vy:0,direction,landed:true};death?.cancel();death=null;node.style.opacity='1';delete node.dataset.dead;node.dataset.sceneState='walking';paint();};
 const tick=now=>{
  frame=0;if(!alive||drag)return;const dt=Math.max(0,Math.min(.05,(now-stamp)/1000));stamp=now;
  if(deadUntil){if(now>=deadUntil){deadUntil=0;respawn();}}
  else if(!body.landed){
   body=fallStep(body,dt,bounds.floor);paint();node.dataset.sceneState='falling';
   if(body.landed){
    const lethal=Math.sqrt(2*1200*Math.max(75,bounds.height*.3));
    if(body.impactSpeed>lethal){node.dataset.dead='true';node.dataset.sceneState='dead';deadUntil=now+650;death=node.animate([{transform:`scaleX(${body.direction}) rotate(0deg)`,opacity:1},{transform:`scaleX(${body.direction}) rotate(${body.direction*85}deg) scaleY(.65)`,opacity:0}],{duration:550,easing:'ease-out'});node.style.opacity='0';}
    else{body.vx=body.direction*34;node.dataset.sceneState='walking';}
   }
  }else{body.y=bounds.floor;body.x+=body.vx*dt;if(body.x>bounds.width+body.width||body.x< -body.width*1.5)respawn();paint();}
  if(!reduced())frame=requestAnimationFrame(tick);
 };
 listen(node,'click',stop);
 listen(node,'pointerdown',event=>{
  if(event.button!==0||deadUntil)return;stop(event);cancelAnimationFrame(frame);frame=0;measure();
  const stage=root.getBoundingClientRect(),box=node.getBoundingClientRect();
  drag={id:event.pointerId,x:event.clientX,y:event.clientY,left:box.left-stage.left,top:box.top-stage.top,lastX:event.clientX,lastY:event.clientY,at:event.timeStamp,vx:0,vy:0};
  body={...body,x:drag.left,y:drag.top,vx:0,vy:0,landed:false};node.dataset.sceneState='held';node.dataset.dragging='true';node.style.cursor='grabbing';paint();node.setPointerCapture(event.pointerId);
 });
 listen(node,'pointermove',event=>{
  if(!drag||event.pointerId!==drag.id)return;stop(event);const dt=Math.max(.008,(event.timeStamp-drag.at)/1000);
  drag.vx=drag.vx*.4+(event.clientX-drag.lastX)/dt*.6;drag.vy=drag.vy*.4+(event.clientY-drag.lastY)/dt*.6;drag.lastX=event.clientX;drag.lastY=event.clientY;drag.at=event.timeStamp;
  body.x=Math.max(0,Math.min(bounds.width-body.width,drag.left+event.clientX-drag.x));body.y=Math.max(0,Math.min(bounds.floor,drag.top+event.clientY-drag.y));paint();
 });
 const release=event=>{
  if(!drag||event.pointerId!==undefined&&event.pointerId!==drag.id)return;
  stop(event);const id=drag.id,recent=event.timeStamp-drag.at<100;
  body.vx=recent?Math.max(-280,Math.min(280,drag.vx)):0;body.vy=recent?Math.max(-360,Math.min(360,drag.vy)):0;if(Math.abs(body.vx)>10)body.direction=body.vx>0?1:-1;
  drag=null;delete node.dataset.dragging;node.style.cursor='grab';node.dataset.sceneState='falling';try{node.releasePointerCapture(id);}catch{}
  if(reduced()){body.y=bounds.floor;body.landed=true;body.vx=body.direction*34;node.dataset.sceneState='walking';paint();}else start();
 };
 for(const type of ['pointerup','pointercancel','lostpointercapture'])listen(node,type,release);
 listen(window,'pointerup',release);listen(window,'blur',release);
 const motionChange=()=>{if(reduced()){cancelAnimationFrame(frame);frame=0;if(drag)release(new Event('blur'));if(deadUntil){deadUntil=0;respawn();}body.y=bounds.floor;body.landed=true;node.dataset.sceneState='walking';paint();}else start();};
 listen(media,'change',motionChange);
 const observer=new ResizeObserver(measure);observer.observe(root);observer.observe(node);
 const preference=new MutationObserver(motionChange);preference.observe(document.documentElement,{attributes:true,attributeFilter:['data-motion']});
 node.dataset.sceneState='walking';measure();start();
 return()=>{alive=false;cancelAnimationFrame(frame);death?.cancel();observer.disconnect();preference.disconnect();clean.forEach(fn=>fn());};
}
