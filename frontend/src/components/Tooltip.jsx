import { useId, useLayoutEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { Info } from 'lucide-react';
import './SettingsControls.css';

export default function Tooltip({ text, children, label }) {
  const ref=useRef(null),popup=useRef(null),id=useId();
  const [open,setOpen]=useState(false),[position,setPosition]=useState({});
  useLayoutEffect(()=>{
    if(!open)return;
    const layout=()=>{const rect=ref.current.getBoundingClientRect(),size=popup.current?.getBoundingClientRect();if(!size)return;setPosition({position:'fixed',width:'max-content',maxWidth:Math.min(340,innerWidth-24),left:Math.max(12,Math.min(rect.x+rect.width/2-size.width/2,innerWidth-size.width-12)),...(rect.bottom+size.height+16>innerHeight?{bottom:innerHeight-rect.top+8}:{top:rect.bottom+8})});};
    layout();const dismiss=()=>setOpen(false);window.addEventListener('scroll',dismiss,true);window.addEventListener('resize',dismiss);
    return()=>{window.removeEventListener('scroll',dismiss,true);window.removeEventListener('resize',dismiss);};
  },[open,text]);
  return <span ref={ref} className="tooltip-anchor" onPointerEnter={()=>setOpen(true)} onPointerLeave={()=>setOpen(false)} onFocus={()=>setOpen(true)} onBlur={()=>setOpen(false)} onKeyDown={event=>{if(event.key==='Escape'){event.stopPropagation();setOpen(false);}}}>
    {children || <button type="button" className="hint-icon" aria-label={label || '说明'} aria-describedby={open?id:undefined} onClick={()=>setOpen(value=>!value)}><Info size={14}/></button>}
    {open&&String(text||'').trim()&&createPortal(<div ref={popup} role="tooltip" id={id} className="tb-tooltip" style={position}>{text}</div>,ref.current?.closest('dialog') || document.body)}
  </span>;
}
