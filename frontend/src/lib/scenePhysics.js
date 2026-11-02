export function fallStep(body,seconds,floor,gravity=1200){
 const dt=Math.max(0,Math.min(.05,seconds)),next={...body,x:body.x+body.vx*dt,y:body.y+body.vy*dt+.5*gravity*dt*dt,vy:body.vy+gravity*dt};
 if(next.y>=floor){
  const distance=Math.max(0,floor-body.y),time=(-body.vy+Math.sqrt(body.vy*body.vy+2*gravity*distance))/gravity;
  return {...next,y:floor,impactSpeed:Math.max(0,body.vy+gravity*Math.min(dt,time)),landed:true};
 }
 return {...next,landed:false};
}

export function cloudStep(body,seconds,width,height){
 const dt=Math.max(0,Math.min(.05,seconds)),vx=body.wind+(body.vx-body.wind)*Math.exp(-.8*dt),vy=body.vy*Math.exp(-1.6*dt);
 let x=body.x+(body.vx+vx)*.5*dt,y=body.y+(body.vy+vy)*.5*dt;
 if(x>width+body.width)x=-body.width;else if(x< -body.width*1.5)x=width;
 if(y<0||y>height)y=Math.max(0,Math.min(height,y));
 return {...body,x,y,vx,vy};
}
