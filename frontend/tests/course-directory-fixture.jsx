import React,{useRef,useState} from 'react';
import {createRoot} from 'react-dom/client';
import {LecturesPanel} from '../src/pages/LecturesPanel.jsx';
import ProfileBadge from '../src/components/ProfileBadge.jsx';
import {FOUNDATION_LESSONS} from '../src/lib/learningCurriculum.js';
import {TIER_NAMES} from '../src/lib/rankTiers.js';
import '../src/styles/workspace.css';
import '../src/styles/revision.css';
import '../src/app/LearningBrowser.css';
const lessons=FOUNDATION_LESSONS.filter(item=>item.kind==='language').map((item,index)=>({...item,title:item.title||'基础学习 '+index,concept:item.title||item.id,markdown:'## '+(item.title||'基础学习')+'\n\n'+('阅读正文。\n\n'.repeat(90))}));
const calls=[],api=async path=>path==='lectures'?{lectures:lessons,learningQueue:{foundationIds:lessons.map(item=>item.id)}}:lessons.find(item=>item.id===new URL(path,'https://fixture/').searchParams.get('id'));
function Fixture(){
 const [selected,setSelected]=useState(null),[prefs,setPrefs]=useState({}),visit=useRef({});
 window.courseFixture={calls,lessons};
 const open=id=>{calls.push({kind:'open',id});setSelected(id);},replace=id=>{calls.push({kind:'replace',id});setSelected(id);};
 return <><div id="tb-page-search" style={{height:44}}/>{selected?<div className="study-browser study-compact"><main className="study-pane study-lecture" style={{height:'100vh'}}><LecturesPanel study initialLecture={selected} api={api} prefs={prefs} setPrefs={setPrefs} visit={visit.current} onOpenLecture={open} onNextLecture={replace}/></main></div>:<main className="workspace-area" style={{height:'calc(100vh - 44px)'}}><LecturesPanel api={api} prefs={prefs} setPrefs={setPrefs} onOpenLecture={open}/></main>}<div className="growth-dashboard fixture-profiles" style={{position:'fixed',bottom:16,right:16,zIndex:5,width:'fit-content',background:'var(--panel-base)',padding:8,display:'flex',gap:16}}>{[25,50,75,100].map(value=><ProfileBadge key={value} compact={false} nickname={String(value)+'%'} growth={{level:14,currentLevelXp:value,nextLevelXp:100,ranked:{tier:TIER_NAMES[1],abilityScore:800,qualified:true}}}/>)}</div></>;
}
document.documentElement.dataset.theme='dark';createRoot(document.getElementById('root')).render(<Fixture/>);
