import {useEffect} from 'react';
const visible=node=>node.getClientRects().length>0&&!node.closest('[inert],[hidden],[aria-hidden=true]');
const arrows={w:'ArrowUp',a:'ArrowLeft',s:'ArrowDown',d:'ArrowRight'};
const arrowCodes={ArrowUp:38,ArrowLeft:37,ArrowDown:40,ArrowRight:39};
const editing='input,textarea,select,[contenteditable]:not([contenteditable=false]),.cm-editor';
function scrollDirection(target,key,host) {
  const horizontal=key==='ArrowLeft'||key==='ArrowRight',direction=key==='ArrowUp'||key==='ArrowLeft'?-1:1;
  // Synthetic keyboard events have no browser default scrolling. Follow only
  // the focused target's ancestor chain; never pick a neighbouring reading pane.
  for(let node=target?.nodeType===1?target:host.document.activeElement;node;node=node.parentElement){
    const style=host.getComputedStyle(node),overflow=horizontal?style.overflowX:style.overflowY;
    const size=horizontal?node.scrollWidth-node.clientWidth:node.scrollHeight-node.clientHeight,position=horizontal?node.scrollLeft:node.scrollTop;
    const viewport=node===host.document.scrollingElement&&!['hidden','clip'].includes(overflow);
    if(size>0&&(/^(auto|scroll|overlay)$/.test(overflow)||viewport)&&(direction<0?position>0:position<size-1)){
      node.scrollBy({[horizontal?'left':'top']:direction*40,behavior:'instant'});return;
    }
  }
}
// Redispatch to the original target so each control keeps its own arrow semantics.
// In particular, grids/trees/menus must not fall through to page-wide pagination.
export function installDirectionKeys(host=window) {
  const forwarded=new WeakSet();
  const map=event=>{
    if(forwarded.has(event)||event.defaultPrevented||event.isComposing||event.keyCode===229||event.altKey||event.ctrlKey||event.metaKey||event.shiftKey||event.getModifierState?.('AltGraph'))return;
    const key=arrows[event.key?.toLowerCase()];if(!key)return;
    const path=event.composedPath?.()||[event.target];
    if(path.some(node=>node?.closest?.(editing)))return;
    const target=event.target;if(!target?.dispatchEvent)return;
    const mapped=new host.KeyboardEvent(event.type,{key,code:key,keyCode:arrowCodes[key],which:arrowCodes[key],bubbles:true,cancelable:true,composed:true,repeat:event.repeat,view:host});
    forwarded.add(mapped);
    event.preventDefault();event.stopImmediatePropagation();
    target.dispatchEvent(mapped);
    if(event.type==='keydown'&&!mapped.defaultPrevented&&!path.some(node=>node?.closest?.('[role=slider],[role=spinbutton],audio,video')))
      scrollDirection(target,key,host);
  };
  host.addEventListener('keydown',map,true);host.addEventListener('keyup',map,true);
  return()=>{host.removeEventListener('keydown',map,true);host.removeEventListener('keyup',map,true);};
}
export default function useNavigationKeys() {
  useEffect(()=>{
    const removeDirectionKeys=installDirectionKeys();
    const key=event=>{
      if(event.defaultPrevented||event.isComposing||event.altKey||event.ctrlKey||event.metaKey||event.shiftKey)return;
      if(event.target.closest?.('input,textarea,select,[contenteditable]:not([contenteditable=false]),.cm-editor,[role=slider],[role=grid],[role=tree],video'))return;
      if(document.querySelector('dialog[open],[aria-modal=true],[data-popconfirm],.tb-select-menu,.filter-popover'))return;
      if(event.key==='Backspace') {
        const up=[...document.querySelectorAll('[data-folder-up]')].find(visible);
        if(up){event.preventDefault();if(!up.disabled)up.click();}
        return;
      }
      const direction=event.key==='ArrowLeft'?'上一页':event.key==='ArrowRight'?'下一页':null;
      if(!direction)return;
      const containers=[...document.querySelectorAll('.library-pagination,.competition-pagination,.submission-page-controls,.activity-pagination,[data-pagination]')].filter(visible);
      if(containers.length!==1)return;
      const button=[...containers[0].querySelectorAll('button')].find(node=>(node.getAttribute('aria-label')||node.textContent).includes(direction));
      if(button){event.preventDefault();if(!button.disabled)button.click();}
    };
    window.addEventListener('keydown',key);
    return()=>{removeDirectionKeys();window.removeEventListener('keydown',key);};
  },[]);
}
