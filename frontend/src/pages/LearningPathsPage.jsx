import { ArrowLeft, BookOpen, Code2, Search } from 'lucide-react';
import {useEffect,useLayoutEffect,useRef,useState} from 'react';
import PageSearch from '../components/PageSearch.jsx';
import KnapsackCourse from './algorithm-lab/KnapsackCourse.jsx';
import GraphCourse from './algorithm-lab/GraphCourse.jsx';
import SortingCourse from './algorithm-lab/SortingCourse.jsx';
import SORTING_COURSES from '../../../backend/resources/sorting-lab.json';
import GRAPH_COURSES from '../../../backend/resources/graph-lab.json';
import SequenceCourse from './algorithm-lab/SequenceCourse.jsx';
import './algorithm-lab/algorithmLab.css';
import './algorithm-lab/sequenceLab.css';

const COURSES = [
  ...Object.entries(SORTING_COURSES).map(([id,c])=>({id,title:c.title,search:id+' 冒泡 插入 选择 归并 快速 随机 桶 基数 排序',description:c.description,meta:`${c.chapters.length} 节互动课 · 5 道跟做题`,first:c.chapters[0].id})),
  ...Object.entries(GRAPH_COURSES).map(([id,c])=>({id,title:c.title,search:id,description:c.description,meta:"7 节互动课 · 5 道跟做题",first:"0"})),
  { id: 'prefix-difference', title: '前缀和与差分', search: 'prefix sum difference', description: '从区间总账走到边界事件。亲手把累计量与变化量互相还原，分清何时只用其中一个、何时组合使用。', meta: '7 节互动课 · 一维与二维 · 5 道跟做题', first: 'sum' },
  { id: 'two-pointers', title: '双指针算法', search: 'two pointers sliding window 滑动窗口 快慢指针 相向指针', description: '移动之前，先证明不会漏掉答案。从排除候选，到伸缩窗口与原地保留，再用负数亲手检验移动的依据。', meta: '7 节互动课 · 相向、滑窗、快慢 · 5 道跟做题', first: 'pair' },
  { id: 'knapsack', title: '背包 DP', search: '动态规划 knapsack', description: '从一次装包开始，学会定义小问题、推导选择、辨认倒序更新背后的旧状态。', meta: '7 节互动课 · 状态、选择与读写顺序 · 5 道跟做题', first: 'pack' },
];

export default function LearningPathsPage({ rows = [], prefs, setPrefs, onTrain, lockedProblems = [], visit, standalone = false }) {
  const [query,setQuery]=useState('');
  const matches = COURSES.filter(course => `${course.title} ${course.search}`.toLowerCase().includes(query.trim().toLowerCase()));
  const fallback=useRef({leftAt:null,scrollTop:0}),session=visit||fallback.current,panel=useRef(null);
  const [resume,setResume]=useState(()=>standalone||Number.isFinite(session.leftAt)&&Date.now()>=session.leftAt&&Date.now()-session.leftAt<180000);
  useLayoutEffect(()=>{
    const node=panel.current;
    if(!resume)setPrefs(previous=>({...previous,learningPaths:{...previous.learningPaths,activePath:null}}));
    else (node.querySelector('.lab-lesson')||node).scrollTop=session.scrollTop||0;
    session.leftAt=null;
    return()=>{session.leftAt=Date.now();session.scrollTop=(node.querySelector('.lab-lesson')||node).scrollTop;};
  },[]);
  const open = (course,mode) => {setResume(true);if(panel.current)panel.current.scrollTop=0;setPrefs(previous => ({ ...previous, learningPaths: { ...previous.learningPaths, activePath: course.id, [course.id]: { ...previous.learningPaths?.[course.id], ...(mode==='continue'?{}:{mode}), ...(mode==='learn'?{labV1:{...previous.learningPaths?.[course.id]?.labV1,chapter:course.first}}:{}) } } }));};
  const back = () => setPrefs(previous => ({ ...previous, learningPaths: { ...previous.learningPaths, activePath: null } }));
  useEffect(()=>{
    if(!resume||!COURSES.some(course=>course.id===prefs.learningPaths?.activePath))return;
    const escape=event=>{if(event.key!=='Escape'||event.defaultPrevented||event.target.closest?.('input,textarea,select,[contenteditable=true]')||document.querySelector('dialog[open],.tb-select-menu'))return;event.preventDefault();back();};
    window.addEventListener('keydown',escape);return()=>window.removeEventListener('keydown',escape);
  },[resume,prefs.learningPaths?.activePath]);
  const active = resume && COURSES.find(course=>course.id===prefs.learningPaths?.activePath);
  const actions = <button type="button" className="lab-icon-button" aria-label="返回算法实验室" title="返回算法实验室" onClick={back}><ArrowLeft size={17}/></button>;
  return <div ref={panel} className="learning-paths-page scroll-panel" aria-label="算法实验室">
    {active ? SORTING_COURSES[active.id] ? <SortingCourse key={active.id} courseId={active.id} rows={rows} prefs={prefs} setPrefs={setPrefs} onTrain={onTrain} lockedProblems={lockedProblems} headerActions={actions}/> : GRAPH_COURSES[active.id] ? <GraphCourse key={active.id} courseId={active.id} rows={rows} prefs={prefs} setPrefs={setPrefs} onTrain={onTrain} lockedProblems={lockedProblems} headerActions={actions}/> : active.id==='knapsack' ? <KnapsackCourse rows={rows} prefs={prefs} setPrefs={setPrefs} onTrain={onTrain} lockedProblems={lockedProblems} headerActions={actions}/> : <SequenceCourse key={active.id} courseId={active.id} rows={rows} prefs={prefs} setPrefs={setPrefs} onTrain={onTrain} lockedProblems={lockedProblems} headerActions={actions}/> : <div className="lab-catalog lab-multi-catalog">
      <PageSearch><label className="search-box"><Search size={17}/><input aria-label="搜索算法" value={query} onChange={event=>setQuery(event.target.value)}/></label></PageSearch>{matches.length ? matches.map((course,i)=><section className="lab-panel" key={course.id} aria-label={course.title}><span className="seq-catalog-number">{String(i+1).padStart(2,'0')}</span><h3>{course.title}</h3><p className="seq-catalog-description">{course.description}</p><p className="seq-catalog-meta">{course.meta}</p><div className="lab-course-options"><button type="button" className="lab-button" onClick={() => open(course,'learn')}><BookOpen size={17}/>学算法</button>{prefs.learningPaths?.[course.id]?.labV1&&<button type="button" className="lab-button lab-button-quiet" onClick={()=>open(course,'continue')}>继续上次</button>}{(prefs.learningPaths?.[course.id]?.guided || prefs.learningPaths?.[course.id]?.mode === 'guided') && <button type="button" className="lab-button lab-button-quiet" onClick={() => open(course,'guided')}><Code2 size={17}/>继续做题</button>}</div></section>) : <p className="progress-muted">没有匹配的算法。</p>}
    </div>}
  </div>;
}
