import React,{useState} from 'react';
import {createRoot} from 'react-dom/client';
import TasksBoard from '../src/components/TasksBoard.jsx';
import {trainingDay} from '../src/lib/trainingDate.js';
import '../src/styles/workspace.css';
const now=Date.now(),today=trainingDay(now),startAt=new Date(now+1800000).toISOString(),endAt=new Date(now+9000000).toISOString();
const event={id:'real-calendar',title:'日历里的正式比赛',url:'https://codeforces.com/contest/1000',startAt,endAt};
const snapshot={revision:'1',config:{goal:{title:'原训练目标'},weekdayMinutes:60,weekendMinutes:60},plan:{id:'original-plan',week:today,tracks:[],days:Array.from({length:7},()=>({date:today,minutes:60})),tasks:[{key:'read',id:'read',kind:'lecture',title:'原有学习任务',minutes:20,status:'pending',date:today,order:1},{key:'review',id:'review',kind:'review',title:'原有复习任务',minutes:40,status:'pending',date:today,order:2}]},topics:[],availableTopics:[],history:[],recommendation:{title:'原主线'}};
function App(){const[prefs,setPrefs]=useState({}),[records,setRecords]=useState([]),[owner,setOwner]=useState('account-a'),[clock,setClock]=useState(now);
 window.calendarCalls=window.calendarCalls||[];window.calendarFixture={live:()=>setClock(Date.parse(startAt)+1),running:()=>setRecords([{id:'receipt',name:event.title,status:'running',startedAt:startAt,constraints:{calendarEvent:event},slots:[]}]),complete:()=>{setClock(Date.parse(endAt)+1);setRecords([{id:'receipt',name:event.title,status:'finished',startedAt:startAt,finishedAt:endAt,constraints:{calendarEvent:event},slots:[{judgeScope:'official',attempts:1,verdict:'WA'}]}]);},switchOwner:()=>{setRecords([]);setOwner('account-b');setClock(now);}};
 return <main style={{height:'100dvh'}}><TasksBoard owner={owner} model={{snapshot:{...snapshot,activeContest:records.find(record=>record.status==='running')},update:async()=>snapshot}} api={async()=>({})} prefs={prefs} setPrefs={setPrefs} onOpenTask={task=>window.calendarCalls.push({kind:task.kind,id:task.id})} calendar={{now:clock,snapshot:{contests:[event]}}} contestRecords={records} onCalendarTask={task=>window.calendarCalls.push({kind:task.kind,id:task.id,status:task.status})}/></main>;}
document.documentElement.dataset.theme='dark';createRoot(document.getElementById('root')).render(<App/>);
