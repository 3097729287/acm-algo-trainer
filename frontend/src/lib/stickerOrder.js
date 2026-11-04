// Visual stacking is local, belongs to the current account, and never changes inventory.
const prefix='tb.sticker-order.v1:';
const clean=values=>Array.isArray(values)?[...new Set(values.filter(id=>typeof id==='string'&&id.length>0&&id.length<200))].slice(-1000):[];
export function readStickerOrder(owner){if(!owner)return [];try{return clean(JSON.parse(localStorage.getItem(prefix+owner)));}catch{return [];}}
export function bringStickerForward(owner,order,id){const next=clean([...order.filter(value=>value!==id),id]);if(owner)try{localStorage.setItem(prefix+owner,JSON.stringify(next));}catch{}return next;}
