export const ROCKET_FLIGHT_MS=3400;

// Integrate a cosine throttle ramp: ignition, acceleration, cruise and braking.
function travel(t){
 const u=Math.max(0,Math.min(1,(t-.045)/.955)),up=.22,down=.28,area=1-(up+down)/2;
 if(u<up)return {distance:(u-up/Math.PI*Math.sin(Math.PI*u/up))/2/area,thrust:(1-Math.cos(Math.PI*u/up))/2};
 if(u>1-down){const left=1-u;return {distance:1-(left-down/Math.PI*Math.sin(Math.PI*left/down))/2/area,thrust:(1-Math.cos(Math.PI*left/down))/2};}
 return {distance:(u-up/2)/area,thrust:1};
}

export function rocketFlight({width,height,x,y,angle=0,size=56}){
 if(![width,height,x,y,size,angle].every(Number.isFinite)||width<=0||height<=0)return [];
 const radians=angle*Math.PI/180,heading={x:Math.sin(radians),y:-Math.cos(radians)},origin={x:x*width,y:y*height},margin=size*Math.SQRT1_2+2;
 const a=Math.min(240,Math.min(width,height)*.3),b=a*.66;
 const options=[1,-1].map(side=>{
  const normal={x:Math.cos(radians)*side,y:Math.sin(radians)*side};let scale=1;
  for(const [axis,extent] of [['x',width],['y',height]]){
   const center=normal[axis]*b,radius=Math.hypot(heading[axis]*a,normal[axis]*b),low=center-radius,high=center+radius;
   if(low<0)scale=Math.min(scale,(origin[axis]-margin)/-low);
   if(high>0)scale=Math.min(scale,(extent-margin-origin[axis])/high);
  }
  return {side,scale:Math.max(0,scale)};
 });
 const {side,scale}=options.sort((first,second)=>second.scale-first.scale)[0];
 if(scale<.015)return [];
 let previousAngle=0;
 return Array.from({length:181},(_,index)=>{
  const offset=index/180,{distance,thrust}=travel(offset),phase=distance*Math.PI*2;
  // The original artwork points up. Its parent already carries the saved rotation.
  const dx=side*b*(1-Math.cos(phase))*scale,dy=-a*Math.sin(phase)*scale;
  let rotation=Math.atan2(side*b*Math.sin(phase),a*Math.cos(phase))*180/Math.PI;
  while(rotation-previousAngle>180)rotation-=360;
  while(rotation-previousAngle< -180)rotation+=360;
  previousAngle=rotation;
  return {offset,x:index===180?0:dx,y:index===180?0:dy,rotation,thrust,
   transform:`translate(${index===180?0:dx}px,${index===180?0:dy}px) rotate(${rotation}deg)`};
 });
}
