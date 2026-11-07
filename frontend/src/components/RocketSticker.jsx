import {useLayoutEffect,useRef} from 'react';
import {rocketFlight,ROCKET_FLIGHT_MS} from '@/lib/rocketFlight.js';

export default function RocketSticker({reaction,point,bounds,size,children}){
 const frame=useRef(null);
 useLayoutEffect(()=>{
  const node=frame.current;if(!node||!reaction)return;
  const media=matchMedia('(prefers-reduced-motion: reduce)');let animations=[];
  const stop=()=>{animations.forEach(animation=>animation.cancel());animations=[];};
  const preferences=()=>{if(media.matches||document.documentElement.dataset.motion==='off')stop();};
  if(!media.matches&&document.documentElement.dataset.motion!=='off'){
   const surface=node.closest('.sticker-surface')?.getBoundingClientRect();
   const frames=rocketFlight({...point,width:surface?.width||bounds.width,height:surface?.height||bounds.height,size});
   if(frames.length){
    animations.push(node.animate(frames.map(({offset,transform})=>({offset,transform})),{duration:ROCKET_FLIGHT_MS,easing:'linear'}));
    const plume=node.querySelector('.rocket-plume');
    if(plume)animations.push(plume.animate(frames.map(({offset,thrust})=>({offset,opacity:offset<.015?offset/.015:offset>.97?(1-offset)/.03:.9,
     transform:`scaleX(${.75+thrust*.25}) scaleY(${.3+thrust*.8})`})),{duration:ROCKET_FLIGHT_MS,easing:'linear'}));
   }
  }
  const observer=new MutationObserver(preferences);observer.observe(document.documentElement,{attributes:true,attributeFilter:['data-motion']});media.addEventListener('change',preferences);
  return()=>{stop();observer.disconnect();media.removeEventListener('change',preferences);};
 },[reaction?.id,point.x,point.y,point.angle,bounds.width,bounds.height,size]);
 return <span ref={frame} className="rocket-flight" data-rocket-flight={reaction?'active':undefined}>{children}</span>;
}
