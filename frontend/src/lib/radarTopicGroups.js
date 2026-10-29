import {canonicalKnowledgeName,knowledgeAliases} from './knowledgeNames.js';

export function radarTopicGroups(topics,availableIndex,availableFallback=new Map()) {
 const unique=new Map(topics.map(([name,difficulty])=>[canonicalKnowledgeName(name),difficulty])),regular=[],rare=[];
 for(const [name,difficulty] of unique){
  const count=availableIndex.get(name)?.size??availableFallback.get(name)??0;
  if(!count)continue;
  const item={name,difficulty,members:[name],tags:knowledgeAliases(name)};
  (count<=2?rare:regular).push(item);
 }
 if(rare.length)regular.push({name:'杂项',difficulty:null,members:rare.map(item=>item.name),tags:[...new Set(rare.flatMap(item=>item.tags))]});
 return regular;
}
