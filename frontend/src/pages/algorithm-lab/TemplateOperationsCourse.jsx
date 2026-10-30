import {useEffect,useRef,useState} from 'react';
import {ArrowLeft,ArrowRight,Check,Code2,List,NotebookPen} from 'lucide-react';
import TEMPLATES from '../../../../backend/resources/code-templates.json';
import GRAPH_COURSES from '../../../../backend/resources/graph-lab.json';
import {ALGORITHM_TOPIC_BY_ID} from '@/lib/algorithmLearning.js';
import Markdown from '@/components/SolutionMarkdown.jsx';
import {CodeBlock,Feedback,Hints} from './LabParts.jsx';
import OperationsExperiment from './OperationsExperiment.jsx';
import LinearBasisExperiment from './LinearBasisExperiment.jsx';
import GuidedProblem from './GuidedProblem.jsx';
import {OPERATION_PRACTICE} from './operationPractice.js';
import useCourseKeys from './useCourseKeys.js';
import './operationsLab.css';

const CHAPTERS=['先解决一个问题','保留什么信息','逐项理解操作','边界与复杂度','用反例排错','连接 C++ 模板','独立练习'];
function Practice({topic,saved,patch,rows,lockedProblems,onTrain}) {
 const tasks=OPERATION_PRACTICE[topic.id]||[],i=Math.min(4,Math.max(0,Number(saved.guided?.active)||0)),task=tasks[i];
 const draft=saved.guided?.problems?.[task.id]||{},[checked,setChecked]=useState(false);
 const update=change=>patch(old=>({...old,guided:{...old.guided,problems:{...old.guided?.problems,[task.id]:{...old.guided?.problems?.[task.id],...change}}}}));
 const practiceIds=topic.practiceIds.length?topic.practiceIds:topic.sections.flatMap(section=>section.sourceProblemIds);
 const row=rows.find(row=>practiceIds.some(id=>row.id===id||row.aliasIds?.includes(id)));
 const locked=row&&lockedProblems.some(lock=>lock.id===row.id||lock.url&&lock.url===row.url||lock.aliasIds?.includes(row.id)||row.aliasIds?.includes(lock.id));
 return <section className="lab-panel operations-practice" key={task.id}>
  <nav className="lab-guided-steps" aria-label="课堂练习">{tasks.map((p,index)=><button key={p.id} type="button" aria-current={index===i?'step':undefined} onClick={()=>patch(old=>({...old,guided:{...old.guided,active:index}}))}>{index+1} {p.title}</button>)}</nav>
  <h2>{task.title}</h2><p>{task.prompt}</p>
  <form className="operations-predict" onSubmit={e=>{e.preventDefault();setChecked(true);}}><label>先独立推演<input aria-label="练习答案" value={draft.answer||''} onChange={e=>{setChecked(false);update({answer:e.target.value});}}/></label><button className="lab-icon-button" aria-label="验证结果" title="验证结果" disabled={!draft.answer?.trim()}><Check size={17}/></button></form>
  {checked&&<Feedback good={draft.answer?.trim()===task.answer}>{draft.answer?.trim()===task.answer?task.reason:'结果还不一致。先列出允许的操作，再找发生变化的第一个位置。'}</Feedback>}
  <Hints items={['先用极小数据逐次写出状态，别把操作返回值当成结构本身。',task.reason]} id={task.id} drafts={draft} updateDraft={(key,value)=>update({[key]:value,assisted:true})}/>
  <label>用自己的话说明状态与操作<textarea aria-label="我的实现说明" value={draft.explanation||''} onChange={e=>update({explanation:e.target.value})}/></label>
  <details open={!!draft.reference} onToggle={e=>{if(e.currentTarget.open!==!!draft.reference)update({reference:e.currentTarget.open,assisted:draft.assisted||e.currentTarget.open});}}><summary>对照关键行</summary><CodeBlock code={task.line}/></details>
  <ul className="seq-checklist">{task.tests.map((test,index)=><li key={test}><label><input type="checkbox" checked={draft.tested?.includes(index)||false} onChange={()=>update({tested:draft.tested?.includes(index)?draft.tested.filter(x=>x!==index):[...(draft.tested||[]),index]})}/>{test}</label></li>)}</ul>
  <p>按题意写出完整输入、操作循环与输出，再用上面的边界自测。课堂核对与自检不产生正式通过记录。</p>
  {row&&<button className="lab-icon-button" aria-label={locked?'返回考场':'进入工作台自行实现'} title={locked?'返回考场':'进入工作台自行实现'} onClick={()=>onTrain?.(row.id,locked?undefined:{assisted:!!draft.assisted})}><NotebookPen size={18}/></button>}
 </section>;
}

