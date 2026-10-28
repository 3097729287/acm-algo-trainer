import {useEffect, useRef, useState} from 'react';
import {createPortal} from 'react-dom';
import {Check, ChevronDown, LoaderCircle, RefreshCw, X} from 'lucide-react';
import CodeEditor from './CodeEditor.jsx';
import './InitialCode.css';

export function InitialCodeButton({title='默认', disabled=false, onClick}) {
  return <button type="button" className="initial-code-trigger" aria-label="选择初始代码模板" aria-haspopup="dialog" title="选择初始代码模板" disabled={disabled} onClick={onClick}><span>{title}</span><ChevronDown size={13}/></button>;
}

export default function InitialCodePicker({api, language, selected='default', onSelect, onClose}) {
  const panel=useRef(null), returnFocus=useRef(document.activeElement), backdropStart=useRef(false), [snapshot,setSnapshot]=useState(null);
  const [identity,setIdentity]=useState(selected), [busy,setBusy]=useState(false), [error,setError]=useState(''), [attempt,setAttempt]=useState(0);
  const closeRef=useRef(onClose);closeRef.current=onClose;
  useEffect(()=>{
    let alive=true;setError('');
    api('initial-code').then(value=>{if(alive)setSnapshot(value);}).catch(issue=>{if(alive)setError(issue.message);});
    return()=>{alive=false;};
  },[api,attempt]);
  useEffect(()=>{
    panel.current?.focus();
    const key=event=>{
      if(event.key==='Escape'){event.preventDefault();event.stopImmediatePropagation();closeRef.current();}
      if(event.key!=='Tab')return;
      const nodes=[...panel.current.querySelectorAll('button:not(:disabled),input:not(:disabled),[tabindex="0"]')].filter(node=>node.getClientRects().length);
      if(!nodes.length){event.preventDefault();return;}
      if(event.shiftKey&&(document.activeElement===nodes[0]||document.activeElement===panel.current)){event.preventDefault();nodes.at(-1).focus();}
      else if(!event.shiftKey&&(document.activeElement===nodes.at(-1)||document.activeElement===panel.current)){event.preventDefault();nodes[0].focus();}
    };
    window.addEventListener('keydown',key,true);
    return()=>{window.removeEventListener('keydown',key,true);if(returnFocus.current?.isConnected)returnFocus.current.focus();};
  },[]);
  const items=(snapshot?.templates||[]).filter(item=>item.language===language);
  const current=items.find(item=>item.id===identity)||items[0];
  const choose=async()=>{
    if(!current||busy)return;setBusy(true);setError('');
    try{
      const result=await api('initial-code/select',{id:current.id,language,revision:snapshot.revisions[language]});
      await onSelect(current,result);onClose();
    }catch(issue){setError(issue.message);if(issue.status===409)setAttempt(value=>value+1);}
    finally{setBusy(false);}
  };
  return createPortal(<div className="modal-overlay initial-code-overlay" onPointerDown={event=>{backdropStart.current=event.target===event.currentTarget;}} onClick={event=>{if(backdropStart.current&&event.target===event.currentTarget)onClose();backdropStart.current=false;}}><section ref={panel} tabIndex={-1} className="modal initial-code-picker" role="dialog" aria-modal="true" aria-label="选择初始代码模板">
    <header><h2>初始代码模板</h2><button type="button" className="icon-button" aria-label="关闭选择器" title="关闭 · Esc" onClick={onClose}><X size={18}/></button></header>
    {error&&<div className="initial-code-error" role="alert">{error}<button type="button" className="icon-button" aria-label="重新读取模板" title="重新读取模板" onClick={()=>setAttempt(value=>value+1)}><RefreshCw size={16}/></button></div>}
    {!snapshot?<div className="initial-code-loading" role="status"><LoaderCircle className="spin" aria-label="正在读取"/></div>:<div className="initial-code-picker-body"><div role="listbox" aria-label="初始代码模板" className="initial-code-options">{items.map((item,index)=><button type="button" key={item.id} role="option" aria-selected={current?.id===item.id} tabIndex={current?.id===item.id?0:-1} onClick={()=>setIdentity(item.id)} onKeyDown={event=>{if(!['ArrowDown','ArrowUp','Home','End'].includes(event.key))return;event.preventDefault();const next=event.key==='Home'?0:event.key==='End'?items.length-1:(index+(event.key==='ArrowDown'?1:-1)+items.length)%items.length;setIdentity(items[next].id);event.currentTarget.parentElement.children[next].focus();}}><span>{item.title}</span>{current?.id===item.id&&<Check size={15}/>}</button>)}</div><div className="initial-code-preview"><CodeEditor value={current?.code||''} language={language} readOnly ariaLabel="初始代码模板预览" docKey={language+':'+current?.id} onLeave={()=>panel.current?.querySelector('[aria-label="使用选中模板"]')?.focus()}/></div></div>}
    <footer><button type="button" className="icon-button primary" aria-label="使用选中模板" title="使用选中模板" disabled={!current||busy} onClick={choose}>{busy?<LoaderCircle className="spin" size={18}/>:<Check size={18}/>}</button></footer>
  </section></div>,document.body);
}
