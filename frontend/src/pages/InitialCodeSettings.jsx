import {useEffect, useRef, useState} from 'react';
import {Check, Code2, PencilLine, LoaderCircle, Plus, Save, Trash2, X} from 'lucide-react';
import CodeEditor from '@/components/CodeEditor.jsx';
import ThemedSelect from '@/components/ThemedSelect.jsx';
import PopConfirm from '@/components/PopConfirm.jsx';
import {InitialCodeSelect} from '@/components/InitialCodePicker.jsx';

function TemplateNameDialog({mode,title,busy,error,onCancel,onConfirm}){
  const dialog=useRef(null),input=useRef(null),[name,setName]=useState(title);
  useEffect(()=>{const previous=document.activeElement;dialog.current.showModal();input.current?.focus();input.current?.select();return()=>{dialog.current?.close();if(previous?.isConnected)previous.focus();};},[]);
  return <dialog ref={dialog} className="initial-code-name-dialog" aria-label={mode==='create'?'新建模板':'重命名模板'} onCancel={event=>{event.preventDefault();if(!busy)onCancel();}}><form onSubmit={event=>{event.preventDefault();if(name.trim()&&!busy)onConfirm(name.trim());}}><h3>{mode==='create'?'新建模板':'重命名模板'}</h3><input ref={input} aria-label="模板名称" placeholder="模板名称" value={name} maxLength={120} disabled={busy} required onChange={event=>setName(event.target.value)}/>{error&&<p role="alert">{error}</p>}<footer><button type="button" className="icon-button" aria-label="取消命名" title="取消" disabled={busy} onClick={onCancel}><X size={17}/></button><button type="submit" className="icon-button primary" aria-label="确认模板名称" title="确认" disabled={busy||!name.trim()}>{busy?<LoaderCircle className="spin" size={17}/>:<Check size={17}/>}</button></footer></form></dialog>;
}

