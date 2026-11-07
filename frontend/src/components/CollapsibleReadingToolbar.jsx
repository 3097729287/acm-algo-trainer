import {useEffect,useLayoutEffect} from 'react';
import {matchesShortcut} from '@/lib/shortcuts.js';
import useWorkbenchToolbar from '@/app/useWorkbenchToolbar.js';
import './CollapsibleReadingToolbar.css';

const selector='.wiki-reader-toolbar,.lectures-detail-bar,.lecture-directory-toolbar,.template-heading,.lab-course-header,.solution-reader-header,.study-single-controls,.study-task-previous,.study-task-next,.reading-toolbar-reveal';

export default function CollapsibleReadingToolbar({root,enabled=true,active=true,shortcuts={}}){
 const toolbar=useWorkbenchToolbar(root,false,{selector,enabled,popupSelector:'[aria-haspopup][aria-expanded="true"]'});
 useLayoutEffect(()=>{
  const node=root.current;if(!node)return;
  node.toggleAttribute('data-reading-toolbar-hidden',enabled&&!toolbar.pinned&&!toolbar.shown);
  return()=>node.removeAttribute('data-reading-toolbar-hidden');
 },[root,enabled,toolbar.pinned,toolbar.shown]);
 useEffect(()=>{
  if(!enabled)return;const frames=new Map();
  const key=event=>{
   if(event.target.ownerDocument!==document&&matchesShortcut(event,'study-toolbar-lock',shortcuts)){
    const forwarded=new KeyboardEvent('keydown',{key:event.key,code:event.code,altKey:event.altKey,shiftKey:event.shiftKey,ctrlKey:event.ctrlKey,metaKey:event.metaKey,bubbles:true,cancelable:true});
    root.current?.dispatchEvent(forwarded);if(forwarded.defaultPrevented){event.preventDefault();event.stopPropagation();}return;
   }
   if(event.defaultPrevented||event.isComposing||!matchesShortcut(event,'toolbar-lock',shortcuts)||document.querySelector('dialog[open],.tb-select-menu,[data-popconfirm]'))return;
   const targetRoot=event.target.closest?.('.reader-full,.lecture-reading-full,.study-pane');
   if(targetRoot&&targetRoot!==root.current&&!root.current?.contains(targetRoot))return;
   if(!root.current?.contains(event.target)&&!active)return;
   event.preventDefault();event.stopPropagation();toolbar.toggle();
  };
  const sync=()=>{
   for(const iframe of root.current?.querySelectorAll('iframe')||[]){
    if(frames.has(iframe))continue;let inner;
    const move=event=>{const bounds=iframe.getBoundingClientRect();root.current?.dispatchEvent(new CustomEvent('tb:reading-pointer',{bubbles:true,detail:{clientX:bounds.left+event.clientX,clientY:bounds.top+event.clientY}}));};
    const detach=()=>{inner?.removeEventListener('keydown',key,true);inner?.removeEventListener('pointermove',move,true);inner?.removeEventListener('pointerdown',move,true);};
    const load=()=>{detach();try{inner=iframe.contentDocument;}catch{inner=null;}inner?.addEventListener('keydown',key,true);inner?.addEventListener('pointermove',move,true);inner?.addEventListener('pointerdown',move,true);};
    iframe.addEventListener('load',load);load();frames.set(iframe,()=>{detach();iframe.removeEventListener('load',load);});
   }
   for(const [iframe,remove]of frames)if(!iframe.isConnected){remove();frames.delete(iframe);}
  };
  const observer=new MutationObserver(sync);if(root.current)observer.observe(root.current,{childList:true,subtree:true});sync();
  window.addEventListener('keydown',key,true);
  return()=>{observer.disconnect();window.removeEventListener('keydown',key,true);for(const remove of frames.values())remove();};
 },[root,enabled,active,shortcuts,toolbar.toggle,toolbar.trackPointer]);
 return enabled&&!toolbar.pinned&&!toolbar.shown?<button type="button" className="reading-toolbar-reveal" aria-label="显示阅读工具栏" onPointerEnter={toolbar.reveal} onFocus={toolbar.reveal} onClick={toolbar.reveal}/>:null;
}
