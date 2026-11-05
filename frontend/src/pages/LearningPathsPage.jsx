import { ArrowLeft, BookOpen, Code2, Search } from 'lucide-react';
import {useCallback,useEffect,useLayoutEffect,useRef,useState} from 'react';
import {recordKnowledgeNavigation} from '@/lib/knowledgeJourney.js';
import {CatalogueGroup as CatalogGroup,CatalogueEntry as CatalogCard} from '@/components/LearningCatalogue.jsx';
import PageSearch from '../components/PageSearch.jsx';
import {useStudyState} from '@/lib/StudyPane.jsx';
import KnapsackCourse from './algorithm-lab/KnapsackCourse.jsx';
import GraphCourse from './algorithm-lab/GraphCourse.jsx';
import SortingCourse from './algorithm-lab/SortingCourse.jsx';
import SORTING_COURSES from '../../../backend/resources/sorting-lab.json';
import GRAPH_COURSES from '../../../backend/resources/graph-lab.json';
import SequenceCourse from './algorithm-lab/SequenceCourse.jsx';
import {startCourseAtBeginning} from './algorithm-lab/courseNavigation.js';
import TemplateOperationsCourse from './algorithm-lab/TemplateOperationsCourse.jsx';
import TemplateStudyCourse from './algorithm-lab/TemplateStudyCourse.jsx';
import {ALGORITHM_TOPICS,ALGORITHM_TOPIC_BY_ID} from '@/lib/algorithmLearning.js';
import './algorithm-lab/algorithmLab.css';
import './algorithm-lab/sequenceLab.css';

import {LAB_CATALOG as COURSES} from '@/lib/labCatalog.js';
const COURSE_GROUPS=[['基础算法',['sorting-basics','prefix-difference','two-pointers','binary-search','window-extrema','divide-sort','bucket-sort']],['搜索',['bfs','dfs']],['数据结构',['dsu','fenwick','segment-tree','binary-lifting','li-chao']],['图论',['dijkstra','dinic']],['字符串',['trie']],['数学',['linear-basis']],['动态规划',['knapsack']]];

export default function LearningPathsPage({ rows = [], prefs, setPrefs:savePreferences, onTrain,onOpenTemplate, lockedProblems = [], visit, standalone = false, initialPath, onOpenDetail, study=false,catalogOnly=false }) {
  const setPrefs=useCallback(update=>savePreferences(previous=>{const next=typeof update==='function'?update(previous):update;return recordKnowledgeNavigation(previous,next);}),[savePreferences]);
  const [query,setQuery]=useStudyState('labQuery','');
  const matches = COURSES.filter(course => `${course.title} ${course.search}`.toLowerCase().includes(query.trim().toLowerCase()));
  const fallback=useRef({leftAt:null,scrollTop:0}),session=visit||fallback.current,panel=useRef(null),enteredCourse=useRef(null);
  const active = !catalogOnly&&COURSES.find(course=>course.id===(initialPath||prefs.learningPaths?.activePath));
  const resume=active&&(study||prefs.learningPaths?.resumePath===active.id);
  const displayedPrefs=initialPath?{...prefs,learningPaths:{...prefs.learningPaths,activePath:initialPath}}:prefs;
  const coursePreferences=active&&enteredCourse.current!==active.id&&!resume?startCourseAtBeginning(displayedPrefs,active):displayedPrefs;
  useLayoutEffect(()=>{
    if(!active){enteredCourse.current=null;return;}
    if(enteredCourse.current===active.id)return;
    enteredCourse.current=active.id;
    if(!resume)setPrefs(previous=>startCourseAtBeginning(previous,active));
  },[active?.id,setPrefs]);
  useLayoutEffect(()=>{
    const node=panel.current;
    (node.querySelector('.lab-lesson')||node).scrollTop=0;
    session.leftAt=null;
    return()=>{session.leftAt=Date.now();session.scrollTop=(node.querySelector('.lab-lesson')||node).scrollTop;};
  },[]);
  const open = course => {if(onOpenDetail){onOpenDetail(course);return;}if(panel.current)panel.current.scrollTop=0;setPrefs(previous=>{const next=startCourseAtBeginning(previous,course);return {...next,learningPaths:{...next.learningPaths,resumePath:null}};});};
  const back = () => setPrefs(previous => ({ ...previous, learningPaths: { ...previous.learningPaths, activePath: null } }));
  useEffect(()=>{
    if(study||!COURSES.some(course=>course.id===(initialPath||prefs.learningPaths?.activePath)))return;
    const escape=event=>{if(event.key!=='Escape'||event.defaultPrevented||event.target.closest?.('input,textarea,select,[contenteditable=true]')||document.querySelector('dialog[open],.tb-select-menu'))return;event.preventDefault();back();};
    window.addEventListener('keydown',escape);return()=>window.removeEventListener('keydown',escape);
  },[prefs.learningPaths?.activePath]);
  const actions = <button type="button" className="lab-icon-button" aria-label="返回实验室" title="返回实验室" onClick={back}><ArrowLeft size={17}/></button>;
  return <div ref={panel} className="learning-paths-page scroll-panel lab-page-surface" aria-label="实验室">
    {active ? ['binary-search','window-extrema'].includes(active.id) ? <TemplateStudyCourse key={active.id} courseId={active.id} rows={rows} prefs={coursePreferences} setPrefs={setPrefs} onTrain={onTrain} lockedProblems={lockedProblems} headerActions={actions}/> : ALGORITHM_TOPIC_BY_ID[active.id] ? <TemplateOperationsCourse key={active.id} courseId={active.id} rows={rows} prefs={coursePreferences} setPrefs={setPrefs} onTrain={onTrain} onOpenTemplate={onOpenTemplate} lockedProblems={lockedProblems} headerActions={actions}/> : SORTING_COURSES[active.id] ? <SortingCourse key={active.id} courseId={active.id} rows={rows} prefs={coursePreferences} setPrefs={setPrefs} onTrain={onTrain} lockedProblems={lockedProblems} headerActions={actions}/> : GRAPH_COURSES[active.id] ? <GraphCourse key={active.id} courseId={active.id} rows={rows} prefs={coursePreferences} setPrefs={setPrefs} onTrain={onTrain} lockedProblems={lockedProblems} headerActions={actions}/> : active.id==='knapsack' ? <KnapsackCourse rows={rows} prefs={coursePreferences} setPrefs={setPrefs} onTrain={onTrain} lockedProblems={lockedProblems} headerActions={actions}/> : <SequenceCourse key={active.id} courseId={active.id} rows={rows} prefs={coursePreferences} setPrefs={setPrefs} onTrain={onTrain} lockedProblems={lockedProblems} headerActions={actions}/> : <div className="learning-catalogue lab-learning-catalogue">
      <PageSearch><label className="search-box"><Search size={17}/><input aria-label="搜索算法" value={query} onChange={event=>setQuery(event.target.value)}/></label></PageSearch>{matches.length ? COURSE_GROUPS.filter(([,ids])=>matches.some(course=>ids.includes(course.id))).map(([group,ids])=><CatalogGroup key={group} title={group}>{matches.filter(course=>ids.includes(course.id)).map(course=><CatalogCard key={course.id} title={course.title} icon={<Code2 size={18}/>} label={`打开算法 ${course.title}`} onOpen={()=>open(course)}/>)}</CatalogGroup>) : <p className="progress-muted">没有匹配的算法。</p>}
    </div>}
  </div>;
}
