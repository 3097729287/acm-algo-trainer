// Navigation lives in the existing account-owned SQLite preferences document.
// Code continues to use the workbench's draft store, never this tab manifest.
export const STUDY_KINDS = ['problem','solution','wiki','template','lab','lecture'];
export const MAX_STUDY_TABS=64;
export const STUDY_LABELS = {problem:'题目',solution:'题解',wiki:'维基百科',template:'模板',lab:'实验室',lecture:'从零讲'};
export const studyKey = tab => `${tab.kind}:${tab.id}`;
export const emptyStudyBrowser = () => ({version:1,tabs:[],documents:{},groups:[],chrome:false,active:null,left:null,right:null,focused:null,focusedGroup:null,ratio:50,open:false});
export const studySnapshot=value=>({...value,tabs:value.tabs.map(({kind,id,title,methodId,visit,state,scroll})=>({kind,id,title,...(methodId?{methodId}:{}),visit,state,scroll}))});

function groupId(groups){let id=1;while(groups.some(group=>group.id==='group-'+id))id++;return 'group-'+id;}
function finishGroups(state,groups,focused=state.focused) {
 const valid=new Set(state.tabs.map(tab=>tab.key)),seen=new Set(),ids=new Set();
 const clean=groups.map(group=>{
  const tabs=(group.tabs||[]).filter(key=>{if(!valid.has(key)||seen.has(key))return false;seen.add(key);return true;});
  let id=typeof group.id==='string'&&/^[\w-]{1,100}$/.test(group.id)?group.id:groupId([...ids].map(id=>({id})));
  if(ids.has(id))id=groupId([...ids].map(id=>({id})));ids.add(id);
  return {id,tabs,active:tabs.includes(group.active)?group.active:tabs[0],weight:Number.isFinite(group.weight)&&group.weight>0?Math.min(10000,group.weight):1};
 }).filter(group=>group.tabs.length);
 const missing=state.tabs.map(tab=>tab.key).filter(key=>!seen.has(key));
 if(missing.length){if(clean.length)clean[0].tabs.push(...missing);else clean.push({id:'group-1',tabs:missing,active:missing.includes(state.active)?state.active:missing[0],weight:1});}
 const total=clean.reduce((sum,group)=>sum+group.weight,0)||1;
 for(const group of clean)group.weight=group.weight/total*100;
 const owner=clean.find(group=>group.tabs.includes(focused))||clean.find(group=>group.id===state.focusedGroup)||clean[0];
 if(owner&&owner.tabs.includes(focused))owner.active=focused;
 const active=owner?.active||null;
 return {...state,groups:clean,active,focused:active,focusedGroup:owner?.id||null,left:clean.length>1?clean[0].active:null,right:clean.length>1?clean[1].active:null,ratio:clean.length===2?clean[0].weight:50,chrome:state.chrome===true||clean.length>1,open:state.open&&state.tabs.length>0};
}
export function studyGroups(state) {
 if(Array.isArray(state.groups)&&state.groups.length)return state.groups;
 if(!state.tabs.length)return [];
 if(state.right&&state.tabs.some(tab=>tab.key===state.right)){
  const others=state.tabs.filter(tab=>tab.key!==state.right).map(tab=>tab.key);
  if(others.length)return [{id:'group-1',tabs:others,active:others.includes(state.left)?state.left:others[0],weight:state.ratio||50},{id:'group-2',tabs:[state.right],active:state.right,weight:100-(state.ratio||50)}];
 }
 return [{id:'group-1',tabs:state.tabs.map(tab=>tab.key),active:state.active||state.tabs[0].key,weight:100}];
}
export function activateStudyTab(state,key) {
 if(!state.tabs.some(tab=>tab.key===key))return state;
 return finishGroups({...state,open:true},studyGroups(state).map(group=>({...group,active:group.tabs.includes(key)?key:group.active})),key);
}

export function updateStudyDocument(value,key,document) {
 const previous=value.tabs.find(tab=>tab.key===key);if(!previous)return value;
 const nextKey=studyKey({...previous,id:document.id}),rename=source=>source===key?nextKey:source;
 const tabs=value.tabs.filter(tab=>tab.key===key||tab.key!==nextKey).map(tab=>tab.key===key?{...tab,id:document.id,key:nextKey,title:document.title||tab.title}:tab);
 const groups=studyGroups(value).map(group=>({...group,tabs:group.tabs.filter(item=>item!==nextKey||item===key).map(rename),active:rename(group.active)}));
 return finishGroups({...value,tabs},groups,rename(value.focused));
}

