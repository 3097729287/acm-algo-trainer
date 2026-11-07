import {useLayoutEffect,useRef} from 'react';
import {createPortal} from 'react-dom';
import useReadingZoom from '@/lib/readingZoom.js';
import CollapsibleReadingToolbar from './CollapsibleReadingToolbar.jsx';

// Keep one portal target while moving it out of workspace stacking/containment.
// Fullscreen therefore preserves the reading stack and scroll position.
export default function ReaderFrame({fullscreen,width,children,onKeyDown,identity,shortcuts}){
 useReadingZoom();
 const marker=useRef(null),frame=useRef(null);
 const keyHandler=useRef(onKeyDown);keyHandler.current=onKeyDown;
 if(!frame.current)frame.current=document.createElement('aside');
 useLayoutEffect(()=>{
  const node=frame.current,parent=marker.current.parentNode;
  node.className='reader-panel'+(fullscreen?' reader-full':'');
  node.dataset.problemId=identity||'reader';
  node.setAttribute('aria-label','题解阅读');node.tabIndex=0;
  node.style.width=fullscreen?'':typeof width==='number'?width+'px':width||'';
  if(fullscreen){node.setAttribute('role','dialog');node.setAttribute('aria-modal','true');document.body.appendChild(node);}
  else{node.removeAttribute('role');node.removeAttribute('aria-modal');parent.insertBefore(node,marker.current);}
  const shell=document.querySelector('.app-shell'),wasInert=shell?.inert;
  if(fullscreen&&shell)shell.inert=true;
  if(fullscreen)node.focus({preventScroll:true});
  return()=>{if(fullscreen&&shell)shell.inert=wasInert;};
 },[fullscreen,width,identity]);
 useLayoutEffect(()=>{const node=frame.current,key=event=>keyHandler.current?.(event);node.addEventListener('keydown',key);return()=>node.removeEventListener('keydown',key);},[]);
 useLayoutEffect(()=>()=>frame.current.remove(),[]);
 return <><span ref={marker} hidden aria-hidden="true"/>{createPortal(<><CollapsibleReadingToolbar root={frame} enabled={fullscreen} shortcuts={shortcuts}/>{children}</>,frame.current)}</>;
}
