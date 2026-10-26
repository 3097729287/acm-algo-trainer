import React from 'react';
import {createRoot} from 'react-dom/client';
import ActivityPage from '../src/pages/ActivityPage.jsx';
import TrainingListsPage from '../src/pages/TrainingListsPage.jsx';
import RankingsPage from '../src/pages/CommunityPanel.jsx';
import '../src/styles/workspace.css';
import '../src/styles/refinements.css';
import '../src/styles/polish.css';
import '../src/styles/unified.css';
import '../src/styles/revision.css';
const image='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/lAAAAABJRU5ErkJggg==';
const rows=[{id:'one',title:'排序题',problem:'P1001',url:'https://www.luogu.com.cn/problem/P1001',tags:['排序'],difficulty:800}];
const lists=[{id:'list',title:'排序专项',available:true,children:[],tags:['数组'],categories:[{id:'practice',name:'专题练习',order:0,position:0}],problems:[{pid:'P1001',problemId:'one'}]}];
let labels={},avatarCalls=0;
const api=async(path,body)=>{
 if(path==='training-lists')return {lists,tags:labels};
 if(path.startsWith('leaderboard/avatar')){window.avatarCalls=++avatarCalls;if(avatarCalls===1)throw new Error('temporary');return {avatarData:image};}
 if(path.startsWith('leaderboard?'))return {configured:true,status:'ready',period:'daily',self:{userId:'self'},date:'2026-10-26',entries:[{userId:'self',nickname:'自己',count:10,publicProgress:{level:9,currentLevelXp:680,nextLevelXp:1800}},{userId:'other',nickname:'有头像的用户',count:5,avatarHash:'fixture',publicProgress:{level:3,currentLevelXp:100,nextLevelXp:400}},{userId:'old',nickname:'旧版用户',count:2,publicProgress:{level:2}}]};
 return {};
};
document.documentElement.dataset.theme='dark';
const mode=new URLSearchParams(location.search).get('view');
createRoot(document.getElementById('root')).render(<><div id="tb-page-search" style={{height:60,display:'flex',alignItems:'center',gap:12}}/><main className="workspace-area" style={{height:'calc(100dvh - 80px)',padding:12}}>{mode==='activity'?<ActivityPage insights={{activity:Array.from({length:26},(_,i)=>({date:'2026-10-'+String(i+1).padStart(2,'0'),officialAccepted:i===25?2:5}))}}/>:mode==='lists'?<TrainingListsPage api={api} rows={rows} onTrain={()=>{}}/>:<RankingsPage api={api} avatarData={image} ownGrowth={{level:9,currentLevelXp:680,nextLevelXp:1800}}/>}</main></>);
