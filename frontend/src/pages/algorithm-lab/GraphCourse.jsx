import {useEffect,useRef,useState} from 'react';
import {ArrowLeft,ArrowRight,List} from 'lucide-react';
import COURSES from '../../../../backend/resources/graph-lab.json';
import GraphExperiment from './GraphExperiment.jsx';
import GuidedProblem from './GuidedProblem.jsx';
import {CodeBlock} from './LabParts.jsx';
import useCourseKeys from './useCourseKeys.js';
import {chapterMenuTitle} from './courseNavigation.js';
import './graphLab.css';

import {GRAPH_CODE as CODE} from './graphCode.js';

export default function GraphCourse({courseId,prefs,setPrefs,rows=[],lockedProblems=[],onTrain,headerActions}){
 const course=COURSES[courseId],saved=prefs.learningPaths?.[courseId]||{},guided=saved.mode==='guided';
 const index=guided?Math.max(0,Math.min(4,Number(saved.guided?.active)||0)):Math.max(0,course.chapters.findIndex(c=>c.id===saved.labV1?.chapter)),count=guided?5:course.chapters.length;
 const chapter=course.chapters[index],problem=course.problems[index],main=useRef(null),menu=useRef(null),toggle=useRef(null),[open,setOpen]=useState(false);
 const patch=fn=>setPrefs(previous=>({...previous,learningPaths:{...previous.learningPaths,[courseId]:fn(previous.learningPaths?.[courseId]||{})}}));
 const navigate=to=>{setOpen(false);patch(old=>guided?{...old,guided:{...old.guided,active:to}}:{...old,labV1:{...old.labV1,chapter:course.chapters[to].id}});};
 const update=fn=>patch(old=>({...old,guided:{...old.guided,problems:{...old.guided?.problems,[problem.pid]:fn(old.guided?.problems?.[problem.pid]||{})}}}));
 useEffect(()=>{main.current.scrollTop=0;main.current.focus({preventScroll:true});},[index,guided]);
 useEffect(()=>{if(!open)return;const close=e=>{if(e.type==='keydown'?e.key==='Escape':!menu.current?.contains(e.target)){if(e.type==='keydown'){e.preventDefault();e.stopPropagation();toggle.current?.focus();}setOpen(false);}};document.addEventListener('pointerdown',close);document.addEventListener('keydown',close);return()=>{document.removeEventListener('pointerdown',close);document.removeEventListener('keydown',close);};},[open]);
 useCourseKeys({index,count,navigate,menuOpen:open});
 return <div className="algorithm-lab seq-course" aria-label={course.title}><header className="lab-course-header"><h1>{course.title}</h1><span className="lab-position">{guided?'跟做 ':''}{index+1} / {count}</span><aside className="lab-course-tools"><div className="lab-menu" ref={menu}><button type="button" className="lab-menu-toggle" ref={toggle} aria-label="目录" aria-expanded={open} onClick={()=>setOpen(v=>!v)}><List size={17}/>目录</button>{open&&<nav aria-label="课程章节">{(guided?course.problems:course.chapters).map((item,i)=><button key={i} aria-current={i===index?'step':undefined} onClick={()=>navigate(i)}><span>{i+1}</span><b>{guided?item.title:chapterMenuTitle(item)}</b></button>)}</nav>}</div><nav className="lab-page-navigation" aria-label="章节翻页"><button className="lab-icon-button" aria-label="上一页" disabled={!index} onClick={()=>navigate(index-1)}><ArrowLeft size={18}/></button><button className="lab-icon-button" aria-label="下一页" disabled={index===count-1} onClick={()=>navigate(index+1)}><ArrowRight size={18}/></button></nav></aside><div className="lab-header-actions">{guided&&<button className="lab-icon-button" aria-label="返回学算法" onClick={()=>patch(old=>({...old,mode:'learn'}))}>课程</button>}{headerActions}</div></header><main className="lab-lesson" ref={main} tabIndex={-1} aria-label={guided?problem.title:chapter.title}>{guided?<GuidedProblem key={problem.pid} problem={problem} experiment={<GraphExperiment kind={courseId}/>} draft={saved.guided?.problems?.[problem.pid]||{}} update={update} rows={rows} lockedProblems={lockedProblems} onTrain={onTrain}/>:<><section className="lab-story graph-lesson-copy"><h2>{chapter.title}</h2>{chapter.paragraphs.map(p=><p key={p}>{p}</p>)}</section>{index===5?<CodeBlock code={CODE[courseId]}/>:index<5?<GraphExperiment key={courseId+index} kind={courseId}/>:<section className="lab-panel"><h3>去题目里重新识别模型</h3><p>五题的题面、原站评分和样例已收录。先思考，再推演，最后独立实现。</p><button className="lab-button" onClick={()=>patch(old=>({...old,mode:'guided'}))}>跟着做五道题<ArrowRight size={16}/></button></section>}</>}</main></div>;
}
