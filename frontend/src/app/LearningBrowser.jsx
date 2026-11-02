import {forwardRef,lazy,Suspense,useCallback,useEffect,useImperativeHandle,useLayoutEffect,useMemo,useRef,useState} from 'react';
import {createPortal} from 'react-dom';
import {ArrowLeft,BookOpen,BookText,Code2,Columns2,FlaskConical,LoaderCircle,NotebookTabs,Plus,Search,X} from 'lucide-react';
import {StudyPaneContext} from '@/lib/StudyPane.jsx';
import {buildLearningIndex,closeStudyTab,emptyStudyBrowser,learningSearch,MAX_STUDY_TABS,openStudyTab,restoreStudyBrowser,splitStudyTab,STUDY_LABELS,studyKey,studySnapshot,updateStudyDocument} from '@/lib/learningBrowser.js';
import {foundationLectures,lectureDestination} from '@/lib/algorithmLearning.js';
import {LAB_CATALOG} from '@/lib/labCatalog.js';
import InlineTitle from '@/components/InlineTitle.jsx';
import './LearningBrowser.css';

const Workbench=lazy(()=>import('./Workbench.jsx'));
const WikiPage=lazy(()=>import('@/pages/WikiPage.jsx'));
const TemplatesPage=lazy(()=>import('@/pages/TemplatesPage.jsx'));
const LearningPathsPage=lazy(()=>import('@/pages/LearningPathsPage.jsx'));
const LecturesPanel=lazy(()=>import('@/pages/LecturesPanel.jsx').then(module=>({default:module.LecturesPanel})));
const SolutionReader=lazy(()=>import('@/components/SolutionReader.jsx'));
const ICONS={problem:Code2,solution:BookText,wiki:NotebookTabs,template:Code2,lab:FlaskConical,lecture:BookOpen};
const loading=<div className="study-loading" role="status" aria-label="正在载入"><LoaderCircle size={23} className="spin"/></div>;
const scrollSelectors=['.wb-statement','.cm-scroller','.wb-console-content','.lab-lesson','.lectures-detail','.template-explanation','.templates-page','.reader-content'];
const checkpoint=()=>window.dispatchEvent(new Event('tb:study-checkpoint'));
function readScroll(root){return scrollSelectors.flatMap(selector=>[...root.querySelectorAll(selector)].map((node,index)=>[`${selector}|${index}`,Math.round(node.scrollTop),Math.round(node.scrollLeft)])).filter(([,top,left])=>top||left);}
function restoreScroll(root,positions){for(const [key,top,left] of positions){const [selector,index]=key.split('|'),node=root.querySelectorAll(selector)[Number(index)];if(node){node.scrollTop=top;node.scrollLeft=left;}}}

function StudySolution({tab,api,prefs,setPrefs,onTrain,onOpen,onPatch}) {
 const [reader,setReader]=useState(null),[error,setError]=useState('');
 useEffect(()=>{let live=true;setReader(null);api('solution?id='+encodeURIComponent(tab.id)).then(value=>{if(live)setReader(value);}).catch(issue=>{if(live)setError(issue.message);});return()=>{live=false;};},[api,tab.id]);
 return <div className="study-solution"><SolutionReader reader={reader} error={error} api={api} prefs={prefs} setPrefs={setPrefs} methodId={tab.methodId} onMethodChange={methodId=>onPatch({methodId})} onTrain={onTrain} embedded onOpenLecture={id=>onOpen({kind:'lecture',id})}/></div>;
}

