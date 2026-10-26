import {categoryPath} from './trainingListCatalog.js';

export function listTags(list,custom={}) {
 const labels=[...(list.topicPath||[]).map(name=>name.replace(/^\d+\s+/,'')),
  ...categoryPath(list.displayTitle||list.title),...(list.tags||[]),...custom[list.id]||[]];
 return [...new Set(labels.filter(label=>typeof label==='string'&&label.trim()&&label!=='综合训练'))];
}

export function trainingTagIndex(lists,custom={}) {
 const byList=new Map(),byTag=new Map();
 for(const list of lists){
  const tags=listTags(list,custom);byList.set(list.id,tags);
  for(const tag of tags){if(!byTag.has(tag))byTag.set(tag,new Set());byTag.get(tag).add(list.id);}
 }
 return {byList,byTag,matches:(id,tags)=>tags.every(tag=>byTag.get(tag)?.has(id))};
}
