import {lessonKey} from '@/lib/lessonKey.js';
import {foundationLectures,lectureDestination} from '@/lib/algorithmLearning.js';
import PageSearch from '@/components/PageSearch.jsx';
import {lessonLevel} from '@/lib/difficultyPresentation.js';
import Tooltip from '@/components/Tooltip.jsx';
import FolderSelect from '@/components/FolderSelect.jsx';
import { lectureFolderOptions, lectureMatchesFolder,primaryLectureTopic } from '@/lib/lectureFolders.js';
import {canonicalKnowledgeName} from '@/lib/knowledgeNames.js';
import SortDirection from '@/components/SortDirection.jsx';
import { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import ReadingImage, { readingUrlTransform } from '@/components/ReadingImage.jsx';
import InlineTitle from '@/components/InlineTitle.jsx';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import { ArrowLeft, ArrowRight, BookOpen, Check, ExternalLink, House, LoaderCircle, Maximize2, Minimize2, Search } from 'lucide-react';
import { normalizeMarkdown } from '@/lib/normalizeMarkdown.js';
import './LecturesPanel.css';

function LessonTitle({ children }) {
  return <span className="inline-lesson-markdown"><ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[[rehypeKatex, { strict: 'ignore', throwOnError: false }]]} components={{ p: ({ children }) => <span>{children}</span> }}>{normalizeMarkdown(children || '')}</ReactMarkdown></span>;
}

function LessonMarkdown({ lesson }) {
  return <div className="lecture-markdown"><ReactMarkdown urlTransform={readingUrlTransform} remarkPlugins={[remarkGfm, remarkMath]} rehypePlugins={[rehypeKatex]} components={{
    img: ({ node, ...props }) => <ReadingImage {...props} images={lesson.images} />,
    a: ({ children, ...props }) => <a {...props} target="_blank" rel="noreferrer">{children}</a>,
  }}>{normalizeMarkdown(lesson.markdown || '')}</ReactMarkdown></div>;
}

export function LectureDisclosure({ lecture = {}, inlineMarkdown, images, api, onTrain, onError }) {
  const [open, setOpen] = useState(false), [content, setContent] = useState(null), [error, setError] = useState('');
  useEffect(() => {
    if (!open || inlineMarkdown != null || content || !lecture.id) return;
    let cancelled = false;
    api('lecture?id=' + encodeURIComponent(lecture.id)).then(value => {
      if (!cancelled) { setContent(value); setError(''); }
    }).catch(issue => { if (!cancelled) { setError(issue.message); onError?.(issue.message); } });
    return () => { cancelled = true; };
  }, [open, inlineMarkdown, lecture.id, api, !!content]);
  const display = inlineMarkdown != null ? { ...lecture, markdown: inlineMarkdown, images } : content;
  return <details className="lecture-disclosure" onToggle={event => setOpen(event.currentTarget.open)}>
    <summary><BookOpen size={15} /><span><LessonTitle>{lecture.displayTitle || lecture.concept || lecture.title || '从零讲'}</LessonTitle></span></summary>
    {open && <div className="lecture-disclosure-body">
      {display ? <LessonMarkdown lesson={display} /> : error ? <p role="alert">{error}</p> : <p role="status"><LoaderCircle size={15} className="spin" />正在读取完整讲解</p>}
      {lecture.sourceContest && <div className="lecture-source"><span>来源：{lecture.sourceContest} · {lecture.sourceProblem} <InlineTitle>{lecture.sourceTitle}</InlineTitle></span>{onTrain && lecture.sourceProblemIds?.[0] && <button type="button" className="icon-button" aria-label="练习原题" title="练习原题" onClick={() => onTrain(lecture.sourceProblemIds[0])}><ExternalLink size={16} /></button>}</div>}
    </div>}
  </details>;
}

