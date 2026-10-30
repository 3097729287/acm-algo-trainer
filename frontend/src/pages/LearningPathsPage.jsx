import { ArrowLeft, BookOpen, Code2, Search } from 'lucide-react';
import {useEffect,useLayoutEffect,useRef,useState} from 'react';
import CatalogGroup from '@/components/CatalogGroup.jsx';
import CatalogCard from '@/components/CatalogCard.jsx';
import PageSearch from '../components/PageSearch.jsx';
import KnapsackCourse from './algorithm-lab/KnapsackCourse.jsx';
import GraphCourse from './algorithm-lab/GraphCourse.jsx';
import SortingCourse from './algorithm-lab/SortingCourse.jsx';
import SORTING_COURSES from '../../../backend/resources/sorting-lab.json';
import GRAPH_COURSES from '../../../backend/resources/graph-lab.json';
import SequenceCourse from './algorithm-lab/SequenceCourse.jsx';
import {startCourseAtBeginning} from './algorithm-lab/courseNavigation.js';
import TemplateOperationsCourse from './algorithm-lab/TemplateOperationsCourse.jsx';
import {ALGORITHM_TOPICS,ALGORITHM_TOPIC_BY_ID} from '@/lib/algorithmLearning.js';
import './algorithm-lab/algorithmLab.css';
import './algorithm-lab/sequenceLab.css';

const COURSE_ORDER = ['sorting-basics','prefix-difference','two-pointers','divide-sort','bucket-sort','bfs','dfs','dsu','fenwick','segment-tree','binary-lifting','li-chao','dijkstra','dinic','trie','linear-basis','knapsack'];
const COURSE_GROUPS=[['基础算法',COURSE_ORDER.slice(0,5)],['搜索', ['bfs','dfs']],['数据结构',['dsu','fenwick','segment-tree','binary-lifting','li-chao']],['图论',['dijkstra','dinic']],['字符串',['trie']],['数学',['linear-basis']],['动态规划',['knapsack']]];
const COURSES = [
  ...ALGORITHM_TOPICS.filter(topic=>topic.id!=='dsu').map(topic=>({id:topic.id,title:topic.title,search:topic.id+' '+topic.operations.map(op=>op[0]).join(' '),first:'0'})),
  ...Object.entries(SORTING_COURSES).map(([id,c])=>({id,title:c.title,search:id+' 冒泡 插入 选择 归并 快速 随机 桶 基数 排序',description:c.description,meta:`${c.chapters.length} 节互动课 · 5 道跟做题`,first:c.chapters[0].id})),
  ...Object.entries(GRAPH_COURSES).map(([id,c])=>({id,title:c.title,search:id,description:c.description,meta:"7 节互动课 · 5 道跟做题",first:"0"})),
  { id: 'prefix-difference', title: '前缀和与差分', search: 'prefix sum difference', description: '从区间总账走到边界事件。亲手把累计量与变化量互相还原，分清何时只用其中一个、何时组合使用。', meta: '7 节互动课 · 一维与二维 · 5 道跟做题', first: 'sum' },
  { id: 'two-pointers', title: '双指针算法', search: 'two pointers sliding window 滑动窗口 快慢指针 相向指针', description: '移动之前，先证明不会漏掉答案。从排除候选，到伸缩窗口与原地保留，再用负数亲手检验移动的依据。', meta: '7 节互动课 · 相向、滑窗、快慢 · 5 道跟做题', first: 'pair' },
  { id: 'knapsack', title: '背包 DP', search: '动态规划 knapsack', description: '从一次装包开始，学会定义小问题、推导选择、辨认倒序更新背后的旧状态。', meta: '7 节互动课 · 状态、选择与读写顺序 · 5 道跟做题', first: 'pack' },
].sort((a,b)=>COURSE_ORDER.indexOf(a.id)-COURSE_ORDER.indexOf(b.id));

