import {BACKGROUND_THEMES,STICKER_RARITIES} from './stickerPolicy.js';
export const BACKGROUND_CARDS=Object.freeze(BACKGROUND_THEMES.map(theme=>({id:`background-${theme.id}`,shape:`background-${theme.id}`,theme:theme.id,kind:'background',title:theme.title,baseScale:1,minScale:1,maxScale:1})));
const aliases=new Map(BACKGROUND_THEMES.flatMap(theme=>[theme.id,...(theme.legacyThemes||[])].map(id=>[id,`background-${theme.id}`])));
const reviewedRarities=new Map(Object.entries(STICKER_RARITIES));
export function canonicalStickerId(id){const theme=(id||'').replace(/^background-/,'').replace(/-(common|rare|epic|legendary)$/,'');return id?.startsWith('background-')&&aliases.has(theme)?aliases.get(theme):id;}
export function normalizeStickerInventory(value){
 if(!value?.catalogue||!value?.units)return value;
 const entry=unit=>({...unit,stickerId:canonicalStickerId(unit.stickerId)});
 const hasBackgrounds=value.capabilities?.backgrounds||value.catalogue.some(item=>item.kind==='background');
 return {...value,catalogue:[...value.catalogue.filter(item=>item.kind!=='background').map(item=>({...item,rarity:reviewedRarities.get(item.id)||item.rarity})),...(hasBackgrounds?BACKGROUND_CARDS:[])],
  units:value.units.map(entry),scenePresets:(value.scenePresets||[]).map(preset=>({...preset,items:(preset.items||[]).map(entry)})),
  ...(value.discoveredStickers?{discoveredStickers:[...new Set(value.discoveredStickers.map(canonicalStickerId))]}:{}),
 };
}
