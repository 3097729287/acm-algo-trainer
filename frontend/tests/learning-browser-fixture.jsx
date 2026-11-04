import React,{useCallback,useEffect,useRef,useState} from 'react';
import {createRoot} from 'react-dom/client';
import LearningBrowser from '../src/app/LearningBrowser.jsx';
import InitialCodeSettings from '../src/pages/InitialCodeSettings.jsx';
import {FOUNDATION_LESSONS} from '../src/lib/learningCurriculum.js';
import TEMPLATES from '../../backend/resources/code-templates.json';
import '../src/styles/workspace.css';
import '../src/styles/refinements.css';
import '../src/styles/polish.css';
import '../src/styles/unified.css';
import '../src/styles/revision.css';
import '../src/styles/interaction.css';
import 'katex/dist/katex.min.css';

window.__tbAccountUserId='fixture-A';
document.documentElement.dataset.theme='dark';
const rows=[{id:'fixture:A',title:'小月的数组',platform:'牛客',tags:['并查集'],solutionAvailable:true},{id:'fixture:B',title:'并查集合并查询',platform:'Codeforces',tags:['并查集'],solutionAvailable:true},{id:'fixture:P1706',title:'全排列问题',platform:'洛谷',url:'https://www.luogu.com.cn/problem/P1706',tags:['枚举'],solutionAvailable:false}];
const oldLectures=[{id:'lecture:fixture-io',title:'输入输出',concept:'输入输出',markdown:'## 输入输出\n\n'+('读入两个数，然后输出它们的和。\n\n'.repeat(100)),tags:['输入输出'],images:{}}];
const lectures=FOUNDATION_LESSONS.map((item,index)=>({...item,concept:item.title,markdown:'## 正文 '+index+'\n\n'+('基础阅读内容。\n\n'.repeat(100)),images:{}}));
const articles=[{id:'ds/stack',title:'栈',category:'数据结构',url:'https://oi-wiki.org/ds/stack/'},{id:'ds/queue',title:'队列',category:'数据结构',url:'https://oi-wiki.org/ds/queue/'},{id:'ds/dsu',title:'并查集',category:'数据结构',url:'https://oi-wiki.org/ds/dsu/'},{id:'basic/complexity',title:'复杂度简介',category:'基础',url:'https://oi-wiki.org/basic/complexity/'}];
rows.push({id:'fixture:C',title:'下一道推荐题',platform:'Codeforces',tags:['输入输出'],solutionAvailable:true});
let initialCodes={selection:{cpp17:'own:one',python3:'default'},revisions:{cpp17:4,python3:7},templates:[{id:'default',title:'默认',language:'cpp17',code:'int main(){return 0;}',builtin:true},{id:'new',title:'new',language:'cpp17',code:'// new-template\nint main(){return 1;}',revision:1},{id:'own:one',title:'模板1',language:'cpp17',code:'// saved-one\nint main(){return 2;}',revision:1},{id:'default',title:'默认',language:'python3',code:'# python-default\n',builtin:true},{id:'own:python',title:'Python 模板',language:'python3',code:'print(42)',revision:1}]};
const calls=[];
const storage=key=>'learning-fixture.'+window.__tbAccountUserId+'.'+key;
const read=(key,fallback)=>{try{return JSON.parse(localStorage.getItem(storage(key)))??fallback;}catch{return fallback;}};
async function api(path,body){
 calls.push({path,body});if(path==='initial-code')return structuredClone(initialCodes);if(path==='initial-code/select'){if(body.revision!==initialCodes.revisions[body.language])throw new Error('fixture stale revision');initialCodes={...initialCodes,selection:{...initialCodes.selection,[body.language]:body.id}};return structuredClone(initialCodes);}const url=new URL(path,'https://fixture/');
 if(path==='templates')return {templates:[...TEMPLATES.templates,...read('templates',[])]};
 if(path==='templates/save'){
  const templates=read('templates',[]),template={...body,id:body.id||'own:'+crypto.randomUUID(),revision:(body.revision||0)+1,builtin:false};
  const updated=[...templates.filter(item=>item.id!==template.id),...body.delete?[]:[template]];
  localStorage.setItem(storage('templates'),JSON.stringify(updated));return {template,templates:[...TEMPLATES.templates,...updated]};
 }
 if(path==='lectures')return {lectures,learningQueue:{version:1,foundationIds:lectures.map(item=>item.id),encounteredIds:[]}};
 if(url.pathname==='/lecture'){if(window.studyFixture?.lectureDelay)await new Promise(resolve=>setTimeout(resolve,window.studyFixture.lectureDelay));return lectures.find(item=>item.id===url.searchParams.get('id'));}
 if(url.pathname==='/wiki')return url.searchParams.has('id')?{article:{...articles.find(item=>item.id===url.searchParams.get('id')),html:'<article><h1>并查集</h1><a href="https://oi-wiki.org/ds/stack/">栈</a><a href="https://oi-wiki.org/ds/queue/">队列</a><a href="https://www.luogu.com.cn/problem/P1706" target="_blank">Luogu P1706 全排列问题</a>'+Array.from({length:100},(_,i)=>`<h2 id="section-${i}">集合 ${i}</h2><p>并查集维护互不相交的集合。合并与查询代表元。</p>`).join('')+'<blockquote>本页面贡献者：测试署名。CC BY-SA 4.0 和 SATA。</blockquote></article>'}}:{articles};
 if(url.pathname==='/problem'){
  const id=url.searchParams.get('id'),draft=read('drafts',{})[id];
  return {...rows.find(row=>row.id===id),markdown:'## 题目描述\n\n'+('给定交错输入的两个数组，分别输出。\n\n'.repeat(100)),samples:[{input:'2\n1 10 2 20\n',output:'1 2\n10 20\n'}],limits:{timeMs:1000,memoryMb:256},judge:{scope:'samples'},initialCode:{...initialCodes,templates:initialCodes.templates.filter(row=>row.id===initialCodes.selection[row.language])},draft:draft?.code||'',draftSavedAt:draft?.at||null,draftLanguage:'cpp17',submissions:[]};
 }
 if(path==='draft'){const drafts=read('drafts',{});drafts[body.id]={code:body.code,at:new Date().toISOString()};localStorage.setItem(storage('drafts'),JSON.stringify(drafts));return {savedAt:drafts[body.id].at};}
 if(url.pathname==='/solution')return {...rows.find(row=>row.id===url.searchParams.get('id')),markdown:'## 还原数组\n\n按输入顺序，依次读入 a[i] 和 b[i]。\n\n'+('每次读取一对数。\n\n'.repeat(80)),detailedSolution:{markdown:'## 详细题解\n\n输入交错，输出分别进行。'},lectures:[]};
 if(path==='workspace')return {summary:{}};
 throw new Error('Unexpected isolated fixture request: '+path);
}
function Fixture(){
 const [owner,setOwner]=useState('fixture-A'),[prefs,setPrefs]=useState(()=>read('prefs',{learningPaths:{}})),browser=useRef(null),[practice,setPractice]=useState({training:[],reviews:{tasks:[]}}),[settings,setSettings]=useState(false);
 useEffect(()=>{localStorage.setItem(storage('prefs'),JSON.stringify(prefs));},[prefs]);
 const train=useCallback((id,options={})=>browser.current.open({kind:'problem',id,title:rows.find(row=>row.id===id)?.title,newTab:options.newTab,visit:options.recommendation||options.stage?{practiceFlow:{stage:options.stage||'recommendation',openedAt:new Date().toISOString()}}:{}}),[]);
 const flush=useCallback(value=>{setPrefs(previous=>({...previous,learningPaths:{...previous.learningPaths,browserV1:value}}));return Promise.resolve(true);},[]);
 window.studyFixture={learn:id=>setPrefs(previous=>({...previous,learnedLectures:[id]})),lectureDelay:window.studyFixture?.lectureDelay||0,calls,lectures,settings:setSettings,practice:setPractice,hide:()=>browser.current.hide(),open:tab=>browser.current.open(tab),state:()=>browser.current.getState(),prefs:()=>prefs,account:id=>{window.__tbAccountUserId=id;setPrefs(read('prefs',{learningPaths:{}}));setOwner(id);}};
 return <div className="app-shell"><button onClick={()=>train(rows[0].id)}>题目入口</button><button onClick={()=>browser.current.open({kind:'lab',id:'sorting-basics',title:'排序基础'})}>实验室入口</button><button onClick={()=>browser.current.resume()}>恢复标签</button><div id="tb-page-search"/>
  {settings&&<InitialCodeSettings api={api}/>}<LearningBrowser ref={browser} api={api} accountId={owner} ready rows={rows} prefs={prefs} setPrefs={setPrefs} onTrain={train} onProgress={()=>{}} onNotice={()=>{}} onFlush={flush} practiceWorkspace={practice} recommendations={[{kind:'random',id:'fixture:P1706',title:'全排列问题'},{kind:'problem',id:'fixture:C',title:'下一道推荐题'}]}/>
 </div>;
}
createRoot(document.getElementById('root')).render(<Fixture/>);
