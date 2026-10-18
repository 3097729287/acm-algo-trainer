import React,{useState} from 'react';
import {createRoot} from 'react-dom/client';
import Workbench from '../src/app/Workbench.jsx';
import MockProblemPicker from '../src/app/MockProblemPicker.jsx';
import '../src/styles/workspace.css';
import '../src/styles/refinements.css';

const slots=[{id:'fixture1',letter:'P13089',title:'We are watching you!',verdict:null},{id:'fixture2',letter:'P13090',title:'XCPC',verdict:null}];
const contest={id:'replay',strategy:'replay',status:'running',name:'重现赛 · 福建省赛 2025',accepted:0,total:2,slots};
const fixture=window.replayFixture={calls:[],status:'ready'};
async function api(path,body){
 fixture.calls.push({path,body});
 const url=new URL('http://fixture/'+path);
 if(url.pathname==='/problem')return {id:url.searchParams.get('id'),title:slots.find(s=>s.id===url.searchParams.get('id')).title,url:'https://www.luogu.com.cn/problem/P13089',markdown:'## 题目描述\n\n测试原题面。',draft:'int main() { return 0; }',submissions:[],samples:[],limits:{timeMs:2000,memoryMb:256},statementAvailable:true,locked:true};
 if(path==='draft')return {savedAt:new Date().toISOString()};
 if(path==='official/submit')return {sessionId:'fixture-submit',status:fixture.status,transport:'external'};
 if(url.pathname==='/official/status')return {sessionId:'fixture-submit',status:fixture.status,transport:'external'};
 if(path==='official/close')return {status:'closed'};
 throw Error('Unexpected API '+path);
}
function Fixture(){const [id,setId]=useState(slots[0].id);return <div className="app-shell mock-focus" style={{height:'100dvh',display:'block'}}><Workbench api={api} problemId={id} contest={contest} headerStart={<MockProblemPicker contest={contest} currentId={id} onSelect={setId} onHistory={()=>{}}/>}/></div>}
document.documentElement.dataset.theme='dark';
createRoot(document.getElementById('root')).render(<Fixture/>);
