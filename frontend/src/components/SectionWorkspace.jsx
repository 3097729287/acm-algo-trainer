import {useCallback,useEffect,useMemo,useRef,useState} from 'react';
import {Columns2} from 'lucide-react';
import {StudyPaneContext} from '@/lib/StudyPane.jsx';
import {activateStudyTab,emptyStudyBrowser,moveStudyTab,openStudyTab,resizeStudyGroups,restoreStudyBrowser,splitStudyTab,studyGroups,studySnapshot} from '@/lib/learningBrowser.js';
import './SectionWorkspace.css';

function Pane({tab,visible,focused,patch,topbarSearch=false,children}){
 const [search,setSearch]=useState(null),[location,setLocation]=useState(null);
 const remember=useCallback((key,value)=>patch(tab.key,previous=>Object.is(previous.state[key],value)?previous:{...previous,state:{...previous.state,[key]:value}}),[tab.key,patch]);
 const context=useMemo(()=>({key:tab.key,state:tab.state,scope:'section',visible,focused,embedded:true,topbarSearch,remember,pageHosts:{'tb-page-search':search,'tb-page-location':location}}),[tab.key,tab.state,visible,focused,topbarSearch,remember,search,location]);
 return <section className="section-document" hidden={!visible} role="tabpanel" id={'section-panel-'+tab.id} aria-label={tab.title}>
  <div className="section-document-tools"><div ref={setLocation}/><div ref={setSearch}/></div>
  <div className="section-document-content"><StudyPaneContext.Provider value={context}>{children}</StudyPaneContext.Provider></div>
 </section>;
}
export default function SectionWorkspace({id,entries,activeId,onActivate,render,prefs,setPrefs,owner}){
 const signature=entries.map(item=>item.id+':'+item.title).join('|'),root=useRef(null),drag=useRef(null),resize=useRef(null);
 const [drop,setDrop]=useState(null),[dragging,setDragging]=useState(false),[visited,setVisited]=useState(new Set());
 const make=()=>{let value=restoreStudyBrowser(prefs.learningPaths?.sectionWorkspaces?.[id]);const allowed=new Set(entries.map(item=>item.id));value={...value,tabs:value.tabs.filter(tab=>allowed.has(tab.id))};value=restoreStudyBrowser(value);const focused=value.focused;for(const item of entries)if(!value.tabs.some(tab=>tab.id===item.id))value=openStudyTab(value,{kind:'panel',id:item.id,title:item.title});return activateStudyTab(value,activeId?'panel:'+activeId:focused||'panel:'+entries[0]?.id);};
 const [state,setState]=useState(make),groups=studyGroups(state),activeKeys=groups.map(group=>group.active),activeSignature=activeKeys.join('|');
 useEffect(()=>{setState(previous=>{let value={...previous,tabs:previous.tabs.filter(tab=>entries.some(item=>item.id===tab.id))};value=restoreStudyBrowser(value);for(const item of entries)if(!value.tabs.some(tab=>tab.id===item.id))value=openStudyTab(value,{kind:'panel',id:item.id,title:item.title});return value;});},[signature]);
 useEffect(()=>{if(activeId)setState(previous=>activateStudyTab(previous,'panel:'+activeId));},[activeId]);
 useEffect(()=>setVisited(previous=>new Set([...previous,...activeKeys])),[activeSignature]);
 useEffect(()=>{const saved=studySnapshot(state);setPrefs(previous=>{if(owner&&window.__tbAccountUserId&&window.__tbAccountUserId!==owner)return previous;if(JSON.stringify(previous.learningPaths?.sectionWorkspaces?.[id])===JSON.stringify(saved))return previous;return {...previous,learningPaths:{...previous.learningPaths,sectionWorkspaces:{...previous.learningPaths?.sectionWorkspaces,[id]:saved}}};});},[state,id,owner]);
 const activate=key=>{setState(previous=>activateStudyTab(previous,key));onActivate?.(state.tabs.find(tab=>tab.key===key)?.id);};
 const patch=useCallback((key,update)=>setState(previous=>({...previous,tabs:previous.tabs.map(tab=>tab.key===key?update(tab):tab)})),[]);
 const clear=()=>{drag.current=null;setDragging(false);setDrop(null);};
 const hit=(event,group)=>{const box=event.currentTarget.getBoundingClientRect(),x=(event.clientX-box.left)/box.width;return {groupId:group.id,side:x<.22?'left':x>.78?'right':'center'};};
 const commit=(event,group,beforeKey)=>{event.preventDefault();const key=drag.current||event.dataTransfer.getData('application/x-tobe-section-tab');if(!key)return;const target=beforeKey?{groupId:group.id,side:'center'}:hit(event,group);setState(previous=>target.side==='center'?moveStudyTab(previous,key,target.groupId,beforeKey):splitStudyTab(previous,key,{targetGroupId:target.groupId,side:target.side}));onActivate?.(state.tabs.find(tab=>tab.key===key)?.id);clear();};
 return <div ref={root} className="section-workspace" data-section={id} data-split={groups.length>1} data-dragging={dragging} style={{gridTemplateColumns:groups.flatMap((group,index)=>[...(index?['7px']:[]),`minmax(160px,${group.weight}fr)`]).join(' ')}}
  onPointerMove={event=>{if(resize.current===null)return;const box=root.current.getBoundingClientRect();setState(previous=>resizeStudyGroups(previous,resize.current,(event.clientX-box.left)/box.width*100,box.width));}} onPointerUp={()=>{resize.current=null;}} onPointerCancel={()=>{resize.current=null;}}>
  {groups.map((group,index)=><div key={group.id} className="section-pane" data-group-id={group.id} style={{gridColumn:index*2+1}} onPointerDownCapture={()=>{if(state.focusedGroup!==group.id)activate(group.active);}} onFocusCapture={()=>{if(state.focusedGroup!==group.id)activate(group.active);}} onDragOver={event=>{if(!drag.current)return;event.preventDefault();event.dataTransfer.dropEffect='move';setDrop(hit(event,group));}} onDrop={event=>commit(event,group)}>
   <nav className="section-bookmarks" role="tablist" aria-label={{learning:'学习书签',tasks:'任务书签',rankings:'排行榜书签'}[id]||'页面书签'}>
    {group.tabs.map(key=>{const tab=state.tabs.find(tab=>tab.key===key);return <button draggable key={key} role="tab" aria-selected={group.active===key} aria-controls={'section-panel-'+tab.id} onClick={()=>activate(key)} onKeyDown={event=>{if(event.altKey&&event.key==='Enter'){event.preventDefault();setState(previous=>splitStudyTab(previous,key,{targetGroupId:group.id}));}else if(['ArrowLeft','ArrowRight'].includes(event.key)){event.preventDefault();const next=group.tabs[(group.tabs.indexOf(key)+(event.key==='ArrowRight'?1:-1)+group.tabs.length)%group.tabs.length];activate(next);}}} onDragStart={event=>{drag.current=key;setDragging(true);event.dataTransfer.effectAllowed='move';event.dataTransfer.setData('application/x-tobe-section-tab',key);}} onDragEnd={clear} onDragOver={event=>{if(drag.current){event.preventDefault();event.stopPropagation();setDrop({groupId:group.id,side:'center'});}}} onDrop={event=>{event.stopPropagation();commit(event,group,key);}}>{tab.title}</button>;})}
    <button type="button" className="section-split-button" aria-label="将当前书签向右分屏" title="向右分屏 · Alt+Enter" disabled={group.tabs.length<2} onClick={()=>setState(previous=>splitStudyTab(previous,group.active,{targetGroupId:group.id}))}><Columns2 size={15}/></button>
   </nav>
   {state.tabs.filter(tab=>group.tabs.includes(tab.key)&&(visited.has(tab.key)||group.active===tab.key)).map(tab=><Pane key={tab.key} tab={tab} visible={group.active===tab.key} focused={state.focused===tab.key} patch={patch} topbarSearch={id==='learning'||id==='rankings'}>{render(tab.id)}</Pane>)}
   {dragging&&drop?.groupId===group.id&&<div className={'section-drop-preview drop-'+drop.side} aria-hidden="true"/>}
  </div>)}
  {groups.slice(0,-1).map((group,index)=><div key={'resize-'+group.id} className="section-divider" style={{gridColumn:index*2+2}} role="separator" tabIndex="0" aria-label="调整书签分屏宽度" aria-orientation="vertical" aria-valuenow={Math.round(group.weight)} onPointerDown={event=>{if(event.button!==0)return;event.preventDefault();resize.current=index;root.current.setPointerCapture(event.pointerId);}} onDoubleClick={()=>setState(previous=>{const list=studyGroups(previous),before=list.slice(0,index).reduce((sum,item)=>sum+item.weight,0);return resizeStudyGroups(previous,index,before+(list[index].weight+list[index+1].weight)/2,1000);})} onKeyDown={event=>{if(!['ArrowLeft','ArrowRight'].includes(event.key))return;event.preventDefault();setState(previous=>{const list=studyGroups(previous),boundary=list.slice(0,index+1).reduce((sum,item)=>sum+item.weight,0);return resizeStudyGroups(previous,index,boundary+(event.key==='ArrowRight'?3:-3),1000);});}}/>)}
 </div>;
}
