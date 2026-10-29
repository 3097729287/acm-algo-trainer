import React from 'react';
import {createRoot} from 'react-dom/client';
import ProfileBadge from '../src/components/ProfileBadge.jsx';
import MedalEmblem from '../src/components/MedalEmblem.jsx';
import {TIER_NAMES} from '../src/components/TierIcon.jsx';
import PracticeStreak from '../src/components/PracticeStreak.jsx';
import {AchievementPanel} from '../src/pages/ProgressPanels.jsx';
import KnowledgeRadar,{KNOWLEDGE_DOMAINS} from '../src/components/KnowledgeRadar.jsx';
import '../src/styles/workspace.css';
import '../src/styles/polish.css';
import '../src/styles/unified.css';
import '../src/styles/revision.css';

document.documentElement.dataset.theme='dark';
document.documentElement.dataset.accent='teal';
const view=new URLSearchParams(location.search).get('view');
const achievements=[
 ['difficulty-1500','进阶第一步'],['difficulty-1800','攻坚突破'],['difficulty-2100','高难突破'],['difficulty-2400','钻石攻坚者'],
 ['difficulty-2700','大师挑战者'],['difficulty-3000','宗师突破'],['difficulty-3300','王者之路'],['difficulty-3600','巅峰解题者'],
 ['independent-5','独立五题'],['independent-25','独立积累'],['independent-100','百题先锋'],['independent-300','算法精英'],
 ['contest-1','完成模拟赛'],['contest-5','模拟赛常客'],['streak-30','连续训练 30 天'],['streak-90','连续训练 90 天'],
 ['streak-180','连续训练 180 天'],['streak-365','连续训练 365 天'],['streak-730','连续训练 2 年'],['platforms-2','跨平台练习'],
 ['missions-1','领取每日奖励'],['missions-10','任务积累'],['missions-50','日积月累'],
].map(([id,name])=>({id,name,description:name,target:100,progress:12,unlocked:false,rewardXp:40}));
if(view==='streak'){
 createRoot(document.getElementById('root')).render(<main style={{padding:28,color:'var(--text)',background:'var(--bg)',minHeight:'100vh'}}>
  <h1 style={{fontSize:20}}>连续练习火焰</h1>
  <div className="streak-preview" style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(110px,1fr))',gap:18,maxWidth:1100}}>
   {[1,2,4,7,15,30,60].map(days=><section key={days} style={{display:'grid',gap:16,justifyItems:'center',padding:20,border:'1px solid var(--line)',borderRadius:12,background:'var(--panel)'}}>
    <span>{days} 天起</span><PracticeStreak days={days}/><PracticeStreak days={days} completedToday/>
   </section>)}
  </div>
 </main>);
}
else if(view==='radar-frequency'){
 const topics=Array.from({length:26},(_,i)=>`知识点${String(i+1).padStart(2,'0')}`),rows=[];
 const counts=topics.map((name,i)=>({name,count:3+(i*11)%26}));
 for(const {name,count} of counts)for(let i=0;i<count;i++)rows.push({id:`${name}-${i}`,url:`https://example.invalid/${name}/${i}`,tags:[name]});
 // Aliases/duplicate catalog records must not inflate distinct availability.
 rows.push({...rows[0],id:'mirror-of-first'});
 rows.push({id:'rare-a',url:'https://example.invalid/rare/shared',tags:['罕见甲','罕见乙']},{id:'rare-b',url:'https://example.invalid/rare/second',tags:['罕见乙']});
 const categories=[{name:'基础技巧',children:[...topics,'罕见甲','罕见乙'].map(name=>({name}))}];
 window.radarFrequencyExpected=[...counts,{name:'杂项',count:2}].sort((a,b)=>b.count-a.count);
 createRoot(document.getElementById('root')).render(<main style={{padding:24,maxWidth:1000}}><KnowledgeRadar rows={rows} categories={categories}/></main>);
}
else if(view==='radar-performance'){
 const topics=KNOWLEDGE_DOMAINS.flatMap(domain=>domain.topics.map(([name])=>name));
 const rows=Array.from({length:6000},(_,id)=>({id:String(id),url:`https://example.com/${id}`,tags:[topics[id%topics.length],topics[(id+7)%topics.length]],knowledgeCategories:[]}));
 const knowledge=topics.map((name,index)=>({name,evidenceIds:Array.from({length:60},(_,id)=>(index*13+id)%500)}));
 const evidence=Array.from({length:500},(_,id)=>({id,rated:true,score:70,weight:1,solved:true}));
 window.radarStarted=performance.now();
 function MeasuredRadar(){React.useEffect(()=>{window.radarReady=performance.now();},[]);return <main style={{padding:24,maxWidth:1000}}><KnowledgeRadar rows={rows} knowledge={knowledge} knowledgeEvidence={evidence}/></main>;}
 createRoot(document.getElementById('root')).render(<MeasuredRadar/>);
}
else if(view==='radar')createRoot(document.getElementById('root')).render(<main style={{padding:24,maxWidth:960}}><KnowledgeRadar knowledge={[{name:'KMP',evidenceIds:[0,1,2,3,4],available:200},{name:'字典树',evidenceIds:[5,6,7],available:100}]} knowledgeEvidence={Array.from({length:8},(_,id)=>({id,rated:id<5,difficulty:id<5?1800:null,weight:1,solved:true}))}/></main>);
else if(view==='achievements')createRoot(document.getElementById('root')).render(<main style={{padding:28}}><AchievementPanel achievements={achievements}/></main>);
else
createRoot(document.getElementById('root')).render(<main className="tier-preview-grid" style={{display:'grid',gridTemplateColumns:'repeat(5,minmax(0,1fr))',gap:20,padding:28}}>
 {TIER_NAMES.map((tier,index)=><section className="tier-preview" key={tier} style={{display:'flex',flexDirection:'column',alignItems:'center',gap:22,padding:'28px 16px',border:'1px solid var(--line)',borderRadius:16,background:'var(--panel)'}}>
  <ProfileBadge compact={false} nickname={tier} growth={{level:8,currentLevelXp:975,nextLevelXp:1600,ranked:{badge:`tier-${index}`,tier,qualified:true,abilityScore:800+index*200}}}/>
  <MedalEmblem index={index} size={100}/>
 </section>)}
 <section style={{gridColumn:'1 / -1',display:'flex',gap:28,justifyContent:'center'}}>{[0,1,2,4,7,15,30,60].map(days=><PracticeStreak key={days} days={days}/>)}</section>
 <style>{`.tier-preview .profile-badge{border:0;background:transparent;flex-direction:column;gap:14px}.tier-preview .profile-avatar-button{width:110px;height:110px}.tier-preview .profile-avatar-face{width:67%;height:67%}.tier-preview .profile-avatar-face svg{width:32px;height:32px}.tier-preview .profile-level-number{font-size:12px;height:20px;min-width:28px}.tier-preview .profile-nickname{font-size:1rem}`}</style>
</main>);
