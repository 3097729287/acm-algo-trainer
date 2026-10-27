import {VisualPreferences} from '../src/components/SettingsControls.jsx';
import {Difficulty} from '../src/components/ProblemTableParts.jsx';
import {DifficultyDisplayProvider} from '../src/components/DifficultyDisplay.jsx';
import React,{useState} from 'react';
import {createRoot} from 'react-dom/client';
import TrainingListsPage from '../src/pages/TrainingListsPage.jsx';
import AddToTrainingLists from '../src/components/AddToTrainingLists.jsx';
import ActivityPage from '../src/pages/ActivityPage.jsx';
import MockSetup from '../src/app/MockSetup.jsx';
import '../src/styles/workspace.css';import '../src/styles/refinements.css';import '../src/styles/polish.css';import '../src/styles/unified.css';import '../src/styles/revision.css';
window.__tbAccountUserId='revision1420';
const rows=Array.from({length:20},(_,i)=>({id:`p${i}`,title:`${i===0?'Z':'A'} 练习 ${i}`,problem:`P${i}`,url:`https://www.luogu.com.cn/problem/P${i}`,tags:i%2?['分治']:['DFS'],difficulty:1000+i*100,platform:'洛谷',accepted:i===0}));
const fixture=window.fixture={likes:{'luogu-112':{total:7,likedToday:false}},calls:[],lists:[{id:'luogu-112',title:'搜索',available:true,aggregateChildren:false,children:[],problems:rows.map(row=>({problemId:row.id,pid:row.problem,sections:[]})),categories:[{id:'basic',name:'基础',order:0}]}]};
const visit={state:{curriculumVersion:1,mode:'source',folder:[]}};
const api=async(path,body)=>{
 fixture.calls.push({path,body});
 if(path.startsWith('training-lists?'))return {lists:fixture.lists.filter(list=>list.custom)};
 if(path==='training-lists')return {lists:fixture.lists};
 if(path==='training-list-likes'&&!body){await new Promise(resolve=>setTimeout(resolve,250));return {available:true,likes:structuredClone(fixture.likes)};}
 if(path==='training-list-likes'){await new Promise(resolve=>setTimeout(resolve,60));const old=fixture.likes[body.listId];fixture.likes[body.listId]={total:old.total+(body.liked===old.likedToday?0:body.liked?1:-1),likedToday:body.liked};return {likes:{...fixture.likes[body.listId]}};}
 if(path==='training-lists/save'){
  const list={id:body.id||'custom:'+crypto.randomUUID(),title:body.title,custom:true,available:true,aggregateChildren:false,children:[],topicPath:['我的题单'],categories:[{id:'personal',name:'我的题单',order:-1}],problems:(body.problemIds||[]).map((id,i)=>({problemId:id,pid:id,sections:[],addedAt:`2026-10-27T00:${String(i).padStart(2,'0')}:00Z`}))};
  fixture.lists=[...fixture.lists.filter(item=>item.id!==list.id),list];return {list,customLists:fixture.lists.filter(list=>list.custom)};
 }
 if(path==='training-lists/add'){for(const list of fixture.lists.filter(list=>body.listIds.includes(list.id)))list.problems.push(...body.problemIds.map((id,i)=>({problemId:id,pid:id,sections:[],addedAt:`2026-10-27T00:${String(i).padStart(2,'0')}:00Z`})));return {customLists:fixture.lists.filter(list=>list.custom)};}
 if(path==='contests/preview')return {plan:{previewId:'preview',name:'训练试卷',duration:120,slots:rows.slice(0,13).map((row,i)=>({id:row.id,title:i===0?'非常长的题名 '.repeat(20):row.title,letter:String.fromCharCode(65+i)}))}};
 if(path==='contests/replay-options')return {contests:[]};
 throw Error('Unexpected fixture API '+path);
};
function Fixture(){
 const [screen,setScreen]=useState('lists'),[adding,setAdding]=useState(null),[prefs,updatePrefs]=useState(()=>JSON.parse(localStorage.getItem('revision1421-preferences')||'{}'));
 const setPrefs=update=>updatePrefs(previous=>{const next=typeof update==='function'?update(previous):update;localStorage.setItem('revision1421-preferences',JSON.stringify(next));return next;});
 fixture.screen=setScreen;fixture.add=setAdding;
 const today=new Date().toLocaleDateString('sv-SE'),days=[0,1,4,7,10,13,16,19,24].map((n,i)=>{const date=new Date(today+'T00:00:00Z');date.setUTCDate(date.getUTCDate()-i);return {date:date.toISOString().slice(0,10),officialAccepted:n};});
 return <div className="workspace-area" style={{height:'100dvh',padding:16,display:'flex',flexDirection:'column'}}>{screen==='difficulty'?<DifficultyDisplayProvider mode={prefs.difficultyDisplay}><VisualPreferences prefs={prefs} setPrefs={setPrefs}/><div data-testid="difficulty-preview"><Difficulty row={{difficulty:900,difficultyEstimated:true,platform:'洛谷'}} value={900}/><Difficulty row={{difficulty:1200,difficultyEstimated:true,platform:'AtCoder'}} value={1200}/></div></DifficultyDisplayProvider>:screen==='lists'?<TrainingListsPage rows={rows} api={api} visit={visit} prefs={{favorites:['p1']}} onAddToList={ids=>setAdding(Array.isArray(ids)?ids:[ids])}/>:screen==='activity'?<ActivityPage insights={{activity:days}}/>:<MockSetup api={api} rows={rows} onError={console.error}/>} {adding&&<AddToTrainingLists problemIds={adding} api={api} onSave={()=>setAdding(null)} onClose={()=>setAdding(null)}/>}</div>;
}
createRoot(document.getElementById('root')).render(<Fixture/>);
