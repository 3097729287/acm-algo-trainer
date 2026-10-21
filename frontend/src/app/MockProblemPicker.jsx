import { useEffect, useId, useLayoutEffect, useRef, useState } from 'react';
import {createPortal} from 'react-dom';
import { Check, ChevronDown, History } from 'lucide-react';
import { verdictLabel } from '@/models/workspaceModel.js';
import InlineTitle from '@/components/InlineTitle.jsx';
import './MockProblemPicker.css';

export default function MockProblemPicker({ contest, currentId, onSelect, onHistory }) {
  const [open, setOpen] = useState(false);
  const [position,setPosition]=useState({});
  const rootRef = useRef(null), triggerRef = useRef(null), menuRef = useRef(null);
  const menuId = useId();
  const current = contest.slots.find(slot => slot.id === currentId);

  useEffect(() => {
    if (!open) return;
    (menuRef.current?.querySelector('[aria-checked="true"]') || menuRef.current?.querySelector('button'))?.focus({preventScroll:true});
    const dismiss = event => {
      if (!rootRef.current?.contains(event.target)&&!menuRef.current?.contains(event.target)) setOpen(false);
    };
    document.addEventListener('pointerdown', dismiss);
    return () => document.removeEventListener('pointerdown', dismiss);
  }, [open]);

  useLayoutEffect(()=>{
    if(!open)return;
    const layout=()=>{const box=triggerRef.current.getBoundingClientRect(),width=Math.min(380,innerWidth-16);setPosition({position:'fixed',top:box.bottom+6,left:Math.max(8,Math.min(box.left,innerWidth-width-8)),width,maxHeight:Math.max(80,Math.min(440,innerHeight-box.bottom-14))});};
    layout();window.addEventListener('resize',layout);window.addEventListener('scroll',layout,true);
    return()=>{window.removeEventListener('resize',layout);window.removeEventListener('scroll',layout,true);};
  },[open]);

  const close = () => {
    setOpen(false);
    triggerRef.current?.focus();
  };
  const handleKeys = event => {
    if (event.key === 'Escape' && open) {
      event.preventDefault();
      event.stopPropagation();
      close();
    } else if (['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(event.key)) {
      event.preventDefault();
      event.stopPropagation();
      if (!open) { setOpen(true); return; }
      const items = [...menuRef.current.querySelectorAll('button')];
      const index = items.indexOf(document.activeElement);
      const next = event.key === 'Home' ? 0 : event.key === 'End' ? items.length - 1
        : (index + (event.key === 'ArrowDown' ? 1 : -1) + items.length) % items.length;
      items[next]?.focus();
    }
  };

  return <div className="mock-problem-picker" ref={rootRef} onKeyDown={handleKeys}
    onBlur={event => { if (!event.currentTarget.contains(event.relatedTarget)&&!menuRef.current?.contains(event.relatedTarget)) setOpen(false); }}>
    <button type="button" className="mock-problem-trigger" ref={triggerRef}
      aria-label={'选择比赛题目，当前 ' + (current?.letter || '')}
      aria-haspopup="menu" aria-expanded={open} aria-controls={menuId}
      title="选择比赛题目 · 题面聚焦时可按数字切题" onClick={() => setOpen(value => !value)}>
      <span className="mock-picker-letter">{current?.letter}</span>
      <span>选题</span><ChevronDown size={13} aria-hidden="true" />
    </button>
    {open && createPortal(<div className="mock-problem-menu" style={position} ref={menuRef} id={menuId} role="menu" aria-label="模拟赛题目">
      <div className="mock-picker-summary" role="presentation">
        <strong>{contest.name}</strong><span>{contest.accepted}/{contest.total} 原站 AC</span>
      </div>
      {contest.slots.map(slot => <button type="button" key={slot.id} role="menuitemradio"
        aria-checked={slot.id === currentId}
        className={'mock-picker-item' + (slot.id === currentId ? ' active' : '') + (slot.accepted ? ' solved' : '')}
        onClick={() => { close(); onSelect(slot.id); }}>
        <span className="mock-picker-letter">{slot.letter}</span>
        <span className="mock-picker-title"><InlineTitle>{slot.title}</InlineTitle></span>
        <span className="mock-picker-verdict">{slot.accepted ? <><Check size={12} aria-hidden="true" />AC</> : slot.verdict ? verdictLabel(slot.verdict) : '未提交'}</span>
      </button>)}
      <button type="button" className="mock-picker-history" role="menuitem" onClick={() => { close(); onHistory(); }}>
        <History size={14} aria-hidden="true" />模拟赛记录
      </button>
    </div>,document.body)}
  </div>;
}
