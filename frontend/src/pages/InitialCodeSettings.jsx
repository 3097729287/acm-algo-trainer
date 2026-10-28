import {useEffect, useRef, useState} from 'react';
import {Check, Code2, Copy, LoaderCircle, Plus, Save, Trash2} from 'lucide-react';
import CodeEditor from '@/components/CodeEditor.jsx';
import ThemedSelect from '@/components/ThemedSelect.jsx';
import PopConfirm from '@/components/PopConfirm.jsx';
import InitialCodePicker, {InitialCodeButton} from '@/components/InitialCodePicker.jsx';

export default function InitialCodeSettings({api, shortcuts={}}){
  const [snapshot,setSnapshot]=useState(null),[language,setLanguage]=useState('cpp17'),[identity,setIdentity]=useState('default');
  const [draft,setDraft]=useState(null),[picker,setPicker]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState(''),[deleting,setDeleting]=useState(null);
  const buffers=useRef(new Map()), titleRef=useRef(null), toolbarRef=useRef(null);
  const load=(value,lang=language,id=value.selection[lang]||'default')=>{
    setSnapshot(value);setIdentity(id);setLanguage(lang);
    const item=value.templates.find(row=>row.language===lang&&row.id===id)||value.templates.find(row=>row.language===lang&&row.id==='default');
    setDraft(buffers.current.get(lang+':'+id)||item);
  };
  useEffect(()=>{let alive=true;api('initial-code').then(value=>{if(alive)load(value,'cpp17');}).catch(issue=>{if(alive)setError(issue.message);});return()=>{alive=false;};},[api]);
  const change=value=>{const next={...draft,...value};buffers.current.set(language+':'+identity,next);setDraft(next);};
  const create=(copy=false)=>{
    const item=snapshot.templates.find(row=>row.language===language&&row.id==='default');
    const next={id:'new',title:'',language,code:copy?draft.code:item.code,builtin:false};
    // Retain unsaved buffers while another template is being previewed.
    const remembered=buffers.current.get(language+':new');
    setIdentity('new');setDraft(remembered||next);requestAnimationFrame(()=>titleRef.current?.focus());
  };
  const save=async()=>{
    if(!draft||busy)return;setBusy(true);setError('');
    try{
      const value=await api('initial-code/save',{...(identity!=='new'?{id:identity,revision:draft.revision}:{}),title:draft.title,language,code:draft.code});
      buffers.current.delete(language+':'+identity);
      load(value,language,value.template.id);
      const chosen=await api('initial-code/select',{id:value.template.id,language,revision:value.revisions[language]});
      load(chosen,language,value.template.id);
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
      <div ref={toolbarRef} className="initial-code-settings-toolbar"><ThemedSelect aria-label="模板语言" value={language} disabled={busy} onChange={event=>load(snapshot,event.target.value)}><option value="cpp17">C++17</option><option value="python3">Python 3</option></ThemedSelect><InitialCodeButton title={identity==='new'?'新模板':draft.title} disabled={busy} onClick={()=>setPicker(true)}/><div className="initial-code-settings-actions"><button type="button" className="icon-button" aria-label="新建初始代码模板" title="新建模板" onClick={()=>create()} disabled={busy}><Plus size={17}/></button><button type="button" className="icon-button" aria-label="复制为初始代码模板" title="另存为" onClick={()=>create(true)} disabled={busy}><Copy size={17}/></button>{!draft.builtin&&<><button type="button" className="icon-button" aria-label="删除初始代码模板" title="删除模板" onClick={event=>setDeleting(event.currentTarget)} disabled={busy}><Trash2 size={17}/></button><button type="button" className="icon-button primary" aria-label="保存初始代码模板" title="保存并使用" onClick={save} disabled={busy||!draft.title.trim()}>{busy?<LoaderCircle className="spin" size={17}/>:<Save size={17}/>}</button></>}{snapshot.selection[language]===identity&&<Check size={16} aria-label="当前初始代码模板"/>}</div></div>
      {!draft.builtin&&<input ref={titleRef} className="initial-code-title" aria-label="初始代码模板名称" placeholder="模板名称" value={draft.title} maxLength={120} disabled={busy} onChange={event=>change({title:event.target.value})}/>}
      <div className="initial-code-settings-editor"><CodeEditor shortcuts={shortcuts} value={draft.code} onChange={code=>change({code})} onCommand={command=>{if(command==='save'&&!draft.builtin)void save();}} onLeave={()=>toolbarRef.current?.querySelector('button:not(:disabled)')?.focus()} language={language} readOnly={draft.builtin||busy} ariaLabel="初始代码模板内容" docKey={language+':'+identity}/></div>
    </>}
    {picker&&<InitialCodePicker api={api} language={language} selected={identity} onClose={()=>setPicker(false)} onSelect={(item,value)=>load(value,language,item.id)}/>}
    {deleting&&<PopConfirm anchor={deleting} title="删除这个模板？" busy={busy} error={error} cancelLabel="×" confirmLabel={<Trash2 size={15}/>} cancelAriaLabel="取消删除" confirmAriaLabel="确认删除模板" onCancel={()=>setDeleting(null)} onConfirm={remove}/>}
  </section>;
}