export function restoreStudyBrowser(value) {
 const result=emptyStudyBrowser(),seen=new Set();
 if(!value||typeof value!=='object')return result;
 if(value.documents&&typeof value.documents==='object')result.documents=Object.fromEntries(Object.entries(value.documents).filter(([key,doc])=>doc&&STUDY_KINDS.includes(doc.kind)&&typeof doc.id==='string'&&doc.id.length<=400&&key===studyKey(doc)));
 for(const source of (Array.isArray(value.tabs)?value.tabs:[]).slice(0,MAX_STUDY_TABS)){
  if(!STUDY_KINDS.includes(source?.kind)||typeof source.id!=='string'||!source.id||source.id.length>400)continue;
  const key=studyKey(source);if(seen.has(key))continue;seen.add(key);
  result.tabs.push({kind:source.kind,id:source.id,key,title:String(source.title||STUDY_LABELS[source.kind]).slice(0,200),
   ...(source.methodId?{methodId:String(source.methodId).slice(0,200)}:{}),
   visit:source.visit&&typeof source.visit==='object'?source.visit:{},state:source.state&&typeof source.state==='object'?source.state:{},
   scroll:Array.isArray(source.scroll)?source.scroll.slice(0,16).filter(item=>Array.isArray(item)&&typeof item[0]==='string'&&Number.isFinite(item[1])&&Number.isFinite(item[2])):[]});
 }
 const valid=key=>seen.has(key)?key:null;
 result.active=valid(value.active)||result.tabs[0]?.key||null;
 result.right=valid(value.right);result.left=valid(value.left);
 if(!result.right||result.right===result.left){result.right=null;result.left=null;}
 result.focused=valid(value.focused)||result.right||result.active;
 result.ratio=Number.isFinite(value.ratio)?Math.max(20,Math.min(80,value.ratio)):50;
 result.open=value.open===true&&result.tabs.length>0;
 result.chrome=typeof value.chrome==='boolean'?value.chrome:result.tabs.length>1;
 result.focusedGroup=typeof value.focusedGroup==='string'?value.focusedGroup:null;
 const groups=Array.isArray(value.groups)?value.groups.slice(0,MAX_STUDY_TABS).filter(group=>group&&Array.isArray(group.tabs)):studyGroups(result);
 return finishGroups(result,groups,result.focused);
}

export function openStudyTab(state,source) {
 if(!STUDY_KINDS.includes(source?.kind)||!source.id)return state;
 const key=studyKey(source),existing=state.tabs.find(tab=>tab.key===key);
 if(!existing&&state.tabs.length>=MAX_STUDY_TABS)return state;
 const tab=existing?{...existing,...(source.methodId?{methodId:source.methodId}:{}),...(source.title?{title:source.title}:{})}:{...source,key,title:source.title||STUDY_LABELS[source.kind],visit:source.visit||{},state:source.state||{},scroll:source.scroll||[]};
 const tabs=existing?state.tabs.map(item=>item.key===key?tab:item):[...state.tabs,tab];
 let groups=studyGroups(state).map(group=>({...group,tabs:[...group.tabs]}));
 if(!groups.length)groups=[{id:'group-1',tabs:[],active:null,weight:100}];
 const target=existing?groups.find(group=>group.tabs.includes(key)):groups.find(group=>group.id===state.focusedGroup)||groups.find(group=>group.tabs.includes(state.focused))||groups[0];
 if(!existing)target.tabs.push(key);target.active=key;
 return finishGroups({...state,tabs,open:true,chrome:state.chrome||state.open&&tabs.length>1},groups,key);
}

export function closeStudyTab(state,key) {
 if(!state.tabs.some(tab=>tab.key===key))return state;
 const tabs=state.tabs.filter(tab=>tab.key!==key),groups=studyGroups(state).map(group=>{
  const at=group.tabs.indexOf(key),remaining=group.tabs.filter(item=>item!==key);
  return {...group,tabs:remaining,active:group.active===key?remaining[Math.min(at,remaining.length-1)]:group.active};
 });
 const owner=groups.find(group=>group.id===state.focusedGroup),focused=state.focused===key?owner?.active||groups.find(group=>group.active)?.active:state.focused;
 return finishGroups({...state,tabs,chrome:tabs.length>1&&state.chrome},groups,focused);
}

export function replaceStudyProblem(state,key,source){
 const old=state.tabs.find(tab=>tab.key===key);if(old?.kind!=='problem'||!source?.id)return state;
 return replaceStudyContent(state,key,{...source,kind:'problem'});
}

