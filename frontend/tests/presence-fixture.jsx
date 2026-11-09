import React,{useState} from 'react';
import {createRoot} from 'react-dom/client';
import usePresence from '../src/lib/usePresence.js';
import {registerShortcutRoute} from '../src/lib/applicationShortcuts.js';
import RankingsPage from '../src/pages/CommunityPanel.jsx';
import DuelCommunity from '../src/components/DuelCommunity.jsx';
import '../src/styles/workspace.css';
import '../src/styles/refinements.css';
import '../src/styles/polish.css';
import '../src/styles/unified.css';
import '../src/styles/revision.css';
import '../src/styles/interaction.css';
import '../src/styles/followups-160.css';
import '../src/pages/ProgressPanels.css';
document.documentElement.dataset.theme='dark';
const ids=Array.from({length:5},(_,i)=>`${i+1}0000000-0000-4000-8000-000000000001`);
const users=ids.map((userId,i)=>({userId,activity:['problem','replay','lecture','lab','wiki'][i]}));
const entries=users.map((item,i)=>({...item,rank:i+1,nickname:['甲','乙','丙','丁','戊'][i],rating:1100-i*30,count:20-i,online:true}));
entries.push({userId:'60000000-0000-4000-8000-000000000001',rank:6,nickname:'未打开',rating:900,count:1,online:false,idle:false,activity:null});
const activities=new Map(users.map(row=>[row.userId,row.activity]));
const controls={ids,calls:[],hold:null,pending:[],fail:false,native:{available:false}};window.presenceFixture=controls;
controls.shortcutsHandled=0;
registerShortcutRoute({key:'presence-shortcut-interoperability',bindings:[{id:'next',combo:'Ctrl+ArrowRight'}],
 handle:()=>{controls.shortcutsHandled++;return true;},enabled:()=>Boolean(window.__tbAccountUserId)});
function snapshots(){
 const active=users.filter(row=>!['idle','offline'].includes(activities.get(row.userId))).map(row=>({...row,activity:activities.get(row.userId)}));
 const idleUsers=users.filter(row=>activities.get(row.userId)==='idle').map(row=>({userId:row.userId,activity:'idle'}));
 return {active,idleUsers,entries:entries.map(row=>({...row,online:active.some(user=>user.userId===row.userId),idle:idleUsers.some(user=>user.userId===row.userId),activity:activities.get(row.userId)==='offline'?null:activities.get(row.userId)||null}))};
}
async function api(path,body){
 const owner=window.__tbAccountUserId;controls.calls.push({path,body,owner});
 if(path==='desktop/input-activity')return {...controls.native,...(controls.native.at===undefined?{}:{ageSeconds:(performance.now()-controls.native.at)/1000})};
 if(path==='presence'){
  if(controls.fail)throw new Error('Fixture offline');
  if(controls.hold===owner)return new Promise(resolve=>controls.pending.push(resolve));
  activities.set(owner,body.activity);const {active,idleUsers}=snapshots();
  return {owner,available:true,serverNow:Date.now(),count:owner===ids[1]?2:active.length,users:active,idleUsers};
 }
 if(path.startsWith('leaderboard?')){const {entries}=snapshots();return {configured:true,status:'ready',hasSnapshot:true,period:new URL('http://fixture/'+path).searchParams.get('period'),date:new Date(Date.now()+8*3600000).toISOString().slice(0,10),entries,self:entries.find(row=>row.userId===owner)};}
 if(path.startsWith('duel/board?'))return {owner,mode:new URL('http://fixture/'+path).searchParams.get('mode'),date:'2026-11-04',entries:snapshots().entries,records:[{id:'record-1',finishedAt:Date.now(),winner:ids[0],players:[{userId:ids[0],nickname:'甲',rating:1000,change:20},{userId:ids[1],nickname:'乙',rating:1000,change:-20}]}],next:null};
 throw new Error('Unexpected presence fixture route: '+path);
}
function Fixture(){
 const [owner,setOwner]=useState(undefined),[activity,setActivity]=useState('online'),[mode,setMode]=useState('ranked');
 const presence=usePresence(api,owner,activity);
 controls.owner=(value,next='problem')=>{window.__tbAccountUserId=value;setOwner(value);setActivity(next);};controls.activity=setActivity;controls.mode=setMode;
 return <main style={{padding:20,color:'var(--text)',background:'var(--bg)',minHeight:'100dvh',minWidth:0}}>
  <span role="status" aria-label="在线人数">在线 · {presence?.available?presence.count:'—'}人</span>
  <RankingsPage api={api} presence={presence}/>
  <DuelCommunity api={api} owner={owner} mode={mode}/>
 </main>;
}
createRoot(document.getElementById('root')).render(<Fixture/>);
