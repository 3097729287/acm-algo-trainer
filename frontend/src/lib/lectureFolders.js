import {canonicalKnowledgeName} from './knowledgeNames.js';

const originalPaths = item => [...new Set([item.category, ...(item.categories || [])].filter(Boolean))]
  .map(value => String(value).split(/\s*\/\s*/).map(part => part.trim()).filter(Boolean));
const indices=new WeakMap();
function indexTree(categories){
  if(indices.has(categories))return indices.get(categories);
  const result=new Map();
  const visit=(nodes,prefix=[])=>{for(const node of nodes){const path=[...prefix,node.name];result.set(canonicalKnowledgeName(node.name),path);if(node.children?.length)visit(node.children,path);else for(const tag of node.tags||[])result.set(canonicalKnowledgeName(tag),path);}};
  visit(categories);indices.set(categories,result);return result;
}
export function primaryLectureTopic(item){return canonicalKnowledgeName(item.knowledgeName||item.tags?.[0]||String(item.concept||item.title||'').split(/[：:]/)[0]);}
const EMPTY=[];
export function lectureFolderPaths(item,categories=EMPTY){
  if(!categories.length)return originalPaths(item);
  const index=indexTree(categories),known=[];
  for(const topic of [primaryLectureTopic(item),...(item.tags||[]),...originalPaths(item).flat()]){
    const path=index.get(canonicalKnowledgeName(topic));
    if(path&&!known.some(value=>JSON.stringify(value)===JSON.stringify(path)))known.push(path);
  }
  if(known.length)return known.filter(path=>!known.some(other=>other.length>path.length&&path.every((part,i)=>other[i]===part)));
  return originalPaths(item).length?originalPaths(item):[['编程基础',primaryLectureTopic(item)||'其他']];
}

export function lectureMatchesFolder(item, path,categories=EMPTY) {
  return !path.length || lectureFolderPaths(item,categories).some(parts => path.every((part, index) => parts[index] === part));
}

export function lectureFolderOptions(entries,categories=EMPTY) {
  const clone=(nodes,prefix=[])=>nodes.map(node=>{const path=[...prefix,node.name];return {label:node.name,selectionLabel:path.join(' / '),value:JSON.stringify(path),children:node.children?.length?clone(node.children,path):[]};});
  const roots = clone(categories);
  for (const item of entries) for (const path of lectureFolderPaths(item,categories)) {
    let nodes = roots;
    for (let index = 0; index < path.length; index++) {
      const prefix = path.slice(0, index + 1), value = JSON.stringify(prefix);
      let folder = nodes.find(node => node.value === value);
      if (!folder) { folder = { label: path[index], selectionLabel: prefix.join(' / '), value, children: [] }; nodes.push(folder); }
      nodes = folder.children;
    }
  }
  const finish = nodes => (categories.length?nodes:nodes.sort((a,b) => a.label.localeCompare(b.label, 'zh-CN', {numeric:true})))
    .map(node => ({ ...node, children: node.children.length ? finish(node.children) : undefined }));
  return finish(roots);
}
