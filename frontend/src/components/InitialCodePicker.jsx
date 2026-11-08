import {useEffect, useRef, useState} from 'react';
import ThemedSelect from './ThemedSelect.jsx';
import './InitialCode.css';

export function InitialCodeSelect({api,snapshot,language,selected='default',disabled=false,onSelect,onError,onOpenChange,title,fullCatalog=false}) {
  const [busy,setBusy]=useState(false),[catalog,setCatalog]=useState(null),generation=useRef(0),pending=useRef(false),errorRef=useRef(onError);errorRef.current=onError;
  const owner=window.__tbAccountUserId;
  useEffect(()=>{
    let live=true;setCatalog(null);
    if(!fullCatalog&&snapshot)api('initial-code').then(value=>{if(live&&owner===window.__tbAccountUserId)setCatalog(value);}).catch(error=>{if(live){setCatalog(snapshot);errorRef.current?.(error.message);}});
    return()=>{live=false;};
  },[api,snapshot,fullCatalog,owner]);
  useEffect(()=>{pending.current=false;setBusy(false);return()=>{generation.current++;};},[api,language]);
  const choices=fullCatalog?snapshot:catalog||snapshot;
  const items=(choices?.templates||[]).filter(item=>item.language===language),single=!fullCatalog&&items.length===1;
  const blocked=disabled||busy||!snapshot||!fullCatalog&&!catalog;
  const choose=async id=>{
    const item=items.find(row=>row.id===id);
    if(blocked||pending.current||!item)return;const seq=++generation.current;pending.current=true;setBusy(true);onError?.('');
    try {
      const result=await api('initial-code/select',{id,language,revision:choices.revisions[language]});
      const current=result.templates?.find(row=>row.language===language&&row.id===id)||item;
      if(seq===generation.current&&owner===window.__tbAccountUserId)await onSelect(current,result);
    }
    catch(error){if(seq===generation.current)onError?.(error.message);}
    finally{if(seq===generation.current){pending.current=false;setBusy(false);}}
  };
  return <ThemedSelect hideSelectedOption hideChevron aria-label="选择初始代码模板" title={single?`${title||'选择初始代码模板'} · 双击使用此模板`:title} onOpenChange={onOpenChange} className="initial-code-select" value={selected} disabled={blocked}
    onChange={event=>void choose(event.target.value)}
    onDoubleClick={event=>{if(single){event.preventDefault();event.stopPropagation();void choose(items[0].id);}}}
    onKeyDown={event=>{if(single&&event.key==='Enter'&&!event.altKey&&!event.ctrlKey&&!event.metaKey&&!event.shiftKey){event.preventDefault();event.stopPropagation();void choose(items[0].id);}}}
  >{items.map(item=><option key={item.id} value={item.id}>{item.title}</option>)}</ThemedSelect>;
}
