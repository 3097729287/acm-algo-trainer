import {REWARDS} from './sticker-rewards.mjs';

// Collapse historic rarity aliases by theme without removing a single owned
// unit, gift, placement, claim or saved preset. Persist on the next normal write.
const themes=new Map(REWARDS.backgroundThemes.flatMap(theme=>[theme.id,...(theme.legacyThemes||[])].map(id=>[id,theme])));
export function canonicalBackgroundId(id){
 const match=/^background-(.+?)(?:-(common|rare|epic|legendary))?$/.exec(id||'');
 const theme=match&&themes.get(match[1]);return theme?`background-${theme.id}`:id;
}
export function normalizeBackgroundState(state){
 const entry=value=>{if(!value||typeof value!=='object')return value;const result={...value,...(value.stickerId?{stickerId:canonicalBackgroundId(value.stickerId)}:{})};if(result.stickerId?.startsWith('background-'))delete result.rarity;return result;};
 const opening=value=>{if(!value)return value;const result={...value,...(value.drops?{drops:value.drops.map(entry)}:{})};if(result.kind==='background')delete result.rarity;return result;};
 return {...state,units:(state.units||[]).map(entry),
  ...(state.discoveredStickers?{discoveredStickers:[...new Set(state.discoveredStickers.map(canonicalBackgroundId))]}:{}),
  ...(state.scenePresets?{scenePresets:state.scenePresets.map(preset=>({...preset,items:preset.items.map(entry)}))}:{}),
  ...(state.boxes?{boxes:Object.fromEntries(Object.entries(state.boxes).map(([id,box])=>[id,opening(box)]))}:{}),
  ...(state.backgroundRewards?{backgroundRewards:Object.fromEntries(Object.entries(state.backgroundRewards).map(([id,reward])=>[id,{...reward,...(reward.opening?{opening:opening(reward.opening)}:{})}]))}:{}),
 };
}
