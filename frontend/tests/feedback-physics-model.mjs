import assert from 'node:assert/strict';
import {fallStep,cloudStep} from '../src/lib/scenePhysics.js';
import {imageSurface} from '../src/lib/readingImageTheme.js';
import {original} from '../src/lib/problemIdentity.js';

for(const step of [.01,.02,.05]){
 let body={x:20,y:0,vx:10,vy:0};for(let t=0;t<1-1e-8;t+=step)body=fallStep(body,step,2000);
 assert(Math.abs(body.y-600)<1e-7);assert(Math.abs(body.vy-1200)<1e-7);assert(Math.abs(body.x-30)<1e-7);
}
let body={x:0,y:0,vx:0,vy:0};for(let t=0;t<1;t+=.01){body=fallStep(body,.01,300);if(body.landed)break;}
assert(body.landed);assert.equal(body.y,300);assert(Math.abs(body.impactSpeed-Math.sqrt(2*1200*300))<1e-6);
let cloud={x:100,y:60,width:80,vx:200,vy:-100,wind:20};const next=cloudStep(cloud,.05,600,300);
assert(next.x>cloud.x);assert(next.y<cloud.y);assert(next.vx<cloud.vx&&next.vx>20);
for(let t=0;t<10;t+=.05)cloud=cloudStep(cloud,.05,600,300);assert(Math.abs(cloud.vx-20)<1);assert(Math.abs(cloud.vy)<.001);
const pixels=(r,g,b,a)=>Array.from({length:120},(_,i)=>i<40?[r,g,b,a]:[0,0,0,0]).flat();
assert.equal(imageSurface(pixels(0,0,0,255)),'paper');assert.equal(imageSurface(pixels(255,255,255,255)),'ink');
assert.equal(imageSurface([0,0,0,0,0,0,0,0]),'native');assert.equal(imageSurface(Array(100).fill([0,0,0,255]).flat()),'native');
for(const [a,b] of [['https://poj.org/problem?id=1','https://poj.org/problem?id=2'],['https://acm.hdu.edu.cn/showproblem.php?pid=1','https://acm.hdu.edu.cn/showproblem.php?pid=2'],['https://onlinejudge.org/index.php?problem=1','https://onlinejudge.org/index.php?problem=2']])assert.notEqual(original({url:a}),original({url:b}));
assert.equal(original({url:'https://uva.onlinejudge.org/index.php?page=show_problem&problem=4222'}),original({url:'http://onlinejudge.org/index.php?problem=4222&Itemid=8'}));
console.log('PASS constant-gravity trajectory/contact, inertial cloud motion, transparent diagram contrast, query-based judge identities');
