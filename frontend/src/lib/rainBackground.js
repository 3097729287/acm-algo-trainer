import {RainRipple} from 'rain-ripple';
import {RainScene} from '../vendor/rain-lake/scene.js';

// Rain Lake owns every rain stroke, impact and propagating water wave. Keep its
// source unchanged; adapt only placement, damping, palette and host lifecycle.
export class RainBackground{
 constructor(host,{light=false,lightning=false,onFrame=()=>{}}={}){
  this.host=host;this.onFrame=onFrame;this.paused=true;this.destroyed=false;
  this.canvas=document.createElement('canvas');this.canvas.style.cssText='position:absolute;inset:0;width:100%;height:100%;pointer-events:none';this.canvas.style.filter=light?'invert(1) hue-rotate(180deg)':'';host.append(this.canvas);
  this.engine=new RainScene(this.canvas,{width:1,height:1});
  const spawn=this.engine._spawn.bind(this.engine);
  this.engine._spawn=()=>{const count=this.engine.rain.length;spawn();if(this.engine.rain.length===count)return;const drop=this.engine.rain.at(-1),fall=drop.fall;drop.z=this.engine.depth*.42+drop.z*.58;drop.fall=Math.max(fall,this.engine.project(drop.x,drop.z).y+this.engine.height*.12);drop.duration*=drop.fall/fall;};
  // The optional flash is the pinned rain-ripple routine, without its ground,
  // rain renderer, additional canvas or independent animation loop.
  this.flash={ctx:this.engine.ctx,width:1,height:1,_lightning:0,options:{lightning}};
  this.tick=now=>{if(this.paused||this.destroyed)return;this.raf=requestAnimationFrame(this.tick);const elapsed=(now-this.lastFrame)/1000;if(elapsed<1/24)return;const dt=Math.min(elapsed,.1);this.lastFrame=now;this.engine.step(dt);this.engine.draw();RainRipple.prototype._updateLightning.call(this.flash);this.onFrame(dt);};
  this.resize();
 }
 resize(){
  const box=this.host.getBoundingClientRect(),width=Math.max(1,box.width),height=Math.max(1,box.height);if(this.width===width&&this.height===height)return;this.width=width;this.height=height;
  this.engine.resize(width,height,Math.min(devicePixelRatio||1,1.25));this.engine.fish.draw=()=>{};
  const wave=this.engine.wave;wave.current.fill(0);wave.previous.fill(0);wave.next.fill(0);this.engine.rain=[];this.engine.splashes=[];this.engine.impactCount=0;
  // Lengthen the upstream rings while retaining its absorbing shore boundary.
  for(let i=0;i<wave.damping.length;i++)if(wave.damping[i]<=wave.fixedDt*.66)wave.damping[i]*=.45;
  this.engine.rainRate*=.65;for(let i=0;i<180;i++)this.engine.step(1/30);
  this.flash.width=width;this.flash.height=height;this.engine.draw();
 }
 setLightning(enabled){this.flash.options.lightning=enabled===true;if(!enabled){this.flash._lightning=0;if(this.paused)this.engine.draw();}}
 setPaused(paused){if(this.paused===paused||this.destroyed)return;this.paused=paused;if(paused)cancelAnimationFrame(this.raf);else{this.lastFrame=performance.now();this.raf=requestAnimationFrame(this.tick);}}
 destroy(){this.paused=true;this.destroyed=true;cancelAnimationFrame(this.raf);this.canvas.remove();}
}
