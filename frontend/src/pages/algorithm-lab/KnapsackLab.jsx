import { useEffect, useRef, useState } from 'react';
import { ArrowLeft, ArrowRight, Check, ChevronDown, List } from 'lucide-react';
import { CHAPTERS, CHECK_IDS } from './knapsackCourse.js';
import { PackingExperiment, TraceExperiment } from './KnapsackExperiments.jsx';
import StateExperiment from './StateExperiment.jsx';
import { DebugWorkshop, PracticeWorkshop, TemplateWorkshop, TransferWorkshop } from './KnapsackChallenges.jsx';
import './algorithmLab.css';

export function labProgress(prefs) {
  const saved = prefs?.learningPaths?.knapsack?.labV1;
  if (!saved || typeof saved !== 'object') return { chapter: 'pack', passed: {}, drafts: {} };
  return { chapter: CHAPTERS.some(item => item.id === saved.chapter) ? saved.chapter : 'pack',
    passed: saved.passed && typeof saved.passed === 'object' ? Object.fromEntries(CHECK_IDS.filter(id => saved.passed[id] === true).map(id => [id, true])) : {},
    drafts: saved.drafts && typeof saved.drafts === 'object' && !Array.isArray(saved.drafts) ? saved.drafts : {} };
}

const CONTENT = { pack: PackingExperiment, state: StateExperiment, trace: TraceExperiment, code: TemplateWorkshop, debug: DebugWorkshop, transfer: TransferWorkshop, practice: PracticeWorkshop };

export default function KnapsackLab({ prefs, setPrefs, rows = [], onTrain, headerActions }) {
  const saved = labProgress(prefs), chapterIndex = CHAPTERS.findIndex(item => item.id === saved.chapter), chapter = CHAPTERS[chapterIndex];
  const Content = CONTENT[chapter.id], heading = useRef(null), previousChapter = useRef(chapter.id), menu = useRef(null), menuButton = useRef(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const patch = update => setPrefs(previous => { const current = labProgress(previous), next = update(current); return { ...previous, learningPaths: { ...previous.learningPaths, knapsack: { ...previous.learningPaths?.knapsack, labV1: { ...next, version: 1 } } } }; });
  const navigate = id => { patch(current => ({ ...current, chapter: id })); setMenuOpen(false); };
  const onPass = id => { if (CHECK_IDS.includes(id)) patch(current => current.passed[id] ? current : { ...current, passed: { ...current.passed, [id]: true } }); };
  const updateDraft = (id, value) => patch(current => ({ ...current, drafts: { ...current.drafts, [id]: value } }));
  useEffect(() => {
    if (previousChapter.current !== chapter.id) { heading.current?.scrollIntoView({ block: 'start' }); heading.current?.focus({ preventScroll: true }); previousChapter.current = chapter.id; }
  }, [chapter.id]);
  useEffect(() => {
    if (!menuOpen) return;
    const outside = event => { if (!menu.current?.contains(event.target)) setMenuOpen(false); };
    const escape = event => { if (event.key === 'Escape') { setMenuOpen(false); menuButton.current?.focus(); } };
    document.addEventListener('pointerdown', outside);
    document.addEventListener('keydown', escape);
    return () => { document.removeEventListener('pointerdown', outside); document.removeEventListener('keydown', escape); };
  }, [menuOpen]);
  const recommended = CHAPTERS.find(item => item.checks.some(id => !saved.passed[id]));
  return <div className="algorithm-lab" aria-label="背包 DP">
    <header className="lab-course-header">
      <h1>背包 DP</h1><span className="lab-position">{chapterIndex + 1} / {CHAPTERS.length}</span>
      <div className="lab-header-actions"><div className="lab-menu" ref={menu}>
        <button type="button" ref={menuButton} className="lab-menu-toggle" aria-expanded={menuOpen} aria-controls="lab-chapters" onClick={() => setMenuOpen(value => !value)}><List size={17}/>目录<ChevronDown size={14}/></button>
        {menuOpen && <nav id="lab-chapters" aria-label="课程章节">{CHAPTERS.map((item, i) => <button type="button" key={item.id} aria-current={item.id === chapter.id ? 'step' : undefined} onClick={() => navigate(item.id)}><span>{String(i + 1).padStart(2, '0')}</span><b>{item.title}</b>{item.checks.every(id => saved.passed[id]) && <Check size={14} aria-label="已完成"/>}</button>)}</nav>}
      </div>{headerActions}</div>
    </header>
    <main className="lab-lesson" ref={heading} tabIndex={-1} aria-label={chapter.title}>
      <Content key={chapter.id} drafts={saved.drafts} passed={saved.passed} onPass={onPass} updateDraft={updateDraft} rows={rows} onTrain={onTrain}/>
      <footer className="lab-lesson-footer"><button type="button" className="lab-text-button" disabled={chapterIndex === 0} onClick={() => navigate(CHAPTERS[chapterIndex - 1].id)}><ArrowLeft size={15}/>上一节</button>{chapterIndex < CHAPTERS.length - 1 ? <button type="button" className="lab-button" onClick={() => navigate(CHAPTERS[chapterIndex + 1].id)}>下一节：{CHAPTERS[chapterIndex + 1].title}<ArrowRight size={16}/></button> : recommended ? <button type="button" className="lab-button" onClick={() => navigate(recommended.id)}>继续未完成的练习<ArrowRight size={16}/></button> : <span className="lab-completed"><Check size={17}/>练习已完成</span>}</footer>
    </main>
  </div>;
}
