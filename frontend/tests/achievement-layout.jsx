import React,{useState} from 'react';
import {createRoot} from 'react-dom/client';
import {AchievementPanel} from '../src/pages/ProgressPanels.jsx';
import RankingMedal from '../src/components/RankingMedal.jsx';
import '../src/styles/workspace.css';
import '../src/styles/polish.css';
import '../src/styles/unified.css';
import '../src/styles/revision.css';
import '../src/styles/interaction.css';

const items=[
 {id:'morning',name:'晨光第一行',description:'早上提交一次',unlocked:true,unlockedAt:'2026-11-01T00:00:00Z',rewardClaimed:false,rewardXp:20},
 {id:'hard',name:'巅峰解题者',description:'首次 AC 一道难度至少 2300 的题目',unlocked:true,unlockedAt:'2026-10-31T12:00:00Z',rewardClaimed:true,rewardTitle:{id:'difficulty-3600',name:'巅峰解题者',category:'difficulty',target:2300}},
 {id:'long',name:'连续多次间隔复习的长成就名称',description:'三次间隔复习均先错误提交后 AC',unlocked:true,unlockedAt:'2026-10-31T11:00:00Z',rewardClaimed:false,rewardXp:30},
 {id:'later',name:'单日二十题',description:'一天内 AC 二十道不同题目',unlocked:false,progress:8,target:20,rewardXp:80},
];
function Fixture(){
 const [achievements,setAchievements]=useState(items),[claims,setClaims]=useState(0);
 window.rewardFixture={claims,setTheme:value=>document.documentElement.dataset.theme=value};
 return <main style={{maxWidth:1000,margin:'auto',padding:20}}>
  <AchievementPanel achievements={achievements} onClaim={async id=>{setClaims(value=>value+1);await new Promise(resolve=>setTimeout(resolve,150));setAchievements(previous=>previous.map(item=>item.id===id?{...item,rewardClaimed:true}:item));}}/>
  <div className="ranking-table" style={{display:'grid',gridTemplateColumns:'repeat(6,1fr)',gap:16,marginTop:24}}>{['daily','weekly','total'].flatMap(period=>[1,2,3,8,9,30].map(days=><div key={period+days} data-period={period} style={{display:'grid',placeItems:'center'}}><RankingMedal period={period} rank={1} dominance={{days}}/></div>))}</div>
 </main>;
}
document.documentElement.dataset.theme='light';
createRoot(document.getElementById('root')).render(<Fixture/>);
