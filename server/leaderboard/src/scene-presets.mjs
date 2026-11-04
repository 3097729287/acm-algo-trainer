export function resolveScene(preset,units){
 const used=new Set(),matched=[],missing=[];
 for(const entry of preset.items){
  const unit=units.find(unit=>unit.id===entry.unitId&&unit.stickerId===entry.stickerId&&!used.has(unit.id))||units.find(unit=>unit.stickerId===entry.stickerId&&!used.has(unit.id));
  if(unit){used.add(unit.id);matched.push({unit,entry});}else missing.push(entry.stickerId);
 }return {matched,missing};
}
export function giftSceneWarnings(state,unitId){
 const remaining=state.units.filter(unit=>unit.id!==unitId);
 return (state.scenePresets||[]).flatMap(preset=>{const before=resolveScene(preset,state.units).missing.length,after=resolveScene(preset,remaining).missing.length;return after>before?[{id:preset.id,name:preset.name,missing:after-before}]:[];});
}
