import {RainRipple} from 'rain-ripple';
import {createWaterScene} from '../vendor/cheapwater/scene.js';

// The upstream scene owns drops, impacts, expanding rings and both render passes.
export class RainBackground{
 constructor(host,{light=false,lightning=false,onFrame=()=>{}}={}){
  this.host=host;this.onFrame=onFrame;this.paused=true;this.destroyed=false;
  this.engine=createWaterScene(host);this.canvas=this.engine.renderer.domElement;
  this.canvas.style.filter=light?'invert(1) hue-rotate(180deg)':'';
  this.overlay=document.createElement('div');this.overlay.style.cssText='position:absolute;inset:0;pointer-events:none';host.append(this.overlay);
  const overlay=this.overlay;
  this.flash={width:1,height:1,_lightning:0,options:{lightning},ctx:{fillStyle:'',fillRect(){overlay.style.background=this.fillStyle;}}};
  this.tick=now=>{if(this.paused||this.destroyed)return;this.raf=requestAnimationFrame(this.tick);const elapsed=(now-this.lastFrame)/1000;if(elapsed<1/24)return;const dt=Math.min(elapsed,.1);this.lastFrame=now;this.engine.step(dt);this.engine.draw();this.overlay.style.background='';RainRipple.prototype._updateLightning.call(this.flash);this.onFrame(dt);};
  this.resize();this.ready=this.engine.ready.then(()=>{if(this.destroyed)return;for(let i=0;i<210;i++)this.engine.step(1/30);this.engine.draw();});
 }
 resize(){const box=this.host.getBoundingClientRect(),width=Math.max(1,box.width),height=Math.max(1,box.height);if(this.width===width&&this.height===height)return;this.width=width;this.height=height;this.engine.resize(width,height);this.flash.width=width;this.flash.height=height;}
 setLightning(enabled){this.flash.options.lightning=enabled===true;if(!enabled){this.flash._lightning=0;this.overlay.style.background='';}}
 setPaused(paused){if(this.paused===paused||this.destroyed)return;this.paused=paused;if(paused)cancelAnimationFrame(this.raf);else{this.lastFrame=performance.now();this.raf=requestAnimationFrame(this.tick);}}
 destroy(){this.paused=true;this.destroyed=true;cancelAnimationFrame(this.raf);this.engine.destroy();this.overlay.remove();}
}
