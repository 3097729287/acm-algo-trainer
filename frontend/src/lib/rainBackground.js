import {createRipples} from '../vendor/elementalfx/packages/ripples/src/index';
import {createWeather} from '../vendor/elementalfx/packages/weather/src/index';

const TILT=62*Math.PI/180;
const LAKE_TOP=.24;

// Static theme colour only. Both moving water and rain are rendered by the
// pinned MIT library; there are no local water/rain shaders or ring meshes.
function lakeColour(light){
 const canvas=document.createElement('canvas');canvas.width=32;canvas.height=256;
 const ctx=canvas.getContext('2d'),gradient=ctx.createLinearGradient(0,0,0,256);
 for(const [at,color]of light?[[0,'#c4d6df'],[.45,'#a9c3d0'],[1,'#87acbf']]:[[0,'#36576d'],[.45,'#2e4e65'],[1,'#223f55']])gradient.addColorStop(at,color);
 ctx.fillStyle=gradient;ctx.fillRect(0,0,32,256);return canvas;
}

export class RainBackground{
 constructor(host,{light=false,lightning=false,onFrame=()=>{}}={}){
  this.host=host;this.paused=true;this.destroyed=false;this.impactCount=0;this.lastImpact=null;
  this.stage=document.createElement('div');this.stage.className='rain-lake-stage';
  this.stage.style.background=light?'linear-gradient(#d9e4e9,#c4d6df 32%,#87acbf)':'linear-gradient(#243c50,#36576d 32%,#223f55)';
  this.surface=document.createElement('div');this.surface.className='rain-lake-surface';
  this.stage.append(this.surface);host.append(this.stage);this.resize();
  this.water=createRipples(this.surface,{
   source:lakeColour(light),fit:'fill',interactive:false,rain:false,
   resolution:1024,perturbance:.008,highlight:light?.035:.065,damping:.996,speed:.4,
   localCoordinates:true,maxPixelRatio:1,idleTimeout:30,
   respectReducedMotion:false,pauseOffscreen:false,
  });
  this.water.pause();
  this.weather=createWeather(this.stage,{
   preset:'rain',effects:lightning?['rain','lightning']:['rain'],seed:41729,
   rain:{density:.19,size:[9,17],opacity:light?[.25,.48]:[.38,.68],speed:.58,
    colors:light?['#4c718c']:['#bad9ea'],splashes:true,groundTop:LAKE_TOP+.025,depth:[.025,1]},
   wind:{speed:.025,direction:0,gusts:.08,turbulence:.04,pointer:0},
   lightning:{rate:1.5,flash:.045,color:'#b3cadb'},
   ripples:[{element:this.stage,drop:(x,y,radius,strength)=>this.impact(x,y,radius,strength)}],
   layer:'front',zIndex:1,maxPixelRatio:1,respectReducedMotion:false,pauseOffscreen:false,
   onFrame,
  });
  this.weather.pause();
  this.ready=Promise.all([this.water.ready,this.weather.ready]).then(([water,rain])=>{
   if(this.destroyed)return;
   if(!water||!rain)throw Error('Rain lake library unavailable');
   this.canvas=this.surface.querySelector('canvas');
  });
 }
 // Inverse of the CSS perspective below. Drops and ripples share the same
 // screen point at every depth, aspect ratio and device pixel ratio.
 lakePoint(x,y){
  const dy=y-this.horizon;if(dy<0)return null;
  const v=dy/(Math.cos(TILT)+dy*Math.sin(TILT)/this.perspective);
  const inverseScale=1-v*Math.sin(TILT)/this.perspective;
  const u=this.surfaceWidth/2+(x-this.width/2)*inverseScale;
  if(u<0||u>this.surfaceWidth||v<0||v>this.surfaceHeight)return null;
  return{x:u,y:v,scale:1/inverseScale};
 }
 impact(x,y,radius,strength){
  if(this.destroyed)return;
  const local=this.lakePoint(x,y);if(!local)return;
  this.water.drop(local.x,local.y,Math.max(2.5,radius/local.scale),strength*.55);
  this.impactCount++;this.lastImpact={screen:{x,y},local};
 }
 resize(){
  const box=this.host.getBoundingClientRect(),width=Math.max(1,box.width),height=Math.max(1,box.height);
  if(width===this.width&&height===this.height)return;
  this.width=width;this.height=height;this.horizon=height*LAKE_TOP;
  this.perspective=height*1.4;this.surfaceWidth=width*1.04;this.surfaceHeight=height*.94;
  this.stage.style.perspective=`${this.perspective}px`;
  this.stage.style.perspectiveOrigin=`50% ${this.horizon}px`;
  Object.assign(this.surface.style,{left:`${(width-this.surfaceWidth)/2}px`,top:`${this.horizon}px`,width:`${this.surfaceWidth}px`,height:`${this.surfaceHeight}px`});
  this.water?.updateSize();
 }
 setLightning(enabled){if(this.destroyed)return;if(enabled)this.weather.add('lightning');else this.weather.remove('lightning');}
 setPaused(paused){
  if(this.destroyed||paused===this.paused)return;this.paused=paused;
  if(paused){this.water.pause();this.weather.pause();}else{this.water.play();this.weather.play();}
 }
 snapshot(){return this.water.snapshot();}
 destroy(){if(this.destroyed)return;this.destroyed=true;this.paused=true;this.weather.destroy();this.water.destroy();this.stage.remove();}
}
