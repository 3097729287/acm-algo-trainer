import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import { AchievementPanel, CompetitionPage, GrowthPage } from '../src/pages/ProgressPanels.jsx';
import '../src/styles/workspace.css';

document.documentElement.dataset.theme = 'dark';
const title = { id:'ac-500', name:'解题能手', category:'ac', target:500, unlockedAt:'2026-10-16T04:00:00Z' };
const profile = { userId:'public-fixture-id', nickname:'成长测试用户' };
const account = { userId:profile.userId, nickname:profile.nickname, loginId:'fixture-login' };
const rows = Array.from({length:85}, (_,index) => ({id:`fixture-${index}`, title:`题目 ${index}`, problem:'A', contest:`ABC ${index + 1}`, platform:'AtCoder', series:'ABC', difficulty:1000, tags:['模拟'], solutionAvailable:true}));
const hub = {settings:{accounts:{codeforces:'fixture-cf',atcoder:'fixture-at'}}, accounts:[], sync:{busy:false}};
const achievements = [
  {id:'official-500',name:'AC 500题',description:'AC 500 道不同题目',target:500,progress:500,unlocked:true,rewardXp:0,rewardTitle:title},
  {id:'streak-30',name:'连续训练 30 天',description:'连续完成训练',target:30,progress:30,unlocked:true,rewardXp:0,rewardTitle:{id:'streak-30',name:'持之以恒',category:'streak',target:30}},
  {id:'official-750',name:'AC 750题',description:'AC 750 道不同题目',target:750,progress:500,unlocked:false,rewardXp:0,rewardTitle:{id:'ac-750',name:'解题精英',category:'ac',target:750}},
];
const insights = {summary:{totalSolved:500,submissions:800,activeDays:45,streak:30,completedContests:4},growth:{level:10,tier:'大师',badge:'tier-7',titles:[title],equippedTitles:[title]},titles:[title],equippedTitles:[title],knowledge:[],achievements,recommendations:[{problem:rows[0],stage:'consolidate'}],assessment:{rating:1200,evidenceCount:10,platforms:[{platform:'codeforces',rating:1300,maxRating:1400},{platform:'atcoder',rating:800,maxRating:850},{platform:'nowcoder',rating:0},{platform:'luogu',rating:0}]}};
window.fixtureRequests = [];
window.fixtureActions = [];
const api = async (path, body) => {
  window.fixtureRequests.push({path,write:body != null});
  if (path==='profile') return {profile,leaderboard:{configured:true}};
  if (path==='account') return {account};
  if (path==='goals') return {goals:[],contestPlan:{contests:[]}};
  if (path==='translation/settings') return {provider:'deepseek',model:'test-model',configured:false,providers:[{id:'deepseek',name:'DeepSeek'}]};
  if (path==='hub/configure') return {...hub,settings:{accounts:body.accounts}};
  if (path==='hub/sync') return hub;
  throw new Error(`Unexpected fixture request: ${path}`);
};
function Fixture() {
  const [view,setView]=useState('growth'),[newIds,setNewIds]=useState(['official-500','streak-30']);
  const onTrain=id=>window.fixtureActions.push({kind:'train',id});
  return <main style={{padding:18,height:'100vh',overflow:'auto'}}><nav aria-label="测试页面"><button onClick={()=>setView('growth')}>成长测试</button><button onClick={()=>setView('competition')}>比赛测试</button><button onClick={()=>setView('achievements')}>成就测试</button></nav>
    {view==='growth' && <GrowthPage api={api} insights={insights} hub={hub} account={account} profile={profile} onTrain={onTrain}/>}
    {view==='competition' && <CompetitionPage rows={rows} workspace={{training:[]}} onTrain={onTrain} onStartReproduction={name=>window.fixtureActions.push({kind:'start',name})}/>}
    {view==='achievements' && <AchievementPanel achievements={achievements} newIds={newIds} onSeen={id=>setNewIds(ids=>ids.filter(value=>value!==id))}/>}
  </main>;
}
createRoot(document.getElementById('root')).render(<Fixture/>);
