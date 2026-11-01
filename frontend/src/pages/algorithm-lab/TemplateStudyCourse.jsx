import {useEffect,useRef,useState} from 'react';
import {ArrowLeft,ArrowRight,List,NotebookPen} from 'lucide-react';
import BASE from '../../../../backend/resources/code-templates.json';
import GUIDED from '../../../../backend/resources/template-guided.json';
import {teachingTemplates,TEMPLATE_CURRICULUM} from '@/lib/templateCurriculum.js';
import Markdown from '@/components/SolutionMarkdown.jsx';
import TemplateVariations from '@/components/TemplateVariations.jsx';
import TemplateTraceExperiment from './TemplateTraceExperiment.jsx';
import TemplateGuidedProblem from './TemplateGuidedProblem.jsx';
import {CodeBlock} from './LabParts.jsx';
import useCourseKeys from './useCourseKeys.js';

const CHAPTERS=['识别条件','状态推演','变种与不变量','边界与反例','题目迁移','连接代码','独立实现'];
const TEMPLATES=teachingTemplates(BASE.templates);
export default function TemplateStudyCourse({courseId,prefs,setPrefs,rows=[],lockedProblems=[],onTrain,headerActions}){
 const lesson=TEMPLATE_CURRICULUM[courseId],template=TEMPLATES.find(t=>t.id==='builtin:'+courseId),tasks=GUIDED[courseId];
 const saved=prefs.learningPaths?.[courseId]||{},guided=saved.mode==='guided',chapter=Math.max(0,Math.min(6,Number(saved.labV1?.chapter)||0)),problem=Math.max(0,Math.min(4,Number(saved.guided?.active)||0));
 const [menu,setMenu]=useState(false),[contest,setContest]=useState(false),main=useRef(null),outline=useRef(null),toggle=useRef(null);
 const patch=fn=>setPrefs(previous=>({...previous,learningPaths:{...previous.learningPaths,[courseId]:fn(previous.learningPaths?.[courseId]||{})}}));
 const navigate=index=>{setMenu(false);patch(old=>guided?{...old,guided:{...old.guided,active:index}}:{...old,labV1:{...old.labV1,chapter:String(index)}});};
 useEffect(()=>{main.current.scrollTop=0;main.current.focus({preventScroll:true});},[chapter,guided,problem]);
 useEffect(()=>{if(!menu)return;const close=event=>{if(event.type==='keydown'?event.key==='Escape':!outline.current?.contains(event.target)){setMenu(false);if(event.type==='keydown'){event.stopPropagation();toggle.current?.focus();}}};document.addEventListener('pointerdown',close);document.addEventListener('keydown',close);return()=>{document.removeEventListener('pointerdown',close);document.removeEventListener('keydown',close);};},[menu]);
 useCourseKeys({index:guided?problem:chapter,count:guided?5:7,navigate,menuOpen:menu});
 const reference=problemId=>patch(old=>old.referenceProblems?.includes(problemId)?old:{...old,referenceProblems:[...(old.referenceProblems||[]),problemId]});
 const updateExperiment=value=>patch(old=>({...old,labV1:{...old.labV1,drafts:{...old.labV1?.drafts,experiment:value}}}));
 const variations=<TemplateVariations curriculum={lesson} edition={contest?'contest':'teaching'} onTrain={onTrain} onReference={reference} lockedProblems={lockedProblems}/>;
 return <div className="algorithm-lab seq-course" aria-label={courseId==='binary-search'?'整数二分':'单调队列'}>
  <header className="lab-course-header"><h1>{courseId==='binary-search'?'整数二分':'单调队列'}</h1><span className="lab-position">{guided?'跟做':'课程'} {(guided?problem:chapter)+1} / {guided?5:7}</span><aside className="lab-course-tools"><div className="lab-menu" ref={outline}><button type="button" ref={toggle} className="lab-icon-button" aria-label="目录" aria-expanded={menu} onClick={()=>setMenu(v=>!v)}><List size={17}/></button>{menu&&<nav aria-label="课程章节">{CHAPTERS.map((name,i)=><button type="button" key={name} aria-current={!guided&&chapter===i?'step':undefined} onClick={()=>{setMenu(false);patch(old=>({...old,mode:'learn',labV1:{...old.labV1,chapter:String(i)}}));}}>{i+1} {name}</button>)}<button type="button" onClick={()=>{setMenu(false);patch(old=>({...old,mode:'guided'}));}}>跟着做题</button></nav>}</div><nav className="lab-page-navigation" aria-label="章节翻页"><button type="button" className="lab-icon-button" aria-label="上一页" disabled={guided?!problem:!chapter} onClick={()=>navigate((guided?problem:chapter)-1)}><ArrowLeft size={18}/></button><button type="button" className="lab-icon-button" aria-label="下一页" disabled={guided?problem===4:chapter===6} onClick={()=>navigate((guided?problem:chapter)+1)}><ArrowRight size={18}/></button></nav></aside><div className="lab-header-actions">{headerActions}</div></header>
  <main ref={main} tabIndex={-1} className="lab-lesson operations-reading" aria-label={guided?'跟着做题':CHAPTERS[chapter]}>
   {guided?<><nav className="lab-guided-steps" aria-label="跟做题目">{tasks.map((task,i)=><button type="button" key={task.problemId} aria-current={problem===i?'step':undefined} onClick={()=>navigate(i)}>{i+1} {task.pid}</button>)}</nav><TemplateGuidedProblem key={tasks[problem].problemId} task={tasks[problem]} rows={rows} lockedProblems={lockedProblems} onTrain={onTrain} draft={{...saved.guided?.problems?.[tasks[problem].problemId],assisted:!!(saved.guided?.problems?.[tasks[problem].problemId]?.assisted||saved.referenceProblems?.includes(tasks[problem].problemId))}} update={fn=>patch(old=>({...old,guided:{...old.guided,problems:{...old.guided?.problems,[tasks[problem].problemId]:fn(old.guided?.problems?.[tasks[problem].problemId]||{})}}}))}/></>:<>
    <section className="lab-story"><h2>{CHAPTERS[chapter]}</h2></section>
    {chapter===0&&<Markdown text={lesson.markdown}/>}
    {chapter===1&&<TemplateTraceExperiment kind={courseId} draft={saved.labV1?.drafts?.experiment} update={updateExperiment}/>}
    {chapter===2&&variations}
    {chapter===3&&<><p>{courseId==='binary-search'?'先试重复值、全部成立、全部不成立与空数组，再打乱顺序，观察哪条前提失效。':'依次试宽度 1、整个数组、连续相等的最值，再切换最早下标，观察相等候选何时应保留。'}</p><TemplateTraceExperiment kind={courseId} draft={saved.labV1?.drafts?.experiment} update={updateExperiment}/><label>记录第一次偏离、依据与复测数据<textarea aria-label="我的边界实验" value={saved.labV1?.drafts?.boundary||''} onChange={e=>{const value=e.target.value;patch(old=>({...old,labV1:{...old.labV1,drafts:{...old.labV1?.drafts,boundary:value}}}));}}/></label></>}
    {chapter===4&&variations}
    {chapter===5&&<><p>{template.notes}</p><button type="button" className="template-edition-toggle" aria-label={contest?'竞赛版':'讲解版'} onClick={()=>setContest(v=>!v)}>{contest?'竞赛版':'讲解版'}</button><CodeBlock code={(contest?template.contestCode:template.code)+'\n'+(contest?template.contestExample:template.example)} copy/></>}
    {chapter===6&&<section className="lab-panel"><p>五道原题分别练习条件识别、状态推演、代码修改和独立实现。已有进度与草稿保留；课堂操作不产生原站 AC。</p><button type="button" className="lab-icon-button" aria-label="跟着做五道题" onClick={()=>patch(old=>({...old,mode:'guided'}))}><NotebookPen size={18}/></button></section>}
   </>}
  </main>
 </div>;
}
