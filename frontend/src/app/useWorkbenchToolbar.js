import {useCallback,useEffect,useRef,useState} from 'react';

export default function useWorkbenchToolbar(section,held=false,{selector='.wb-pane-header,.wb-compact-toolbar,.wb-toolbar-reveal,.solution-reader-header',popupSelector='[aria-expanded="true"]',enabled=true}={}){
  const [pinned,setPinned]=useState(true),[shown,setShown]=useState(true);
  const pointer=useRef(null),keyboard=useRef(false),refresh=useRef(null);
  const trackPointer=useCallback(event=>{pointer.current={x:event.clientX,y:event.clientY};refresh.current?.();},[]);
  const toggle=useCallback(()=>setPinned(value=>!value),[]);
  useEffect(()=>{
    let timer;
    const cancel=()=>{clearTimeout(timer);timer=undefined;};
    const boundary=()=>section.current?.closest('.study-problem-workspace')||section.current;
    const protectedFocus=()=>keyboard.current&&boundary()?.contains(document.activeElement)&&Boolean(document.activeElement?.closest(selector));
    const popupOpen=()=>held||Boolean([...boundary()?.querySelectorAll(selector)||[]].some(node=>node.querySelector(popupSelector)));
    const update=()=>{
      if(pinned||!enabled){cancel();setShown(true);return;}
      const rect=boundary()?.getBoundingClientRect(),point=pointer.current;
      const bottom=shown?Math.max(rect?.top||0,...[...boundary()?.querySelectorAll(selector)||[]].map(node=>node.getBoundingClientRect().bottom)):(rect?.top||0)+7;
      const inside=rect&&point&&point.x>=rect.left&&point.x<=rect.right&&point.y>=rect.top&&point.y<=bottom;
      if(inside||protectedFocus()||popupOpen()){cancel();if(inside||protectedFocus())setShown(true);return;}
      if(timer!==undefined)return;
      timer=setTimeout(()=>{timer=undefined;if(!protectedFocus()&&!popupOpen())setShown(false);},150);
    };
    const move=event=>{pointer.current={x:event.clientX,y:event.clientY};update();};
    refresh.current=update;
    const press=event=>{keyboard.current=false;move(event);};
    const key=()=>{keyboard.current=true;};
    const node=section.current,forwarded=event=>move(event.detail);
    node?.addEventListener('tb:reading-pointer',forwarded);
    document.addEventListener('pointermove',move,true);document.addEventListener('pointerdown',press,true);
    document.addEventListener('keydown',key,true);document.addEventListener('focusin',update);document.addEventListener('focusout',update);
    const observer=new MutationObserver(update);if(section.current)observer.observe(section.current,{subtree:true,attributes:true,attributeFilter:['aria-expanded']});
    update();
    return()=>{refresh.current=null;node?.removeEventListener('tb:reading-pointer',forwarded);cancel();observer.disconnect();document.removeEventListener('pointermove',move,true);document.removeEventListener('pointerdown',press,true);document.removeEventListener('keydown',key,true);document.removeEventListener('focusin',update);document.removeEventListener('focusout',update);};
  },[pinned,shown,held,section,selector,popupSelector,enabled]);
  return {pinned,shown,toggle,trackPointer,reveal:()=>setShown(true)};
}
