import {forwardRef,lazy,Suspense,useCallback,useEffect,useImperativeHandle,useLayoutEffect,useMemo,useRef,useState} from 'react';
import {createPortal} from 'react-dom';
import {ArrowLeft,BookOpen,BookText,ChevronRight,Code2,FlaskConical,FolderClosed,House,LoaderCircle,NotebookTabs,Plus,Search,X} from 'lucide-react';
import {StudyPaneContext} from '@/lib/StudyPane.jsx';
import {activateStudyTab,buildLearningIndex,closeStudyTab,emptyStudyBrowser,learningDirectory,MAX_STUDY_TABS,moveStudyTab,openStudyTab,resizeStudyGroups,restoreStudyBrowser,splitStudyTab,STUDY_LABELS,studyGroups,studyKey,studySnapshot,updateStudyDocument} from '@/lib/learningBrowser.js';
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

function StudyTab({tab,visible,focused,side,groupId,column,compact,onAdd,patch,focus,api,rows,prefs,setPrefs,onTrain,onProgress,onNotice,onOpen,onClose,onDocumentChange,lockedProblems,categories}) {
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
 useEffect(()=>{if(visible){requestAnimationFrame(()=>restoreScroll(root.current,savedScroll.current));window.dispatchEvent(new Event('resize'));}},[visible,side,groupId,column]);
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
 return <section ref={root} role="tabpanel" id={'study-panel-'+tab.key} aria-label={tab.title} className={'study-pane study-'+tab.kind} data-study-key={tab.key} data-side={side} data-group-id={groupId} data-group-content={groupId} style={{gridColumn:column}} hidden={!visible} inert={!visible?true:undefined} onPointerDownCapture={stopRestore} onKeyDownCapture={stopRestore} onFocusCapture={()=>focus(tab.key)} onScrollCapture={()=>{if(!restoring.current)record();}}>
  {compact&&<div className="study-single-controls"><button type="button" className="study-icon study-back" aria-label="返回列表" title="返回列表 · Esc" onClick={onClose}><ArrowLeft size={18}/></button><button type="button" className="study-icon study-add" aria-label="新建学习标签页" title="新建学习标签页 · Ctrl+T" onClick={()=>onAdd(groupId)}><Plus size={18}/></button></div>}
  <StudyPaneContext.Provider value={context}><Suspense fallback={loading}>{content}</Suspense></StudyPaneContext.Provider>
 </section>;
}

