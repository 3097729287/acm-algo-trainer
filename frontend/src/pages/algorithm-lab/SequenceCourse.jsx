import { useEffect, useRef, useState } from 'react';
import { ArrowLeft, ArrowRight, List } from 'lucide-react';
import { SEQUENCE_COURSES } from './sequenceCode.js';
import { SEQUENCE_PROBLEMS } from './sequenceProblems.js';
import { ChooseExperiment, CodeLesson, CompactExperiment, DifferenceExperiment, InverseExperiment, NegativeExperiment, PairExperiment, PlaneExperiment, PointerTransfer, PrefixDebug, PrefixExperiment, UniqueExperiment, WindowExperiment } from './SequenceExperiments.jsx';
import SequenceGuided from './SequenceGuided.jsx';
import useCourseKeys from './useCourseKeys.js';
import './algorithmLab.css';
import './sequenceLab.css';

const CONTENT = { sum: PrefixExperiment, inverse: InverseExperiment, events: DifferenceExperiment, plane: PlaneExperiment, choose: ChooseExperiment, debug: PrefixDebug, pair: PairExperiment, window: WindowExperiment, unique: UniqueExperiment, compact: CompactExperiment, negative: NegativeExperiment, transfer: PointerTransfer };

export default function SequenceCourse({ courseId, prefs, setPrefs, rows = [], lockedProblems = [], onTrain, headerActions }) {
  const course = SEQUENCE_COURSES[courseId], problems = SEQUENCE_PROBLEMS[courseId], saved = prefs.learningPaths?.[courseId] || {}, lesson = saved.labV1 || {};
  const chapterIndex = Math.max(0, course.chapters.findIndex(([id]) => id === lesson.chapter)), [chapterId, title] = course.chapters[chapterIndex], guided = saved.mode === 'guided';
  const problemIndex = Math.max(0, Math.min(problems.length - 1, Number(saved.guided?.active) || 0)), problem = problems[problemIndex], draft = saved.guided?.problems?.[problem.pid] || {};
  const [menuOpen, setMenuOpen] = useState(false), menu = useRef(null), toggle = useRef(null), main = useRef(null);
  const patch = change => setPrefs(previous => ({ ...previous, learningPaths: { ...previous.learningPaths, [courseId]: change(previous.learningPaths?.[courseId] || {}) } }));
  const updateDraft = (id, value) => patch(current => ({ ...current, labV1: { ...current.labV1, drafts: { ...current.labV1?.drafts, [id]: value } } }));
  const updateProblem = change => patch(current => ({ ...current, guided: { ...current.guided, problems: { ...current.guided?.problems, [problem.pid]: change(current.guided?.problems?.[problem.pid] || {}) } } }));
  const navigate = index => { if (guided) patch(current => ({ ...current, guided: { ...current.guided, active: index } })); else patch(current => ({ ...current, labV1: { ...current.labV1, chapter: course.chapters[index][0] } })); setMenuOpen(false); };
  const changeMode = () => { patch(current => ({ ...current, mode: guided ? 'learn' : 'guided' })); setMenuOpen(false); };
  useEffect(() => { if(main.current)main.current.scrollTop=0; main.current?.focus({ preventScroll: true }); }, [chapterId, guided, problemIndex, draft.step]);
  useEffect(() => {
    if (!menuOpen) return;
    const close = event => { if (event.type === 'keydown' ? event.key === 'Escape' : !menu.current?.contains(event.target)) { if (event.type === 'keydown') { event.preventDefault(); toggle.current?.focus(); } setMenuOpen(false); } };
    document.addEventListener('pointerdown', close); document.addEventListener('keydown', close);
    return () => { document.removeEventListener('pointerdown', close); document.removeEventListener('keydown', close); };
  }, [menuOpen]);
  const index = guided ? problemIndex : chapterIndex, count = guided ? problems.length : course.chapters.length, Content = CONTENT[chapterId];
  useCourseKeys({index,count,navigate,menuOpen});
  return <div className="algorithm-lab seq-course" aria-label={`${course.title}${guided ? ' 跟着做题' : ''}`}>
    <header className="lab-course-header"><h1>{course.title}</h1><span className="lab-position">{guided ? '跟做 ' : ''}{index + 1} / {count}</span><aside className="lab-course-tools" aria-label="课程导航"><div className="lab-menu" ref={menu}><button ref={toggle} type="button" className="lab-menu-toggle" aria-label="目录" aria-expanded={menuOpen} aria-controls="seq-chapters" onClick={() => setMenuOpen(value => !value)}><List size={17}/><span>目录</span></button>{menuOpen && <nav id="seq-chapters" aria-label={guided ? '五道精选题' : '课程章节'}>{(guided ? problems.map(p => [p.pid, p.title]) : course.chapters).map(([id, name], i) => <button type="button" key={id} aria-current={i === index ? 'step' : undefined} onClick={() => navigate(i)}><span>{i + 1}</span><b>{name}</b></button>)}</nav>}</div><nav className="lab-page-navigation" aria-label="章节翻页"><button type="button" className="lab-icon-button" aria-label="上一页" disabled={index === 0} onClick={() => navigate(index - 1)}><ArrowLeft size={18}/></button><button type="button" className="lab-icon-button" aria-label="下一页" disabled={index === count - 1} onClick={() => navigate(index + 1)}><ArrowRight size={18}/></button></nav></aside><div className="lab-header-actions">{guided && <button className="lab-icon-button lab-mode-switch" type="button" aria-label="返回学算法" onClick={changeMode}>课程</button>}{headerActions}</div></header>
    <main ref={main} className="lab-lesson" tabIndex={-1} aria-label={guided ? problem.title : title}>{guided ? <SequenceGuided key={problem.pid} problem={problem} draft={draft} update={updateProblem} rows={rows} lockedProblems={lockedProblems} onTrain={onTrain}/> : <><div key={chapterId}>{chapterId === 'code' ? <CodeLesson course={course} drafts={lesson.drafts || {}} updateDraft={updateDraft}/> : <Content drafts={lesson.drafts || {}} updateDraft={updateDraft} onCheck={id => patch(current => ({ ...current, labV1: { ...current.labV1, checked: { ...current.labV1?.checked, [id]: true } } }))}/>}</div>{chapterIndex === count - 1 && <section className="lab-panel seq-next"><h3>去真实题目里，重新认出这个方法</h3><p>五道精选题从直接应用走向条件变化。每题都可以做小实验、补关键代码、检查反例，最后进入工作台独立实现。</p><button className="lab-button" type="button" onClick={changeMode}>跟着做五道题<ArrowRight size={16}/></button></section>}</>}</main>
  </div>;
}
