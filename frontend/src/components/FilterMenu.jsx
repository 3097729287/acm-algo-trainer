import { useEffect, useId, useLayoutEffect, useRef, useState } from 'react';
import { RotateCcw, SlidersHorizontal, X } from 'lucide-react';

export default function FilterMenu({ children, active = false, label = '筛选', onReset }) {
  const [open, setOpen] = useState(false), host = useRef(null), trigger = useRef(null), id = useId();
  const [position,setPosition]=useState({});
  useLayoutEffect(()=>{
    if(!open)return;
    const layout=()=>{const rect=trigger.current.getBoundingClientRect(),width=Math.min(360,innerWidth-24),top=Math.min(rect.bottom+9,innerHeight-140);setPosition({position:'fixed',left:Math.max(12,Math.min(rect.right-width,innerWidth-width-12)),right:'auto',top,width,maxHeight:Math.max(100,innerHeight-top-16)});};
    layout();window.addEventListener('resize',layout);window.addEventListener('scroll',layout,true);
    return()=>{window.removeEventListener('resize',layout);window.removeEventListener('scroll',layout,true);};
  },[open]);
  useEffect(() => {
    if (!open) return;
    const outside = event => {
      const popup = event.target.closest?.('.tb-select-menu');
      if (popup && host.current?.querySelector(`[aria-controls="${CSS.escape(popup.id)}"]`)) return;
      if (!host.current?.contains(event.target)) setOpen(false);
    };
    const escape = event => { if (event.key === 'Escape') { event.stopPropagation(); setOpen(false); trigger.current?.focus(); } };
    document.addEventListener('pointerdown', outside); host.current?.addEventListener('keydown', escape);
    const node = host.current;
    return () => { document.removeEventListener('pointerdown', outside); node?.removeEventListener('keydown', escape); };
  }, [open]);
  return <div className="filter-menu" ref={host}>
    <button ref={trigger} type="button" className={`icon-button filter-trigger${active ? ' active' : ''}`} aria-label={label} title={label} aria-expanded={open} aria-controls={id} aria-haspopup="dialog" onClick={() => setOpen(value => !value)}><SlidersHorizontal size={17}/>{active && <i className="filter-active-dot"/>}</button>
    {open && <div style={position} onClick={event=>{if(event.target.closest('[data-close-filter]'))setOpen(false);}} id={id} className="filter-popover" role="dialog" aria-label={label}><header><strong>{label}</strong><span/>{onReset && <button type="button" className="icon-button" aria-label="重置筛选" onClick={onReset}><RotateCcw size={16}/></button>}<button type="button" className="icon-button" aria-label="关闭筛选" onClick={() => { setOpen(false); trigger.current?.focus(); }}><X size={16}/></button></header>{children}</div>}
  </div>;
}
