import React,{useState} from 'react';
import {createRoot} from 'react-dom/client';
import TaskContinuation from '../src/components/TaskContinuation.jsx';
import TasksBoard from '../src/components/TasksBoard.jsx';
import {TeamStandings} from '../src/components/RankingsWorkspace.jsx';
import {trainingDay} from '../src/lib/trainingDate.js';
import '../src/styles/workspace.css';
const date=trainingDay(),start={revision:'1',config:{goal:{title:'训练目标'},weekdayMinutes:60,weekendMinutes:60},plan:{id:'flow',tasks:[{key:'read',id:'read',kind:'lecture',title:'阅读窗口边界',minutes:20,status:'pending',date},{key:'practice',id:'practice',kind:'problem',title:'独立练习窗口',minutes:40,status:'pending',date}],tracks:[],days:[]},topics:[],availableTopics:[],history:[],recommendation:{title:'窗口'}};
function App(){
 const [owner,setOwner]=useState('fixture-owner'),[snapshot,setSnapshot]=useState(start),[training,setTraining]=useState([{id:'practice',title:'独立练习窗口',accepted:false}]),[content,setContent]=useState(null),[prefs,setPrefs]=useState({});window.__tbAccountUserId=owner;
 const actions=[{id:'practice',kind:'problem',page:'mine',title:'独立练习窗口'},{id:'replay',kind:'replay',page:'mock',title:'选择一场重现赛'}];
 const update=async(action,body)=>{window.flowCalls.push({action,...body});if(action==='complete'){const value={...snapshot,revision:String(Number(snapshot.revision)+1),plan:{...snapshot.plan,tasks:snapshot.plan.tasks.map(task=>task.key===body.key?{...task,status:'done'}:task)}};setSnapshot(value);return value;}return snapshot;};
 const open=item=>{window.flowOpened.push(item);setContent({kind:item.kind,id:item.id});};
 window.flowCalls=window.flowCalls||[];window.flowOpened=window.flowOpened||[];window.flow={read:()=>setContent({kind:'lecture',id:'read'}),accept:()=>{setSnapshot(previous=>({...previous,revision:String(Number(previous.revision)+1),plan:{...previous.plan,tasks:previous.plan.tasks.map(task=>({...task,status:'done'}))}}));setTraining([{id:'practice',title:'独立练习窗口',accepted:true}]);},switchOwner:()=>{setOwner('another-owner');setContent(null);}};
 return <><TaskContinuation owner={owner} snapshot={snapshot} training={training} actions={actions} content={content} update={update} onOpen={open}/><div style={{height:700}}><TasksBoard owner={owner} model={{snapshot,update}} prefs={prefs} setPrefs={setPrefs} api={async()=>({})} dailyTasks={{tasks:[]}} onOpenTask={open}/></div><TeamStandings snapshot={{entries:[{teamId:'second',name:'乙队',totalScore:60},{teamId:'first',name:'甲队',totalScore:120},{teamId:'tie',name:'丙队',totalScore:60},{teamId:'invalid',name:'无效成绩',totalScore:null}]}}/></>;
}
document.documentElement.dataset.theme='dark';createRoot(document.getElementById('root')).render(<App/>);
