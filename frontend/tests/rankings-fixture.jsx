import React from 'react';
import {createRoot} from 'react-dom/client';
import RankingsPage from '../src/pages/CommunityPanel.jsx';
import RankingMedal from '../src/components/RankingMedal.jsx';
import '../src/styles/workspace.css';
import '../src/pages/ProgressPanels.css';

document.documentElement.dataset.theme='dark';
document.body.style.margin='0';
const initial = [
  {rank:1,userId:'10000000-0000-4000-8000-000000000001',nickname:'练习者一',count:128,publicId:'TB-10000000000040008000000000000001',publicProgress:{level:10,tier:'王者',rankTier:'黄金',rankScore:1560,titles:[{id:'ac-500',name:'破题先锋',category:'ac',target:500},{id:'streak-30',name:'月度恒心',category:'streak',target:30}]}},
  {rank:2,userId:'10000000-0000-4000-8000-000000000002',nickname:'练习者二',count:86},
  {rank:3,userId:'10000000-0000-4000-8000-000000000003',nickname:'练习者三',count:62},
  {rank:4,userId:'10000000-0000-4000-8000-000000000004',nickname:'练习者四',count:41},
];
let rows=initial;
window.rankingWrites=[];window.rankingAdmin=true;window.rankingState=null;
async function api(path,body) {
  if(path==='leaderboard/admin/delete') {
    window.rankingWrites.push(body);
    rows=body.userId ? rows.filter(row=>row.userId!==body.userId) : [];
    return {removed:body.userId?1:4};
  }
  if(path==='leaderboard/sync') { window.rankingSyncs=(window.rankingSyncs || 0)+1; return {}; }
  const period=new URL('http://fixture/'+path).searchParams.get('period');
  await new Promise(resolve=>setTimeout(resolve,period==='daily'?50:10));
  return {configured:true,status:'ready',hasSnapshot:true,isAdmin:window.rankingAdmin,period,date:'2026-10-12',entries:rows,self:initial[0],rewardPolicy:{daily:[100,60,30],weekly:[500,300,150]},...window.rankingState};
}
createRoot(document.getElementById('root')).render(<main style={{padding:'28px',color:'var(--text)',background:'var(--bg)',minHeight:'100vh'}}>
  <RankingsPage api={api}/>
  <section aria-label="九种奖牌预览" style={{marginTop:30,padding:24,border:'1px solid var(--line)',borderRadius:12,background:'var(--panel)'}}>
    <h2 style={{fontSize:18,margin:'0 0 20px'}}>奖牌等级</h2>
    <div style={{display:'flex',alignItems:'center',gap:24,flexWrap:'wrap'}}>{['total','weekly','daily'].flatMap(period=>[1,2,3].map(rank=><div key={period+rank} style={{display:'grid',justifyItems:'center',gap:10,width:90}}><RankingMedal period={period} rank={rank}/><span style={{color:'var(--muted)',fontSize:12}}>{({total:'累计',weekly:'本周',daily:'每日'})[period]}第{rank}名</span></div>))}</div>
  </section>
</main>);
