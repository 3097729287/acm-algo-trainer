import React,{useCallback,useState} from 'react';
import {createRoot} from 'react-dom/client';
import WikiPage from '../src/pages/WikiPage.jsx';
import DuelPage from '../src/pages/DuelPage.jsx';
import {GrowthPage,DailyTasks} from '../src/pages/ProgressPanels.jsx';
import useDuel from '../src/lib/useDuel.js';
import '../src/styles/workspace.css';
import '../src/styles/revision.css';
const auth=JSON.parse(sessionStorage.getItem('next-auth'));
window.__tbAccountUserId=auth.account.userId;
document.documentElement.dataset.theme='dark';
function Fixture(){
 const [page,setPage]=useState('growth');
 const api=useCallback(async(path,body)=>{
  const url=path.startsWith('wiki')?'/test-wiki'+path.slice(4):'/online/v1/'+path.replace(/^duel/,'duels');
  const response=await fetch(url,{method:body===undefined?'GET':'POST',headers:{'Content-Type':'application/json','X-TB-User':auth.account.userId,Authorization:'Bearer '+auth.token},...(body===undefined?{}:{body:JSON.stringify(path==='duel/join'?{...body,handle:auth.handle}:body)})});
  const value=await response.json();if(!response.ok){const issue=new Error(value.error);issue.status=response.status;throw issue;}
  if(path.startsWith('stickers/')){const read=await fetch('/online/v1/stickers',{headers:{'X-TB-User':auth.account.userId,Authorization:'Bearer '+auth.token}});return read.json();}
  return value;
 },[]);
 const duel=useDuel(api,auth.account.userId);
 const growth={level:8,currentLevelXp:120,nextLevelXp:900,ranked:{tier:'黑铁',badge:'tier-1',qualified:true,abilityScore:1200}},summary={officialSolved:18,submissions:32,activeDays:6,streak:3,completedContests:2,longestStreak:4};
 const tasks=['common','rare','epic','legendary'].map((stickerRarity,i)=>({id:stickerRarity,stickerRarity,title:'任务 '+(i+1),description:'通过一道题目',progress:0,target:1,xp:10*(i+1)}));
 return <main style={{height:'100dvh',display:'flex',flexDirection:'column',padding:12,gap:12}}><nav style={{display:'flex',gap:16}}>{['growth','wiki','duel','tasks'].map(id=><button type="button" key={id} onClick={()=>setPage(id)}>{id}</button>)}</nav><div style={{flex:1,minHeight:0}}>{page==='growth'?<GrowthPage api={api} account={auth.account} profile={auth.account} insights={{summary,growth,knowledge:[]}} goalOverview={{goals:[]}}/>:page==='wiki'?<WikiPage api={api}/>:page==='duel'?<DuelPage duel={duel} rows={[]} onTrain={()=>{}}/>:<DailyTasks dailyTasks={{tasks,date:'2026-11-02'}}/>}</div></main>;
}
createRoot(document.getElementById('root')).render(<Fixture/>);
