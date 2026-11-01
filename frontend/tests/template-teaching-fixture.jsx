import React,{useCallback,useState} from 'react';
import {createRoot} from 'react-dom/client';
import TemplatesPage from '../src/pages/TemplatesPage.jsx';
import TemplateStudyCourse from '../src/pages/algorithm-lab/TemplateStudyCourse.jsx';
import {AchievementPanel} from '../src/pages/ProgressPanels.jsx';
import {teachingTemplates} from '../src/lib/templateCurriculum.js';
import BASE from '../../backend/resources/code-templates.json';
import GUIDED from '../../backend/resources/template-guided.json';
import '../src/styles/workspace.css';
import '../src/styles/revision.css';
const templates=teachingTemplates(BASE.templates),calls=[];
const rows=Object.values(GUIDED).flat().map(task=>({id:task.problemId,url:task.url,title:task.title}));
function Fixture(){
 const [page,setPage]=useState('templates'),[course,setCourse]=useState('binary-search'),[prefs,setPrefs]=useState({}),[locked,setLocked]=useState([]),[claims,setClaims]=useState([]);
 const api=useCallback(async path=>{if(path==='templates')return {templates};throw Error('Unexpected isolated API '+path);},[]);
 const train=(id,options)=>calls.push({id,options});
 window.templateTeachingFixture={prefs,calls,setLocked,setCourse,setPage};
 const moments=[{id:'moment-rebound',name:'好，刚才不算',description:'错误回执后再 AC',progress:0,target:1},
  {id:'moment-42',name:'宇宙终极答案',description:'不应提前出现的条件',hidden:true,unlocked:false,target:1},
  {id:'moment-semicolon',name:'; 救世主',description:'仅补上一个分号后 AC',hidden:true,unlocked:true,target:1,progress:1,rewardXp:15,rewardClaimed:claims.includes('moment-semicolon')}];
 return <main style={{height:'100dvh',display:'flex',flexDirection:'column',gap:10,padding:12}}><nav style={{display:'flex',gap:12}}>{['templates','binary-search','window-extrema','achievements'].map(id=><button key={id} type="button" onClick={()=>{if(['binary-search','window-extrema'].includes(id)){setCourse(id);setPage('study');}else setPage(id);}}>{id}</button>)}</nav><div style={{flex:1,minHeight:0,display:'flex'}}>{page==='templates'?<TemplatesPage api={api} onTrain={train} lockedProblems={locked} onOpenCourse={id=>{setCourse(id);setPage('study');}}/>:page==='study'?<TemplateStudyCourse key={course} courseId={course} prefs={prefs} setPrefs={setPrefs} rows={rows} lockedProblems={locked} onTrain={train}/>:<AchievementPanel achievements={moments} onClaim={async id=>setClaims(value=>[...new Set([...value,id])])}/>}</div></main>;
}
createRoot(document.getElementById('root')).render(<Fixture/>);
