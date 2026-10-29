import { useEffect, useId, useLayoutEffect, useRef, useState } from 'react';
import { RotateCcw, SlidersHorizontal, X } from 'lucide-react';
import './FilterMenu.css';

export default function FilterMenu({ children, active = false, label = '筛选', onReset }) {
  const [open, setOpen] = useState(false), host = useRef(null), trigger = useRef(null), id = useId();
  const [position,setPosition]=useState({});
  useLayoutEffect(()=>{
    if(!open)return;
    const layout=()=>{const rect=trigger.current.getBoundingClientRect(),edge=12,width=Math.max(0,Math.min(360,innerWidth-edge*2)),top=Math.max(edge,Math.min(rect.bottom+8,innerHeight-edge-100));setPosition({position:'fixed',left:Math.max(edge,Math.min(rect.left,innerWidth-width-edge)),right:'auto',top,width,maxHeight:Math.max(0,innerHeight-top-edge)});};
    let frame;
    const resize=()=>{layout();cancelAnimationFrame(frame);frame=requestAnimationFrame(layout);};
    const observer=new ResizeObserver(resize);observer.observe(trigger.current);const controls=host.current?.closest('.page-search-controls');if(controls)observer.observe(controls);
    resize();window.addEventListener('resize',resize);window.addEventListener('scroll',resize,true);
    return()=>{cancelAnimationFrame(frame);observer.disconnect();window.removeEventListener('resize',resize);window.removeEventListener('scroll',resize,true);};
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
