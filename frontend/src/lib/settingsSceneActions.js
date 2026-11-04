// Decorative interactions stay inside the owning settings tile. No learning
// progress or rewards are inferred from these gestures.
const ns='http://www.w3.org/2000/svg';
export function attachSceneActions(root,kind){
 const listeners=[],frames=new Set(),timers=new Set(),animations=new Set(),layers=new Set();let alive=true;
 const stop=e=>{e.preventDefault();e.stopPropagation();};
 const reduced=()=>matchMedia('(prefers-reduced-motion: reduce)').matches||document.documentElement.dataset.motion==='off';
 const listen=(node,type,fn)=>{node.addEventListener(type,fn);listeners.push(()=>node.removeEventListener(type,fn));};
 const later=(fn,ms)=>{const id=setTimeout(()=>{timers.delete(id);if(alive)fn();},ms);timers.add(id);return id;};
 const animate=(node,keys,options)=>{const a=node.animate(keys,{...options,duration:reduced()?1:options.duration});animations.add(a);a.finished.finally(()=>animations.delete(a)).catch(()=>{});return a;};
 const loop=step=>{let id,last=performance.now();const tick=now=>{frames.delete(id);if(!alive)return;const dt=Math.min(.05,(now-last)/1000);last=now;if(step(dt,now)!==false){id=requestAnimationFrame(tick);frames.add(id);}};id=requestAnimationFrame(tick);frames.add(id);return()=>{cancelAnimationFrame(id);frames.delete(id);};};
 function interactive(node,name=kind){node.dataset.sceneInteractive=name;node.style.pointerEvents='all';node.style.cursor='pointer';node.style.touchAction='none';}
 function overlay(name){
  const host=root.closest('.settings-tile')||root.parentElement,box=host.getBoundingClientRect(),svg=document.createElementNS(ns,'svg');
  svg.classList.add('settings-scene-effect',name);svg.setAttribute('viewBox',`0 0 ${box.width} ${box.height}`);svg.setAttribute('aria-hidden','true');
  Object.assign(svg.style,{position:'absolute',inset:'0',width:'100%',height:'100%',overflow:'hidden',pointerEvents:'none',color:getComputedStyle(root).color,zIndex:'2'});
  host.append(svg);layers.add(svg);return {svg,box,remove:()=>{svg.remove();layers.delete(svg);}};
 }
 function shatter(node,name,{colour,origin}={}){
  const layer=overlay(name),box=node.getBoundingClientRect(),x=(origin?.x??box.left+box.width/2)-layer.box.left,y=(origin?.y??box.top+box.height/2)-layer.box.top;
  const pieces=Array.from({length:18},(_,i)=>{const p=document.createElementNS(ns,'path');p.setAttribute('d',i%2?'M-5-4 6-2 2 7Z':'M-4-5 5 0 1 5-6 2Z');p.setAttribute('fill',colour||'currentColor');p.setAttribute('fill-opacity','.32');p.setAttribute('stroke','currentColor');p.setAttribute('stroke-width','1');layer.svg.append(p);const a=i/18*Math.PI*2;return {p,vx:Math.cos(a)*(55+i%5*20),vy:Math.sin(a)*(90+i%4*35)-110,spin:(i%2?1:-1)*(100+i*23)};});
  let t=0;const cancel=loop(dt=>{t+=dt;for(const {p,vx,vy,spin} of pieces)p.setAttribute('transform',`translate(${x+vx*t} ${y+vy*t+450*t*t}) rotate(${spin*t})`);if(t>2.8||y-230*t+450*t*t>layer.box.height+40||reduced()){layer.remove();return false;}});
  return ()=>{cancel();layer.remove();};
 }
 if(kind==='globe'){
  const turn=root.querySelector('.globe-turn'),planet=root.querySelector('.globe-planet');let speed=40,angle=0,running=false,exploded=false,pausedCity=[];
  const city=root.getAnimations({subtree:true}).filter(a=>/^(planet-cycle|planet-burst|shockwave-spread|fragment-flight|settings-city-drop-\d+)$/.test(a.animationName||''));
  const buildings=[...root.querySelectorAll('.globe-building')],cityPhase=()=>Number(city.find(a=>a.animationName==='planet-cycle')?.currentTime||0)%14000;
  const fullCity=()=>buildings.every(node=>!node.dataset.uprooted&&getComputedStyle(node).visibility!=='hidden'&&Number(getComputedStyle(node).opacity)>.99);
  const pauseCity=()=>{if(pausedCity.length)return;pausedCity=city.filter(a=>a.playState!=='paused');city.forEach(a=>a.pause());};
  const resumeCity=()=>{if(buildings.some(node=>node.dataset.uprooted))return;if(cityPhase()>=8680)city.forEach(a=>{a.currentTime=8680;});pausedCity.forEach(a=>a.play());pausedCity=[];};
  buildings.forEach(node=>{interactive(node,'building');listen(node,'click',event=>{
   stop(event);if(exploded||node.dataset.uprooted||Number(getComputedStyle(node).opacity)<.99||cityPhase()>=11620)return;node.dataset.uprooted='true';pauseCity();
   const flying=node.cloneNode(true);flying.removeAttribute('data-scene-interactive');flying.style.pointerEvents='none';flying.style.animation='none';flying.style.visibility='visible';node.parentElement.append(flying);
   const a=animate(flying,[{transform:'translateY(0) rotate(0deg)',opacity:1},{transform:'translateY(-56px) rotate(30deg)',opacity:0}],{duration:850,easing:'cubic-bezier(.2,.7,.4,1)',fill:'forwards'});
   node.style.visibility='hidden';later(()=>{node.style.visibility='';const growth=animate(node,[{transform:'translateY(-15px) scaleY(.3)',opacity:0},{transform:'translateY(0) scaleY(1)',opacity:1}],{duration:1000,easing:'ease-out'});growth.finished.then(()=>{if(alive){delete node.dataset.uprooted;resumeCity();}}).catch(()=>{});},1200);
   a.finished.then(()=>flying.remove()).catch(()=>flying.remove());
  });});
  const face=turn.querySelector('circle');interactive(face,'globe');listen(face,'click',event=>{
   stop(event);if(exploded)return;
   if(!running){const m=new DOMMatrixReadOnly(getComputedStyle(turn).transform);angle=Math.atan2(m.b,m.a)*180/Math.PI;turn.style.animation='none';}
   speed+=230;turn.dataset.spinSpeed=String(speed);
   if(speed>=1100&&fullCity()){exploded=true;root.dataset.sceneState='exploded';city.forEach(a=>{a.currentTime=11620;if(!reduced())a.play();});later(()=>{exploded=false;speed=40;delete root.dataset.sceneState;},2380);}
   if(running)return;running=true;loop(dt=>{
    speed=40+(speed-40)*Math.exp(-.7*dt);angle+=speed*dt;turn.style.transform=`rotate(${angle}deg)`;turn.dataset.spinSpeed=String(speed);
    if(speed<41&&!exploded){running=false;turn.style.removeProperty('transform');turn.style.removeProperty('animation');turn.style.animationDelay=`${-(angle%360+360)%360/40}s`;delete turn.dataset.spinSpeed;return false;}
   });
  });
 }
 if(kind==='bulb'){
  const bulb=root.querySelector('.scene-bulb'),glass=root.querySelector('.bulb-glass'),filament=root.querySelector('.bulb-filament'),halo=root.querySelector('.bulb-halo'),rays=root.querySelector('.bulb-rays');let heat=0,lastClick=0,broken=false,cooling=null;
  interactive(glass,'bulb');listen(glass,'click',event=>{
   stop(event);if(broken)return;const now=performance.now();heat=Math.max(0,heat-(now-lastClick)/1200)+1;lastClick=now;
   clearTimeout(cooling);filament.style.animation='none';filament.style.stroke=`rgb(255,${Math.round(Math.max(35,205-heat*32))},${Math.round(Math.max(25,110-heat*16))})`;filament.style.strokeOpacity='1';
   halo.style.animation='none';halo.style.fill='#ffdb75';halo.style.fillOpacity=String(Math.min(.62,.08+heat*.09));halo.setAttribute('r',String(43+heat*2));glass.style.animation='none';glass.style.fill='#ffe7ad';glass.style.fillOpacity=String(Math.min(.66,.1+heat*.09));rays.style.animation='none';rays.style.stroke='#ffe7ad';rays.style.opacity=String(Math.min(1,.45+heat*.09));root.dataset.heat=String(heat);
   const cool=()=>{heat=0;delete root.dataset.heat;halo.setAttribute('r','43');[filament,halo,glass,rays].forEach(node=>{for(const key of ['animation','stroke','fill','stroke-opacity','fill-opacity','opacity'])node.style.removeProperty(key);});};
   if(heat>=6){broken=true;root.dataset.sceneState='broken';shatter(glass,'bulb-glass-fragments',{colour:'#d6eee8'});bulb.style.visibility='hidden';later(()=>{broken=false;bulb.style.visibility='';delete root.dataset.sceneState;cool();},2400);}
   else cooling=later(cool,2200);
  });
 }
 if(kind==='coffee'){
  const cup=root.querySelector('.coffee-vessel');interactive(cup,'coffee');let drag=null,offset={x:0,y:0},cancelFall=null,broken=false;
  listen(cup,'click',stop);
  listen(cup,'pointerdown',event=>{
   if(event.button!==0||broken)return;stop(event);cancelFall?.();const box=cup.getBoundingClientRect(),scale=root.getBoundingClientRect().width/180;
   drag={id:event.pointerId,x:event.clientX,y:event.clientY,offset:{...offset},scale,box,host:root.closest('.settings-tile').getBoundingClientRect()};cup.setPointerCapture(event.pointerId);cup.style.cursor='grabbing';root.dataset.sceneState='held';
  });
  listen(cup,'pointermove',event=>{if(!drag||drag.id!==event.pointerId)return;stop(event);const dx=Math.max(drag.host.left-drag.box.left,Math.min(drag.host.right-drag.box.right,event.clientX-drag.x)),dy=Math.max(drag.host.top+45-drag.box.top,Math.min(drag.host.bottom-drag.box.bottom,event.clientY-drag.y));offset={x:drag.offset.x+dx/drag.scale,y:drag.offset.y+dy/drag.scale};cup.setAttribute('transform',`translate(${offset.x} ${offset.y})`);});
  const release=event=>{if(!drag||drag.id!==event.pointerId)return;stop(event);const high=offset.y< -18;drag=null;cup.style.cursor='grab';try{cup.releasePointerCapture(event.pointerId);}catch{}let vy=0;root.dataset.sceneState='falling';
   cancelFall=loop(dt=>{vy+=800*dt;offset.y+=vy*dt;cup.setAttribute('transform',`translate(${offset.x} ${Math.min(0,offset.y)})`);
    if(offset.y>=0||reduced()){offset.y=0;cup.setAttribute('transform',`translate(${offset.x} 0)`);root.dataset.sceneState=high?'broken':'resting';if(high){broken=true;shatter(cup,'coffee-shards',{colour:'#c2b08e'});cup.style.visibility='hidden';later(()=>{broken=false;offset={x:0,y:0};cup.removeAttribute('transform');cup.style.visibility='';delete root.dataset.sceneState;},2100);}return false;}
   });
  };listen(cup,'pointerup',release);listen(cup,'pointercancel',release);listen(cup,'lostpointercapture',event=>{if(drag)release(event);});
 }
 if(kind==='balloon'){
  const balloon=root.querySelector('.balloon-flight'),head=balloon.querySelector('ellipse');let drag=null,body=null,cancelMove=null,moved=false,popped=false;
  interactive(head,'balloon');balloon.style.touchAction='none';
  listen(head,'pointerdown',event=>{if(event.button!==0||popped)return;stop(event);cancelMove?.();const stage=root.getBoundingClientRect(),box=balloon.getBoundingClientRect();drag={id:event.pointerId,x:event.clientX,y:event.clientY,left:box.left-stage.left,top:box.top-stage.top,width:box.width,height:box.height,vx:0,vy:0,lastX:event.clientX,lastY:event.clientY,last:event.timeStamp};moved=false;body={x:drag.left,y:drag.top};balloon.style.animation='none';balloon.style.bottom='auto';balloon.style.transform='none';balloon.style.opacity='1';balloon.style.left=body.x+'px';balloon.style.top=body.y+'px';balloon.dataset.sceneState='held';head.setPointerCapture(event.pointerId);});
  listen(head,'pointermove',event=>{if(!drag||drag.id!==event.pointerId)return;stop(event);const dt=Math.max(.008,(event.timeStamp-drag.last)/1000);drag.vx=(event.clientX-drag.lastX)/dt;drag.vy=(event.clientY-drag.lastY)/dt;drag.lastX=event.clientX;drag.lastY=event.clientY;drag.last=event.timeStamp;moved||=Math.hypot(event.clientX-drag.x,event.clientY-drag.y)>4;body.x=Math.max(0,Math.min(root.clientWidth-drag.width,drag.left+event.clientX-drag.x));body.y=Math.max(0,Math.min(root.clientHeight-drag.height,drag.top+event.clientY-drag.y));balloon.style.left=body.x+'px';balloon.style.top=body.y+'px';});
  const release=event=>{if(!drag||drag.id!==event.pointerId)return;stop(event);let vx=Math.max(-250,Math.min(250,drag.vx)),vy=Math.max(-200,Math.min(200,drag.vy));drag=null;try{head.releasePointerCapture(event.pointerId);}catch{}if(!moved)return;balloon.dataset.sceneState='drifting';cancelMove=loop(dt=>{vx*=Math.exp(-1.2*dt);vy=-22+(vy+22)*Math.exp(-1.4*dt);body.x=Math.max(0,Math.min(root.clientWidth-balloon.clientWidth,body.x+vx*dt));body.y+=vy*dt;balloon.style.left=body.x+'px';balloon.style.top=body.y+'px';if(body.y< -balloon.clientHeight){balloon.removeAttribute('style');return false;}if(reduced())return false;});};
  listen(head,'pointerup',release);listen(head,'pointercancel',event=>{moved=true;release(event);});
  listen(head,'click',event=>{
   stop(event);if(moved){moved=false;return;}if(popped)return;popped=true;cancelMove?.();const box=balloon.getBoundingClientRect(),layer=overlay('balloon-pop-burst');
   balloon.dataset.popped='true';balloon.style.visibility='hidden';
   const scene=document.createElementNS(ns,'g'),rope=document.createElementNS(ns,'g'),string=balloon.querySelector('.balloon-string').cloneNode(true),rubber=document.createElementNS(ns,'g');
   const x=box.left-layer.box.left,y=box.top-layer.box.top,scale=box.width/90,inverse=90/Math.max(1,box.width);scene.setAttribute('transform',`translate(${x} ${y}) scale(${scale})`);layer.svg.append(scene);scene.append(rope,rubber);rope.append(string);rubber.classList.add('balloon-rubber-fragments');
   string.setAttribute('fill','none');string.setAttribute('stroke','currentColor');string.setAttribute('stroke-width','2');
   const pieces=Array.from({length:15},(_,i)=>{const shape=document.createElementNS(ns,'path'),a=i/15*Math.PI*2+(Math.random()-.5)*.4,speed=90+Math.random()*160;shape.setAttribute('d',i%2?'M-4-2Q0-7 5-3L2 4Q-2 2-4-2Z':'M-3-4Q4-3 5 2L-2 5Z');shape.setAttribute('fill','currentColor');shape.setAttribute('stroke','none');rubber.append(shape);return {shape,vx:Math.cos(a)*speed,vy:Math.sin(a)*speed-50,spin:(Math.random()-.5)*1000,life:.35+Math.random()*.35};});
   let t=0;loop(dt=>{t+=dt;const fall=450*t*t;rope.setAttribute('transform',`translate(${Math.sin(t*5)*8*inverse} ${fall*inverse}) rotate(${Math.sin(t*7)*Math.min(20,t*10)} 45 105)`);
    for(const piece of pieces){piece.shape.setAttribute('transform',`translate(${45+piece.vx*t*inverse} ${42+(piece.vy*t+400*t*t)*inverse}) rotate(${piece.spin*t}) scale(${Math.max(.15,Math.abs(Math.cos(t*10)))} 1)`);piece.shape.setAttribute('opacity',String(Math.max(0,1-t/piece.life)));}
    if(y+fall>layer.box.height+10||reduced()){layer.remove();popped=false;delete balloon.dataset.popped;balloon.removeAttribute('style');balloon.style.animationDelay='0s';return false;}
   });
  });
 }
 return()=>{alive=false;listeners.forEach(fn=>fn());frames.forEach(cancelAnimationFrame);timers.forEach(clearTimeout);animations.forEach(a=>a.cancel());layers.forEach(layer=>layer.remove());};
}
