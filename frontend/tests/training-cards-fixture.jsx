import React,{useState} from 'react';
import {createRoot} from 'react-dom/client';
import TrainingListsPage from '../src/pages/TrainingListsPage.jsx';
import '../src/styles/workspace.css';
import '../src/styles/refinements.css';
import '../src/styles/polish.css';
import '../src/styles/unified.css';
import '../src/styles/revision.css';

const rows=Array.from({length:12},(_,i)=>({id:`p${i}`,title:`练习 ${i+1}`,problem:`P${1000+i}`,platform:'洛谷',url:`https://www.luogu.com.cn/problem/P${1000+i}`,tags:['搜索','DFS'],difficulty:1000+i*50,accepted:i===0,verdict:['AC','WA','TLE','MLE','RE'][i%5]}));
const lists=[{id:'luogu-112',title:'【算法1-7】搜索',available:true,children:[],aggregateChildren:false,problems:rows.map(row=>({problemId:row.id,pid:row.problem,url:row.url,sections:[]})),categories:[{id:'basic',name:'基础',order:0,position:0}]}];
const visit={state:{curriculumVersion:1,mode:'source',folder:['basic']}};
const fixture=window.trainingFixture={calls:[],lists,likes:{'luogu-112':{total:7,likedToday:false}},delay:0,failLike:false};
const api=async(path,body)=>{
  fixture.calls.push({path,body});
  if(path==='training-lists'){if(fixture.delay)await new Promise(resolve=>setTimeout(resolve,fixture.delay));return {lists:fixture.lists,tags:{'luogu-112':['周末']}};}
  if(path.startsWith('training-list-likes?'))return {available:true,likes:fixture.likes,day:'2026-10-26'};
  if(path==='training-list-likes'){if(fixture.failLike)throw Error('测试失败');fixture.likes[body.listId]={total:fixture.likes[body.listId].total+1,likedToday:true};return {likes:fixture.likes[body.listId]};}
  if(path==='training-lists/save'){
    const value={id:body.id||'custom:12345678-1234-1234-1234-123456789abc',title:body.title,custom:true,available:true,children:[],aggregateChildren:false,topicPath:['我的题单'],categories:[{id:'personal',name:'我的题单',order:-1,position:0}],problems:body.problemIds.map(id=>({problemId:id,pid:rows.find(row=>row.id===id).problem,sections:[]}))};
    fixture.lists=[lists[0],value];return {list:value,customLists:[value]};
  }
  if(path==='training-list-tags')return {tags:{[body.listId]:body.tags}};
  throw Error('Unexpected API '+path);
};
function Fixture(){const [generation,setGeneration]=useState(0);fixture.remount=()=>setGeneration(value=>value+1);return <div className="workspace-area" style={{height:'100dvh',padding:16}}><TrainingListsPage key={generation} api={api} rows={rows} visit={visit} onTrain={(id,options)=>fixture.opened={id,...options}}/></div>;}
createRoot(document.getElementById('root')).render(<Fixture/>);
