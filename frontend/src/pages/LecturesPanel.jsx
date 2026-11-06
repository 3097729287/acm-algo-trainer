import {readCatalogue,loadCatalogue} from '@/lib/catalogueCache.js';
import {readingQueue,nextReading} from '@/lib/lectureQueue.js';
import LessonLearnedButton from '@/components/LessonLearnedButton.jsx';
import {lessonKey} from '@/lib/lessonKey.js';
import {lectureDestination} from '@/lib/algorithmLearning.js';
import PageSearch from '@/components/PageSearch.jsx';
import {CatalogueGroup,CatalogueEntry} from '@/components/LearningCatalogue.jsx';
import {useStudyState} from '@/lib/StudyPane.jsx';
import {lectureCurriculum,prerequisiteTitle,LECTURE_ROLES} from '@/lib/learningCurriculum.js';
import {recordKnowledgeLesson} from '@/lib/knowledgeJourney.js';
import FolderSelect from '@/components/FolderSelect.jsx';
import { lectureFolderOptions, lectureMatchesFolder } from '@/lib/lectureFolders.js';
import {canonicalKnowledgeName} from '@/lib/knowledgeNames.js';
import SortDirection from '@/components/SortDirection.jsx';
import { Fragment, useEffect, useId, useLayoutEffect, useMemo, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import ReadingImage, { readingUrlTransform } from '@/components/ReadingImage.jsx';
import InlineTitle from '@/components/InlineTitle.jsx';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import { ArrowLeft, ArrowRight, BookCheck, BookOpen, ExternalLink, House, LoaderCircle, Maximize2, Minimize2, PanelLeft, Search } from 'lucide-react';
import { normalizeMarkdown } from '@/lib/normalizeMarkdown.js';
import './LecturesPanel.css';

function LessonTitle({ children }) {
  return <span className="inline-lesson-markdown"><ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[[rehypeKatex, { strict: 'ignore', throwOnError: false }]]} components={{ p: ({ children }) => <span>{children}</span> }}>{normalizeMarkdown(children || '')}</ReactMarkdown></span>;
}

function catalogueTitle(item) {
  const title=(item.displayTitle||item.concept||item.title).replace(/^从零讲[：:]\s*/,'');
  // Reviewed foundation titles have a descriptive suffix. Problem-specific
  // titles keep their identifying detail instead of collapsing to one topic.
  return ['language','algorithm'].includes(item.curriculum.kind)?title.split(/：|:\s+/)[0]:title;
}

