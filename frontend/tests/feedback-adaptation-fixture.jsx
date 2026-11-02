import React,{useCallback,useState} from 'react';
import {createRoot} from 'react-dom/client';
import {Target,Library,History,FlaskConical} from 'lucide-react';
import TemplatesPage from '../src/pages/TemplatesPage.jsx';
import LearningPathsPage from '../src/pages/LearningPathsPage.jsx';
import WikiPage from '../src/pages/WikiPage.jsx';
import NavigationSettings from '../src/pages/NavigationSettings.jsx';
import ThemedSelect from '../src/components/ThemedSelect.jsx';
import ReadingImage from '../src/components/ReadingImage.jsx';
import {AchievementPanel} from '../src/pages/ProgressPanels.jsx';
import TEMPLATES from '../../backend/resources/code-templates.json';
import '../src/styles/workspace.css';
import '../src/styles/refinements.css';
import '../src/styles/polish.css';
import '../src/styles/unified.css';
import '../src/styles/revision.css';
import '../src/styles/interaction.css';
import '../src/styles/followups-1434.css';
import '../src/app/Workbench.css';

const pages=[{id:'mine',label:'我的训练',icon:Target},{id:'library',label:'题库',icon:Library},{id:'paths',label:'实验室',icon:FlaskConical},{id:'records',label:'提交记录',icon:History}];
const diagram=color=>'data:image/svg+xml;base64,'+btoa(`<svg xmlns="http://www.w3.org/2000/svg" width="240" height="160"><g fill="none" stroke="${color}" stroke-width="3"><circle cx="120" cy="30" r="17"/><path d="M110 44L60 120M130 44L180 120"/><circle cx="60" cy="130" r="17"/><circle cx="180" cy="130" r="17"/></g></svg>`);
const achievements=[{id:'semicolon-savior',name:'救世主',description:'在修改后完成一次正式 AC',unlocked:true,rewardClaimed:true,rewardXp:15,rewardSticker:{shape:'semicolon',rarity:'legendary',title:'分号救世主'}},{id:'wiki-explorer',name:'算法旅行家',description:'在线书中打开不同分类的算法条目',unlocked:true,rewardClaimed:true,rewardXp:10,rewardSticker:{shape:'compass',rarity:'rare',title:'知识旅行家'}},{id:'difficulty-3300',name:'王者之路',description:'在高难度题目中完成独立作答',unlocked:true,rewardClaimed:true,rewardXp:80,rewardTitle:{id:'difficulty-3300',name:'王者之路',category:'difficulty'}}];
document.documentElement.dataset.theme='dark';
function Fixture(){
 const [view,setView]=useState('templates'),[theme,setTheme]=useState('dark'),[font,setFont]=useState(18),[language,setLanguage]=useState('cpp17'),[prefs,setPrefs]=useState({navOrder:['paths','records','library','mine'],hiddenNavPages:['paths'],navLabels:{library:'题库'},navCollapsed:true});
 document.documentElement.dataset.theme=theme;document.documentElement.style.fontSize=font+'px';window.feedbackPrefs=prefs;
 const api=useCallback(async path=>path==='templates'?{templates:TEMPLATES.templates}:fetch('/feedback/'+path).then(response=>response.json()),[]);
 return <><nav style={{display:'flex',gap:12,flexWrap:'wrap',padding:10}}>{['templates','lab','wiki','diagram','navigation','rewards','language'].map(id=><button key={id} onClick={()=>setView(id)}>{id}</button>)}<button onClick={()=>setTheme(value=>value==='dark'?'light':'dark')}>theme</button><button onClick={()=>setFont(value=>value===18?26:18)}>font</button></nav><main className="workspace-area" style={{height:'calc(100dvh - 60px)',overflow:'auto'}}>
 {view==='templates'?<TemplatesPage api={api} onOpenDetail={item=>window.openedTemplate=item.id}/>:view==='lab'?<LearningPathsPage catalogOnly rows={[]} prefs={{}} setPrefs={()=>{}} onOpenDetail={item=>window.openedCourse=item.id}/>:view==='wiki'?<WikiPage api={api}/>:view==='diagram'?<div style={{padding:20}}><ReadingImage src={diagram('black')} alt="黑色线条"/><ReadingImage src={diagram('white')} alt="白色线条"/><WikiPage api={api} initialArticle="ds/dsu"/></div>:view==='navigation'?<NavigationSettings pages={pages} prefs={prefs} setPrefs={setPrefs} level={50}/>:view==='rewards'?<div className="modal wide" style={{width:'min(920px,100%)'}}><div className="modal-body"><AchievementPanel achievements={achievements}/></div></div>:<div className="tb-workbench" style={{width:'100%',height:200}}><div className="wb-pane-header wb-editor-header"><span className="wb-language-select"><ThemedSelect aria-label="编程语言" value={language} onChange={event=>setLanguage(event.target.value)}><option value="cpp17">C++17</option><option value="python3">Python3</option></ThemedSelect></span></div></div>}
 </main></>;
}
createRoot(document.getElementById('root')).render(<Fixture/>);
