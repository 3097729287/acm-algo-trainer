import {useCallback,useEffect,useRef,useState} from 'react';

export default function useWorkbenchToolbar(section,held=false){
  const [pinned,setPinned]=useState(true),[shown,setShown]=useState(true);
  const pointer=useRef(null),keyboard=useRef(false);
  const toggle=useCallback(()=>setPinned(value=>!value),[]);
  useEffect(()=>{
    let timer;
    const cancel=()=>{clearTimeout(timer);timer=undefined;};
    const protectedFocus=()=>keyboard.current&&section.current?.contains(document.activeElement)&&Boolean(document.activeElement?.closest('.wb-pane-header,.wb-compact-toolbar,.wb-toolbar-reveal'));
    const popupOpen=()=>held||Boolean(section.current?.querySelector('.wb-pane-header [aria-expanded="true"],.wb-compact-toolbar [aria-expanded="true"]'));
    const update=()=>{
      if(pinned){cancel();setShown(true);return;}
      const rect=section.current?.getBoundingClientRect(),point=pointer.current;
      const inside=rect&&point&&point.x>=rect.left&&point.x<=rect.right&&point.y>=rect.top&&point.y<=rect.top+(shown?54:7);
      if(inside||protectedFocus()||popupOpen()){cancel();if(inside||protectedFocus())setShown(true);return;}
      if(timer!==undefined)return;
      timer=setTimeout(()=>{timer=undefined;if(!protectedFocus()&&!popupOpen())setShown(false);},150);
    };
    const move=event=>{pointer.current={x:event.clientX,y:event.clientY};update();};
    const press=event=>{keyboard.current=false;move(event);};
    const key=()=>{keyboard.current=true;};
    document.addEventListener('pointermove',move,true);document.addEventListener('pointerdown',press,true);
    document.addEventListener('keydown',key,true);document.addEventListener('focusin',update);document.addEventListener('focusout',update);
    const observer=new MutationObserver(update);if(section.current)observer.observe(section.current,{subtree:true,attributes:true,attributeFilter:['aria-expanded']});
    update();
    return()=>{cancel();observer.disconnect();document.removeEventListener('pointermove',move,true);document.removeEventListener('pointerdown',press,true);document.removeEventListener('keydown',key,true);document.removeEventListener('focusin',update);document.removeEventListener('focusout',update);};
  },[pinned,shown,held,section]);
  return {pinned,shown,toggle,reveal:()=>setShown(true)};
}