export default function TemplateOperationsCourse({courseId,prefs,setPrefs,rows=[],lockedProblems=[],onTrain,onOpenTemplate,headerActions}) {
 const topic=ALGORITHM_TOPIC_BY_ID[courseId],template=TEMPLATES.templates.find(item=>item.id===topic.templateId);
 const saved=prefs.learningPaths?.[courseId]||{},guided=saved.mode==='guided',index=Math.max(0,Math.min(6,Number(saved.labV1?.chapter)||0));
 const [open,setOpen]=useState(false),main=useRef(null),menu=useRef(null),toggle=useRef(null);
 const patch=fn=>setPrefs(previous=>({...previous,learningPaths:{...previous.learningPaths,[courseId]:fn(previous.learningPaths?.[courseId]||{})}}));
 const navigate=to=>{setOpen(false);patch(old=>({...old,labV1:{...old.labV1,chapter:String(to)}}));};
 const update=draft=>patch(old=>({...old,labV1:{...old.labV1,drafts:{...old.labV1?.drafts,experiment:draft}}}));
 useEffect(()=>{main.current.scrollTop=0;main.current.focus({preventScroll:true});},[index,guided,saved.guided?.active]);
 useEffect(()=>{if(!open)return;const close=e=>{if(e.type==='keydown'?e.key==='Escape':!menu.current?.contains(e.target)){if(e.type==='keydown'){e.preventDefault();e.stopPropagation();toggle.current?.focus();}setOpen(false);}};document.addEventListener('pointerdown',close);document.addEventListener('keydown',close);return()=>{document.removeEventListener('pointerdown',close);document.removeEventListener('keydown',close);};},[open]);
 useCourseKeys({index,count:7,navigate,menuOpen:open||guided});
 const experiment=topic.id==='linear-basis'?<LinearBasisExperiment draft={saved.labV1?.drafts?.experiment} update={update}/>:<OperationsExperiment topic={topic} draft={saved.labV1?.drafts?.experiment} update={update}/>;
 const graphProblem=GRAPH_COURSES[courseId]?.problems[Math.min(4,Math.max(0,Number(saved.guided?.active)||0))];
 return <div className="algorithm-lab seq-course" aria-label={topic.title}>
  <header className="lab-course-header"><h1>{topic.title}</h1><span className="lab-position">{guided?'跟做':'课程'} {guided?(Number(saved.guided?.active)||0)+1:index+1} / {guided?5:7}</span>
   <aside className="lab-course-tools"><div className="lab-menu" ref={menu}><button className="lab-icon-button" ref={toggle} aria-label="目录" title="目录" aria-expanded={open} onClick={()=>setOpen(v=>!v)}><List size={17}/></button>{open&&<nav aria-label="课程章节">{CHAPTERS.map((name,i)=><button key={name} aria-current={!guided&&index===i?'step':undefined} onClick={()=>{patch(old=>({...old,mode:'learn'}));navigate(i);}}><span>{i+1}</span><b>{name}</b></button>)}</nav>}</div><nav className="lab-page-navigation" aria-label="章节翻页"><button className="lab-icon-button" aria-label="上一页" disabled={guided?!saved.guided?.active:!index} onClick={()=>guided?patch(old=>({...old,guided:{...old.guided,active:(old.guided?.active||0)-1}})):navigate(index-1)}><ArrowLeft size={18}/></button><button className="lab-icon-button" aria-label="下一页" disabled={guided?Number(saved.guided?.active)===4:index===6} onClick={()=>guided?patch(old=>({...old,guided:{...old.guided,active:(old.guided?.active||0)+1}})):navigate(index+1)}><ArrowRight size={18}/></button></nav></aside>
   <div className="lab-header-actions">{onOpenTemplate&&<button className="lab-icon-button" aria-label="打开对应模板" title="打开对应模板" onClick={()=>onOpenTemplate(topic.templateId)}><Code2 size={17}/></button>}{headerActions}</div>
  </header>
  <main className="lab-lesson operations-reading" ref={main} tabIndex={-1} aria-label={guided?'跟着做题':CHAPTERS[index]}>
   {guided?graphProblem?<GuidedProblem key={graphProblem.pid} problem={graphProblem} draft={saved.guided?.problems?.[graphProblem.pid]||{}} update={fn=>patch(old=>({...old,guided:{...old.guided,problems:{...old.guided?.problems,[graphProblem.pid]:fn(old.guided?.problems?.[graphProblem.pid]||{})}}}))} rows={rows} lockedProblems={lockedProblems} onTrain={onTrain}/>:<Practice key={saved.guided?.active||0} topic={topic} saved={saved} patch={patch} rows={rows} lockedProblems={lockedProblems} onTrain={onTrain}/>:<>
    <section className="lab-story"><h2>{CHAPTERS[index]}</h2><p>{index===0?topic.intro:index===1?topic.invariant:index===2?'先区分修改了结构的操作，与只返回答案的查询。每个操作都要能说出输入、结果和前提。':index===3?topic.boundary:index===4?topic.bug:index===5?'把操作、下标和不变量逐项对应到 C++。模板本身不替题目决定输入输出；最小示例展示完整调用方式。':'先完成五个递进练习，再独立写出完整程序。'}</p></section>
    {index<2&&experiment}
    {index===1&&<><Markdown text={topic.reasoning}/>{topic.sections.map(section=><details key={section.id}><summary>{section.title}</summary>{topic.id==='fenwick'&&<p>这是独立推导，沿用原文注明的内部编号。当前模板的外部调用仍从 0 开始，区间为 [l,r)。</p>}<Markdown text={section.markdown} images={section.images}/></details>)}</>}
    {index===2&&<><div className="operations-table"><table><thead><tr><th>操作</th><th>含义与前提</th></tr></thead><tbody>{topic.operations.map(([name,meaning])=><tr key={name}><th><code>{name}</code></th><td style={{whiteSpace:'normal'}}>{meaning}</td></tr>)}</tbody></table></div>{experiment}</>}
    {index===3&&<section className="lab-panel"><p>{topic.invariant}</p><p>{topic.boundary}</p><p>{topic.bug}</p></section>}
    {index===4&&<section className="lab-panel"><label>写出错误第一次出现的位置、修复依据和复测数据<textarea aria-label="我的排错说明" rows={5} style={{width:'100%',boxSizing:'border-box'}} value={saved.labV1?.drafts?.bug||''} onChange={e=>{const value=e.target.value;patch(old=>({...old,labV1:{...old.labV1,drafts:{...old.labV1?.drafts,bug:value}}}));}}/></label>{experiment}</section>}
    {index===5&&<><Markdown text={template.explanation}/><CodeBlock code={template.code+'\n'+template.example} copy/></>}
    {index===6&&<section className="lab-panel"><p>{topic.id==='dsu'?'沿用五道已核实原题的跟做指导。':'五个原创课堂小例分别检查操作、边界与模型变化；不附加虚构的比赛评级。'}</p><button className="lab-icon-button" aria-label="跟着做五道题" title="跟着做五道题" onClick={()=>patch(old=>({...old,mode:'guided'}))}><ArrowRight size={18}/></button></section>}
   </>}
  </main>
 </div>;
}
