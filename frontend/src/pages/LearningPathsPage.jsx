import { ArrowLeft, BookOpen, Code2 } from 'lucide-react';
import {useEffect,useLayoutEffect,useRef,useState} from 'react';
import KnapsackCourse from './algorithm-lab/KnapsackCourse.jsx';
import './algorithm-lab/algorithmLab.css';

export default function LearningPathsPage({ rows = [], prefs, setPrefs, onTrain, lockedProblems = [], visit }) {
  const fallback=useRef({leftAt:null,scrollTop:0}),session=visit||fallback.current,panel=useRef(null);
  const [resume,setResume]=useState(()=>Number.isFinite(session.leftAt)&&Date.now()>=session.leftAt&&Date.now()-session.leftAt<180000);
  useLayoutEffect(()=>{
    const node=panel.current;
    if(!resume)setPrefs(previous=>({...previous,learningPaths:{...previous.learningPaths,activePath:null}}));
    else node.scrollTop=session.scrollTop||0;
    session.leftAt=null;
    return()=>{session.leftAt=Date.now();session.scrollTop=node.scrollTop;};
  },[]);
  const open = mode => {setResume(true);if(panel.current)panel.current.scrollTop=0;setPrefs(previous => ({ ...previous, learningPaths: { ...previous.learningPaths, activePath: 'knapsack', knapsack: { ...previous.learningPaths?.knapsack, mode, ...(mode==='learn'?{labV1:{...previous.learningPaths?.knapsack?.labV1,chapter:'pack'}}:{}) } } }));};
  const back = () => setPrefs(previous => ({ ...previous, learningPaths: { ...previous.learningPaths, activePath: null } }));
  useEffect(()=>{
    if(!resume||prefs.learningPaths?.activePath!=='knapsack')return;
    const escape=event=>{if(event.key!=='Escape'||event.defaultPrevented||event.target.closest?.('input,textarea,select,[contenteditable=true]')||document.querySelector('dialog[open],.tb-select-menu'))return;event.preventDefault();back();};
    window.addEventListener('keydown',escape);return()=>window.removeEventListener('keydown',escape);
  },[resume,prefs.learningPaths?.activePath]);
  return <div ref={panel} className="learning-paths-page scroll-panel" aria-label="算法实验室">
    {resume&&prefs.learningPaths?.activePath === 'knapsack' ? <KnapsackCourse rows={rows} prefs={prefs} setPrefs={setPrefs} onTrain={onTrain} lockedProblems={lockedProblems} headerActions={<button type="button" className="lab-icon-button" aria-label="返回算法实验室" title="返回算法实验室" onClick={back}><ArrowLeft size={17}/></button>}/> : <div className="lab-catalog lab-only-course">
      <h2>算法实验室</h2><section className="lab-panel"><h3>背包 DP</h3><p>先学会推导，学完后再进入五道真实题目。</p><div className="lab-course-options"><button type="button" className="lab-button" onClick={() => open('learn')}><BookOpen size={17}/>学算法</button>{(prefs.learningPaths?.knapsack?.guided || prefs.learningPaths?.knapsack?.mode === 'guided') && <button type="button" className="lab-button lab-button-quiet" onClick={() => open('guided')}><Code2 size={17}/>继续做题</button>}</div></section>
    </div>}
  </div>;
}
