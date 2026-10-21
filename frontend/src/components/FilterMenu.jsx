import { useEffect, useId, useRef, useState } from 'react';
import { SlidersHorizontal, X } from 'lucide-react';
import Tooltip from './Tooltip.jsx';

export default function FilterMenu({ children, active = false, label = '筛选', onReset }) {
  const [open, setOpen] = useState(false), host = useRef(null), trigger = useRef(null), id = useId();
  useEffect(() => {
    if (!open) return;
    const outside = event => { if (!host.current?.contains(event.target)) setOpen(false); };
    const escape = event => { if (event.key === 'Escape') { event.stopPropagation(); setOpen(false); trigger.current?.focus(); } };
    document.addEventListener('pointerdown', outside); host.current?.addEventListener('keydown', escape);
    const node = host.current;
    return () => { document.removeEventListener('pointerdown', outside); node?.removeEventListener('keydown', escape); };
  }, [open]);
  return <div className="filter-menu" ref={host}>
    <Tooltip text={label}><button ref={trigger} type="button" className={`icon-button filter-trigger${active ? ' active' : ''}`} aria-label={label} aria-expanded={open} aria-controls={id} aria-haspopup="dialog" onClick={() => setOpen(value => !value)}><SlidersHorizontal size={17}/>{active && <i className="filter-active-dot"/>}</button></Tooltip>
    {open && <div onClick={event=>{if(event.target.closest('[data-close-filter]'))setOpen(false);}} id={id} className="filter-popover" role="dialog" aria-label={label}><header><strong>{label}</strong><span/>{onReset && <button type="button" className="text-button" onClick={onReset}>重置</button>}<button type="button" className="icon-button" aria-label="关闭筛选" onClick={() => { setOpen(false); trigger.current?.focus(); }}><X size={16}/></button></header>{children}</div>}
  </div>;
}