function StudyTab({tab,visible,focused,side,patch,focus,api,rows,prefs,setPrefs,onTrain,onProgress,onNotice,onOpen,onClose,onDocumentChange,lockedProblems,categories}) {
 const root=useRef(null),visit=useRef({...tab.visit}),savedScroll=useRef(tab.scroll||[]),restoring=useRef(true),ready=useRef(false);
 const remember=useCallback((key,value)=>patch(tab.key,previous=>Object.is(previous.state[key],value)?previous:{...previous,state:{...previous.state,[key]:value}}),[tab.key,patch]);
 const scope=tab.kind==='lab'?(prefs.learningPaths?.[tab.id]?.mode==='guided'?'guided':prefs.learningPaths?.[tab.id]?.labV1?.chapter||LAB_CATALOG.find(item=>item.id===tab.id)?.first||'0'):'';
 const context=useMemo(()=>({key:tab.key,state:tab.state,scope,focused:visible&&focused,embedded:true,remember}),[tab.key,tab.state,scope,visible,focused,remember]);
 const record=useCallback(()=>{
  if(!ready.current||!root.current?.getClientRects().length||root.current.querySelector('.study-loading,.wb-loading'))return;
  const scroll=readScroll(root.current);savedScroll.current=scroll;
  patch(tab.key,previous=>JSON.stringify(previous.visit)===JSON.stringify(visit.current)&&JSON.stringify(previous.scroll)===JSON.stringify(scroll)?previous:{...previous,visit:{...visit.current},scroll});
 },[patch,tab.key]);
 useLayoutEffect(()=>{
  const node=root.current;
  const restore=()=>{if(restoring.current&&visible){restoreScroll(node,savedScroll.current);const iframe=node.querySelector('.wiki-reader');if(iframe?.contentDocument?.scrollingElement&&tab.visit?.wikiScroll)iframe.contentDocument.scrollingElement.scrollTop=tab.visit.wikiScroll;}};
  const observer=new MutationObserver(()=>{restore();requestAnimationFrame(restore);});observer.observe(node,{childList:true,subtree:true});
  node.addEventListener('load',restore,true);const frame=requestAnimationFrame(()=>{restore();ready.current=true;});
  return()=>{observer.disconnect();node.removeEventListener('load',restore,true);cancelAnimationFrame(frame);};
 },[visible]);
 useEffect(()=>{if(visible){requestAnimationFrame(()=>restoreScroll(root.current,savedScroll.current));window.dispatchEvent(new Event('resize'));}},[visible,side]);
 useEffect(()=>{if(!visible)return;const timer=setInterval(record,1200);return()=>{clearInterval(timer);record();};},[visible,record]);
 useEffect(()=>{window.addEventListener('tb:study-checkpoint',record);return()=>window.removeEventListener('tb:study-checkpoint',record);},[record]);
 const stopRestore=()=>{restoring.current=false;focus(tab.key);};
 const onNext=()=>{const ids=tab.problemIds||rows.map(row=>row.id),index=ids.indexOf(tab.id),id=ids[index+1];if(id)onTrain(id,{problemIds:ids});};
 const target=lectureDestination(tab.id);
 const locked=['problem','solution'].includes(tab.kind)&&lockedProblems.some(item=>(typeof item==='string'?item:item.id)===tab.id);
 const content=locked?<p className="study-locked" role="status">比赛进行中，请从比赛界面打开本题</p>:tab.kind==='problem'?<Workbench problemId={tab.id} preparedProblem={tab.preparedProblem} reviewTask={tab.reviewTask} shortcuts={prefs.shortcuts} api={api} onProgress={value=>onProgress(value,tab.id)} onNotice={onNotice} onExit={onClose} onNext={onNext} onSolution={(id,methodId)=>onOpen({kind:'solution',id,methodId,title:tab.title})}/>
  :tab.kind==='wiki'?<WikiPage api={api} initialArticle={tab.id} visit={visit.current} embedded onOpenArticle={item=>onOpen({kind:'wiki',...item})}/>
  :tab.kind==='template'?<TemplatesPage api={api} visit={visit.current} initialTemplate={tab.id} embedded study shortcuts={prefs.shortcuts} onTrain={onTrain} onOpenCourse={id=>onOpen({kind:'lab',id})} onOpenDetail={item=>onOpen({kind:'template',id:item.id,title:item.title,visit:item.draft?{draft:item.draft}:{}})} onDocumentChange={result=>onDocumentChange(tab.key,result,visit.current)} lockedProblems={lockedProblems}/>
  :tab.kind==='lab'?<LearningPathsPage rows={rows} prefs={prefs} setPrefs={setPrefs} onTrain={onTrain} onOpenTemplate={id=>onOpen({kind:'template',id})} lockedProblems={lockedProblems} visit={visit.current} initialPath={tab.id} study/>
  :tab.kind==='lecture'&&target?<TemplatesPage api={api} visit={visit.current} initialTemplate={target.templateId} embedded study shortcuts={prefs.shortcuts} onTrain={onTrain} onOpenCourse={id=>onOpen({kind:'lab',id})}/>
  :tab.kind==='lecture'?<LecturesPanel api={api} initialLecture={tab.id} visit={visit.current} prefs={prefs} setPrefs={setPrefs} categories={categories} onTrain={onTrain} onOpenTemplate={id=>onOpen({kind:'template',id})} onOpenLecture={id=>onOpen({kind:'lecture',id})} study onError={message=>onNotice?.(message,'error')}/>
  :<StudySolution tab={tab} api={api} prefs={prefs} setPrefs={setPrefs} onTrain={onTrain} onOpen={onOpen} onPatch={values=>patch(tab.key,previous=>({...previous,...values}))}/>;
 return <section ref={root} role="tabpanel" id={'study-panel-'+tab.key} aria-label={tab.title} className={'study-pane study-'+tab.kind} data-study-key={tab.key} data-side={side} hidden={!visible} inert={!visible?true:undefined} onPointerDownCapture={stopRestore} onKeyDownCapture={stopRestore} onFocusCapture={()=>focus(tab.key)} onScrollCapture={()=>{if(!restoring.current)record();}}>
  <StudyPaneContext.Provider value={context}><Suspense fallback={loading}>{content}</Suspense></StudyPaneContext.Provider>
 </section>;
}