const LearningBrowser=forwardRef(function LearningBrowser({api,accountId,ready,rows=[],prefs,setPrefs,onTrain,onProgress,onNotice,onExit,onActiveChange,onFlush,categories=[],lockedProblems=[]},ref){
 const [state,setState]=useState(emptyStudyBrowser),[stateOwner,setStateOwner]=useState(null),[initialized,setInitialized]=useState(false);
 const [searching,setSearching]=useState(null),[query,setQuery]=useState(''),[directory,setDirectory]=useState([]),[resultIndex,setResultIndex]=useState(0),[limit,setLimit]=useState(80);
 const [catalog,setCatalog]=useState({templates:[],lectures:[],wiki:[]}),[catalogLoading,setCatalogLoading]=useState(false),[catalogErrors,setCatalogErrors]=useState([]);
 const [mounted,setMounted]=useState(new Set()),[preview,setPreview]=useState(null),[dragging,setDragging]=useState(false),[resizing,setResizing]=useState(null);
 const frame=useRef(null),input=useRef(null),results=useRef(null),drag=useRef(null),resizeSession=useRef(null),catalogOwner=useRef(null),loadedOwner=useRef(null),current=useRef(state),saveRef=useRef(setPrefs),returnFocus=useRef(null);
 current.current=state;saveRef.current=setPrefs;
 const saved=prefs.learningPaths?.browserV1;
 useEffect(()=>{
  if(!ready||loadedOwner.current===accountId)return;
  loadedOwner.current=accountId;catalogOwner.current=null;setCatalog({templates:[],lectures:[],wiki:[]});setCatalogErrors([]);setSearching(null);setDirectory([]);
  const restored=restoreStudyBrowser(saved);setState(restored);setStateOwner(accountId);setMounted(new Set(studyGroups(restored).map(group=>group.active)));setInitialized(true);
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
 const clearDrag=()=>{drag.current=null;setDragging(false);setPreview(null);};
 const open=useCallback(source=>{
  checkpoint();let tab=source;
  if(source.kind==='lecture'){const moved=lectureDestination(source.id);if(moved)tab={...source,kind:'template',id:moved.templateId};}
  if(tab.kind==='template'&&tab.id==='new')tab={...tab,id:'new-'+crypto.randomUUID()};
  if(current.current.tabs.length>=MAX_STUDY_TABS&&!current.current.tabs.some(item=>item.key===studyKey(tab))){onNotice?.('同时最多打开 64 个学习标签页，请先关闭一个','error');return;}
  const key=studyKey(tab);setMounted(previous=>new Set([...previous,key]));setState(previous=>openStudyTab(previous,tab));setSearching(null);setPreview(null);
 },[onNotice]);
 const hide=useCallback(options=>{
  checkpoint();setSearching(null);setPreview(null);setState(previous=>({...previous,open:false,chrome:previous.tabs.length>1&&previous.chrome}));
  if(!options?.silent)onExit?.();requestAnimationFrame(()=>returnFocus.current?.isConnected&&returnFocus.current.focus({preventScroll:true}));
 },[onExit]);
 const focus=useCallback(key=>setState(previous=>previous.focused===key?previous:activateStudyTab(previous,key)),[]);
 const activate=useCallback(key=>{if(!key)return;checkpoint();setMounted(previous=>new Set([...previous,key]));setState(previous=>activateStudyTab(previous,key));setSearching(null);},[]);
 const close=useCallback(key=>{checkpoint();setState(previous=>closeStudyTab(previous,key));setMounted(previous=>{const next=new Set(previous);next.delete(key);return next;});},[]);
 const documentChanged=useCallback((key,result,visit)=>{
  setCatalog(previous=>({...previous,templates:result.templates||previous.templates}));if(result.deleted){close(key);return;}
  const document=result.template,nextKey=studyKey({kind:'template',id:document.id});
  setMounted(previous=>{const next=new Set(previous);next.delete(key);next.add(nextKey);return next;});
  setState(previous=>updateStudyDocument({...previous,tabs:previous.tabs.map(tab=>tab.key===key?{...tab,visit:{...visit}}:tab)},key,document));
 },[close]);
 useImperativeHandle(ref,()=>({open,hide,resume:()=>setState(previous=>({...previous,open:previous.tabs.length>0})),getState:()=>current.current}),[open,hide]);
 useLayoutEffect(()=>{
  onActiveChange?.(state.open,state.tabs.length);if(!state.open)return;
  returnFocus.current=document.activeElement;const shell=document.querySelector('.app-shell'),wasInert=shell?.inert;if(shell)shell.inert=true;
  return()=>{if(shell)shell.inert=wasInert;if(!current.current.open)requestAnimationFrame(()=>returnFocus.current?.isConnected&&returnFocus.current.focus({preventScroll:true}));};
 },[state.open,onActiveChange]);
 const loadCatalog=useCallback(async()=>{
  if(catalogOwner.current===accountId)return;catalogOwner.current=accountId;setCatalogLoading(true);
  const response=await Promise.allSettled(['templates','lectures','wiki'].map(path=>api(path)));if(loadedOwner.current!==accountId)return;
  const value={},errors=[];response.forEach((answer,i)=>{const key=['templates','lectures','wiki'][i];if(answer.status==='fulfilled')value[key]=key==='wiki'?answer.value.articles||[]:Array.isArray(answer.value)?answer.value:answer.value[key]||[];else{errors.push(answer.reason.message);value[key]=[];}});
  setCatalog(value);setCatalogErrors(errors);setCatalogLoading(false);if(errors.length)catalogOwner.current=null;
 },[accountId,api]);
 const startSearch=useCallback(groupId=>{
  checkpoint();const groups=studyGroups(current.current),group=groups.find(item=>item.id===groupId)||groups.find(item=>item.id===current.current.focusedGroup)||groups[0];if(!group)return;
  setState(previous=>({...activateStudyTab(previous,group.active),chrome:true}));setSearching(group.id);setQuery('');setDirectory([]);setResultIndex(0);setLimit(80);void loadCatalog();requestAnimationFrame(()=>input.current?.focus());
 },[loadCatalog]);
 const index=useMemo(()=>buildLearningIndex({...catalog,rows,lectures:foundationLectures(catalog.lectures),labs:LAB_CATALOG}),[catalog,rows]);
 const listing=useMemo(()=>learningDirectory(index,query,directory),[index,query,directory]),matching=listing.entries;
 const goDirectory=path=>{setDirectory(path);setQuery('');setResultIndex(0);setLimit(80);requestAnimationFrame(()=>input.current?.focus());};
 useEffect(()=>{setResultIndex(0);setLimit(80);if(results.current)results.current.scrollTop=0;},[query,directory.join('/')]);
 useEffect(()=>{if(resultIndex>=limit)setLimit(resultIndex+40);requestAnimationFrame(()=>results.current?.querySelector('#study-result-'+resultIndex)?.scrollIntoView({block:'nearest'}));},[resultIndex]);
 useEffect(()=>{if(searching&&!studyGroups(state).some(group=>group.id===searching))setSearching(null);},[state.groups,searching]);
 useEffect(()=>{if(!state.open)return;const key=event=>{
  if(event.defaultPrevented||event.isComposing||document.querySelector('dialog[open],.tb-select-menu,[data-popconfirm]'))return;
  const control=event.ctrlKey||event.metaKey;
  if(control&&!event.altKey&&event.key.toLowerCase()==='t'){event.preventDefault();startSearch();}
  else if(control&&!event.altKey&&event.key.toLowerCase()==='w'){event.preventDefault();if(searching)setSearching(null);else close(current.current.focused||current.current.active);}
  else if(control&&event.key==='Tab'){
   event.preventDefault();const value=current.current,group=studyGroups(value).find(group=>group.id===value.focusedGroup);if(!group)return;
   const at=group.tabs.indexOf(value.focused);activate(group.tabs[(at+(event.shiftKey?-1:1)+group.tabs.length)%group.tabs.length]);
  }else if(control&&(event.key==='\\'||event.altKey&&['ArrowLeft','ArrowRight'].includes(event.key))){
   event.preventDefault();checkpoint();setSearching(null);setState(previous=>{
    const groups=studyGroups(previous),at=groups.findIndex(group=>group.id===previous.focusedGroup),direction=event.key==='ArrowLeft'?-1:1,target=groups[at+direction];
    return event.altKey&&target?moveStudyTab(previous,previous.focused,target.id):splitStudyTab(previous,previous.focused,{targetGroupId:groups[at]?.id,side:direction<0?'left':'right'});
   });
  }else if(event.key==='Escape'&&!event.target.closest?.('input,textarea,select,[contenteditable=true]')){event.preventDefault();if(searching)setSearching(null);else hide();}
 };window.addEventListener('keydown',key,true);return()=>window.removeEventListener('keydown',key,true);},[state.open,searching,startSearch,close,activate,hide]);
 useEffect(()=>{
  const unknown=state.tabs.filter(tab=>tab.title===STUDY_LABELS[tab.kind]);if(!unknown.length)return;
  setState(previous=>{let changed=false;const tabs=previous.tabs.map(tab=>{const item=index.find(item=>item.key===tab.key)||(tab.kind==='problem'||tab.kind==='solution'?rows.find(row=>row.id===tab.id):tab.kind==='lab'?LAB_CATALOG.find(item=>item.id===tab.id):null);if(item?.title&&item.title!==tab.title){changed=true;return {...tab,title:item.title};}return tab;});return changed?{...previous,tabs}:previous;});
  if(state.open&&unknown.some(tab=>!['problem','solution','lab'].includes(tab.kind)))void loadCatalog();
 },[state.tabs,index,rows,state.open,loadCatalog]);
 const groups=studyGroups(state),visibleKeys=groups.map(group=>group.active);
 useEffect(()=>setMounted(previous=>{const missing=visibleKeys.filter(key=>!previous.has(key));return missing.length?new Set([...previous,...missing]):previous;}),[visibleKeys.join('|')]);
 if(!state.open||stateOwner!==accountId)return null;
 const compact=groups.length===1&&!state.chrome&&!searching;
 const choose=item=>{
  if(!item)return;if(item.type==='folder'){setDirectory(item.path);return;}
  const group=groups.find(group=>group.id===searching);if(group)setState(previous=>activateStudyTab(previous,group.active));
  if(item.kind==='problem')void onTrain(item.id);else open(item);
 };
 const dropLocation=event=>{
  const key=drag.current;if(!key)return null;
  const frameRect=frame.current.getBoundingClientRect(),owner=event.target.closest?.('[data-group-id]'),group=groups.find(group=>group.id===owner?.dataset.groupId)||groups.find(group=>group.id===state.focusedGroup)||groups[0];
  const header=event.target.closest?.('.study-group-header'),content=frame.current.querySelector(`[data-group-content="${group.id}"]:not([hidden])`),bounds=content?.getBoundingClientRect();if(!bounds)return null;
  const wrap=event.target.closest?.('.study-tab-wrap');
  if(header&&wrap){
   const rect=wrap.getBoundingClientRect(),after=event.clientX>=rect.left+rect.width/2,at=group.tabs.indexOf(wrap.dataset.tabKey),before=after?group.tabs[at+1]||null:wrap.dataset.tabKey;
   return {type:'reorder',groupId:group.id,beforeKey:before,x:(after?rect.right:rect.left)-frameRect.left,y:rect.top-frameRect.top,width:2,height:rect.height};
  }
  const edge=Math.min(140,Math.max(48,bounds.width*.22));
  const side=event.clientX<bounds.left+edge?'left':event.clientX>bounds.right-edge?'right':null;
  if(side&&state.tabs.length>1&&(!header||groups.length===1))return {type:'split',groupId:group.id,side,x:bounds.left-frameRect.left+(side==='right'?bounds.width/2:0),y:bounds.top-frameRect.top,width:bounds.width/2,height:bounds.height};
  return {type:header?'reorder':'move',groupId:group.id,beforeKey:null,x:bounds.left-frameRect.left,y:bounds.top-frameRect.top,width:bounds.width,height:bounds.height};
 };
 const dragOver=event=>{if(!drag.current)return;event.preventDefault();event.dataTransfer.dropEffect='move';const next=dropLocation(event);setPreview(previous=>JSON.stringify(previous)===JSON.stringify(next)?previous:next);};
 const drop=event=>{
  if(!drag.current)return;event.preventDefault();event.stopPropagation();checkpoint();const key=drag.current,target=dropLocation(event);clearDrag();setSearching(null);if(!target)return;
  setState(previous=>target.type==='split'?splitStudyTab(previous,key,{targetGroupId:target.groupId,side:target.side}):target.type==='move'&&studyGroups(previous).find(group=>group.id===target.groupId)?.tabs.includes(key)?activateStudyTab(previous,key):moveStudyTab(previous,key,target.groupId,target.beforeKey));
 };
 const stopResize=event=>{resizeSession.current=null;setResizing(null);if(event.currentTarget.hasPointerCapture(event.pointerId))event.currentTarget.releasePointerCapture(event.pointerId);};
 const searchKeys=event=>{
  if(['ArrowDown','ArrowUp'].includes(event.key)){event.preventDefault();if(matching.length)setResultIndex(value=>(value+(event.key==='ArrowDown'?1:-1)+matching.length)%matching.length);}
  else if(event.key==='Enter'){event.preventDefault();choose(matching[resultIndex]);}
  else if(event.key==='Escape'){event.preventDefault();event.stopPropagation();setSearching(null);}
  else if((event.key==='Backspace'&&!query||event.altKey&&event.key==='ArrowLeft')&&listing.path.length){event.preventDefault();goDirectory(listing.path.slice(0,-1));}
 };
 return createPortal(<div ref={frame} className={'study-browser'+(groups.length>1?' study-split':'')+(compact?' study-compact':'')} aria-label="学习内容" data-dragging={dragging||undefined} data-resizing={resizing!==null||undefined} onDragOver={dragOver} onDropCapture={drop} onDragLeave={event=>{if(!frame.current.contains(event.relatedTarget))setPreview(null);}}>
  <main className="study-stage" style={{gridTemplateColumns:groups.map(group=>`minmax(0,${group.weight}fr)`).join(' 1px ')}}>
   {!compact&&groups.map((group,groupIndex)=><header key={group.id} className="study-bar study-group-header" data-group-id={group.id} data-focused={group.id===state.focusedGroup} style={{gridColumn:groupIndex*2+1}} onPointerDownCapture={()=>{checkpoint();focus(group.active);}}>
    {groupIndex===0&&<button type="button" className="study-icon study-back" aria-label="返回列表" title="返回列表 · Esc" onClick={hide}><ArrowLeft size={18}/></button>}
    <div role="tablist" aria-label={`第 ${groupIndex+1} 组学习标签页`} className="study-tabs" onWheel={event=>{if(Math.abs(event.deltaY)>Math.abs(event.deltaX))event.currentTarget.scrollLeft+=event.deltaY;}}>
     {group.tabs.map(key=>{const tab=state.tabs.find(tab=>tab.key===key),Icon=ICONS[tab.kind];return <div key={key} className="study-tab-wrap" data-tab-key={key}>
      <button type="button" role="tab" draggable aria-selected={key===group.active} aria-controls={'study-panel-'+key} tabIndex={key===group.active?0:-1} title={`${tab.title} · ${STUDY_LABELS[tab.kind]}`} onClick={()=>activate(key)} onAuxClick={event=>{if(event.button===1){event.preventDefault();close(key);}}} onKeyDown={event=>{
       if(!['ArrowLeft','ArrowRight','Home','End','Delete'].includes(event.key))return;event.preventDefault();if(event.key==='Delete'){close(key);return;}
       const at=group.tabs.indexOf(key),next=group.tabs[event.key==='Home'?0:event.key==='End'?group.tabs.length-1:(at+(event.key==='ArrowRight'?1:-1)+group.tabs.length)%group.tabs.length];activate(next);requestAnimationFrame(()=>frame.current?.querySelector(`[data-tab-key="${CSS.escape(next)}"] [role="tab"]`)?.focus());
      }} onDragStart={event=>{checkpoint();drag.current=key;setDragging(true);event.dataTransfer.effectAllowed='move';event.dataTransfer.setData('application/x-tobe-study-tab',key);}} onDragEnd={clearDrag}>
       <Icon size={15}/><span><InlineTitle>{tab.title}</InlineTitle></span>
      </button><button type="button" className="study-tab-close" aria-label={'关闭 '+tab.title} title="关闭标签页 · Ctrl+W" onClick={()=>close(key)}><X size={13}/></button>
     </div>;})}
    </div>
    {searching===group.id?<label className="study-search-box"><Search size={16}/><input ref={input} type="search" role="combobox" aria-label="搜索学习内容" aria-expanded="true" aria-controls="study-search-results" aria-activedescendant={matching[resultIndex]?'study-result-'+resultIndex:undefined} autoComplete="off" value={query} onChange={event=>setQuery(event.target.value)} onKeyDown={searchKeys}/><button type="button" className="study-icon" aria-label="关闭搜索" onClick={()=>setSearching(null)}><X size={15}/></button></label>:<button type="button" className="study-icon study-add" aria-label="新建学习标签页" title="新建学习标签页 · Ctrl+T" onClick={()=>startSearch(group.id)}><Plus size={18}/></button>}
    <span className="study-bar-spacer"/>
   </header>)}
   {state.tabs.filter(tab=>mounted.has(tab.key)).map(tab=>{const at=groups.findIndex(group=>group.tabs.includes(tab.key)),group=groups[at];if(!group)return null;return <StudyTab key={tab.key} tab={tab} groupId={group.id} column={at*2+1} compact={compact} onAdd={startSearch} visible={group.active===tab.key&&searching!==group.id} focused={state.focused===tab.key} side={at===0?'left':'right'} patch={patch} focus={focus} api={api} rows={rows} prefs={prefs} setPrefs={setPrefs} onTrain={onTrain} onProgress={onProgress} onNotice={onNotice} onOpen={open} onClose={hide} onDocumentChange={documentChanged} lockedProblems={lockedProblems} categories={categories}/>;})}
   {groups.slice(0,-1).map((group,index)=><div key={group.id+'-divider'} role="separator" tabIndex={0} aria-label={groups.length===2?'调整左右分屏宽度':`调整第 ${index+1} 和第 ${index+2} 分屏宽度`} aria-orientation="vertical" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(group.weight/(group.weight+groups[index+1].weight)*100)} className="study-divider" style={{gridColumn:index*2+2}} data-resizing={resizing===index||undefined} onDoubleClick={()=>setState(previous=>{const list=studyGroups(previous),start=list.slice(0,index).reduce((sum,item)=>sum+item.weight,0);return resizeStudyGroups(previous,index,start+(list[index].weight+list[index+1].weight)/2,1000);})} onKeyDown={event=>{
    if(!['ArrowLeft','ArrowRight','Home'].includes(event.key))return;event.preventDefault();setState(previous=>{const list=studyGroups(previous),start=list.slice(0,index).reduce((sum,item)=>sum+item.weight,0),position=event.key==='Home'?start+(list[index].weight+list[index+1].weight)/2:start+list[index].weight+(event.key==='ArrowRight'?2:-2);return resizeStudyGroups(previous,index,position,1000,0);});
   }} onPointerDown={event=>{if(event.button!==0)return;event.preventDefault();event.currentTarget.focus();event.currentTarget.setPointerCapture(event.pointerId);resizeSession.current={index,snapped:Math.abs(group.weight-groups[index+1].weight)<.01};setResizing(index);}} onPointerMove={event=>{
    const session=resizeSession.current;if(!session||session.index!==index)return;const rect=event.currentTarget.parentElement.getBoundingClientRect(),width=rect.width-groups.length+1,position=(event.clientX-rect.left-index)/width*100;
    setState(previous=>{const next=resizeStudyGroups(previous,index,position,width,session.snapped?52:32);session.snapped=Math.abs(next.groups[index].weight-next.groups[index+1].weight)<.01;return next;});
   }} onPointerUp={stopResize} onPointerCancel={stopResize} onLostPointerCapture={()=>{resizeSession.current=null;setResizing(null);}}/>)}
   {searching&&<section ref={results} id="study-search-results" className="study-results study-directory" data-group-id={searching} data-group-content={searching} style={{gridColumn:Math.max(0,groups.findIndex(group=>group.id===searching))*2+1}} aria-label="学习目录" onScroll={event=>{if(event.currentTarget.scrollTop+event.currentTarget.clientHeight>event.currentTarget.scrollHeight-200)setLimit(value=>value+80);}}>
    <nav className="study-breadcrumbs" aria-label="目录位置"><button type="button" className="study-icon" aria-label="返回上一级目录" disabled={!listing.path.length} onClick={()=>goDirectory(listing.path.slice(0,-1))}><ArrowLeft size={16}/></button><button type="button" aria-label="全部学习目录" onClick={()=>goDirectory([])}><House size={15}/></button>{listing.path.map((part,at)=><span key={at}><ChevronRight size={13}/><button type="button" onClick={()=>goDirectory(listing.path.slice(0,at+1))}>{at===0?STUDY_LABELS[part]:part}</button></span>)}</nav>
    <div role="listbox" aria-label="搜索结果">{catalogLoading&&loading}{matching.slice(0,limit).map((item,i)=>{const Icon=item.type==='folder'?FolderClosed:ICONS[item.kind];return <button type="button" role="option" aria-selected={i===resultIndex} id={'study-result-'+i} key={item.key} className={'study-result'+(item.type==='folder'?' study-folder':'')} data-kind={item.kind} onPointerMove={()=>setResultIndex(i)} onClick={()=>choose(item)}><Icon size={18}/><span><InlineTitle>{item.title}</InlineTitle></span><small>{item.type==='folder'?item.count:item.source}</small>{item.type==='folder'&&<ChevronRight size={15}/>}</button>;})}</div>
    {!catalogLoading&&!matching.length&&<div className="study-empty"><Search size={24}/><span>没有匹配的内容</span></div>}{catalogErrors.length>0&&<p role="alert" className="connection-error">{catalogErrors.join('；')}<button type="button" className="study-icon" aria-label="重新读取" onClick={loadCatalog}><LoaderCircle size={16}/></button></p>}
   </section>}
  </main>
  {preview&&<div className="study-drop-preview" data-placement={preview.side||preview.type} data-drop={preview.type} aria-hidden="true" style={{left:preview.x,top:preview.y,width:preview.width,height:preview.height}}/>}
 </div>,document.body);
});
export default LearningBrowser;
