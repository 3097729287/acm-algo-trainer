import React from 'react';
import {createRoot} from 'react-dom/client';
import MockSetup from '../src/app/MockSetup.jsx';
import {CompetitionPage} from '../src/pages/ProgressPanels.jsx';
import RankingsPage from '../src/pages/CommunityPanel.jsx';
import '../src/styles/workspace.css';
import '../src/styles/polish.css';
import '../src/styles/revision.css';
import '../src/styles/followups-160.css';
import '../src/styles/navigation-review.css';

const definitions=[['1024数学专场考核',10,'牛客','nowcoder:142622','https://ac.nowcoder.com/acm/contest/142622/'],['1101 TTC(Team Training Contest)',12,'Codeforces','codeforces:728862','https://codeforces.com/gym/728862/problem/'],['1025 Graph Theory Assessment',8,'Codeforces','codeforces:726517','https://codeforces.com/gym/726517/problem/']];
const rows=definitions.flatMap(([contest,count,platform,id,url])=>Array.from({length:count},(_,i)=>({id:'remote:'+id+'::'+String.fromCharCode(65+i),contest,platform,problem:String.fromCharCode(65+i),title:'测试赛题 '+(i+1),url:url+String.fromCharCode(65+i),difficulty:800+i*100,tags:[],schoolTraining:true,contestProblemCount:count,solutionAvailable:true,catalogContentReady:id!=='nowcoder:142622',catalogReplayReady:id!=='nowcoder:142622',source:'remote'})));
const events=definitions.map(([name,count,platform])=>({name,displayName:name,count,expectedCount:count,schoolTraining:true,complete:true,duration:120,rules:'acm',platform}));
window.navigationFixture={calls:[]};
async function api(path,body){
 window.navigationFixture.calls.push({path,body});
 if(path==='contests/events')return {events:new URLSearchParams(location.search).has('unready')?events.slice(1):events};
 if(path.startsWith('problem?'))return {statementAvailable:true,markdown:'Fixture problem statement',samples:[{input:'1',output:'2'}]};
 if(path==='contests/preview')return {plan:{previewId:'fixture-preview',event:{name:body.contest,displayName:body.contest},slots:rows.filter(row=>row.contest===body.contest).map(row=>({...row,letter:row.problem})),duration:120,strategy:'replay',difficultyRange:{min:800,max:1700}}};
 if(path.startsWith('leaderboard?'))return {configured:true,hasSnapshot:true,status:'ready',self:{userId:'self'},entries:['短','一个很长的测试昵称','InkStarry'].map((nickname,i)=>({userId:String(i),nickname,rank:i+1,count:22-i,online:i!==2,activity:{page:i===0?'mock':'rankings'},likes:{total:1},publicProgress:{level:i+1}}))};
 if(path==='social'||path==='profile'||path==='social/avatars')return {};
 return {};
}
document.documentElement.dataset.theme='dark';
const mode=new URLSearchParams(location.search).get('mode');
createRoot(document.getElementById('root')).render(<main className="workspace-area" style={{height:'100vh',padding:18}}>{mode==='mock'?<MockSetup rows={rows} api={api} onStarted={()=>{}} onError={()=>{}}/>:mode==='rankings'?<RankingsPage api={api}/>:<CompetitionPage rows={rows} workspace={{training:[],contests:[]}} onStartReproduction={()=>{}}/>}</main>);