const LearningBrowser=forwardRef(function LearningBrowser({api,accountId,ready,rows=[],prefs,setPrefs,onTrain,onProgress,onNotice,onExit,onActiveChange,onFlush,categories=[],lockedProblems=[]},ref){
 const [state,setState]=useState(emptyStudyBrowser),[stateOwner,setStateOwner]=useState(null),[initialized,setInitialized]=useState(false),[searching,setSearching]=useState(false),[query,setQuery]=useState(''),[catalog,setCatalog]=useState({templates:[],lectures:[],wiki:[]}),[catalogLoading,setCatalogLoading]=useState(false),[catalogErrors,setCatalogErrors]=useState([]),[resultIndex,setResultIndex]=useState(0),[limit,setLimit]=useState(80),[preview,setPreview]=useState(false);
 const [mounted,setMounted]=useState(new Set()),frame=useRef(null),input=useRef(null),results=useRef(null),drag=useRef(null),catalogOwner=useRef(null),loadedOwner=useRef(null),pendingSave=useRef(null),current=useRef(state),saveRef=useRef(setPrefs),returnFocus=useRef(null);
 current.current=state;saveRef.current=setPrefs;
 const saved=prefs.learningPaths?.browserV1;
 useEffect(()=>{
  if(!ready||loadedOwner.current===accountId)return;
  loadedOwner.current=accountId;catalogOwner.current=null;setCatalog({templates:[],lectures:[],wiki:[]});setCatalogErrors([]);setSearching(false);
  const restored=restoreStudyBrowser(saved);setState(restored);setStateOwner(accountId);setMounted(new Set([restored.right,restored.left,restored.active].filter(Boolean)));setInitialized(true);
 },[ready,accountId]);
 const persist=useCallback(value=>{
  if(loadedOwner.current!==accountId)return;
  const clean=studySnapshot(value);
  saveRef.current(previous=>JSON.stringify(previous.learningPaths?.browserV1)===JSON.stringify(clean)?previous:{...previous,learningPaths:{...previous.learningPaths,browserV1:clean}});
 },[accountId]);
 useEffect(()=>{if(initialized&&stateOwner===accountId)persist(state);},[state,initialized,stateOwner,accountId,persist]);
 useEffect(()=>{
  const save=()=>{checkpoint();persist(current.current);};
  const beforeExit=event=>{checkpoint();event.detail?.waitUntil?.(new Promise(resolve=>requestAnimationFrame(resolve)).then(()=>{persist(current.current);return onFlush?.(studySnapshot(current.current));}));};
  window.addEventListener('pagehide',save);window.addEventListener('tb-before-update',beforeExit);
  return()=>{window.removeEventListener('pagehide',save);window.removeEventListener('tb-before-update',beforeExit);};
 },[persist,onFlush]);
 const patch=useCallback((key,update)=>setState(previous=>{const old=previous.tabs.find(tab=>tab.key===key);if(!old)return previous;const tab=update(old);return tab===old?previous:{...previous,tabs:previous.tabs.map(item=>item.key===key?tab:item)};}),[]);
 const open=useCallback(source=>{
  checkpoint();
  let tab=source;if(source.kind==='lecture'){const moved=lectureDestination(source.id);if(moved)tab={...source,kind:'template',id:moved.templateId};}
  if(tab.kind==='template'&&tab.id==='new')tab={...tab,id:'new-'+crypto.randomUUID()};
  if(current.current.tabs.length>=MAX_STUDY_TABS&&!current.current.tabs.some(item=>item.key===studyKey(tab))){onNotice?.('同时最多打开 64 个学习标签页，请先关闭一个','error');return;}
  const key=studyKey(tab);setMounted(previous=>new Set([...previous,key]));setState(previous=>openStudyTab(previous,tab));setSearching(false);setPreview(false);
 },[onNotice]);
 const hide=useCallback(options=>{checkpoint();setSearching(false);setPreview(false);setState(previous=>({...previous,open:false}));if(!options?.silent)onExit?.();requestAnimationFrame(()=>returnFocus.current?.isConnected&&returnFocus.current.focus({preventScroll:true}));},[onExit]);
 const focus=useCallback(key=>setState(previous=>previous.focused===key?previous:{...previous,focused:key}),[]);
 const activate=useCallback(key=>{if(!key)return;checkpoint();setMounted(previous=>new Set([...previous,key]));setState(previous=>{const next={...previous,active:key,focused:key,open:true};if(previous.right&&key!==previous.right&&key!==previous.left){if(previous.focused===previous.right)next.right=key;else next.left=key;}return next;});setSearching(false);},[]);
 const close=useCallback(key=>{setState(previous=>closeStudyTab(previous,key));setMounted(previous=>{const next=new Set(previous);next.delete(key);return next;});},[]);
 const documentChanged=useCallback((key,result,visit)=>{
  setCatalog(previous=>({...previous,templates:result.templates||previous.templates}));
  if(result.deleted){close(key);return;}
  const document=result.template,nextKey=studyKey({kind:'template',id:document.id});
  setMounted(previous=>{const next=new Set(previous);next.delete(key);next.add(nextKey);return next;});
  setState(previous=>updateStudyDocument({...previous,tabs:previous.tabs.map(tab=>tab.key===key?{...tab,visit:{...visit}}:tab)},key,document));
 },[close]);
 const split=useCallback(key=>{setState(previous=>splitStudyTab(previous,key));setSearching(false);},[]);
 useImperativeHandle(ref,()=>({open,hide,resume:()=>setState(previous=>({...previous,open:previous.tabs.length>0})),getState:()=>current.current}),[open,hide]);
 useLayoutEffect(()=>{
  onActiveChange?.(state.open,state.tabs.length);
  if(!state.open)return;
  returnFocus.current=document.activeElement;const shell=document.querySelector('.app-shell'),wasInert=shell?.inert;
  if(shell)shell.inert=true;
  return()=>{if(shell)shell.inert=wasInert;if(!current.current.open)requestAnimationFrame(()=>returnFocus.current?.isConnected&&returnFocus.current.focus({preventScroll:true}));};
 },[state.open,onActiveChange]);
 const loadCatalog=useCallback(async()=>{
  if(catalogOwner.current===accountId)return;
  catalogOwner.current=accountId;setCatalogLoading(true);
  const response=await Promise.allSettled(['templates','lectures','wiki'].map(path=>api(path)));
  if(loadedOwner.current!==accountId)return;
  const value={},errors=[];response.forEach((answer,i)=>{const key=['templates','lectures','wiki'][i];if(answer.status==='fulfilled')value[key]=key==='wiki'?answer.value.articles||[]:Array.isArray(answer.value)?answer.value:answer.value[key]||[];else{errors.push(answer.reason.message);value[key]=[];}});
  setCatalog(value);setCatalogErrors(errors);setCatalogLoading(false);if(errors.length)catalogOwner.current=null;
 },[accountId,api]);
 const startSearch=useCallback(()=>{setSearching(true);setQuery('');setResultIndex(0);setLimit(80);void loadCatalog();requestAnimationFrame(()=>input.current?.focus());},[loadCatalog]);
 const index=useMemo(()=>buildLearningIndex({...catalog,rows,lectures:foundationLectures(catalog.lectures),labs:LAB_CATALOG}),[catalog,rows]);
 const matching=useMemo(()=>learningSearch(index,query),[index,query]);
 useEffect(()=>{setResultIndex(0);setLimit(80);if(results.current)results.current.scrollTop=0;},[query]);
 useEffect(()=>{if(!state.open)return;const key=event=>{
  if(event.defaultPrevented||event.isComposing||document.querySelector('dialog[open],.tb-select-menu,[data-popconfirm]'))return;
  if((event.ctrlKey||event.metaKey)&&!event.altKey&&event.key.toLowerCase()==='t'){event.preventDefault();startSearch();}
  else if((event.ctrlKey||event.metaKey)&&!event.altKey&&event.key.toLowerCase()==='w'){event.preventDefault();if(searching)setSearching(false);else close(current.current.focused||current.current.active);}
  else if((event.ctrlKey||event.metaKey)&&event.key==='Tab'){event.preventDefault();const value=current.current,tabs=value.tabs,at=tabs.findIndex(tab=>tab.key===value.focused);activate(tabs[(at+(event.shiftKey?-1:1)+tabs.length)%tabs.length]?.key);}
  else if(event.key==='Escape'&&!event.target.closest?.('input,textarea,select,[contenteditable=true]')){event.preventDefault();if(searching)setSearching(false);else hide();}
 };window.addEventListener('keydown',key,true);return()=>window.removeEventListener('keydown',key,true);},[state.open,searching,startSearch,close,activate,hide]);
 useEffect(()=>{
  const unknown=state.tabs.filter(tab=>tab.title===STUDY_LABELS[tab.kind]);if(!unknown.length)return;
  setState(previous=>{let changed=false;const tabs=previous.tabs.map(tab=>{const item=index.find(item=>item.key===tab.key)||(tab.kind==='problem'||tab.kind==='solution'?rows.find(row=>row.id===tab.id):tab.kind==='lab'?LAB_CATALOG.find(item=>item.id===tab.id):null);if(item?.title&&item.title!==tab.title){changed=true;return {...tab,title:item.title};}return tab;});return changed?{...previous,tabs}:previous;});
  if(state.open&&unknown.some(tab=>!['problem','solution','lab'].includes(tab.kind)))void loadCatalog();
 },[state.tabs,index,rows,state.open,loadCatalog]);
 const visibleKeys=state.right?[state.left,state.right].filter(Boolean):[state.active].filter(Boolean);
 useEffect(()=>setMounted(previous=>{const missing=visibleKeys.filter(key=>!previous.has(key));return missing.length?new Set([...previous,...missing]):previous;}),[visibleKeys.join('|')]);
 if(!state.open||stateOwner!==accountId)return null;
 const choose=item=>{if(item.kind==='problem')void onTrain(item.id);else open(item);};
 const tabKeys=state.tabs.map(tab=>tab.key),dragOver=event=>{if(!drag.current)return;event.preventDefault();event.dataTransfer.dropEffect='move';const rect=frame.current.getBoundingClientRect();setPreview(state.tabs.length>1&&event.clientX>=rect.right-Math.max(80,rect.width*.17));};
 const drop=event=>{if(!drag.current)return;event.preventDefault();const key=drag.current;drag.current=null;if(preview)split(key);setPreview(false);};
 const stopSplit=()=>setState(previous=>({...previous,left:null,right:null,active:previous.focused||previous.active}));
 const selectLeft=key=>{setMounted(previous=>new Set([...previous,key]));setState(previous=>({...previous,left:key,focused:key,active:key}));};
 return createPortal(<div ref={frame} className={'study-browser'+(state.right?' study-split':'')} aria-label="学习内容" onDragOver={dragOver} onDrop={drop} onDragLeave={event=>{if(!frame.current.contains(event.relatedTarget))setPreview(false);}}>
  <header className="study-bar" onPointerDownCapture={checkpoint}>
   <button type="button" className="study-icon study-back" aria-label="返回列表" title="返回列表 · Esc" onClick={hide}><ArrowLeft size={18}/></button>
   <div role="tablist" aria-label="学习标签页" className="study-tabs" onWheel={event=>{if(Math.abs(event.deltaY)>Math.abs(event.deltaX))event.currentTarget.scrollLeft+=event.deltaY;}}>
    {state.tabs.map(tab=>{const Icon=ICONS[tab.kind],selected=visibleKeys.includes(tab.key);return <div key={tab.key} className="study-tab-wrap" data-side={tab.key===state.right?'right':tab.key===state.left?'left':undefined}>
     <button type="button" role="tab" draggable aria-selected={selected} aria-controls={'study-panel-'+tab.key} tabIndex={tab.key===state.focused?0:-1} title={`${tab.title} · ${STUDY_LABELS[tab.kind]}`} onClick={()=>activate(tab.key)} onAuxClick={event=>{if(event.button===1){event.preventDefault();close(tab.key);}}} onKeyDown={event=>{if(!['ArrowLeft','ArrowRight','Home','End','Delete'].includes(event.key))return;event.preventDefault();if(event.key==='Delete')close(tab.key);else{const at=tabKeys.indexOf(tab.key),next=event.key==='Home'?0:event.key==='End'?tabKeys.length-1:(at+(event.key==='ArrowRight'?1:-1)+tabKeys.length)%tabKeys.length;activate(tabKeys[next]);requestAnimationFrame(()=>frame.current?.querySelectorAll('[role=tab]')[next]?.focus());}}} onDragStart={event=>{drag.current=tab.key;event.dataTransfer.effectAllowed='move';event.dataTransfer.setData('application/x-tobe-study-tab',tab.key);}} onDragEnd={()=>{drag.current=null;setPreview(false);}} onDrop={event=>{if(preview||!drag.current)return;event.preventDefault();event.stopPropagation();const key=drag.current;drag.current=null;setState(previous=>{const source=previous.tabs.find(item=>item.key===key),tabs=previous.tabs.filter(item=>item.key!==key),at=tabs.findIndex(item=>item.key===tab.key);tabs.splice(at<0?tabs.length:at,0,source);return {...previous,tabs};});}}><Icon size={15}/><span><InlineTitle>{tab.title}</InlineTitle></span></button>
     <button type="button" className="study-tab-close" aria-label={'关闭标签 '+tab.title} title="关闭标签" onClick={()=>close(tab.key)}><X size={13}/></button>
    </div>;})}
   </div>
   {searching?<div className="study-search-box"><Search size={16}/><input ref={input} aria-label="搜索学习内容" autoComplete="off" value={query} role="combobox" aria-expanded="true" aria-controls="study-search-results" aria-activedescendant={matching[resultIndex]?'study-result-'+resultIndex:undefined} onChange={event=>setQuery(event.target.value)} onKeyDown={event=>{if(event.isComposing||event.nativeEvent.isComposing)return;if(event.key==='Escape'){event.preventDefault();setSearching(false);frame.current.querySelector('[role=tab][aria-selected=true]')?.focus();}else if(['ArrowDown','ArrowUp'].includes(event.key)){event.preventDefault();const next=Math.max(0,Math.min(matching.length-1,resultIndex+(event.key==='ArrowDown'?1:-1)));setResultIndex(next);setLimit(value=>Math.max(value,next+1));requestAnimationFrame(()=>document.getElementById('study-result-'+next)?.scrollIntoView({block:'nearest'}));}else if(event.key==='Enter'&&matching[resultIndex]){event.preventDefault();choose(matching[resultIndex]);}}}/><button type="button" className="study-icon" aria-label="关闭搜索" onClick={()=>setSearching(false)}><X size={16}/></button></div>:<button type="button" className="study-icon study-add" aria-label="新建学习标签页" title="搜索学习内容 · Ctrl+T" onClick={startSearch}><Plus size={19}/></button>}
   <div className="study-bar-spacer"/>
   <button type="button" className="study-icon study-split-toggle" aria-label={state.right?'退出分屏':'左右分屏'} title={state.right?'退出分屏':'左右分屏'} disabled={state.tabs.length<2} onClick={()=>state.right?stopSplit():split(state.focused||state.active)}><Columns2 size={18}/></button>
  </header>
  <main className="study-stage" style={{'--study-left':state.ratio+'%'}}>
   {state.tabs.filter(tab=>mounted.has(tab.key)).map(tab=><StudyTab key={tab.key} tab={tab} visible={visibleKeys.includes(tab.key)} focused={state.focused===tab.key} side={tab.key===state.right?'right':state.right?'left':'full'} patch={patch} focus={focus} api={api} rows={rows} prefs={prefs} setPrefs={setPrefs} onTrain={onTrain} onProgress={onProgress} onNotice={onNotice} onOpen={open} onClose={hide} onDocumentChange={documentChanged} lockedProblems={lockedProblems} categories={categories}/>)}
   {state.right&&!state.left&&<div className="study-left-choice" aria-label="选择左侧标签页">{state.tabs.filter(tab=>tab.key!==state.right).map(tab=>{const Icon=ICONS[tab.kind];return <button type="button" key={tab.key} onClick={()=>selectLeft(tab.key)}><Icon size={18}/><span><InlineTitle>{tab.title}</InlineTitle></span><small>{STUDY_LABELS[tab.kind]}</small></button>;})}</div>}
   {state.right&&<div role="separator" aria-label="调整左右分屏宽度" aria-orientation="vertical" aria-valuemin={20} aria-valuemax={80} aria-valuenow={Math.round(state.ratio)} tabIndex={0} className="study-divider" onDoubleClick={()=>setState(previous=>({...previous,ratio:50}))} onKeyDown={event=>{if(['ArrowLeft','ArrowRight','Home','End'].includes(event.key)){event.preventDefault();setState(previous=>({...previous,ratio:event.key==='Home'?20:event.key==='End'?80:Math.max(20,Math.min(80,previous.ratio+(event.key==='ArrowRight'?2:-2)))}));}}} onPointerDown={event=>{if(event.button!==0)return;event.preventDefault();event.currentTarget.setPointerCapture(event.pointerId);event.currentTarget.dataset.resizing='true';}} onPointerMove={event=>{if(event.currentTarget.dataset.resizing!=='true')return;const rect=event.currentTarget.parentElement.getBoundingClientRect();const minimum=Math.max(20,Math.min(40,280/rect.width*100));setState(previous=>({...previous,ratio:Math.max(minimum,Math.min(100-minimum,(event.clientX-rect.left)/rect.width*100))}));}} onPointerUp={event=>{delete event.currentTarget.dataset.resizing;if(event.currentTarget.hasPointerCapture(event.pointerId))event.currentTarget.releasePointerCapture(event.pointerId);}} onPointerCancel={event=>{delete event.currentTarget.dataset.resizing;}}/>}
  </main>
  {searching&&<div ref={results} id="study-search-results" className="study-results" role="listbox" aria-label="搜索结果" onScroll={event=>{if(event.currentTarget.scrollTop+event.currentTarget.clientHeight>event.currentTarget.scrollHeight-200)setLimit(value=>value+80);}}>
   {catalogLoading&&loading}{matching.slice(0,limit).map((item,i)=>{const Icon=ICONS[item.kind];return <button type="button" role="option" aria-selected={i===resultIndex} id={'study-result-'+i} key={item.key} className="study-result" onPointerMove={()=>setResultIndex(i)} onClick={()=>choose(item)}><Icon size={18}/><span><InlineTitle>{item.title}</InlineTitle></span><small>{item.source}</small></button>;})}
   {!catalogLoading&&!matching.length&&<div className="study-empty"><Search size={24}/><span>没有匹配的内容</span></div>}{catalogErrors.length>0&&<p role="alert" className="connection-error">{catalogErrors.join('；')}<button type="button" className="study-icon" aria-label="重新读取" onClick={loadCatalog}><LoaderCircle size={16}/></button></p>}
  </div>}
  {preview&&<div className="study-drop-preview" aria-hidden="true"><Columns2 size={32}/></div>}
 </div>,document.body);
});
export default LearningBrowser;
