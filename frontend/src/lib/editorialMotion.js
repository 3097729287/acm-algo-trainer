// A portable SVG remains an ordinary animated image outside ToBe. Its optional
// metadata contains passive image frames for the accessible step player.
const prefix='data:image/svg+xml;base64,',cache=new Map();
export function readEditorialMotion(source){
 if(typeof source!=='string'||!source.startsWith(prefix)||source.length>2_000_000)return null;
 if(cache.has(source))return cache.get(source);
 let result=null;
 try{
  const bytes=Uint8Array.from(atob(source.slice(prefix.length)),char=>char.charCodeAt(0));
  const svg=new TextDecoder('utf-8',{fatal:true}).decode(bytes);
  if(svg.includes('id="tb-editorial-motion"')){
   const document=new DOMParser().parseFromString(svg,'image/svg+xml');
   const element=document.querySelector('metadata[id="tb-editorial-motion"]');
   const value=JSON.parse(element?.textContent||'null');
   if(!document.querySelector('parsererror')&&value?.version===1&&typeof value.title==='string'&&value.title.length<=100&&Array.isArray(value.steps)&&value.steps.length>=2&&value.steps.length<=48){
    const steps=value.steps.map(step=>{
     if(typeof step.caption!=='string'||step.caption.length>220||typeof step.image!=='string'||!step.image.startsWith(prefix)||step.image.length>220_000||!/^data:image\/svg\+xml;base64,[a-z\d+/=]+$/i.test(step.image))throw Error('Invalid motion frame');
     return Object.freeze({caption:step.caption,image:step.image,duration:Math.min(8000,Math.max(900,Number(step.duration)||2100))});
    });
    result=Object.freeze({title:value.title,steps:Object.freeze(steps)});
   }
  }
 }catch{/* Unrecognized metadata retains the ordinary image fallback. */}
 cache.set(source,result);while(cache.size>8)cache.delete(cache.keys().next().value);
 return result;
}
