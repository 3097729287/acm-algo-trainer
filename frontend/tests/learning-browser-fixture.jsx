import React,{useCallback,useEffect,useRef,useState} from 'react';
import {createRoot} from 'react-dom/client';
import LearningBrowser from '../src/app/LearningBrowser.jsx';
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
const lectures=[{id:'lecture:fixture-io',title:'输入输出',concept:'输入输出',markdown:'## 输入输出\n\n'+('读入两个数，然后输出它们的和。\n\n'.repeat(100)),tags:['输入输出'],images:{}}];
const articles=[{id:'ds/dsu',title:'并查集',category:'数据结构',url:'https://oi-wiki.org/ds/dsu/'},{id:'basic/complexity',title:'复杂度简介',category:'基础',url:'https://oi-wiki.org/basic/complexity/'}];
const calls=[];
const storage=key=>'learning-fixture.'+window.__tbAccountUserId+'.'+key;
const read=(key,fallback)=>{try{return JSON.parse(localStorage.getItem(storage(key)))??fallback;}catch{return fallback;}};
async function api(path,body){
 calls.push({path,body});const url=new URL(path,'https://fixture/');
 if(path==='templates')return {templates:[...TEMPLATES.templates,...read('templates',[])]};
 if(path==='templates/save'){
  const templates=read('templates',[]),template={...body,id:body.id||'own:'+crypto.randomUUID(),revision:(body.revision||0)+1,builtin:false};
  const updated=[...templates.filter(item=>item.id!==template.id),...body.delete?[]:[template]];
  localStorage.setItem(storage('templates'),JSON.stringify(updated));return {template,templates:[...TEMPLATES.templates,...updated]};
 }
 if(path==='lectures')return {lectures};
 if(url.pathname==='/lecture')return lectures.find(item=>item.id===url.searchParams.get('id'));
 if(url.pathname==='/wiki')return url.searchParams.has('id')?{article:{...articles.find(item=>item.id===url.searchParams.get('id')),html:'<article><h1>并查集</h1><a href="https://www.luogu.com.cn/problem/P1706" target="_blank">Luogu P1706 全排列问题</a>'+Array.from({length:100},(_,i)=>`<h2 id="section-${i}">集合 ${i}</h2><p>并查集维护互不相交的集合。合并与查询代表元。</p>`).join('')+'<blockquote>本页面贡献者：测试署名。CC BY-SA 4.0 和 SATA。</blockquote></article>'}}:{articles};
 if(url.pathname==='/problem'){
  const id=url.searchParams.get('id'),draft=read('drafts',{})[id];
  return {...rows.find(row=>row.id===id),markdown:'## 题目描述\n\n'+('给定交错输入的两个数组，分别输出。\n\n'.repeat(100)),samples:[{input:'2\n1 10 2 20\n',output:'1 2\n10 20\n'}],limits:{timeMs:1000,memoryMb:256},judge:{scope:'samples'},draft:draft?.code||'',draftSavedAt:draft?.at||null,draftLanguage:'cpp17',submissions:[]};
 }
 if(path==='draft'){const drafts=read('drafts',{});drafts[body.id]={code:body.code,at:new Date().toISOString()};localStorage.setItem(storage('drafts'),JSON.stringify(drafts));return {savedAt:drafts[body.id].at};}
 if(url.pathname==='/solution')return {...rows.find(row=>row.id===url.searchParams.get('id')),markdown:'## 还原数组\n\n按输入顺序，依次读入 a[i] 和 b[i]。\n\n'+('每次读取一对数。\n\n'.repeat(80)),detailedSolution:{markdown:'## 详细题解\n\n输入交错，输出分别进行。'},lectures:[]};
 if(path==='workspace')return {summary:{}};
 throw new Error('Unexpected isolated fixture request: '+path);
}
function Fixture(){
 const [owner,setOwner]=useState('fixture-A'),[prefs,setPrefs]=useState(()=>read('prefs',{learningPaths:{}})),browser=useRef(null);
 useEffect(()=>{localStorage.setItem(storage('prefs'),JSON.stringify(prefs));},[prefs]);
 const train=useCallback(id=>browser.current.open({kind:'problem',id,title:rows.find(row=>row.id===id)?.title}),[]);
 const flush=useCallback(value=>{setPrefs(previous=>({...previous,learningPaths:{...previous.learningPaths,browserV1:value}}));return Promise.resolve(true);},[]);
 window.studyFixture={calls,open:tab=>browser.current.open(tab),state:()=>browser.current.getState(),prefs:()=>prefs,account:id=>{window.__tbAccountUserId=id;setPrefs(read('prefs',{learningPaths:{}}));setOwner(id);}};
 return <div className="app-shell"><button onClick={()=>train(rows[0].id)}>题目入口</button><button onClick={()=>browser.current.open({kind:'lab',id:'sorting-basics',title:'排序基础'})}>实验室入口</button><button onClick={()=>browser.current.resume()}>恢复标签</button><div id="tb-page-search"/>
  <LearningBrowser ref={browser} api={api} accountId={owner} ready rows={rows} prefs={prefs} setPrefs={setPrefs} onTrain={train} onProgress={()=>{}} onNotice={()=>{}} onFlush={flush}/>
 </div>;
}
createRoot(document.getElementById('root')).render(<Fixture/>);