const EMPTY_CATEGORIES=[];
export function LecturesPanel({ lectures, api, initialLecture, onTrain, onError,onFullscreenChange,onOpenTemplate,categories=EMPTY_CATEGORIES,visit,prefs={},setPrefs }) {
  const [snapshot, setSnapshot] = useState(lectures || null), [query, setQuery] = useState(visit?.query||''), [selected, setSelected] = useState(initialLecture || visit?.selected || null);
  const moved=lectureDestination(selected);
  useEffect(()=>{if(moved&&onOpenTemplate){setSelected(null);if(visit)visit.selected=null;onOpenTemplate(moved.templateId);}},[moved,onOpenTemplate,visit]);
  const [readingFull,setReadingFull]=useState(visit?.readingFull||false);
  const readingScroll=useRef(null);
  const changeReadingFull=value=>{readingScroll.current=detail.current?.scrollTop||0;setReadingFull(value);};
  useLayoutEffect(()=>{onFullscreenChange?.(readingFull&&Boolean(selected));return()=>onFullscreenChange?.(false);},[readingFull,Boolean(selected),onFullscreenChange]);
  useEffect(()=>{if(visit)visit.readingFull=readingFull;},[readingFull,visit]);
  useEffect(()=>{if(!readingFull)return;const escape=event=>{if(event.key==='Escape'&&!document.querySelector('dialog[open],[aria-modal=true]')){event.preventDefault();event.stopImmediatePropagation();changeReadingFull(false);}};window.addEventListener('keydown',escape,true);return()=>window.removeEventListener('keydown',escape,true);},[readingFull]);
  const [history,setHistory]=useState(visit?.history||[]),restoreScroll=useRef(visit?.scrollTop??null);
  const openLecture=(id,root=false)=>{if(root)setHistory([]);else if(selected&&id!==selected)setHistory(old=>[...old,{id:selected,scrollTop:detail.current?.scrollTop||0}]);restoreScroll.current=0;setSelected(id);};
  const backLecture=()=>{const previous=history.at(-1);if(!previous)return;setHistory(old=>old.slice(0,-1));restoreScroll.current=previous.scrollTop;setSelected(previous.id);};
  const [classification, setClassification] = useState(visit?.classification||''),[descending,setDescending]=useState(visit?.descending||false);
  const [lesson, setLesson] = useState(null), [error, setError] = useState('');
  const seq = useRef(0),detail=useRef(null);
  useLayoutEffect(()=>{if(readingScroll.current===null)return;const top=readingScroll.current;readingScroll.current=null;const frame=requestAnimationFrame(()=>{if(detail.current)detail.current.scrollTop=top;});return()=>cancelAnimationFrame(frame);},[readingFull]);
  useEffect(()=>{if(visit)Object.assign(visit,{query,selected,classification,descending,history});},[query,selected,classification,descending,history,visit]);
  useEffect(() => { if (initialLecture && initialLecture!==visit?.selected) {setHistory([]);restoreScroll.current=0;setSelected(initialLecture);} }, [initialLecture]);
  useEffect(() => {
    if (lectures) { setSnapshot(lectures); return; }
    let cancelled = false;
    api('lectures').then(value => { if (!cancelled) { setSnapshot(value); setError(''); } }).catch(issue => { if (!cancelled) { setError(issue.message); onError?.(issue.message); } });
    return () => { cancelled = true; };
  }, [api, lectures]);
  useEffect(() => {
    if (!selected) { setLesson(null); return; }
    if(detail.current)detail.current.scrollTop=0;
    const current = ++seq.current; setLesson(null); setError('');
    api('lecture?id=' + encodeURIComponent(selected)).then(value => { if (seq.current === current) setLesson(value); }).catch(issue => { if (seq.current === current) setError(issue.message); });
    return () => { seq.current++; };
  }, [selected, api]);
  useEffect(()=>{if(lesson&&detail.current){detail.current.scrollTop=restoreScroll.current??0;restoreScroll.current=null;}},[lesson]);
  const entries = foundationLectures(Array.isArray(snapshot) ? snapshot : snapshot?.lectures || []);
  const classifications = useMemo(() => lectureFolderOptions(entries,categories), [snapshot,categories]);
  const sorted=useMemo(()=>entries.map((item,index)=>({...item,listIndex:index,displayDifficulty:lessonLevel(item)})).sort((a,b)=>['基础','进阶','深入'].indexOf(a.displayDifficulty)-['基础','进阶','深入'].indexOf(b.displayDifficulty)||a.listIndex-b.listIndex),[snapshot]);
  const categoryPath = classification ? JSON.parse(classification) : [];
  const filtered = sorted.filter(item => lectureMatchesFolder(item, categoryPath,categories) && `${item.concept} ${item.displayTitle || ''} ${item.originalTitle || item.title} ${(item.tags || []).join(' ')} ${item.category || ''} ${item.sourceContest} ${item.sourceTitle}`.toLowerCase().includes(query.trim().toLowerCase()));
  if(descending)filtered.reverse();
  const current=entries.find(item=>item.id===selected)||lesson;
  const prerequisites=useMemo(()=>{
    if(!current)return [];
    const primary=primaryLectureTopic(current),seen=new Set([primary]);
    return (current.tags||[]).map(canonicalKnowledgeName).filter(tag=>{if(seen.has(tag))return false;seen.add(tag);return true;}).map(tag=>({tag,target:sorted.find(item=>item.id!==selected&&primaryLectureTopic(item)===tag)})).filter(item=>item.target);
  },[current,sorted,selected]);
  const toggleLearned=()=>setPrefs?.(previous=>{const keys=new Set(previous.learnedLectures||[]),key=lessonKey(lesson);keys.has(key)?keys.delete(key):keys.add(key);return {...previous,learnedLectures:[...keys]};});
  const isLearned=(prefs.learnedLectures||[]).includes(lessonKey(lesson));
  return <div className="lectures-page" aria-label="从零讲知识总结">
    <PageSearch><label className="search-box"><Search size={17}/><input aria-label="搜索从零讲知识" value={query} onChange={event=>setQuery(event.target.value)}/></label><SortDirection label="切换讲解排序方向" descending={descending} onChange={setDescending}/><FolderSelect iconOnly label="从零讲知识分类" placeholder="全部知识分类" options={classifications} value={classification} onChange={event=>setClassification(event.target.value)}/></PageSearch>
    <div className={'lectures-layout' + (selected ? ' has-selection' : '')+(readingFull&&selected?' lecture-reading-full':'')}>
      <nav className="lectures-list" aria-label="完整知识讲解">{filtered.map(item => <button key={item.id} className={selected === item.id ? 'selected' : ''} onClick={() => openLecture(item.id,true)}><span className="lecture-item-heading"><strong><LessonTitle>{item.displayTitle || item.concept || item.title}</LessonTitle></strong><Tooltip text="课程学习层次，与比赛题目的 CF 分数无关"><b className={'lecture-difficulty lecture-level-'+['基础','进阶','深入'].indexOf(item.displayDifficulty)}>{item.displayDifficulty}</b></Tooltip></span><span className="lecture-category">{primaryLectureTopic(item)}</span></button>)}{snapshot && !filtered.length && <p>没有匹配的完整讲解。仅有指针的段落会链接已有讲解。</p>}</nav>
      <article ref={detail} onScroll={event=>{if(visit)visit.scrollTop=event.currentTarget.scrollTop;}} className="lectures-detail" tabIndex={0} aria-label="知识讲解正文">
        {selected ? <><div className="lectures-detail-bar"><button type="button" onClick={backLecture} disabled={!history.length} data-folder-up className="icon-button" aria-label="返回上篇" title={history.length?"返回上篇讲解":"已到起始讲解"}><ArrowLeft size={17} /></button>{history.length>0&&<button type="button" className="icon-button" aria-label="返回根页面" title="返回根页面" onClick={()=>{restoreScroll.current=history[0].scrollTop;setSelected(history[0].id);setHistory([]);}}><House size={15}/></button>}{lesson&&setPrefs&&<button type="button" className="icon-button" aria-label={isLearned?'取消已学会':'标记已学会'} title={isLearned?'取消已学会':'标记已学会'} aria-pressed={isLearned} onClick={toggleLearned}><Check size={15}/></button>}{lesson && onTrain && lesson.sourceProblemIds?.[0] && <button type="button" className="icon-button" aria-label="练习来源题" title="练习来源题" onClick={() => onTrain(lesson.sourceProblemIds[0])}><ExternalLink size={17} /></button>}{lesson&&<span className="lecture-source-inline" aria-label="来源题目" title={[lesson.sourceContest,lesson.sourceProblem,lesson.sourceTitle].filter(Boolean).join(" · ")}>{lesson.sourceContest} · {lesson.sourceProblem} <InlineTitle>{lesson.sourceTitle}</InlineTitle></span>}<button type="button" className="icon-button lecture-fullscreen-toggle" aria-label={readingFull?'退出从零讲全屏':'从零讲全屏'} title={readingFull?'退出从零讲全屏 · Esc':'从零讲全屏'} aria-pressed={readingFull} onClick={()=>changeReadingFull(!readingFull)}>{readingFull?<Minimize2 size={17}/>:<Maximize2 size={17}/>}</button></div>{lesson ? <>{prerequisites.length>0&&<nav className="lecture-prerequisites" aria-label="相关知识从零讲"><span>用到的其他知识</span>{prerequisites.map(({tag,target})=><button type="button" key={tag} onClick={()=>openLecture(target.id)}><BookOpen size={14}/>从零讲：{tag}<ArrowRight size={13}/></button>)}</nav>}<LessonMarkdown lesson={lesson} /></> : error ? <p role="alert">{error}</p> : <p role="status">正在读取完整讲解…</p>}</> : <div className="lectures-intro"><BookOpen size={25} /><h3>选一个知识点开始阅读</h3>{entries.length > 0 && <button onClick={() => openLecture(filtered[0]?.id || entries[0].id,true)}>阅读第一篇<ArrowRight size={14} /></button>}{error && <p role="alert">{error}</p>}</div>}
      </article>
    </div>
  </div>;
}
