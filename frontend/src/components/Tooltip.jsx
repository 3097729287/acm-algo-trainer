import { useId, useLayoutEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { Info } from 'lucide-react';
import './SettingsControls.css';

export default function Tooltip({ text, children, label }) {
  const ref=useRef(null),id=useId();
  const [open,setOpen]=useState(false),[position,setPosition]=useState({});
  useLayoutEffect(()=>{
    if(!open)return;
    const layout=()=>{const rect=ref.current.getBoundingClientRect(),estimate=Array.from(String(text||'')).reduce((sum,char)=>sum+(/[^\x00-\x7f]/.test(char)?13:7),24),width=Math.min(300,innerWidth-24,Math.max(72,estimate));setPosition({position:'fixed',width,left:Math.max(12,Math.min(rect.x+rect.width/2-width/2,innerWidth-width-12)),...(rect.bottom+100>innerHeight?{bottom:innerHeight-rect.top+8}:{top:rect.bottom+8})});};
    layout();const dismiss=()=>setOpen(false);window.addEventListener('scroll',dismiss,true);window.addEventListener('resize',dismiss);
    return()=>{window.removeEventListener('scroll',dismiss,true);window.removeEventListener('resize',dismiss);};
  },[open,text]);
  return <span ref={ref} className="tooltip-anchor" onPointerEnter={()=>setOpen(true)} onPointerLeave={()=>setOpen(false)} onFocus={()=>setOpen(true)} onBlur={()=>setOpen(false)} onKeyDown={event=>{if(event.key==='Escape'){event.stopPropagation();setOpen(false);}}}>
    {children || <button type="button" className="hint-icon" aria-label={label || '说明'} aria-describedby={open?id:undefined} onClick={()=>setOpen(value=>!value)}><Info size={14}/></button>}
    {open&&createPortal(<div role="tooltip" id={id} className="tb-tooltip" style={position}>{text}</div>,ref.current?.closest('dialog') || document.body)}
  </span>;
}
