import {RainRipple} from 'rain-ripple';

// Lifecycle and theme adaptation only. The upstream library owns the horizon,
// depth-scaled rain, impact splashes and expanding rings.
export class RainBackground{
 constructor(host,{light=false,lightning=false,onFrame=()=>{}}={}){
  this.engine=new RainRipple(host,{rainCount:130,groundTop:.5,wind:-.35,lightning,autoStart:false,zIndex:0});
  this.canvas=this.engine.canvas;this.canvas.style.filter=light?'invert(1) hue-rotate(180deg)':'';this.paused=true;
  const tick=this.engine._tick.bind(this.engine);this.engine._tick=now=>{const running=this.engine._running,dt=Math.max(0,Math.min((now-this.engine._lastTime)/1000,.05));tick(now);if(running)onFrame(dt);};
  this.still();
 }
 still(){const now=performance.now();this.engine._running=true;this.engine._lastTime=now;this.engine._tick(now);this.engine.stop();}
 resize(){this.engine.resize();if(this.paused)this.still();}
 setLightning(enabled){this.engine.setOptions({lightning:enabled});if(!enabled){this.engine._lightning=0;if(this.paused)this.still();}}
 setPaused(paused){if(this.paused===paused)return;this.paused=paused;paused?this.engine.stop():this.engine.start();}
 destroy(){this.paused=true;this.engine.destroy();}
}
