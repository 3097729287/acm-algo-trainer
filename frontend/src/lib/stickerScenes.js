import {stickerSize} from './stickerPlacement.js';
export function resolvePreset(preset,units){
 const used=new Set(),matched=[],missing=[];
 for(const entry of preset.items||[]){
  const unit=units.find(u=>u.id===entry.unitId&&u.stickerId===entry.stickerId&&!used.has(u.id))||units.find(u=>u.stickerId===entry.stickerId&&!used.has(u.id));
  if(unit){used.add(unit.id);matched.push({unit,entry});}else missing.push(entry.stickerId);
 }return {matched,missing};
}
export function previewPreset(preset,state){
 const {matched,missing}=resolvePreset(preset,state.units),entries=new Map(matched.map(({unit,entry})=>[unit.id,entry]));
 return {...state,activePresetId:preset.id,scene:{presetId:preset.id,missing},units:state.units.map(unit=>{const entry=entries.get(unit.id);return {...unit,placement:entry?{...entry.placement}:null,...(entry?.appearance?{appearance:{...entry.appearance}}:{})};})};
}
export function giftPresetWarnings(state,unitId){
 if(!state)return [];
 const remaining=state.units.filter(unit=>unit.id!==unitId);
 return (state.scenePresets||[]).flatMap(preset=>{const before=resolvePreset(preset,state.units).missing.length,after=resolvePreset(preset,remaining).missing.length;return after>before?[{name:preset.name,missing:after-before}]:[];});
}
// A small spatial index bounds work per cloud during pointer movement. Effects
// only change presentation; they never consume or rewrite inventory units.
export function stickerWeather(units,byId,bounds){
 const buckets=new Map(),clouds=[],cell=100,width=bounds.width||800,height=bounds.height||600;
 for(const unit of units){
  if(!unit.placement)continue;
  const item=byId.get(unit.stickerId),point=unit.placement,entry={unit,item,x:point.x*width,y:point.y*height};
  if(item?.shape==='cloud')clouds.push(entry);
  if(['drop','bolt','sun'].includes(item?.shape)){const key=Math.floor(entry.x/cell)+':'+Math.floor(entry.y/cell);if(!buckets.has(key))buckets.set(key,[]);buckets.get(key).push(entry);}
 }
 const effects=new Map(),hidden=new Set();
 for(const cloud of clouds){
  const radius=Math.max(100,stickerSize(bounds,cloud.unit.placement.scale,cloud.item)*1.3),range=Math.ceil(radius/cell),cx=Math.floor(cloud.x/cell),cy=Math.floor(cloud.y/cell),near=[];
  for(let x=cx-range;x<=cx+range;x++)for(let y=cy-range;y<=cy+range;y++)for(const entry of buckets.get(x+':'+y)||[])if(Math.hypot(cloud.x-entry.x,cloud.y-entry.y)<=radius)near.push(entry);
  const drops=near.filter(e=>e.item.shape==='drop'&&!hidden.has(e.unit.id));if(drops.length<3)continue;
  const bolt=near.find(e=>e.item.shape==='bolt'),sun=near.find(e=>e.item.shape==='sun');
  effects.set(cloud.unit.id,bolt?'thunder':sun?'rainbow':'rain');for(const drop of drops.slice(0,3))hidden.add(drop.unit.id);
 }
 return {effects,hidden};
}
