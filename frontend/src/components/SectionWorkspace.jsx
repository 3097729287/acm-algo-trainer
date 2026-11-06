import {readSectionBookmark,rememberSectionBookmark} from '@/lib/bookmarkMemory.js';
import BookmarkLabel from './BookmarkLabel.jsx';
import PageBookmarks from './PageBookmarks.jsx';
import {useCallback,useEffect,useLayoutEffect,useMemo,useRef,useState} from 'react';
import {StudyPaneContext} from '@/lib/StudyPane.jsx';
import {activateStudyTab,moveStudyTab,openStudyTab,restoreStudyBrowser,studyGroups,studySnapshot} from '@/lib/learningBrowser.js';
import './SectionWorkspace.css';

function Pane({tab,visible,focused,patch,topbarSearch=false,children}){
 const [search,setSearch]=useState(null),[location,setLocation]=useState(null),root=useRef(null),scroll=useRef(tab.state.sectionScroll||{});
 useLayoutEffect(()=>{if(!visible)return;const node=root.current;let restoring=true;const touched=()=>{restoring=false;};node.addEventListener('wheel',touched,{passive:true});node.addEventListener('pointerdown',touched,{passive:true});const restore=()=>{if(!restoring)return;const panes=[...node.querySelectorAll('*')];for(const [index,point]of Object.entries(scroll.current)){const target=panes[Number(index)];if(target){target.scrollTop=point[0];target.scrollLeft=point[1];}}};const observer=new MutationObserver(restore);observer.observe(node,{childList:true,subtree:true});restore();return()=>{observer.disconnect();node.removeEventListener('wheel',touched);node.removeEventListener('pointerdown',touched);};},[visible]);
 const saveScroll=()=>{const points={};[...root.current.querySelectorAll('*')].forEach((node,index)=>{if(node.scrollTop||node.scrollLeft)points[index]=[Math.round(node.scrollTop),Math.round(node.scrollLeft)];});scroll.current=points;patch(tab.key,previous=>({...previous,state:{...previous.state,sectionScroll:points}}));};
 const remember=useCallback((key,value)=>patch(tab.key,previous=>Object.is(previous.state[key],value)?previous:{...previous,state:{...previous.state,[key]:value}}),[tab.key,patch]);
 const context=useMemo(()=>({key:tab.key,state:tab.state,scope:'section',visible,focused,embedded:true,topbarSearch,remember,pageHosts:{'tb-page-search':search,'tb-page-location':location}}),[tab.key,tab.state,visible,focused,topbarSearch,remember,search,location]);
 return <section ref={root} onScrollCapture={saveScroll} className="section-document" hidden={!visible} role="tabpanel" id={'section-panel-'+tab.id} aria-label={tab.title}>
  <div className="section-document-tools"><div ref={setLocation}/><div ref={setSearch}/></div>
  <div className="section-document-content"><StudyPaneContext.Provider value={context}>{children}</StudyPaneContext.Provider></div>
 </section>;
}
// Top-level bookmarks keep the existing per-page state while merging old split layouts.
function oneGroup(value){
 value=restoreStudyBrowser(value);const groups=studyGroups(value),tabs=groups.flatMap(group=>group.tabs);
 return restoreStudyBrowser({...value,groups:tabs.length?[{id:groups[0].id,tabs,active:value.focused,weight:100}]:[]});
}
export default function SectionWorkspace({id,entries,activeId,onActivate,render,prefs,setPrefs,owner}){
 const signature=entries.map(item=>item.id+':'+item.title).join('|'),drag=useRef(null),[drop,setDrop]=useState(null);
 const includeEntries=value=>{for(const [index,item] of entries.entries()){if(value.tabs.some(tab=>tab.id===item.id))continue;const following=entries.slice(index+1).map(item=>'panel:'+item.id).find(key=>value.tabs.some(tab=>tab.key===key));value=openStudyTab(value,{kind:'panel',id:item.id,title:item.title});if(following)value=moveStudyTab(value,'panel:'+item.id,studyGroups(value)[0].id,following);}return value;};
 const make=(value,preferSaved=false)=>{value=oneGroup(value);value={...value,tabs:value.tabs.map(tab=>({...tab,title:entries.find(item=>item.id===tab.id)?.title||tab.title}))};const focused=value.focused;value=oneGroup({...value,tabs:value.tabs.filter(tab=>entries.some(item=>item.id===tab.id))});value=includeEntries(value);return activateStudyTab(value,preferSaved&&focused?focused:activeId?'panel:'+activeId:focused||'panel:'+entries[0]?.id);};
 const [state,setState]=useState(()=>{const cached=readSectionBookmark(owner,id);return make(cached||prefs.learningPaths?.sectionWorkspaces?.[id],Boolean(cached));}),[visited,setVisited]=useState(new Set());
 const group=studyGroups(state)[0],activeKey=group?.active;
 const previousSignature=useRef(signature);
 useLayoutEffect(()=>{if(previousSignature.current===signature)return;previousSignature.current=signature;setState(previous=>make(previous));},[signature]);
 const previousRequest=useRef(activeId);
 useEffect(()=>{if(activeId&&activeId!==previousRequest.current)setState(previous=>activateStudyTab(previous,'panel:'+activeId));previousRequest.current=activeId;},[activeId]);
 useLayoutEffect(()=>{const selected=state.tabs.find(tab=>tab.key===activeKey)?.id;if(selected)onActivate?.(selected);},[]);
 useEffect(()=>setVisited(previous=>new Set([...previous,activeKey])),[activeKey]);
 useLayoutEffect(()=>{const saved=studySnapshot(state);rememberSectionBookmark(owner,id,saved);setPrefs(previous=>{if(owner&&window.__tbAccountUserId&&window.__tbAccountUserId!==owner)return previous;if(JSON.stringify(previous.learningPaths?.sectionWorkspaces?.[id])===JSON.stringify(saved))return previous;return {...previous,learningPaths:{...previous.learningPaths,sectionWorkspaces:{...previous.learningPaths?.sectionWorkspaces,[id]:saved}}};});},[state,id,owner]);
 const activate=key=>{setState(previous=>activateStudyTab(previous,key));onActivate?.(state.tabs.find(tab=>tab.key===key)?.id);};
 const patch=useCallback((key,update)=>setState(previous=>({...previous,tabs:previous.tabs.map(tab=>tab.key===key?update(tab):tab)})),[]);
 const clear=()=>{drag.current=null;setDrop(null);};
 const commit=(event,beforeKey=null)=>{event.preventDefault();event.stopPropagation();const key=drag.current;if(!key)return;setState(previous=>moveStudyTab(previous,key,studyGroups(previous)[0].id,beforeKey));onActivate?.(state.tabs.find(tab=>tab.key===key)?.id);clear();};
 return <div className="section-workspace" data-section={id} data-split="false" style={{gridTemplateColumns:'minmax(0,1fr)'}}>
  <div className="section-pane" data-group-id={group?.id}>
   <PageBookmarks><nav className="section-bookmarks" role="tablist" aria-label={{learning:'学习书签',tasks:'任务书签',rankings:'排行榜书签',training:'组合页面 我的训练'}[id]||'页面书签'} onDragOver={event=>{if(drag.current){event.preventDefault();event.dataTransfer.dropEffect='move';}}} onDrop={event=>commit(event)}>
    {group?.tabs.map(key=>{const tab=state.tabs.find(tab=>tab.key===key),entry=entries.find(item=>item.id===tab.id),Icon=entry?.icon;return <button draggable key={key} role="tab" aria-selected={activeKey===key} aria-controls={'section-panel-'+tab.id} data-drop-before={drop===key||undefined} onClick={()=>activate(key)} onKeyDown={event=>{if(['ArrowLeft','ArrowRight'].includes(event.key)){event.preventDefault();activate(group.tabs[(group.tabs.indexOf(key)+(event.key==='ArrowRight'?1:-1)+group.tabs.length)%group.tabs.length]);}}} onDragStart={event=>{drag.current=key;event.dataTransfer.effectAllowed='move';event.dataTransfer.setData('application/x-tobe-bookmark',key);}} onDragEnd={clear} onDragOver={event=>{if(drag.current){event.preventDefault();event.stopPropagation();setDrop(key);}}} onDrop={event=>commit(event,key)}><BookmarkLabel icon={Icon}>{tab.title}</BookmarkLabel>{entry?.attention&&<i className="training-tab-dot" role="img" aria-label="有未完成训练待办"/>}</button>;})}
   </nav></PageBookmarks>
   {state.tabs.filter(tab=>visited.has(tab.key)||activeKey===tab.key).map(tab=><Pane key={tab.key} tab={tab} visible={activeKey===tab.key} focused={activeKey===tab.key} patch={patch} topbarSearch={['learning','rankings','training','tasks'].includes(id)}>{render(tab.id)}</Pane>)}
  </div>
 </div>;
}
