export const NAVIGATION_ORDER=Object.freeze(['mine','library','training-lists','competitions','mock','growth','records','activity','rankings','paths','templates','lectures']);

const previousDefaults=[
 ['training-lists'],
 ['mine','library','training-lists','competitions','mock','rankings','growth','records','paths','templates','lectures','activity'],
 ['mine','library','training-lists','competitions','mock','paths','rankings','growth','records','activity','lectures'],
 ['mine','library','training-lists','competitions','mock','paths','rankings','growth','records','activity','lectures','templates'],
 ['mine','library','training-lists','competitions','mock','records','growth','activity','lectures','templates','paths','rankings'],
];

// Only known shipped defaults migrate. A different saved order stays personal.
export function navigationOrder(value){
 const order=Array.isArray(value)?value.filter(id=>id!=='today'):[];
 if(!order.length||previousDefaults.some(previous=>previous.length===order.length&&previous.every((id,index)=>id===order[index])))return [...NAVIGATION_ORDER];
 const next=[...order];
 if(!next.includes('training-lists')){const index=next.indexOf('library');next.splice(index<0?next.length:index+1,0,'training-lists');}
 return next;
}
