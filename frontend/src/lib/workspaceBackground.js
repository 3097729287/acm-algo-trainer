import {canonicalStickerId,normalizeStickerInventory} from './stickerCatalogue.js';
export function chooseBuiltinBackground(prefs,id){return {...prefs,backdrop:id,learningPaths:{...prefs.learningPaths,workspaceBackground:{kind:id==='custom'?'image':'builtin',id}}};}
export function chooseRewardBackground(prefs,id){return {...prefs,learningPaths:{...prefs.learningPaths,workspaceBackground:{kind:'reward',id:canonicalStickerId(id)}}};}
export function ownedBackgrounds(inventory,owner){
 if(!inventory||inventory.owner!==owner||!Array.isArray(inventory.units)||!Array.isArray(inventory.catalogue))return [];
 const value=normalizeStickerInventory(inventory),counts=new Map();for(const unit of value.units)counts.set(unit.stickerId,(counts.get(unit.stickerId)||0)+1);
 return value.catalogue.filter(item=>item.kind==='background'&&counts.has(item.id)).map(item=>({...item,count:counts.get(item.id),unlimited:value.unlimited===true}));
}
export function workspaceBackground(prefs,inventory,owner){
 const selected=prefs.learningPaths?.workspaceBackground;
 if(selected?.kind==='reward'){const item=ownedBackgrounds(inventory,owner).find(item=>item.id===canonicalStickerId(selected.id));if(item)return {kind:'motion',id:item.theme,source:'reward',item};}
 if(prefs.backdrop==='custom')return {kind:'image',id:'custom',source:'image'};
 return prefs.backdrop&&prefs.backdrop!=='none'?{kind:'motion',id:prefs.backdrop,source:'builtin'}:{kind:'none',id:'none',source:'builtin'};
}
