import {canonicalKnowledgeName,knowledgeAliases} from './knowledgeNames.js';

// Use the same distinct-problem count shown by the table, after aliases and
// rare-topic unions have been resolved. Stable ties retain taxonomy order.
export function orderRadarNodes(nodes) {
 return nodes.map((node,index)=>({node,index})).sort((a,b)=>
  (Number.isFinite(b.node.available)?b.node.available:0)-(Number.isFinite(a.node.available)?a.node.available:0)
   ||a.index-b.index).map(item=>item.node);
}

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