export function replaceStudyContent(state,key,source){
 const old=state.tabs.find(tab=>tab.key===key);if(!old||!source?.id||!STUDY_KINDS.includes(source.kind))return state;
 const nextKey=studyKey(source);if(nextKey===key)return {...state,open:true,tabs:state.tabs.map(tab=>tab.key===key?{...tab,...source,visit:{...tab.visit,...source.visit},state:tab.state,scroll:tab.scroll}:tab)};
 if(state.tabs.some(tab=>tab.key===nextKey))return activateStudyTab({...state,tabs:state.tabs.map(tab=>tab.key===nextKey?{...tab,...source,visit:{...tab.visit,...source.visit},state:tab.state,scroll:tab.scroll}:tab)},nextKey);
 const rename=value=>value===key?nextKey:value;
 const next={...source,key:nextKey,title:source.title||STUDY_LABELS[source.kind],visit:source.visit||{},state:source.state||{},scroll:source.scroll||[]};
 const groups=studyGroups(state).map(group=>({...group,tabs:group.tabs.map(rename),active:rename(group.active)}));
 const {kind,id,title,methodId,visit,state:documentState,scroll}=old;
 const documents={...state.documents,[key]:{kind,id,title,methodId,visit,state:documentState,scroll}};
 return finishGroups({...state,open:true,documents,tabs:state.tabs.map(tab=>tab.key===key?next:tab)},groups,nextKey);
}

export function splitStudyTab(state,key,{targetGroupId,side='right'}={}) {
 if(!state.tabs.some(tab=>tab.key===key)||state.tabs.length<2)return state;
 const groups=studyGroups(state),target=groups.find(group=>group.id===targetGroupId)||groups.find(group=>group.tabs.includes(key))||groups[0],at=groups.indexOf(target),id=groupId(groups);
 const next=groups.map(group=>{
  const index=group.tabs.indexOf(key),tabs=group.tabs.filter(item=>item!==key);
  return {...group,tabs,active:group.active===key?tabs[Math.min(index,tabs.length-1)]:group.active,weight:group.id===target.id?group.weight/2:group.weight};
 });
 next.splice(at+(side==='left'?0:1),0,{id,tabs:[key],active:key,weight:target.weight/2});
 return finishGroups({...state,open:true,chrome:true},next,key);
}

export function moveStudyTab(state,key,targetGroupId,beforeKey=null) {
 const groups=studyGroups(state),target=groups.find(group=>group.id===targetGroupId);
 if(!target||!state.tabs.some(tab=>tab.key===key)||beforeKey===key)return state;
 const next=groups.map(group=>{
  const at=group.tabs.indexOf(key),tabs=group.tabs.filter(item=>item!==key);
  return {...group,tabs,active:group.active===key?tabs[Math.min(at,tabs.length-1)]:group.active};
 });
 const destination=next.find(group=>group.id===targetGroupId),at=beforeKey?destination.tabs.indexOf(beforeKey):-1;
 destination.tabs.splice(at<0?destination.tabs.length:at,0,key);destination.active=key;
 return finishGroups({...state,chrome:true},next,key);
}

export function resizeStudyGroups(state,index,position,width,snapPixels=14) {
 const groups=studyGroups(state).map(group=>({...group})),a=groups[index],b=groups[index+1];if(!a||!b)return state;
 const start=groups.slice(0,index).reduce((sum,group)=>sum+group.weight,0),total=a.weight+b.weight,midpoint=start+total/2;
 const minimum=Math.min(120/Math.max(1,width)*100,total*.2);
 let boundary=Math.max(start+minimum,Math.min(start+total-minimum,position));
 if(Math.abs(boundary-midpoint)*width/100<=snapPixels)boundary=midpoint;
 a.weight=boundary-start;b.weight=total-a.weight;
 return finishGroups(state,groups,state.focused);
}