export default function LearningPathsPage({ rows = [], prefs, setPrefs, onTrain,onOpenTemplate, lockedProblems = [], visit, standalone = false }) {
  const [query,setQuery]=useState('');
  const matches = COURSES.filter(course => `${course.title} ${course.search}`.toLowerCase().includes(query.trim().toLowerCase()));
  const fallback=useRef({leftAt:null,scrollTop:0}),session=visit||fallback.current,panel=useRef(null),enteredCourse=useRef(null);
  const active = COURSES.find(course=>course.id===prefs.learningPaths?.activePath);
  const coursePreferences=active&&enteredCourse.current!==active.id?startCourseAtBeginning(prefs,active):prefs;
  useLayoutEffect(()=>{
    if(!active){enteredCourse.current=null;return;}
    if(enteredCourse.current===active.id)return;
    enteredCourse.current=active.id;
    setPrefs(previous=>startCourseAtBeginning(previous,active));
  },[active?.id,setPrefs]);
  useLayoutEffect(()=>{
    const node=panel.current;
    (node.querySelector('.lab-lesson')||node).scrollTop=0;
    session.leftAt=null;
    return()=>{session.leftAt=Date.now();session.scrollTop=(node.querySelector('.lab-lesson')||node).scrollTop;};
  },[]);
  const open = course => {if(panel.current)panel.current.scrollTop=0;setPrefs(previous=>startCourseAtBeginning(previous,course));};
  const back = () => setPrefs(previous => ({ ...previous, learningPaths: { ...previous.learningPaths, activePath: null } }));
  useEffect(()=>{
    if(!COURSES.some(course=>course.id===prefs.learningPaths?.activePath))return;
    const escape=event=>{if(event.key!=='Escape'||event.defaultPrevented||event.target.closest?.('input,textarea,select,[contenteditable=true]')||document.querySelector('dialog[open],.tb-select-menu'))return;event.preventDefault();back();};
    window.addEventListener('keydown',escape);return()=>window.removeEventListener('keydown',escape);
  },[prefs.learningPaths?.activePath]);
  const actions = <button type="button" className="lab-icon-button" aria-label="返回实验室" title="返回实验室" onClick={back}><ArrowLeft size={17}/></button>;
  return <div ref={panel} className="learning-paths-page scroll-panel lab-page-surface" aria-label="实验室">
    {active ? ALGORITHM_TOPIC_BY_ID[active.id] ? <TemplateOperationsCourse key={active.id} courseId={active.id} rows={rows} prefs={coursePreferences} setPrefs={setPrefs} onTrain={onTrain} onOpenTemplate={onOpenTemplate} lockedProblems={lockedProblems} headerActions={actions}/> : SORTING_COURSES[active.id] ? <SortingCourse key={active.id} courseId={active.id} rows={rows} prefs={coursePreferences} setPrefs={setPrefs} onTrain={onTrain} lockedProblems={lockedProblems} headerActions={actions}/> : GRAPH_COURSES[active.id] ? <GraphCourse key={active.id} courseId={active.id} rows={rows} prefs={coursePreferences} setPrefs={setPrefs} onTrain={onTrain} lockedProblems={lockedProblems} headerActions={actions}/> : active.id==='knapsack' ? <KnapsackCourse rows={rows} prefs={coursePreferences} setPrefs={setPrefs} onTrain={onTrain} lockedProblems={lockedProblems} headerActions={actions}/> : <SequenceCourse key={active.id} courseId={active.id} rows={rows} prefs={coursePreferences} setPrefs={setPrefs} onTrain={onTrain} lockedProblems={lockedProblems} headerActions={actions}/> : <div className="lab-catalog lab-multi-catalog">
      <PageSearch><label className="search-box"><Search size={17}/><input aria-label="搜索算法" value={query} onChange={event=>setQuery(event.target.value)}/></label></PageSearch>{matches.length ? COURSE_GROUPS.filter(([,ids])=>matches.some(course=>ids.includes(course.id))).map(([group,ids])=><CatalogGroup key={group} title={group}>{matches.filter(course=>ids.includes(course.id)).map(course=><CatalogCard key={course.id} title={course.title} icon={<Code2 size={18}/>} label={`打开算法 ${course.title}`} onOpen={()=>open(course)}/>)}</CatalogGroup>) : <p className="progress-muted">没有匹配的算法。</p>}
    </div>}
  </div>;
}