export default function InitialCodeSettings({api, shortcuts={}}){
  const [snapshot,setSnapshot]=useState(null),[language,setLanguage]=useState('cpp17'),[identity,setIdentity]=useState('default');
  const [draft,setDraft]=useState(null),[busy,setBusy]=useState(false),[error,setError]=useState(''),[deleting,setDeleting]=useState(null);
  const buffers=useRef(new Map()), toolbarRef=useRef(null);
  const [naming,setNaming]=useState(null),[saved,setSaved]=useState(false);
  useEffect(()=>{if(!saved)return;const timer=setTimeout(()=>setSaved(false),2200);return()=>clearTimeout(timer);},[saved]);
  const catalogRevision=useRef(0),view=useRef(null);view.current={language,identity,busy};
  const load=(value,lang=language,id=value.selection[lang]||'default')=>{
    catalogRevision.current++;
    setSnapshot(value);setIdentity(id);setLanguage(lang);
    const item=value.templates.find(row=>row.language===lang&&row.id===id)||value.templates.find(row=>row.language===lang&&row.id==='default');
    setDraft(buffers.current.get(lang+':'+id)||item);
  };
  useEffect(()=>{
    let alive=true,pending=false;
    const refresh=async(initial=false)=>{if(pending||document.hidden||view.current.busy)return;pending=true;const revision=catalogRevision.current;
      try{const value=await api('initial-code');if(!alive||revision!==catalogRevision.current||view.current.busy)return;
        if(initial)load(value,'cpp17');else{const {language,identity}=view.current;if(buffers.current.has(language+':'+identity)){setSnapshot(value);return;}const next=value.templates.some(item=>item.language===language&&item.id===identity)?identity:value.selection[language]||'default';load(value,language,next);}
      }catch(issue){if(alive&&initial)setError(issue.message);}finally{pending=false;}};
    const focus=()=>void refresh();void refresh(true);window.addEventListener('focus',focus);document.addEventListener('visibilitychange',focus);
    return()=>{alive=false;window.removeEventListener('focus',focus);document.removeEventListener('visibilitychange',focus);};
  },[api]);
  const change=value=>{setSaved(false);catalogRevision.current++;const next={...draft,...value};buffers.current.set(language+':'+identity,next);setDraft(next);};
  const confirmName=async title=>{
    if(busy||!naming)return;catalogRevision.current++;setBusy(true);setError('');setSaved(false);
    const mode=naming.mode,code=mode==='create'?snapshot.templates.find(row=>row.language===language&&row.id==='default').code:draft.code;
    try{
      const value=await api('initial-code/save',{...(mode==='rename'?{id:identity,revision:draft.revision}:{}),title,language,code});
      const chosen=await api('initial-code/select',{id:value.template.id,language,revision:value.revisions[language]});
      if(mode==='rename')buffers.current.delete(language+':'+identity);
      load(chosen,language,value.template.id);setNaming(null);setSaved(true);
    }catch(issue){setError(issue.message);}finally{setBusy(false);}
  };
  const save=async()=>{
    if(!draft||busy)return;catalogRevision.current++;setBusy(true);setError('');setSaved(false);
    try{
      const value=await api('initial-code/save',{...(identity!=='new'?{id:identity,revision:draft.revision}:{}),title:draft.title,language,code:draft.code});
      buffers.current.delete(language+':'+identity);
      load(value,language,value.template.id);
      const chosen=await api('initial-code/select',{id:value.template.id,language,revision:value.revisions[language]});
      load(chosen,language,value.template.id);setSaved(true);
    }catch(issue){setError(issue.message);}finally{setBusy(false);}
  };
  const remove=async()=>{
    if(!draft||draft.builtin||busy)return;
    if(identity==='new'){buffers.current.delete(language+':new');load(snapshot);setDeleting(null);return;}
    setBusy(true);setError('');
    try{const value=await api('initial-code/save',{id:identity,revision:draft.revision,delete:true});buffers.current.delete(language+':'+identity);load(value);setDeleting(null);}catch(issue){setError(issue.message);}finally{setBusy(false);}
  };
  return <section className="initial-code-settings" aria-label="初始代码模板"><h2><Code2 size={19}/>初始代码模板</h2>
    {error&&<p role="alert" className="connection-error">{error}</p>}
    {!snapshot||!draft?<LoaderCircle className="spin" aria-label="正在读取"/>:<>
      <div ref={toolbarRef} className="initial-code-settings-toolbar"><ThemedSelect hideSelectedOption hideChevron aria-label="模板语言" value={language} disabled={busy} onChange={event=>{setSaved(false);load(snapshot,event.target.value);}}><option value="cpp17">C++17</option><option value="python3">Python 3</option></ThemedSelect><InitialCodeSelect fullCatalog api={api} snapshot={snapshot} language={language} selected={identity} disabled={busy} onSelect={(item,value)=>{setSaved(false);load(value,language,item.id);}} onError={setError}/><div className="initial-code-settings-actions">{saved&&<span className="initial-code-save-notice" role="status">代码已保存</span>}<button type="button" className="icon-button" aria-label="新建初始代码模板" title="新建模板" onClick={()=>{setError('');setNaming({mode:'create',title:''});}} disabled={busy}><Plus size={17}/></button><button type="button" className="icon-button" aria-label="重命名初始代码模板" title="重命名" onClick={()=>{setError('');setNaming({mode:'rename',title:draft.title});}} disabled={busy||draft.builtin}><PencilLine size={17}/></button>{!draft.builtin&&<button type="button" className="icon-button" aria-label="删除初始代码模板" title="删除模板" onClick={event=>setDeleting(event.currentTarget)} disabled={busy}><Trash2 size={17}/></button>}<button type="button" className="icon-button primary" aria-label="保存初始代码模板" title="保存" onClick={save} disabled={busy||!draft.title.trim()}>{busy?<LoaderCircle className="spin" size={17}/>:<Save size={17}/>}</button></div></div>
      <div className="initial-code-settings-editor"><CodeEditor shortcuts={shortcuts} value={draft.code} onChange={code=>change({code})} onCommand={command=>{if(command==='save')void save();}} onLeave={()=>toolbarRef.current?.querySelector('button:not(:disabled)')?.focus()} language={language} readOnly={busy} ariaLabel="初始代码模板内容" docKey={language+':'+identity}/></div>
    </>}
    {deleting&&<PopConfirm anchor={deleting} title="删除这个模板？" busy={busy} error={error} cancelLabel="×" confirmLabel={<Trash2 size={15}/>} cancelAriaLabel="取消删除" confirmAriaLabel="确认删除模板" onCancel={()=>setDeleting(null)} onConfirm={remove}/>}
    {naming&&<TemplateNameDialog {...naming} busy={busy} error={error} onCancel={()=>setNaming(null)} onConfirm={confirmName}/>}
  </section>;
}
