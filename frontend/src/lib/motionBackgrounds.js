import {BACKGROUND_THEMES} from './stickerPolicy.js';
import threeURL from '../vendor/vanta/three.r134.min.js?url';
const effects=import.meta.glob('../vendor/vanta/vanta.*.min.js',{eager:true,query:'?url',import:'default'});
const images=import.meta.glob('../assets/backgrounds/*.jpg',{eager:true,query:'?url',import:'default'});
export const MOTION_SCENES=BACKGROUND_THEMES.map(theme=>({id:theme.id,name:theme.title,collection:theme.title,source:theme.id==='meteors'?'Web Motion Showcase':theme.id==='rainfall'?'CheapWater':'Vanta.js',hint:theme.id==='meteors'?'蓝白细尾流星':theme.id==='rainfall'?'雨落湖面，多圈涟漪缓缓扩散':'移动鼠标改变视角',colors:['#071321','#16475e']}));
export const backgroundThumbnail=id=>images[`../assets/backgrounds/${id}.jpg`];
const scripts=new Map();
function script(url){if(!scripts.has(url))scripts.set(url,new Promise((resolve,reject)=>{const tag=document.createElement('script');tag.src=url;tag.onload=resolve;tag.onerror=()=>{scripts.delete(url);tag.remove();reject(Error('Background library unavailable'));};document.head.append(tag);}));return scripts.get(url);}
const options={
 waves:{color:0x125f86,shininess:35,waveHeight:18,waveSpeed:.65,zoom:.85},
 clouds:{skyColor:0x4488af,cloudColor:0x94aabb,cloudShadowColor:0x263e59,sunColor:0xf6b89e,sunGlareColor:0xcba9a1,sunlightColor:0xf8d6c4,speed:.65},
 fog:{highlightColor:0x9b85d5,midtoneColor:0x316c97,lowlightColor:0x142346,baseColor:0x090f22,blurFactor:.55,speed:1.2,zoom:.85},
 birds:{backgroundColor:0x091c2b,color1:0x65cfc4,color2:0x9b99df,colorMode:'lerp',birdSize:1.2,wingSpan:23,speedLimit:4,separation:40,alignment:35,cohesion:25,quantity:3},
 net:{backgroundColor:0x081522,color:0x52a8bd,points:10,maxDistance:22,spacing:18},
};
// Lifecycle only: all geometry, shaders and motion come from the upstream library.
export class MotionScene{
 constructor(host,{id='waves',paused=false,lightning=false,onError=()=>{}}={}){
  this.host=host;this.paused=paused;this.lightning=lightning;this.onError=onError;this.generation=0;this.frames=0;this.time=0;this.destroyed=false;host.classList.add('motion-background');
  this.visibility=()=>this.sync();document.addEventListener('visibilitychange',this.visibility);
  this.media=matchMedia('(prefers-reduced-motion: reduce)');this.media.addEventListener('change',this.visibility);
  this.theme=document.documentElement.dataset.theme;
  this.observer=new MutationObserver(()=>{const theme=document.documentElement.dataset.theme;if(theme!==this.theme){this.theme=theme;this.ready=this.setScene(this.id);}else this.sync();});this.observer.observe(document.documentElement,{attributes:true,attributeFilter:['data-theme','data-motion']});
  this.resizeObserver=new ResizeObserver(()=>{if(this.effect){this.effect.resize();this.render();}this.rain?.resize();});this.resizeObserver.observe(host);
  this.ready=this.setScene(id);
 }
 get stopped(){return this.paused||document.hidden||this.media.matches||document.documentElement.dataset.motion==='off';}
 async setScene(id){
  const ticket=++this.generation;this.dispose();this.id=id;this.host.dataset.scene=id;this.host.dataset.library=id==='meteors'?'web-motion-showcase':'vanta';this.host.dataset.ready='loading';
  const preview=backgroundThumbnail(id);this.host.style.backgroundImage=preview?`url("${preview}")`:'';
  if(id==='meteors'){this.meteors();this.host.dataset.ready='true';this.sync();return;}
  if(id==='rainfall'){
   try{const {RainBackground}=await import('./rainBackground.js');if(this.destroyed||ticket!==this.generation)return;
    const rain=new RainBackground(this.host,{light:document.documentElement.dataset.theme==='light',lightning:this.lightning,onFrame:dt=>{this.frames++;this.time+=dt;}});this.rain=rain;await rain.ready;if(this.destroyed||ticket!==this.generation)return;
    this.host.dataset.library='cheapwater';this.host.dataset.ready='true';this.host.style.backgroundImage='';this.sync();
   }catch(error){if(!this.destroyed&&ticket===this.generation){this.dispose();this.host.dataset.ready='fallback';this.onError(error);}}return;
  }
  try{
   await script(threeURL);const url=effects[`../vendor/vanta/vanta.${id}.min.js`];if(!url)throw Error('Unknown background');await script(url);
   if(this.destroyed||ticket!==this.generation)return;
   const light=document.documentElement.dataset.theme==='light';
   const effect=window.VANTA[id.toUpperCase()]({el:this.host,THREE:window.THREE,...options[id],...(light&&['net','birds'].includes(id)?{backgroundColor:0xeaf1f6}:{}),minHeight:1,minWidth:1,scale:1.5,scaleMobile:2,mouseControls:true,touchControls:false,gyroControls:false});
   this.effect=effect;if(!effect.renderer)throw Error('WebGL unavailable');
   const update=effect.onUpdate;effect.onUpdate=(...args)=>{this.frames++;this.time=(effect.t||0)/60;update?.apply(effect,args);};
   // Paused mouse input must never redraw or restart the GPU loop.
   const move=effect.triggerMouseMove.bind(effect);effect.triggerMouseMove=(...args)=>{if(!this.stopped)move(...args);};
   this.host.dataset.ready='true';this.host.style.backgroundImage='';this.sync();this.render();
  }catch(error){if(!this.destroyed&&ticket===this.generation){this.dispose();this.host.dataset.ready='fallback';this.host.style.backgroundImage=preview?`url("${preview}")`:'';this.onError(error);}}
 }
 render(){if(this.effect?.renderer&&this.effect?.scene)this.effect.renderer.render(this.effect.scene,this.effect.camera);}
 sync(){const stopped=this.stopped;this.host.dataset.paused=String(stopped);this.rain?.setPaused(stopped);const effect=this.effect;if(!effect)return;if(stopped){cancelAnimationFrame(effect.req);effect.req=null;}else if(effect.req==null){effect.prevNow=performance.now();effect.animationLoop();}}
 setLightning(value){this.lightning=value===true;this.host.dataset.lightning=String(this.lightning);this.rain?.setLightning(this.lightning);}
 setPaused(value){this.paused=value;this.sync();}
 snapshot(){this.render();return this.rain?.canvas.toDataURL('image/jpeg',.88)||this.effect?.renderer?.domElement.toDataURL('image/jpeg',.88)||backgroundThumbnail(this.id)||'';}
 meteors(){const sky=document.createElement('div');sky.className='meteors-background';const stars=document.createElementNS('http://www.w3.org/2000/svg','svg');stars.setAttribute('viewBox','0 0 1600 1000');stars.classList.add('meteors-background-stars');let seed=5;const random=()=>{seed=(seed*16807)%2147483647;return seed/2147483647;};for(let i=0;i<180;i++){const star=document.createElementNS(stars.namespaceURI,'circle');for(const [key,value]of Object.entries({cx:random()*1600,cy:random()*1000,r:.3+random()*1.2,opacity:.2+random()*.8}))star.setAttribute(key,value);stars.append(star);}const rays=document.createElement('div');rays.className='meteors-background-rays';for(let i=0;i<28;i++){const ray=document.createElement('span');ray.className='meteors-background-ray';ray.style.cssText=`top:${random()*70-10}%;left:${random()*90+10}%;--meteor-tail:${160+random()*120}px;animation-duration:${1+random()*1.2}s;animation-delay:${-random()*6}s`;rays.append(ray);}sky.append(stars,rays);this.host.append(sky);}
 dispose(){this.rain?.destroy();this.rain=null;const effect=this.effect;this.effect=null;if(effect){cancelAnimationFrame(effect.req);const renderer=effect.renderer;effect.destroy();renderer?.dispose();renderer?.forceContextLoss();}this.host.replaceChildren();}
 destroy(){this.destroyed=true;this.generation++;this.dispose();this.observer.disconnect();this.resizeObserver.disconnect();this.media.removeEventListener('change',this.visibility);document.removeEventListener('visibilitychange',this.visibility);}
}
