import assert from 'node:assert/strict';
import {rocketFlight} from '../src/lib/rocketFlight.js';
let checks=0;
for(const [width,height,size] of [[900,960,100],[1000,420,56],[360,420,48]])for(const [x,y] of [[.5,.35],[.15,.15],[.85,.8]])for(const angle of [0,35,78,90,180,270,-125]){
 const frames=rocketFlight({width,height,x,y,angle,size}),radians=angle*Math.PI/180,cos=Math.cos(radians),sin=Math.sin(radians);assert(frames.length);
 assert(Math.abs(frames[0].x)<1e-10);assert(Math.abs(frames[0].y)<1e-10);assert.equal(frames.at(-1).x,0);assert.equal(frames.at(-1).y,0);
 assert(Math.abs(Math.abs(frames.at(-1).rotation)-360)<1e-6,'One complete turn finishes facing the saved heading');
 const first=frames.find(frame=>Math.hypot(frame.x,frame.y)>.05),direction={x:first.x*cos-first.y*sin,y:first.x*sin+first.y*cos};
 assert((direction.x*Math.sin(radians)-direction.y*Math.cos(radians))/Math.hypot(direction.x,direction.y)>.999,'Launch follows the actual nose direction');
 for(const frame of frames){const cx=x*width+frame.x*cos-frame.y*sin,cy=y*height+frame.x*sin+frame.y*cos;assert(cx-size*.7>=0&&cx+size*.7<=width&&cy-size*.7>=0&&cy+size*.7<=height,'The flight stays inside its surface');}
 const speed=(at)=>Math.hypot(frames[at+1].x-frames[at-1].x,frames[at+1].y-frames[at-1].y);
 assert(speed(55)>speed(15)*2,'Accelerates after ignition');assert(speed(140)>speed(174)*3,'Brakes smoothly before returning');
 checks++;
}
assert.deepEqual(rocketFlight({width:0,height:0,x:.5,y:.5,size:56}),[]);
console.log(JSON.stringify({ok:true,flightScenarios:checks,noseAligned:true,closedLoop:true,variableSpeed:true,bounded:true}));
