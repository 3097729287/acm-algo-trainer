import {WaveField} from './wave-field.js?v=0.1.0';
import {FishShadows} from './fish-shadows.js?v=0.1.0';

export const CAMERA_TILT=Math.PI/4;
const FLAT=Math.sin(CAMERA_TILT),MAX_RAIN=64;
class Random{
 constructor(seed){this.state=seed>>>0;}
 next(){this.state=(Math.imul(this.state,1664525)+1013904223)>>>0;return this.state/4294967296;}
}
const hash=(x,y)=>{let n=Math.imul(x+17,374761393)^Math.imul(y+31,668265263);n=Math.imul(n^(n>>>13),1274126177);return ((n^(n>>>16))>>>0)/4294967296;};

export class RainScene{
 constructor(canvas,{width=1280,height=720,dpr=1,seed=27}={}){
  this.canvas=canvas;this.ctx=canvas.getContext('2d',{alpha:false});this.random=new Random(seed);
  this.waveCanvas=(canvas.ownerDocument||document).createElement('canvas');this.waveContext=this.waveCanvas.getContext('2d');
  this.fish=new FishShadows(seed+6);this.wave=new WaveField({width:1,depth:1,cellSize:5});this.time=0;this.resize(width,height,dpr);
 }
 resize(width,height,dpr=1){
  this.width=Math.max(1,width);this.height=Math.max(1,height);this.depth=this.height/FLAT;this.dpr=Math.min(1.25,Math.max(1,dpr||1));
  this.canvas.width=Math.round(this.width*this.dpr);this.canvas.height=Math.round(this.height*this.dpr);
  this.wave.resize({width:this.width,depth:this.depth,cellSize:5});
  this.waveCanvas.width=this.wave.cols;this.waveCanvas.height=this.wave.rows;this.wavePixels=this.waveContext.createImageData(this.wave.cols,this.wave.rows);
  this.fish.resize(this.width,this.depth);this.rain=[];this.splashes=[];this.impactCount=0;this.spawnDebt=0;
  this.rainRate=15*Math.min(1.25,Math.max(.65,this.width*this.height/921600));
  this.samples=[];const cw=this.width<600?5.2:6.3,ch=this.width<600?7.2:8.4;this.glyphSize=ch*.93;
  for(let y=ch*.5,row=0;y<this.height;y+=ch,row++)for(let x=cw*.5,col=0;x<this.width;x+=cw,col++){
   const i=Math.min(this.wave.cols-2,Math.max(1,Math.round(x/this.width*(this.wave.cols-1))));
   const j=Math.min(this.wave.rows-2,Math.max(1,Math.round(y/this.height*(this.wave.rows-1))));
   this.samples.push({x,y,k:j*this.wave.cols+i,noise:hash(col,row)});
  }
  this.ctx.setTransform(this.dpr,0,0,this.dpr,0,0);
  this.base=this.ctx.createLinearGradient(0,0,this.width*.15,this.height);this.base.addColorStop(0,'#27363b');this.base.addColorStop(.42,'#1c2b31');this.base.addColorStop(1,'#0e1c23');
  this.edge=this.ctx.createRadialGradient(this.width*.48,this.height*.43,this.width*.1,this.width*.5,this.height*.5,Math.max(this.width,this.height)*.74);this.edge.addColorStop(0,'rgba(1,9,14,0)');this.edge.addColorStop(1,'rgba(1,9,14,.34)');
  for(let i=0;i<96;i++)this.step(1/30);
 }
 project=(x,z,depth=0)=>({x,y:z*FLAT+depth*.6,scale:1});
 _spawn(){
  if(this.rain.length>=MAX_RAIN)return;
  const r=this.random,x=r.next()*this.width,z=(.015+r.next()*.97)*this.depth,duration=.36+r.next()*.43,near=z/this.depth;
  const fall=190+r.next()*140+near*80;
  this.rain.push({x,z,age:0,duration,fall,length:12+r.next()*19+near*9,alpha:.18+r.next()*.10+near*.06,force:.30+r.next()*.5,drift:(r.next()-.5)*3});
 }
 step(dt){
  const delta=Math.min(.1,Math.max(0,Number.isFinite(dt)?dt:0));this.time+=delta;
  this.spawnDebt+=delta*this.rainRate;while(this.spawnDebt>=1){this.spawnDebt--;this._spawn();}
  for(let i=this.rain.length-1;i>=0;i--){const drop=this.rain[i];drop.age+=delta;if(drop.age>=drop.duration){const radius=Math.max(4.8,Math.min(this.wave.cellX,this.wave.cellZ)*.9);this.wave.disturb(drop.x,drop.z,-drop.force,radius);this.wave.disturb(drop.x,drop.z,drop.force/(1.7*1.7),radius*1.7);this.impactCount++;if(this.splashes.length<24)this.splashes.push({x:drop.x,y:drop.z*FLAT,age:0,life:.15});this.rain.splice(i,1);}}
  for(let i=this.splashes.length-1;i>=0;i--){this.splashes[i].age+=delta;if(this.splashes[i].age>this.splashes[i].life)this.splashes.splice(i,1);}
  this.wave.step(delta);this.fish.step(delta,this.time);
 }
 _surface(){
  const w=this.wave,a=w.current,n=w.cols,m=w.rows,data=this.wavePixels.data;data.fill(0);
  for(let j=1;j<m-1;j++)for(let i=1;i<n-1;i++){
   const k=j*n+i,slope=(a[k+1]-a[k-1])*.35+(a[k+n]-a[k-n])*.78;
   const glow=Math.min(.26,Math.abs(slope)*3.4);if(glow<.003)continue;
   const p=k*4;if(slope>=0){data[p]=172;data[p+1]=191;data[p+2]=193;}else{data[p]=0;data[p+1]=9;data[p+2]=17;}
   data[p+3]=Math.round(glow*255);
  }
  this.waveContext.putImageData(this.wavePixels,0,0);this.ctx.imageSmoothingEnabled=true;this.ctx.drawImage(this.waveCanvas,0,0,this.width,this.height);
  const ctx=this.ctx;ctx.font=`${this.glyphSize}px ui-monospace,Menlo,Consolas,monospace`;ctx.textAlign='center';ctx.textBaseline='middle';
  for(const s of this.samples){
   const k=s.k,h=a[k],dx=a[k+1]-a[k-1],dz=a[k+n]-a[k-n];
   const brightness=dx*.25+dz*.78;
   if(Math.abs(brightness)<.006||Math.abs(h)<.004)continue;
   const alpha=Math.min(.32,Math.abs(brightness)*4.5)*(.65+s.noise*.35);if(alpha<.022)continue;
   const flat=Math.abs(dx)<Math.abs(dz)*.65,glyph=flat?(Math.abs(h)>.035?'_':'-'):(dx*dz>0?'.':':');
   ctx.globalAlpha=alpha;ctx.fillStyle=brightness>0?'#b2c4c6':'#07151c';ctx.fillText(glyph,s.x,s.y);
  }ctx.globalAlpha=1;
 }
 draw(){
  const ctx=this.ctx;ctx.setTransform(this.dpr,0,0,this.dpr,0,0);ctx.globalAlpha=1;ctx.fillStyle=this.base;ctx.fillRect(0,0,this.width,this.height);
  this.fish.draw(ctx,this.project,this.time);
  // Broad reflected storm light, without a skyline or drawn cloud outlines.
  const drift=Math.sin(this.time*.018)*this.width*.08;
  const light=ctx.createRadialGradient(this.width*.46+drift,this.height*.16,0,this.width*.46+drift,this.height*.16,this.width*.7);light.addColorStop(0,'rgba(126,147,147,.045)');light.addColorStop(1,'rgba(126,147,147,0)');ctx.fillStyle=light;ctx.fillRect(0,0,this.width,this.height);
  this._surface();
  ctx.lineWidth=.6;ctx.strokeStyle='#a8b7b9';
  for(const drop of this.rain){const p=drop.age/drop.duration,end=drop.z*FLAT-(1-p)*drop.fall,x=drop.x+(1-p)*drop.drift;ctx.globalAlpha=drop.alpha;ctx.beginPath();ctx.moveTo(x,end-drop.length);ctx.lineTo(x-.2,end);ctx.stroke();}
  for(const splash of this.splashes){const f=1-splash.age/splash.life;ctx.globalAlpha=f*.22;ctx.fillStyle='#a5b7bb';ctx.fillRect(splash.x-.5,splash.y-.5,1,1);}
  ctx.globalAlpha=1;ctx.fillStyle=this.edge;ctx.fillRect(0,0,this.width,this.height);
 }
 get pixelBytes(){return this.canvas.width*this.canvas.height*4+this.waveCanvas.width*this.waveCanvas.height*4;}
}