const aliasGroups=[['并查集','dsu','union find','union-find','disjoint set'],['树状数组','fenwick','binary indexed tree'],['线段树','segment tree','segment-tree'],['离散化','coordinate compression','compression'],['二分','binary search','binary-search'],['广度优先','宽度优先','bfs'],['深度优先','dfs'],['最短路','dijkstra'],['线性基','linear basis','linear-basis'],['背包','knapsack'],['排序','sorting','sort']];
const normalize=value=>String(value||'').normalize('NFKC').toLowerCase().replace(/\s+/g,' ').trim();
const containsTerm=(text,word)=>/^[\x00-\x7f]+$/.test(word)?new RegExp('(^|[^a-z0-9])'+word.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+'($|[^a-z0-9])').test(text):text.includes(word);
function expanded(value){let text=normalize(value);for(const group of aliasGroups)if(group.some(alias=>containsTerm(text,alias)))text+=' '+group.join(' ');return text;}
const SOURCE_ALIASES={problem:['题目','题库','problem','problems','题解','solution','editorial'],wiki:['百科','维基百科','wiki','oi wiki','oi-wiki'],template:['模板','template','templates'],lab:['实验室','实验','lab'],lecture:['从零讲','讲义','lecture']};
function searchScope(query) {
 let text=normalize(query),kinds=null;
 for(const [kind,names] of Object.entries(SOURCE_ALIASES)){
  const name=names.find(name=>text===name||text.startsWith(name+' ')||text.endsWith(' '+name));
  if(name){kinds=[kind];text=text===name?'':text.startsWith(name+' ')?text.slice(name.length).trim():text.slice(0,-name.length).trim();break;}
 }
 return {text,kinds};
}
export function learningSearch(index,query) {
 const {text,kinds}=searchScope(query);
 const words=text.split(' ').filter(Boolean);
 return index.filter(item=>(!kinds||kinds.includes(item.kind))&&words.every(word=>containsTerm(expanded(item.search||item.title),word)))
  .map((item,at)=>({item,rank:normalize(item.title)===text?0:normalize(item.title).startsWith(text)&&text?1:normalize(item.title).includes(text)&&text?2:3,at}))
  .sort((a,b)=>a.rank-b.rank||a.at-b.at).map(value=>value.item);
}

export const LEARNING_FOLDERS=['problem','wiki','template','lab','lecture'];
export function learningDirectory(index,query='',path=[]) {
 const {kinds,text}=searchScope(query),matches=learningSearch(index,query);
 const current=kinds?[kinds[0]]:path[0]==='solution'?['problem',...path.slice(1)]:path;
 if(!current.length){
  const sources=LEARNING_FOLDERS;
  return {path:[],entries:sources.filter(kind=>!query.trim()||matches.some(item=>item.kind===kind)).map(kind=>({type:'folder',key:'source:'+kind,kind,title:STUDY_LABELS[kind],path:[kind],count:matches.filter(item=>item.kind===kind).length}))};
 }
 const [kind,...categories]=current,items=matches.filter(item=>item.kind===kind),folders=new Map(),files=[];
 for(const item of items){
  const parts=String(item.category||'').split(/\s*[/／]\s*/).map(part=>part.trim()).filter(Boolean);
  if(!categories.every((part,at)=>parts[at]===part))continue;
  if(parts.length>categories.length&&!text&&!query.trim()){
   const title=parts[categories.length],existing=folders.get(title);
   if(existing)existing.count++;else folders.set(title,{type:'folder',key:'folder:'+current.join('/')+'/'+title,kind,title,path:[...current,title],count:1});
  }else files.push({...item,type:'file'});
 }
 return {path:current,entries:[...[...folders.values()].sort((a,b)=>a.title.localeCompare(b.title,'zh-CN')),...files]};
}

export function buildLearningIndex({rows=[],templates=[],lectures=[],wiki=[],labs=[]}) {
 const result=[],seen=new Set();
 const add=(kind,item,title,extra='')=>{if(!item?.id||!title)return;const key=studyKey({kind,id:item.id});if(seen.has(key))return;seen.add(key);result.push({kind,id:item.id,key,title,category:item.category||'',search:`${title} ${extra}`,source:STUDY_LABELS[kind]});};
 for(const item of wiki)add('wiki',item,item.title,`${item.category||''} ${item.id}`);
 for(const item of templates)add('template',item,item.title,`${item.category||''} ${(item.tags||[]).join(' ')} ${item.learningPath||''}`);
 for(const item of labs)add('lab',item,item.title,item.search||'');
 for(const item of lectures)add('lecture',item,(item.displayTitle||item.concept||item.title||'').replace(/^从零讲[：:]\s*/,''),`${item.title||''} ${(item.tags||[]).join(' ')} ${item.category||''}`);
 for(const item of rows){
  const tags=(item.tags||item.knowledge||[]),extra=`${item.platform||''} ${item.contest||item.contestName||''} ${item.code||''} ${Array.isArray(tags)?tags.map(tag=>typeof tag==='string'?tag:tag.name).join(' '):''} ${(item.categories||[]).map(tag=>typeof tag==='string'?tag:tag.name).join(' ')}`;
  add('problem',item,item.title,extra);
 }
 return result;
}
