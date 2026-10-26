import React,{useState,useEffect} from 'react';
import {createRoot} from 'react-dom/client';
import ActivityPage from '../src/pages/ActivityPage.jsx';
import PagePagination from '../src/components/PagePagination.jsx';
import SubmissionRecords from '../src/pages/SubmissionRecords.jsx';
import TrainingListsPage from '../src/pages/TrainingListsPage.jsx';
import PreferencesPage from '../src/pages/PreferencesPage.jsx';
import {CompetitionPage,GrowthPage} from '../src/pages/ProgressPanels.jsx';
import LearningPathsPage from '../src/pages/LearningPathsPage.jsx';
import MockSetup from '../src/app/MockSetup.jsx';
import RandomProblem from '../src/components/RandomProblem.jsx';
import RankingsPage from '../src/pages/CommunityPanel.jsx';
import useNavigationKeys from '../src/lib/useNavigationKeys.js';
import '../src/styles/workspace.css';
import '../src/styles/refinements.css';
import '../src/styles/polish.css';
import '../src/styles/unified.css';
import '../src/styles/revision.css';
const mode=new URLSearchParams(location.search).get('view')||'activity';
const rows=Array.from({length:40},(_,i)=>({id:'p'+i,title:'练习 '+i,platform:'AtCoder',contest:'ABC '+(480-i),problem:'A',url:`https://atcoder.jp/contests/abc${480-i}/tasks/abc${480-i}_a`,difficulty:800+i*100,tags:['前缀和']}));
const logs=Array.from({length:60},(_,i)=>({id:'s'+i,problemId:rows[i%40].id,title:'练习 '+i,submittedAt:new Date(Date.UTC(2026,9,25-Math.floor(i/3),10,i%3)).toISOString(),verdict:i%3?'WA':'AC'}));
const avatar='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jPqEAAAAASUVORK5CYII=';
window.fixture={calls:[],avatar};
async function api(path,body){window.fixture.calls.push({path,body});const q=new URLSearchParams(path.split('?')[1]);
 if(path.startsWith('submissions')){const offset=Number(q.get('offset'));return {total:logs.length,offset,submissions:logs.slice(offset,offset+Number(q.get('limit')))};}
 if(path==='training-lists')return {lists:[{id:'test',title:'前缀和练习',available:true,children:[],categories:[{id:'practice',name:'专题练习'}],problems:rows.map(row=>({pid:row.problem,problemId:row.id,url:row.url}))}]};
 if(path.startsWith('leaderboard/avatar'))return {avatarData:avatar,avatarHash:'a'.repeat(64)};
 if(path.startsWith('leaderboard'))return {configured:true,status:'ready',hasSnapshot:true,date:'2026-10-26',period:q.get('period')||'daily',entries:[{rank:1,userId:'10000000-0000-4000-8000-000000000001',nickname:'自己',count:8,publicProgress:{level:9,currentLevelXp:50,nextLevelXp:200,titles:[]}},{rank:2,userId:'10000000-0000-4000-8000-000000000002',nickname:'另一位用户',count:3,avatarHash:'a'.repeat(64),publicProgress:{level:8,currentLevelXp:150,nextLevelXp:200,titles:[]}}],self:{userId:'10000000-0000-4000-8000-000000000001'}};
 if(path==='contests/events')return {events:[167,166,165].map(n=>({name:'周赛 '+n,displayName:'周赛 '+n,platform:'牛客',series:'周赛',count:7,duration:120,rules:'acm'}))};
 if(path==='goals')return {goals:[],contestPlan:{contests:[]}};
 return {};
}
function Fixture(){useNavigationKeys();const [page,setPage]=useState(1),[prefs,setPrefs]=useState({learningPaths:{},motion:true,theme:'dark',panelStyle:'minimal',panelOpacity:76}),[tab,setTab]=useState('home');useEffect(()=>{document.documentElement.dataset.motion=prefs.motion?'on':'off';},[prefs.motion]);return <><div id="tb-page-search" style={{height:60,display:'flex',gap:12,alignItems:'center',paddingLeft:30}}/><main className="workspace-area" style={{height:'calc(100dvh - 80px)',padding:12}}>
 {mode==='activity'?<ActivityPage insights={{activity:Array.from({length:25},(_,i)=>({date:`2026-10-${String(i+1).padStart(2,'0')}`,officialAccepted:i+1}))}}/>:
 mode==='records'?<SubmissionRecords api={api} rows={rows}/>:
 ['lists','list-problems'].includes(mode)?<TrainingListsPage rows={rows} api={api} visit={mode==='list-problems'?{state:{curriculumVersion:1,mode:'source',trail:['test']}}:undefined} onTrain={id=>window.fixture.calls.push({train:id})}/>:
 mode==='competitions'?<CompetitionPage rows={rows} workspace={{training:[],contests:[]}} hub={{}} onStartReproduction={()=>{}}/>:
 mode==='settings'?<PreferencesPage tab={tab} onTab={setTab} prefs={prefs} setPrefs={setPrefs} api={api} rows={rows} commands={{pages:[]}} display={{available:false,fullscreen:false}} onTutorial={()=>{window.fixture.guideOpened=true;}}/>:
 mode==='growth'?<GrowthPage rows={rows} api={api} account={{userId:'self',nickname:'练习者'}} insights={{summary:{totalSolved:10,submissions:20,activeDays:5,streak:3},growth:{level:9,currentLevelXp:50,nextLevelXp:200,titles:[]},knowledge:[],assessment:{rating:1000,evidenceCount:5,platforms:[]}}}/>:mode==='lab'?<LearningPathsPage standalone prefs={prefs} setPrefs={setPrefs}/>:
 mode==='mock'?<div className="mock-page"><MockSetup api={api} categories={[{name:'基础技巧',children:[{name:'前缀和',tags:['前缀和']}]}]}/></div>:
 mode==='random'?<div style={{display:'flex',justifyContent:'center'}}><RandomProblem rows={rows} onChoose={()=>{window.fixture.chosen=true;}}/></div>:
 mode==='rankings'?<RankingsPage api={api} avatarData={avatar} ownGrowth={{level:9,currentLevelXp:80,nextLevelXp:200}}/>:
 <div className="list-page"><div className="table-scroll" style={{flex:1}}>题库</div><PagePagination label="题库分页" count="共 13268 题" page={page} pages={1021} previousLabel="题库上一页" nextLabel="题库下一页" onPrevious={()=>setPage(page-1)} onNext={()=>setPage(page+1)}/></div>}
 </main></>;}
document.documentElement.dataset.theme='dark';
createRoot(document.getElementById('root')).render(<Fixture/>);
