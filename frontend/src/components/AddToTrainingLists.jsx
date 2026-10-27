import {dialogPointerDown,dialogBackdropClick} from '@/lib/dialogBackdrop.js';
import {useEffect,useRef,useState} from 'react';
import {Check,Plus,RotateCw,Search,X} from 'lucide-react';
import './AddToTrainingLists.css';

export default function AddToTrainingLists({problemIds,api,onClose,onSave}) {
  const dialog=useRef(null),submit=useRef(false);
  const [lists,setLists]=useState(null),[selected,setSelected]=useState([]),[query,setQuery]=useState('');
  const [busy,setBusy]=useState(false),[error,setError]=useState(''),[attempt,setAttempt]=useState(0);
  const [creating,setCreating]=useState(false),[name,setName]=useState('');
  const creatingRef=useRef(false);
  useEffect(()=>{const node=dialog.current;node.showModal();return()=>node.close();},[]);
  useEffect(()=>{
    let alive=true;setError('');
    api('training-lists?custom=1').then(value=>{if(alive)setLists(value.lists.filter(list=>list.custom));}).catch(issue=>{if(alive)setError(issue.message||'题单读取失败');});
    return()=>{alive=false;};
  },[api,attempt]);
  async function save(event){
    event.preventDefault();if(submit.current||!selected.length)return;
    submit.current=true;setBusy(true);setError('');
    try{onSave(await api('training-lists/add',{listIds:selected,problemIds}));}
    catch(issue){setError(issue.message||'添加失败');submit.current=false;setBusy(false);}
  }
  async function create(){
    if(busy||creatingRef.current||!name.trim())return;
    creatingRef.current=true;setBusy(true);setError('');
    try{
      const result=await api('training-lists/save',{title:name.trim()});
      setLists(result.customLists);setSelected(previous=>[...previous,result.list.id]);setQuery('');setName('');setCreating(false);
      window.dispatchEvent(new Event('tb:training-lists-changed'));
    }catch(issue){setError(issue.message||'新建失败');}
    finally{creatingRef.current=false;setBusy(false);}
  }
  return <dialog onPointerDown={dialogPointerDown} onClick={dialogBackdropClick} ref={dialog} className="social-comment-dialog add-training-lists" aria-labelledby="add-training-lists-title" onCancel={event=>{event.preventDefault();if(!busy)onClose();}}>
    <header><h3 id="add-training-lists-title">加入题单</h3><button type="button" aria-label="关闭加入题单" disabled={busy} onClick={onClose}><X size={18}/></button></header>
    <form onSubmit={save}>
      <div className="add-training-list-summary">{problemIds.length} 道题</div>
      <div className="add-training-list-create">{creating?<><input autoFocus aria-label="新题单名称" maxLength={80} value={name} disabled={busy} onChange={event=>setName(event.target.value)} onKeyDown={event=>{if(event.key==='Enter'){event.preventDefault();create();}if(event.key==='Escape'){event.preventDefault();event.stopPropagation();setCreating(false);}}}/><button type="button" className="icon-button" aria-label="保存新题单" disabled={busy||!name.trim()} onClick={create}><Check size={18}/></button><button type="button" className="icon-button" aria-label="取消新建题单" disabled={busy} onClick={()=>setCreating(false)}><X size={18}/></button></>:<button type="button" className="icon-button" aria-label="新建题单" title="新建题单" disabled={busy} onClick={()=>setCreating(true)}><Plus size={18}/></button>}</div>
      {lists?.length>0&&<label className="search-box"><Search size={16}/><input aria-label="搜索自建题单" value={query} disabled={busy} onChange={event=>setQuery(event.target.value)}/></label>}
      <div className="add-training-list-options" aria-label="自建题单" aria-busy={!lists&&!error}>
        {!lists&&!error&&<p role="status">正在读取题单…</p>}
        {lists?.filter(list=>list.title.toLocaleLowerCase().includes(query.trim().toLocaleLowerCase())).map(list=><label key={list.id}><input type="checkbox" checked={selected.includes(list.id)} disabled={busy} onChange={event=>setSelected(previous=>event.target.checked?[...previous,list.id]:previous.filter(id=>id!==list.id))}/><span>{list.title}</span><small>{list.problems.length} 题</small></label>)}
        {lists?.length===0&&<p className="progress-muted">暂无自建题单</p>}
        {!!lists?.length&&!lists.some(list=>list.title.toLocaleLowerCase().includes(query.trim().toLocaleLowerCase()))&&<p className="progress-muted">没有匹配的题单</p>}
      </div>
      {error&&<p role="alert" className="connection-error">{error}{!lists&&<button type="button" className="icon-button" aria-label="重新读取" onClick={()=>setAttempt(value=>value+1)}><RotateCw size={16}/></button>}</p>}
      <footer><button type="button" className="icon-button" aria-label="取消" disabled={busy} onClick={onClose}><X size={18}/></button><button className="primary" aria-label="添加" disabled={busy||!selected.length}><Check size={18}/></button></footer>
    </form>
  </dialog>;
}
