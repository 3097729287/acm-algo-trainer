import {BACKGROUND_THEMES,STICKER_RARITIES} from './stickerPolicy.js';
export const BACKGROUND_CARDS=Object.freeze(BACKGROUND_THEMES.map(theme=>({id:`background-${theme.id}-${theme.rarity}`,shape:`background-${theme.id}`,theme:theme.id,kind:'background',rarity:theme.rarity,title:theme.title,baseScale:1,minScale:1,maxScale:1})));
const themes=new Map(BACKGROUND_CARDS.map(item=>[item.theme,item]));
const reviewedRarities=new Map(Object.entries(STICKER_RARITIES));
export function canonicalStickerId(id){const match=/^background-(.+)-(common|rare|epic|legendary)$/.exec(id||'');return (match&&themes.get(match[1])?.id)||id;}
export function normalizeStickerInventory(value){
 if(!value?.catalogue||!value?.units)return value;
 const entry=unit=>({...unit,stickerId:canonicalStickerId(unit.stickerId)});
 const hasBackgrounds=value.capabilities?.backgrounds||value.catalogue.some(item=>item.kind==='background');
 return {...value,catalogue:[...value.catalogue.filter(item=>item.kind!=='background'||!themes.has(item.theme||item.shape?.replace('background-',''))).map(item=>({...item,rarity:reviewedRarities.get(item.id)||item.rarity})),...(hasBackgrounds?BACKGROUND_CARDS:[])],
  units:value.units.map(entry),scenePresets:(value.scenePresets||[]).map(preset=>({...preset,items:(preset.items||[]).map(entry)})),
  ...(value.discoveredStickers?{discoveredStickers:[...new Set(value.discoveredStickers.map(canonicalStickerId))]}:{}),
 };
}
