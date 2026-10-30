import {useRef,useState} from 'react';
import {createRoot} from 'react-dom/client';
import {BookOpen,Code2,FlaskConical} from 'lucide-react';
import LearningPathsPage from '../src/pages/LearningPathsPage.jsx';
import TemplatesPage from '../src/pages/TemplatesPage.jsx';
import {LecturesPanel} from '../src/pages/LecturesPanel.jsx';
import {ALGORITHM_TOPICS} from '../src/lib/algorithmLearning.js';
import TEMPLATES from '../../backend/resources/code-templates.json';
import 'katex/dist/katex.min.css';
import '../src/styles/workspace.css';
import '../src/styles/refinements.css';
import '../src/styles/polish.css';
import '../src/styles/unified.css';
import '../src/styles/revision.css';
function Fixture(){
 const [view,setView]=useState('lab'),[prefs,setPrefsRaw]=useState(()=>JSON.parse(localStorage.getItem('operations-fixture')||'{"learningPaths":{}}')),[lectures,setLectures]=useState([]),[initialLecture,setInitialLecture]=useState(null),[locked,setLocked]=useState([]);
 const templates=useRef({}),visits=useRef({}),setPrefs=fn=>setPrefsRaw(old=>{const next=typeof fn==='function'?fn(old):fn;localStorage.setItem('operations-fixture',JSON.stringify(next));return next;});
 const openTemplate=id=>{templates.current.selected=id;setInitialLecture(null);setView('templates');};
 const openCourse=id=>{setPrefs(old=>({...old,learningPaths:{...old.learningPaths,activePath:id,[id]:{...old.learningPaths?.[id],mode:'learn'}}}));setView('lab');};
 const api=async path=>path==='templates'?TEMPLATES:path==='lectures'?{lectures}:lectures.find(x=>x.id===new URLSearchParams(path.split('?')[1]).get('id'));
 window.fixture={prefs,view,seed:setPrefs,lectures:setLectures,lock:setLocked,openTemplate,openCourse,openLecture:id=>{setInitialLecture(id);setView('lectures');}};
 return <><header style={{height:55,display:'flex',gap:12,padding:8}}><button aria-label="实验室" onClick={()=>setView('lab')}><FlaskConical size={18}/></button><button aria-label="模板" onClick={()=>{templates.current.selected=null;setView('templates');}}><Code2 size={18}/></button><button aria-label="从零讲" onClick={()=>setView('lectures')}><BookOpen size={18}/></button><div id="tb-page-search" style={{display:'flex',minWidth:0}}/></header><main className="workspace-area" style={{height:'calc(100dvh - 55px)',padding:10}}>{view==='lab'?<LearningPathsPage rows={[]} prefs={prefs} setPrefs={setPrefs} lockedProblems={locked} onOpenTemplate={openTemplate}/>:view==='templates'?<TemplatesPage api={api} visit={templates.current} onOpenCourse={openCourse}/>:<LecturesPanel api={api} lectures={{lectures}} initialLecture={initialLecture} visit={visits.current} prefs={prefs} setPrefs={setPrefs} onOpenTemplate={openTemplate}/>}</main></>;
}
document.documentElement.dataset.theme='dark';
createRoot(document.getElementById('root')).render(<Fixture/>);
