import {REWARDS} from './sticker-rewards.mjs';

// Collapse historic rarity aliases by theme without removing a single owned
// unit, gift, placement, claim or saved preset. Persist on the next normal write.
const themes=new Map(REWARDS.backgroundThemes.map(theme=>[theme.id,theme]));
export function canonicalBackgroundId(id){
 const match=/^background-(.+)-(common|rare|epic|legendary)$/.exec(id||'');
 const theme=match&&themes.get(match[1]);
 return theme?`background-${theme.id}-${theme.rarity}`:id;
}
export function normalizeBackgroundState(state){
 const entry=value=>value&&typeof value==='object'?{...value,...(value.stickerId?{stickerId:canonicalBackgroundId(value.stickerId)}:{})}:value;
 const opening=value=>value?{...value,...(value.drops?{drops:value.drops.map(entry)}:{})}:value;
 return {...state,units:(state.units||[]).map(entry),
  ...(state.discoveredStickers?{discoveredStickers:[...new Set(state.discoveredStickers.map(canonicalBackgroundId))]}:{}),
  ...(state.scenePresets?{scenePresets:state.scenePresets.map(preset=>({...preset,items:preset.items.map(entry)}))}:{}),
  ...(state.boxes?{boxes:Object.fromEntries(Object.entries(state.boxes).map(([id,box])=>[id,opening(box)]))}:{}),
  ...(state.backgroundRewards?{backgroundRewards:Object.fromEntries(Object.entries(state.backgroundRewards).map(([id,reward])=>[id,{...reward,...(reward.opening?{opening:opening(reward.opening)}:{})}]))}:{}),
 };
}
