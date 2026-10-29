import {useCallback,useEffect,useLayoutEffect,useMemo,useRef,useState} from 'react';
import {ArrowLeft,ArrowUpRight,BookOpen,BookText,Check,House,LoaderCircle,Maximize2,Minimize2,X} from 'lucide-react';
import Markdown from './SolutionMarkdown.jsx';
import {solutionBlocks} from '@/lib/practiceMetadata.js';
import {primaryLectureTopic} from '@/lib/lectureFolders.js';
import {canonicalKnowledgeName} from '@/lib/knowledgeNames.js';
import './SolutionReader.css';
import InlineTitle from './InlineTitle.jsx';

import {lessonKey} from '@/lib/lessonKey.js';
export default function SolutionReader({reader,error,api,methodId,onMethodChange,onClose,fullscreen,onFullscreen,prefs,setPrefs,onTrain}){
 const copyCode=useCallback(text=>navigator.clipboard?.writeText(String(text)),[]);
 const methods=reader?.methods?.length?reader.methods:reader?[{...reader,id:'original'}]:[];
 const method=methods.find(item=>item.id===methodId)||methods.find(item=>item.id===reader?.primaryMethod)||methods[0];
 const [variants,setVariants]=useState({}),[stack,setStack]=useState([]),[catalog,setCatalog]=useState([]);
 const body=useRef(null),restore=useRef(0),positions=useRef(new Map()),sequence=useRef(0);
 const variant=variants[method?.id]||'default',rootKey=`${method?.id}:${variant}`;
 const selected=stack.at(-1),learned=new Set(prefs?.learnedLectures||[]);
 useEffect(()=>{setStack([]);restore.current=positions.current.get(rootKey)||0;},[method?.id]);
 useEffect(()=>{let alive=true;api('lectures').then(value=>{if(alive)setCatalog(value.lectures||[]);}).catch(()=>{});return()=>{alive=false;sequence.current++;};},[api]);
 const rootDocument=method?(variant==='detailed'?method.detailedSolution:method):null;
 const document=selected||rootDocument;
 const lectures=useMemo(()=>{const values=new Map();for(const item of [...catalog,...(reader?.lectures||[]),...(method?.lectures||[])])values.set(item.id||lessonKey(item),item);return [...values.values()];},[catalog,reader,method]);
 const blocks=useMemo(()=>solutionBlocks(document?.markdown||'',lectures),[document?.markdown,lectures]);
 const remember=()=>{const top=body.current?.scrollTop||0;if(stack.length)selected.scrollTop=top;else positions.current.set(rootKey,top);return top;};
 const open=async(lecture,inlineMarkdown,images)=>{
  const key=lessonKey(lecture);if(selected&&key===lessonKey(selected))return;
  const parentScroll=remember(),stamp=++sequence.current;
  const entry={...lecture,markdown:inlineMarkdown!=null?inlineMarkdown.replace(/^\s*#{1,6}\s*从零讲[：:][^\n]*(?:\r?\n|$)/,''):lecture.markdown,images:images||lecture.images||{},parentScroll,scrollTop:0,loading:!inlineMarkdown&&!lecture.markdown};
  restore.current=0;setStack(old=>[...old,entry]);
  if(!entry.loading)return;
  try{const value=await api('lecture?id='+encodeURIComponent(lecture.id));if(stamp===sequence.current)setStack(old=>old.map((item,index)=>index===old.length-1?{...entry,...value,loading:false}:item));}
  catch(issue){if(stamp===sequence.current)setStack(old=>old.map((item,index)=>index===old.length-1?{...item,loading:false,error:issue.message}:item));}
 };
 const back=()=>{if(!stack.length)return;sequence.current++;restore.current=selected.parentScroll||0;setStack(old=>old.slice(0,-1));};
 const root=()=>{if(!stack.length)return;sequence.current++;restore.current=stack[0].parentScroll||0;setStack([]);};
 useLayoutEffect(()=>{if(body.current){body.current.scrollTop=restore.current??(selected?.scrollTop||positions.current.get(rootKey)||0);restore.current=null;}},[selected,document?.markdown,rootKey]);
 useEffect(()=>{const key=event=>{if(event.key!=='Backspace'||event.defaultPrevented||!stack.length||event.ctrlKey||event.metaKey||event.altKey||event.isComposing)return;if(event.target.closest?.('input,textarea,select,[contenteditable=true],.cm-editor')||window.document.querySelector('dialog[open],[aria-modal=true]'))return;event.preventDefault();event.stopImmediatePropagation();back();};window.addEventListener('keydown',key,true);return()=>window.removeEventListener('keydown',key,true);},[stack]);
 const toggleLearned=lecture=>{const id=lessonKey(lecture);setPrefs?.(previous=>{const keys=new Set(previous.learnedLectures||[]);keys.has(id)?keys.delete(id):keys.add(id);return {...previous,learnedLectures:[...keys]};});};
 const link=(lecture,markdown,images,key)=>learned.has(lessonKey(lecture))?null:<div className="lesson-reader-link" key={key||lessonKey(lecture)}><button type="button" onClick={()=>open(lecture,markdown,images)}><BookOpen size={15}/><span>{lecture.displayTitle||lecture.concept||lecture.heading||lecture.title||'从零讲'}</span></button><button type="button" className="icon-button" aria-label={`标记已学会 ${lecture.concept||lecture.heading||lecture.title}`} title="标记已学会" onClick={()=>toggleLearned(lecture)}><Check size={15}/></button></div>;
 const related=selected?(selected.tags||[]).map(canonicalKnowledgeName).filter((tag,index,tags)=>tag!==primaryLectureTopic(selected)&&tags.indexOf(tag)===index).map(tag=>lectures.find(item=>item.id!==selected.id&&primaryLectureTopic(item)===tag)).filter(Boolean):[];
 return <><header className="solution-reader-header">
  {stack.length>0&&<><button type="button" className="icon-button" aria-label="返回上一级" title="返回上一级 · Backspace" onClick={back}><ArrowLeft size={17}/></button><button type="button" className="icon-button" aria-label="返回题解" title="返回题解" onClick={root}><House size={17}/></button></>}
  <strong><InlineTitle>{selected?.concept||selected?.displayTitle||selected?.title||reader?.title||'题解'}</InlineTitle></strong>
  {selected?<button type="button" className="icon-button" aria-label={learned.has(lessonKey(selected))?'取消已学会':'标记已学会'} aria-pressed={learned.has(lessonKey(selected))} title={learned.has(lessonKey(selected))?'取消已学会':'标记已学会'} onClick={()=>toggleLearned(selected)}><Check size={17}/></button>:reader&&<button type="button" className="icon-button solution-version-toggle" aria-label={variant==='default'?'切换为详细题解':'切换为默认题解'} title={variant==='default'?'切换为详细题解':'切换为默认题解'} aria-pressed={variant==='detailed'} onClick={()=>{remember();restore.current=positions.current.get(`${method.id}:${variant==='default'?'detailed':'default'}`)||0;setVariants(old=>({...old,[method.id]:variant==='default'?'detailed':'default'}));}}>{variant==='default'?<BookText size={17}/>:<BookOpen size={17}/>}</button>}
  <button type="button" className="icon-button" aria-label={fullscreen?'退出题解全屏':'题解全屏'} onClick={onFullscreen}>{fullscreen?<Minimize2 size={17}/>:<Maximize2 size={17}/>}</button><button type="button" className="icon-button" aria-label="收起题解" onClick={onClose}><X size={17}/></button>
 </header><div ref={body} className="reader-content" tabIndex={0} aria-label={selected?'从零讲正文':'题解正文'} onScroll={remember}>
  {!reader?error?<p role="alert">{error}</p>:<LoaderCircle className="spin" size={22}/>:selected?.loading?<LoaderCircle className="spin" size={22}/>:selected?.error?<p role="alert">{selected.error}</p>:<>
   {related.map(item=>link(item))}
   {blocks.map((block,index)=>block.type==='lecture'?link(block.lecture||{heading:block.heading},block.markdown,document?.images,index):<Markdown key={index} text={block.markdown} images={document?.images} onCopy={copyCode}/>)}
   {!selected&&variant==='detailed'&&!method?.detailedSolution&&<p role="status">详细题解待补充</p>}
   {!selected&&(method?.lectureIds?lectures.filter(item=>method.lectureIds.includes(item.id)):reader?.lectures||[]).filter(item=>!blocks.some(block=>block.type==='lecture'&&lessonKey(block.lecture||{heading:block.heading})===lessonKey(item))).map(item=>link(item))}
   {selected&&selected.sourceProblemIds?.[0]&&onTrain&&<button type="button" className="icon-button" aria-label="练习来源题" title="练习来源题" onClick={()=>onTrain(selected.sourceProblemIds[0])}><ArrowUpRight size={17}/></button>}
  </>}
 </div>{reader?.url&&<footer><a href={reader.url} target="_blank" rel="noreferrer">原题链接 <ArrowUpRight size={12}/></a></footer>}</>;
}
