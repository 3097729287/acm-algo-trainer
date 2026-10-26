import {useEffect,useMemo,useRef,useState} from 'react';
import {ArrowDown,ArrowUp,Check,Plus,Search,X} from 'lucide-react';

export default function TrainingListEditor({list,rows,api,onSave,onClose}) {
  const dialog=useRef(null),name=useRef(null);
  const [title,setTitle]=useState(list?.title||''),[ids,setIds]=useState(()=>list?.problems.map(item=>item.row?.id||item.problemId)||[]);
  const [search,setSearch]=useState(''),[busy,setBusy]=useState(false),[error,setError]=useState('');
  const byId=useMemo(()=>new Map(rows.map(row=>[row.id,row])),[rows]);
  const selected=useMemo(()=>new Set(ids),[ids]);
  const matches=useMemo(()=>{
    const words=search.trim().toLocaleLowerCase().split(/\s+/);
    return rows.filter(row=>!row.locked&&words.every(word=>[row.problem,row.title,...row.tags||[]].join(' ').toLocaleLowerCase().includes(word))).slice(0,50);
  },[rows,search]);
  useEffect(()=>{const node=dialog.current;node.showModal();name.current.focus();return()=>node.close();},[]);
  function toggle(id){setIds(value=>value.includes(id)?value.filter(item=>item!==id):value.length<1000?[...value,id]:value);}
  function move(index,offset){setIds(value=>{const next=[...value];[next[index],next[index+offset]]=[next[index+offset],next[index]];return next;});}
  async function save(event){
    event.preventDefault();if(busy||!title.trim())return;
    setBusy(true);setError('');
    try{const result=await api('training-lists/save',{...(list?{id:list.id}:{}),title:title.trim(),problemIds:ids});onSave(result);}
    catch(issue){setError(issue.message);setBusy(false);}
  }
  return <dialog ref={dialog} className="social-comment-dialog training-list-editor" aria-labelledby="training-list-editor-title" onCancel={event=>{event.preventDefault();if(!busy)onClose();}}>
    <header><h3 id="training-list-editor-title">{list?'编辑题单':'新建题单'}</h3><button type="button" aria-label="关闭题单编辑" disabled={busy} onClick={onClose}><X size={18}/></button></header>
    <form onSubmit={save}>
      <label>题单名称<input ref={name} value={title} onChange={event=>setTitle(event.target.value)} maxLength={80} required disabled={busy}/></label>
      <div className="training-list-editor-columns">
        <section aria-label="选择题目"><label className="training-editor-search"><Search size={16}/><input aria-label="搜索题目" value={search} onChange={event=>setSearch(event.target.value)} disabled={busy}/></label><div className="training-editor-questions">{matches.map(row=><button type="button" key={row.id} className="training-editor-choice" aria-pressed={selected.has(row.id)} disabled={busy||!selected.has(row.id)&&ids.length>=1000} onClick={()=>toggle(row.id)}><span>{row.problem} · {row.title}</span>{selected.has(row.id)?<Check size={16}/>:<Plus size={16}/>}</button>)}</div></section>
        <section aria-label="已选题目"><div className="training-editor-selected-count">已选 {ids.length} 道题</div><ol className="training-editor-questions">{ids.map((id,index)=><li key={id}><span>{index+1}. {byId.get(id)?.title||id}</span><button type="button" aria-label={`上移第 ${index+1} 题`} disabled={busy||index===0} onClick={()=>move(index,-1)}><ArrowUp size={14}/></button><button type="button" aria-label={`下移第 ${index+1} 题`} disabled={busy||index===ids.length-1} onClick={()=>move(index,1)}><ArrowDown size={14}/></button><button type="button" aria-label={`移除第 ${index+1} 题`} disabled={busy} onClick={()=>toggle(id)}><X size={14}/></button></li>)}</ol></section>
      </div>
      {error&&<p role="alert" className="connection-error">{error}</p>}
      <footer><button type="button" className="text-button" disabled={busy} onClick={onClose}>取消</button><button className="primary" disabled={busy||!title.trim()}>保存</button></footer>
    </form>
  </dialog>;
}
