import React,{useRef,useState} from 'react';
import {createRoot} from 'react-dom/client';
import {LecturesPanel} from '../src/pages/LecturesPanel.jsx';
import LearningBrowser from '../src/app/LearningBrowser.jsx';
import {AchievementPanel} from '../src/pages/ProgressPanels.jsx';
import {FOUNDATION_LESSONS} from '../src/lib/learningCurriculum.js';
import '../src/styles/workspace.css';
import '../src/styles/refinements.css';
import '../src/styles/unified.css';
import '../src/styles/revision.css';
import '../src/styles/followups-1434.css';
import 'katex/dist/katex.min.css';
const foundations=FOUNDATION_LESSONS.filter(item=>item.kind==='language');
const entries=[...foundations.map(item=>({...item,concept:item.title,markdown:`## ${item.title}\n\n`+'隔离测试正文。\n\n'.repeat(80),images:{}})),
 {id:'encountered',title:'已练习题的讲解',sourceProblemIds:['reached'],markdown:'## 已练习题\n\n来自实际队列投影的测试正文。',images:{}},
 {id:'unseen',title:'尚未练习题的讲解',sourceProblemIds:['future'],markdown:'## 隐藏条目',images:{}},
 {id:'read-before',title:'以前读过的讲解',sourceProblemIds:['old'],markdown:'## 保留已读内容',images:{}}];
const snapshot=()=>({lectures:entries,learningQueue:{version:1,foundationIds:foundations.map(item=>item.id),encounteredIds:['encountered']}});
const api=async path=>path==='lectures'?snapshot():path.startsWith('lecture?id=')?entries.find(item=>item.id===decodeURIComponent(path.slice(11))):path==='templates'?{templates:[]}:path==='wiki'?{articles:[]}:{};
const medals=[...[500,750,1000,1500,2000].map((target,i)=>({id:'ac-'+target,name:'AC '+target+'题',description:'AC 不同题目',target,progress:114,rewardTitle:{name:['解题能手','解题精英','千题大师','解题宗师','双千传奇'][i],category:'ac',target}})),
 ...[1500,1600,1700,1800,1900,2000,2150,2300].map(target=>({id:'difficulty-'+target,name:'突破 '+target,description:'首次 AC 指定难度的新题',target:1,progress:0,rewardXp:180,rewardTitle:{name:'难度进阶成就勋章 '+target,category:'difficulty',target}}))];
function Fixture(){
 const [prefs,setPrefs]=useState({learnedLectures:['read-before'],learningPaths:{}}),[active,setActive]=useState(false),[gallery,setGallery]=useState(false),browser=useRef(null),visit=useRef({});
 window.__tbAccountUserId='guidance-owner';
 window.guidanceFixture={prefs:()=>prefs,state:()=>browser.current.getState(),gallery:()=>setGallery(true),home:()=>browser.current.hide()};
 return <div className="app-shell"><div id="tb-page-search"/>{gallery?<main style={{width:'min(950px,calc(100vw - 32px))',margin:'16px auto'}}><AchievementPanel achievements={medals}/></main>:<>
  <main hidden={active} style={{height:'100vh',padding:18}}><LecturesPanel lectures={snapshot()} api={api} visit={visit.current} prefs={prefs} setPrefs={setPrefs} onOpenLecture={id=>browser.current.open({kind:'lecture',id,title:entries.find(item=>item.id===id)?.title})}/></main>
  <LearningBrowser ref={browser} api={api} accountId="guidance-owner" ready prefs={prefs} setPrefs={setPrefs} onActiveChange={value=>setActive(value)} onTrain={()=>{}}/>
 </>}</div>;
}
document.documentElement.dataset.theme='dark';createRoot(document.getElementById('root')).render(<Fixture/>);
