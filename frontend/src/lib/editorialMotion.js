// A portable SVG remains an ordinary animated image outside ToBe. Its optional
// metadata contains passive image frames for the accessible step player.
const prefix='data:image/svg+xml;base64,',cache=new Map();
const image=value=>typeof value==='string'&&value.length<=220_000&&/^data:image\/svg\+xml;base64,[a-z\d+/=]+$/i.test(value);
const number=value=>typeof value==='number'&&Number.isFinite(value)&&Math.abs(value)<=5000;
const color=value=>typeof value==='string'&&/^(?:#[0-9a-f]{6}|none)$/i.test(value);
function readScene(value,count){
 if(!value)return null;
 if(value.version!==1||!number(value.width)||value.width<300||value.width>1600||!number(value.height)||value.height<150||value.height>1200||!image(value.background)||!Array.isArray(value.frames)||value.frames.length!==count)throw Error('Invalid scene');
 const frames=value.frames.map(frame=>{
  if(!Array.isArray(frame)||frame.length>100)throw Error('Too many moving objects');
  const ids=new Set();
  return Object.freeze(frame.map(item=>{
   if(!item||!['box','text','dot','line','rect'].includes(item.kind)||typeof item.id!=='string'||!/^[-\w:]{1,80}$/.test(item.id)||ids.has(item.id)||!number(item.x)||!number(item.y))throw Error('Invalid moving object');
   ids.add(item.id);const result={id:item.id,kind:item.kind,x:item.x,y:item.y};
   for(const name of ['w','h','r','u','v','width','size','opacity','delay','arc'])if(item[name]!==undefined){if(!number(item[name]))throw Error('Invalid geometry');result[name]=item[name];}
   for(const name of ['color','fill'])if(item[name]!==undefined){if(!color(item[name]))throw Error('Invalid paint');result[name]=item[name];}
   if(item.text!==undefined){if(typeof item.text!=='string'||item.text.length>120)throw Error('Invalid label');result.text=item.text;}
   if(item.anchor!==undefined){if(!['start','middle','end'].includes(item.anchor))throw Error('Invalid alignment');result.anchor=item.anchor;}
   for(const name of ['enter','exit'])if(item[name]!==undefined){if(!Array.isArray(item[name])||item[name].length!==2||!item[name].every(number))throw Error('Invalid motion origin');result[name]=Object.freeze([...item[name]]);}
   return Object.freeze(result);
  }));
 });
 return Object.freeze({width:value.width,height:value.height,background:value.background,frames:Object.freeze(frames)});
}
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
    result=Object.freeze({title:value.title,steps:Object.freeze(steps),scene:readScene(value.scene,steps.length)});
   }
  }
 }catch{/* Unrecognized metadata retains the ordinary image fallback. */}
 cache.set(source,result);while(cache.size>8)cache.delete(cache.keys().next().value);
 return result;
}
