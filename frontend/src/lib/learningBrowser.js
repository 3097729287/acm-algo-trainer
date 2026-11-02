// Navigation lives in the existing account-owned SQLite preferences document.
// Code continues to use the workbench's draft store, never this tab manifest.
export const STUDY_KINDS = ['problem','solution','wiki','template','lab','lecture'];
export const MAX_STUDY_TABS=64;
export const STUDY_LABELS = {problem:'题目',solution:'题解',wiki:'维基百科',template:'模板',lab:'实验室',lecture:'从零讲'};
export const studyKey = tab => `${tab.kind}:${tab.id}`;
export const emptyStudyBrowser = () => ({version:1,tabs:[],active:null,left:null,right:null,focused:null,ratio:50,open:false});
export const studySnapshot=value=>({...value,tabs:value.tabs.map(({kind,id,title,methodId,visit,state,scroll})=>({kind,id,title,...(methodId?{methodId}:{}),visit,state,scroll}))});

export function updateStudyDocument(value,key,document) {
 const previous=value.tabs.find(tab=>tab.key===key);if(!previous)return value;
 const nextKey=studyKey({...previous,id:document.id}),rename=source=>source===key?nextKey:source;
 const tabs=value.tabs.filter(tab=>tab.key===key||tab.key!==nextKey).map(tab=>tab.key===key?{...tab,id:document.id,key:nextKey,title:document.title||tab.title}:tab);
 const result={...value,tabs,active:rename(value.active),focused:rename(value.focused),left:rename(value.left),right:rename(value.right)};
 if(result.left&&result.left===result.right)result.left=null;
 return result;
}

export function restoreStudyBrowser(value) {
 const result=emptyStudyBrowser(),seen=new Set();
 if(!value||typeof value!=='object')return result;
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
 return result;
}

export function openStudyTab(state,source) {
 if(!STUDY_KINDS.includes(source?.kind)||!source.id)return state;
 const key=studyKey(source),existing=state.tabs.find(tab=>tab.key===key);
 if(!existing&&state.tabs.length>=MAX_STUDY_TABS)return state;
 const tab=existing?{...existing,...(source.methodId?{methodId:source.methodId}:{}),...(source.title?{title:source.title}:{})}:{...source,key,title:source.title||STUDY_LABELS[source.kind],visit:source.visit||{},state:{},scroll:[]};
 const tabs=existing?state.tabs.map(item=>item.key===key?tab:item):[...state.tabs,tab];
 const next={...state,tabs,active:key,focused:key,open:true};
 if(state.right){
  if(key===state.left||key===state.right)return next;
  if(state.focused===state.right)next.right=key;else next.left=key;
 }
 return next;
}

export function closeStudyTab(state,key) {
 const at=state.tabs.findIndex(tab=>tab.key===key),tabs=state.tabs.filter(tab=>tab.key!==key);
 if(at<0)return state;
 const replacement=tabs[Math.min(at,tabs.length-1)]?.key||null;
 let left=state.left===key?null:state.left,right=state.right===key?null:state.right;
 let active=state.active===key?replacement:state.active;
 if(state.right&&(!left||!right)){
  const remaining=left||right;
  if(tabs.length===1){active=remaining;left=null;right=null;}
  else if(!right){right=remaining;left=null;}
 }
 return {...state,tabs,active,left,right,focused:state.focused===key?(right||active):state.focused,open:state.open&&tabs.length>0};
}

export function splitStudyTab(state,key) {
 if(!state.tabs.some(tab=>tab.key===key)||state.tabs.length<2)return state;
 const others=state.tabs.filter(tab=>tab.key!==key);
 return {...state,open:true,right:key,left:others.length===1?others[0].key:null,active:key,focused:key,ratio:50};
}

const aliasGroups=[['并查集','dsu','union find','union-find','disjoint set'],['树状数组','fenwick','binary indexed tree'],['线段树','segment tree','segment-tree'],['离散化','coordinate compression','compression'],['二分','binary search','binary-search'],['广度优先','宽度优先','bfs'],['深度优先','dfs'],['最短路','dijkstra'],['线性基','linear basis','linear-basis'],['背包','knapsack'],['排序','sorting','sort']];
const normalize=value=>String(value||'').normalize('NFKC').toLowerCase().replace(/\s+/g,' ').trim();
const containsTerm=(text,word)=>/^[\x00-\x7f]+$/.test(word)?new RegExp('(^|[^a-z0-9])'+word.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+'($|[^a-z0-9])').test(text):text.includes(word);
function expanded(value){let text=normalize(value);for(const group of aliasGroups)if(group.some(alias=>containsTerm(text,alias)))text+=' '+group.join(' ');return text;}
const SOURCE_ALIASES={problem:['题目','题库','problem','problems'],solution:['题解','solution','editorial'],wiki:['百科','维基百科','wiki','oi wiki','oi-wiki'],template:['模板','template','templates'],lab:['实验室','实验','lab'],lecture:['从零讲','讲义','lecture']};
export function learningSearch(index,query) {
 let text=normalize(query),kinds=null;
 for(const [kind,names] of Object.entries(SOURCE_ALIASES)){
  const name=names.find(name=>text===name||text.startsWith(name+' ')||text.endsWith(' '+name));
  if(name){kinds=[kind];text=text===name?'':text.startsWith(name+' ')?text.slice(name.length).trim():text.slice(0,-name.length).trim();break;}
 }
 const words=text.split(' ').filter(Boolean);
 return index.filter(item=>(!kinds||kinds.includes(item.kind))&&words.every(word=>containsTerm(expanded(item.search||item.title),word)))
  .map((item,at)=>({item,rank:normalize(item.title)===text?0:normalize(item.title).startsWith(text)&&text?1:normalize(item.title).includes(text)&&text?2:3,at}))
  .sort((a,b)=>a.rank-b.rank||a.at-b.at).map(value=>value.item);
}

export function buildLearningIndex({rows=[],templates=[],lectures=[],wiki=[],labs=[]}) {
 const result=[],seen=new Set();
 const add=(kind,item,title,extra='')=>{if(!item?.id||!title)return;const key=studyKey({kind,id:item.id});if(seen.has(key))return;seen.add(key);result.push({kind,id:item.id,key,title,search:`${title} ${extra}`,source:STUDY_LABELS[kind]});};
 for(const item of wiki)add('wiki',item,item.title,`${item.category||''} ${item.id}`);
 for(const item of templates)add('template',item,item.title,`${item.category||''} ${(item.tags||[]).join(' ')} ${item.learningPath||''}`);
 for(const item of labs)add('lab',item,item.title,item.search||'');
 for(const item of lectures)add('lecture',item,(item.displayTitle||item.concept||item.title||'').replace(/^从零讲[：:]\s*/,''),`${item.title||''} ${(item.tags||[]).join(' ')} ${item.category||''}`);
 for(const item of rows){
  const tags=(item.tags||item.knowledge||[]),extra=`${item.platform||''} ${item.contest||item.contestName||''} ${item.code||''} ${Array.isArray(tags)?tags.map(tag=>typeof tag==='string'?tag:tag.name).join(' '):''} ${(item.categories||[]).map(tag=>typeof tag==='string'?tag:tag.name).join(' ')}`;
  add('problem',item,item.title,extra);
  if(item.hasSolution||item.solution||item.solutionAvailable||item.solutionMethods?.length)add('solution',item,item.title,extra);
 }
 return result;
}
