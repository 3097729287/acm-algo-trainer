import { useEffect, useRef, useState } from 'react';
import { ArrowLeft, ArrowRight, Check, List } from 'lucide-react';
import { CHAPTERS, CHECK_IDS } from './knapsackCourse.js';
import { EXPEDITION_REVISION } from './knapsackModel.js';
import PackingExperiment from './PackingExperiment.jsx';
import { TraceExperiment } from './KnapsackExperiments.jsx';
import StateExperiment from './StateExperiment.jsx';
import { DebugWorkshop, PracticeWorkshop, TemplateWorkshop, TransferWorkshop } from './KnapsackChallenges.jsx';
import './algorithmLab.css';
import useCourseKeys from './useCourseKeys.js';

export function labProgress(prefs) {
  const saved = prefs?.learningPaths?.knapsack?.labV1;
  if (!saved || typeof saved !== 'object') return { chapter: 'pack', passed: {}, drafts: {}, exampleRevision: EXPEDITION_REVISION };
  const passed = saved.passed && typeof saved.passed === 'object' ? Object.fromEntries(CHECK_IDS.filter(id => saved.passed[id] === true).map(id => [id, true])) : {};
  const drafts = saved.drafts && typeof saved.drafts === 'object' && !Array.isArray(saved.drafts) ? { ...saved.drafts } : {};
  if (saved.exampleRevision !== EXPEDITION_REVISION) {
    delete passed.transition;
    delete drafts.transition;
    const old = drafts.traceConfig;
    if (old?.capacity === 4 && Array.isArray(old.items) && old.items.map(item => `${item.id}:${item.weight}:${item.value}`).join(',') === 'A:3:5,B:2:3,C:2:3') delete drafts.traceConfig;
  }
  return { chapter: CHAPTERS.some(item => item.id === saved.chapter) ? saved.chapter : 'pack',
    passed, drafts, exampleRevision: EXPEDITION_REVISION };
}

const CONTENT = { pack: PackingExperiment, state: StateExperiment, trace: TraceExperiment, code: TemplateWorkshop, debug: DebugWorkshop, transfer: TransferWorkshop, practice: PracticeWorkshop };

export default function KnapsackLab({ prefs, setPrefs, rows = [], onTrain, onGuided, headerActions }) {
  const saved = labProgress(prefs), chapterIndex = CHAPTERS.findIndex(item => item.id === saved.chapter), chapter = CHAPTERS[chapterIndex];
  const Content = CONTENT[chapter.id], heading = useRef(null), previousChapter = useRef(chapter.id), menu = useRef(null), menuButton = useRef(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const patch = update => setPrefs(previous => { const current = labProgress(previous), next = update(current); return { ...previous, learningPaths: { ...previous.learningPaths, knapsack: { ...previous.learningPaths?.knapsack, labV1: { ...next, version: 1 } } } }; });
  const navigate = id => { patch(current => ({ ...current, chapter: id })); setMenuOpen(false); };
  useCourseKeys({index:chapterIndex,count:CHAPTERS.length,navigate:index=>navigate(CHAPTERS[index].id),menuOpen});
  const onPass = id => { if (CHECK_IDS.includes(id)) patch(current => current.passed[id] ? current : { ...current, passed: { ...current.passed, [id]: true } }); };
  const updateDraft = (id, value) => patch(current => ({ ...current, drafts: { ...current.drafts, [id]: value } }));
  useEffect(() => {
    if (previousChapter.current !== chapter.id) { if(heading.current)heading.current.scrollTop=0; heading.current?.focus({ preventScroll: true }); previousChapter.current = chapter.id; }
  }, [chapter.id]);
  useEffect(() => {
    if (!menuOpen) return;
    const outside = event => { if (!menu.current?.contains(event.target)) setMenuOpen(false); };
    const escape = event => { if (event.key === 'Escape') { event.preventDefault();setMenuOpen(false); menuButton.current?.focus(); } };
    document.addEventListener('pointerdown', outside);
    document.addEventListener('keydown', escape);
    return () => { document.removeEventListener('pointerdown', outside); document.removeEventListener('keydown', escape); };
  }, [menuOpen]);
  return <div className="algorithm-lab" aria-label="背包 DP">
    <header className="lab-course-header"><div className="lab-header-actions">{headerActions}</div>
      <h1>背包 DP</h1><span className="lab-position">{chapterIndex + 1} / {CHAPTERS.length}</span>
    <aside className="lab-course-tools" aria-label="课程导航"><nav className="lab-page-navigation" aria-label="章节翻页"><button type="button" className="lab-icon-button" aria-label="上一页" title={chapterIndex ? `上一页：${CHAPTERS[chapterIndex - 1].title}` : '已经是第一页'} disabled={!chapterIndex} onClick={() => navigate(CHAPTERS[chapterIndex - 1].id)}><ArrowLeft size={18}/></button><button type="button" className="lab-icon-button" aria-label="下一页" title={chapterIndex < CHAPTERS.length - 1 ? `下一页：${CHAPTERS[chapterIndex + 1].title}` : '已经是最后一页'} disabled={chapterIndex === CHAPTERS.length - 1} onClick={() => navigate(CHAPTERS[chapterIndex + 1].id)}><ArrowRight size={18}/></button></nav><div className="lab-menu" ref={menu}>
        <button type="button" ref={menuButton} className="lab-menu-toggle" aria-label="目录" title="课程目录" aria-expanded={menuOpen} aria-controls="lab-chapters" onClick={() => setMenuOpen(value => !value)}><List size={17}/><span>目录</span></button>
        {menuOpen && <nav id="lab-chapters" aria-label="课程章节">{CHAPTERS.map((item, i) => <button type="button" key={item.id} aria-current={item.id === chapter.id ? 'step' : undefined} onClick={() => navigate(item.id)}><span>{String(i + 1).padStart(2, '0')}</span><b>{item.title}</b>{item.checks.every(id => saved.passed[id]) && <Check size={14} aria-label="已完成"/>}</button>)}</nav>}
      </div></aside></header>
    <main className="lab-lesson" ref={heading} tabIndex={-1} aria-label={chapter.title}>
      <Content key={chapter.id} drafts={saved.drafts} passed={saved.passed} onPass={onPass} updateDraft={updateDraft} rows={rows} onTrain={onTrain} onGuided={onGuided}/>
    </main>
  </div>;
}
