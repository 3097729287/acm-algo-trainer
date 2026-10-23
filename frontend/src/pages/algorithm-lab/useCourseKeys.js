import {useEffect} from 'react';

export default function useCourseKeys({index,count,navigate,menuOpen=false}) {
  useEffect(()=>{
    const move=event=>{
      if(event.defaultPrevented||event.altKey||event.ctrlKey||event.metaKey||menuOpen)return;
      if(!['ArrowLeft','ArrowRight'].includes(event.key))return;
      if(event.target?.closest?.('input,textarea,select,[contenteditable="true"],[role="slider"],.cm-editor,[role="dialog"],dialog[open]'))return;
      const target=index+(event.key==='ArrowRight'?1:-1);
      if(target<0||target>=count)return;
      event.preventDefault();navigate(target);
    };
    window.addEventListener('keydown',move);
    return()=>window.removeEventListener('keydown',move);
  },[index,count,navigate,menuOpen]);
}