function LessonMarkdown({ lesson }) {
  const markdown=normalizeMarkdown(lesson.markdown||''),title=lesson.displayTitle||lesson.concept||lesson.title;
  const needsTitle=lectureCurriculum(lesson).kind==='language'&&title&&!/^ {0,3}#\s+\S/m.test(markdown.replace(/```[\s\S]*?```|~~~[\s\S]*?~~~/g,''));
  return <div className="lecture-markdown">{needsTitle&&<h1 className="lecture-title"><LessonTitle>{title.replace(/^从零讲[：:]\s*/,'')}</LessonTitle></h1>}<ReactMarkdown urlTransform={readingUrlTransform} remarkPlugins={[remarkGfm, remarkMath]} rehypePlugins={[rehypeKatex]} components={{
    img: ({ node, ...props }) => <ReadingImage {...props} images={lesson.images} />,
    a: ({ children, ...props }) => <a {...props} target="_blank" rel="noreferrer">{children}</a>,
  }}>{markdown}</ReactMarkdown></div>;
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
export function LecturesPanel({ lectures, api, initialLecture, onTrain, onError,onFullscreenChange,onOpenTemplate,categories=EMPTY_CATEGORIES,visit,prefs={},setPrefs,onOpenLecture,onNextLecture,study=false,directoryOpen:controlledDirectoryOpen,onDirectoryChange }) {
  const [snapshot, setSnapshot] = useState(()=>lectures||readCatalogue(api,window.__tbAccountUserId||'local','lectures')||null), [query, setQuery] = useStudyState('lectureQuery',visit?.query||''), [selected, setSelected] = useState(initialLecture || visit?.selected || null);
  const moved=lectureDestination(selected);
  useEffect(()=>{if(moved&&onOpenTemplate){setSelected(null);if(visit)visit.selected=null;onOpenTemplate(moved.templateId);}},[moved,onOpenTemplate,visit]);
  const [showLearned,setShowLearned]=useState(true);
  const learnedKeys=useMemo(()=>new Set(prefs.learnedLectures||[]),[prefs.learnedLectures]);
  const [readingFull,setReadingFull]=useState(visit?.readingFull||false);
  const [localDirectoryOpen,setLocalDirectoryOpen]=useState(visit?.directoryOpen||false),directoryId=useId(),directory=useRef(null);
  const directoryOpen=controlledDirectoryOpen??localDirectoryOpen;
  const setDirectoryOpen=value=>{const next=typeof value==='function'?value(directoryOpen):value;setLocalDirectoryOpen(next);if(visit)visit.directoryOpen=next;onDirectoryChange?.(next);};
  useEffect(()=>{if(visit)visit.directoryOpen=directoryOpen;},[directoryOpen,visit]);
  useLayoutEffect(()=>{if(directoryOpen&&directory.current)directory.current.scrollTop=visit?.directoryScrollTop||0;},[directoryOpen,initialLecture]);
  const readingScroll=useRef(null);
  const changeReadingFull=value=>{readingScroll.current=detail.current?.scrollTop||0;setReadingFull(value);};
  useLayoutEffect(()=>{onFullscreenChange?.(readingFull&&Boolean(selected));return()=>onFullscreenChange?.(false);},[readingFull,Boolean(selected),onFullscreenChange]);
  useEffect(()=>{if(visit)visit.readingFull=readingFull;},[readingFull,visit]);
  useEffect(()=>{if(!readingFull)return;const escape=event=>{if(event.key==='Escape'&&!document.querySelector('dialog[open],[aria-modal=true]')){event.preventDefault();event.stopImmediatePropagation();changeReadingFull(false);}};window.addEventListener('keydown',escape,true);return()=>window.removeEventListener('keydown',escape,true);},[readingFull]);
  const [history,setHistory]=useState(visit?.history||[]),restoreScroll=useRef(visit?.scrollTop??null);
  const openLecture=(id,root=false)=>{if(onOpenLecture){onOpenLecture(id);return;}if(root)setHistory([]);else if(selected&&id!==selected)setHistory(old=>[...old,{id:selected,scrollTop:detail.current?.scrollTop||0}]);restoreScroll.current=0;setSelected(id);};
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
    loadCatalogue(api,window.__tbAccountUserId||'local','lectures',{refresh:true}).then(value => { if (!cancelled) { setSnapshot(value); setError(''); } }).catch(issue => { if (!cancelled) { setError(issue.message); onError?.(issue.message); } });
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
  const entries=useMemo(()=>readingQueue(snapshot,prefs,selected,{includeAll:window.__tbAdmin===true}),[snapshot,prefs.learnedLectures,selected]);
  const classifications = useMemo(() => lectureFolderOptions(entries,categories), [entries,categories]);
  const sorted=entries;
  const currentIndex=sorted.findIndex(item=>item.id===selected),previous=currentIndex>0?sorted[currentIndex-1]:null;
  const next=nextReading(sorted,selected);
  const categoryPath = classification ? JSON.parse(classification) : [];
  const filtered = sorted.filter(item => (showLearned||!learnedKeys.has(lessonKey(item))) && lectureMatchesFolder(item, categoryPath,categories) && `${item.concept} ${item.displayTitle || ''} ${item.originalTitle || item.title} ${(item.tags || []).join(' ')} ${item.category || ''} ${item.sourceContest} ${item.sourceTitle}`.toLowerCase().includes(query.trim().toLowerCase()));
  if(descending)filtered.reverse();
  const groups=[...new Set(filtered.map(item=>item.curriculum.kind))];
  const current=entries.find(item=>item.id===selected)||lesson;
  const prerequisites=useMemo(()=>lectureCurriculum(current||{}).prerequisites.map(id=>({id,title:prerequisiteTitle(id),destination:lectureDestination(id)})),[current]);
  const openPrerequisite=item=>item.destination&&onOpenTemplate?onOpenTemplate(item.destination.templateId):openLecture(item.id);
  const toggleLearned=()=>setPrefs?.(previous=>{const keys=new Set(previous.learnedLectures||[]),key=lessonKey(lesson);keys.has(key)?keys.delete(key):keys.add(key);return recordKnowledgeLesson(previous,{...previous,learnedLectures:[...keys]},key);});
  const isLearned=(prefs.learnedLectures||[]).includes(lessonKey(lesson));
  return <div className="lectures-page" aria-label="从零讲知识总结">
    <PageSearch><label className="search-box"><Search size={17}/><input aria-label="搜索从零讲知识" value={query} onChange={event=>setQuery(event.target.value)}/></label><SortDirection label="切换讲解排序方向" descending={descending} onChange={setDescending}/><FolderSelect iconOnly label="从零讲知识分类" placeholder="全部知识分类" options={classifications} value={classification} onChange={event=>setClassification(event.target.value)}/><button type="button" className="icon-button lecture-learned-filter" aria-label={showLearned?'隐藏已学会':'显示已学会'} title={showLearned?'隐藏已学会':'显示已学会'} aria-pressed={showLearned} onClick={()=>setShowLearned(value=>!value)}>{showLearned?<BookCheck size={17}/>:<BookOpen size={17}/>}</button></PageSearch>
    {!selected&&error&&<p role="alert">{error}</p>}
    {!selected&&!study?<div className="learning-catalogue lecture-catalogue" aria-label="完整知识讲解">
      {groups.map(kind=><CatalogueGroup key={kind} title={kind==='language'?'基础学习':LECTURE_ROLES[kind]}>{filtered.filter(item=>item.curriculum.kind===kind).map(item=>{const title=catalogueTitle(item);return <CatalogueEntry key={item.id} className={'lecture-entry'+(learnedKeys.has(lessonKey(item))?' lecture-learned':'')} title={<LessonTitle>{title}</LessonTitle>} label={title} onOpen={()=>openLecture(item.id,true)}/>;})}</CatalogueGroup>)}
      {!snapshot&&!error&&<LoaderCircle className="spin" role="status" aria-label="正在读取完整讲解" size={19}/>}
      {snapshot&&!filtered.length&&<p className="progress-muted">没有匹配的完整讲解。</p>}
    </div>:<div className={'lectures-layout' + (selected ? ' has-selection' : '')+(readingFull&&selected?' lecture-reading-full':'')+(directoryOpen?' lecture-directory-open':'')}>
      {(!study||directoryOpen)&&<nav ref={directory} id={directoryId} className="lectures-list" aria-label="完整知识讲解" onScroll={event=>{if(visit)visit.directoryScrollTop=event.currentTarget.scrollTop;}}>{filtered.map((item,index) => <Fragment key={item.id}>
        {(index===0||filtered[index-1].curriculum.kind!==item.curriculum.kind)&&<h3 className="lecture-curriculum-group">{item.curriculum.kind==='language'?'基础学习':LECTURE_ROLES[item.curriculum.kind]}</h3>}
        <button className={[selected===item.id?'selected':'',learnedKeys.has(lessonKey(item))?'lecture-learned':''].filter(Boolean).join(' ')} aria-current={selected===item.id?'page':undefined} data-lesson-kind={item.curriculum.kind} onClick={() => {if((study||readingFull)&&onNextLecture)onNextLecture(item.id);else openLecture(item.id,true);}}>
          <strong><LessonTitle>{catalogueTitle(item)}</LessonTitle></strong>
        </button>
      </Fragment>)}{snapshot && !filtered.length && <p>没有匹配的完整讲解。仅有指针的段落会链接已有讲解。</p>}</nav>}
      <article ref={detail} onScroll={event=>{if(visit)visit.scrollTop=event.currentTarget.scrollTop;}} className="lectures-detail" tabIndex={0} aria-label="知识讲解正文">
        {selected ? <><div className="lectures-detail-bar">{(study||readingFull)&&<button type="button" className="icon-button lecture-directory-toggle" aria-label="讲解目录" title="讲解目录" aria-expanded={directoryOpen} aria-controls={directoryId} onClick={()=>setDirectoryOpen(value=>!value)}><PanelLeft size={18}/></button>}<button type="button" onClick={()=>{if(history.length)backLecture();else if(previous)(onNextLecture||openLecture)(previous.id);}} disabled={!history.length&&!previous} data-folder-up className="icon-button" aria-label="返回上篇" title={history.length?"返回上篇讲解":previous?"上一篇 · "+(previous.displayTitle||previous.concept||previous.title):"已到第一篇"}><ArrowLeft size={17} /></button>{history.length>0&&<button type="button" className="icon-button" aria-label="返回根页面" title="返回根页面" onClick={()=>{restoreScroll.current=history[0].scrollTop;setSelected(history[0].id);setHistory([]);}}><House size={15}/></button>}{lesson&&setPrefs&&<LessonLearnedButton learned={isLearned} onClick={toggleLearned}/>}{lesson && onTrain && lesson.sourceProblemIds?.[0] && <button type="button" className="icon-button" aria-label="练习来源题" title="练习来源题" onClick={() => onTrain(lesson.sourceProblemIds[0])}><ExternalLink size={17} /></button>}{lesson&&<span className="lecture-source-inline" aria-label="来源题目" title={[lesson.sourceContest,lesson.sourceProblem,lesson.sourceTitle].filter(Boolean).join(" · ")}>{lesson.sourceContest} · {lesson.sourceProblem} <InlineTitle>{lesson.sourceTitle}</InlineTitle></span>}<button type="button" className="lecture-next" aria-label="下一篇" title={next?.displayTitle||next?.concept||next?.title||'已到最后一篇'} disabled={!next} onClick={()=>{if(next)(onNextLecture||openLecture)(next.id);}}>下一篇<ArrowRight size={16}/></button><button type="button" className="icon-button lecture-fullscreen-toggle" aria-label={readingFull?'退出从零讲全屏':'从零讲全屏'} title={readingFull?'退出从零讲全屏 · Esc':'从零讲全屏'} aria-pressed={readingFull} onClick={()=>changeReadingFull(!readingFull)}>{readingFull?<Minimize2 size={17}/>:<Maximize2 size={17}/>}</button></div>{lesson ? <>{prerequisites.length>0&&<nav className="lecture-prerequisites" aria-label="学习先修"><span>先修知识</span>{prerequisites.map(item=><button type="button" key={item.id} onClick={()=>openPrerequisite(item)}><BookOpen size={14}/>{item.title}<ArrowRight size={13}/></button>)}</nav>}<LessonMarkdown lesson={lesson} /></> : error ? <p role="alert">{error}</p> : <p role="status">正在读取完整讲解…</p>}</> : null}
      </article>
    </div>}
  </div>;
}
