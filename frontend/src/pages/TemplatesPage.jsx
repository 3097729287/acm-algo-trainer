import {Fragment,useEffect,useRef,useState} from 'react';
import {ArrowLeft,BookOpen,Check,Code2,Copy,FilePlus2,LoaderCircle,Plus,Save,Search,Trash2} from 'lucide-react';
import PageSearch from '@/components/PageSearch.jsx';
import CodeEditor from '@/components/CodeEditor.jsx';
import ThemedSelect from '@/components/ThemedSelect.jsx';
import PopConfirm from '@/components/PopConfirm.jsx';
import Markdown from '@/components/SolutionMarkdown.jsx';
import './algorithm-lab/algorithmLab.css';
import './algorithm-lab/sequenceLab.css';
import './TemplatesPage.css';

const GROUPS=['基础算法','搜索','数据结构','图论','字符串','数学','动态规划','我的模板'];
const emptyTemplate=()=>({id:null,title:'',category:'我的模板',language:'cpp17',code:'',notes:'',summary:'',builtin:false});
const Button=({label,children,...props})=><button type="button" className="icon-button" aria-label={label} title={label} {...props}>{children}</button>;
export default function TemplatesPage({api,shortcuts={},visit,embedded=false,onUse,language}) {
 const fallback=useRef({}),session=visit||fallback.current;
 const [templates,setTemplates]=useState([]),[query,setQuery]=useState(session.query||''),[selected,setSelected]=useState(session.selected||null),[draft,setDraft]=useState(session.draft||null);
 const [loading,setLoading]=useState(true),[busy,setBusy]=useState(false),[error,setError]=useState(''),[copied,setCopied]=useState(false),[deleting,setDeleting]=useState(null);
 const editor=useRef(null),panel=useRef(null),copyTimer=useRef(null),live=useRef(true);
 useEffect(()=>{live.current=true;api('templates').then(value=>{if(live.current)setTemplates(value.templates||[]);}).catch(issue=>{if(live.current)setError(issue.message);}).finally(()=>{if(live.current)setLoading(false);});return()=>{live.current=false;clearTimeout(copyTimer.current);};},[api]);
 useEffect(()=>{Object.assign(session,{query,selected,draft});},[query,selected,draft,session]);
 const current=draft||templates.find(item=>item.id===selected),own=current&&!current.builtin;
 const matching=templates.filter(item=>(!language||item.language===language)&&`${item.title} ${item.category} ${item.summary} ${(item.tags||[]).join(' ')}`.toLowerCase().includes(query.trim().toLowerCase()));
 const groups=[...GROUPS,...templates.map(item=>item.category)].filter((name,index,all)=>all.indexOf(name)===index&&matching.some(item=>item.category===name));
 const open=item=>{setError('');setSelected(item.id);setDraft(item.builtin?null:{...item});if(panel.current)panel.current.scrollTop=0;};
 const back=()=>{setSelected(null);setDraft(null);setError('');};
 const create=source=>{setSelected('new');setDraft(source?{...source,id:null,title:source.title,builtin:false,revision:undefined}:{...emptyTemplate(),language:language||'cpp17'});setError('');};
 const update=(key,value)=>setDraft(previous=>({...previous,[key]:value}));
 const copy=async code=>{try{await navigator.clipboard.writeText(code);setCopied(true);clearTimeout(copyTimer.current);copyTimer.current=setTimeout(()=>setCopied(false),1800);}catch{setError('复制未完成，请选中代码后复制');}};
 const save=async remove=>{
  if(busy)return;setBusy(true);setError('');
  try {
   const body=remove?{id:current.id,revision:current.revision,delete:true}:{...Object.fromEntries(['id','title','category','language','code','notes','summary','revision'].filter(key=>current[key]!=null).map(key=>[key,current[key]]))};
   const result=await api('templates/save',body);
   if(!live.current)return;setTemplates(result.templates);setDeleting(null);
   if(remove)back();else {setSelected(result.template.id);setDraft({...result.template});}
  } catch(issue){if(live.current)setError(issue.message);}finally{if(live.current)setBusy(false);}
 };
 const tools=<><label className="search-box"><Search size={17}/><input aria-label="搜索模板" value={query} onChange={event=>setQuery(event.target.value)}/></label><Button label="新建模板" onClick={()=>create()}><Plus size={17}/></Button></>;
 return <div ref={panel} className={`templates-page learning-paths-page scroll-panel lab-page-surface ${embedded?'templates-embedded':''}`} aria-label="模板">
  {error&&<p role="alert">{error}</p>}
  {selected&&current?<div className="template-detail">
   <header className="template-heading"><Button label="返回模板" data-folder-up onClick={back}><ArrowLeft size={18}/></Button><h2>{current.title||'新建模板'}</h2><span className="template-language">{current.language==='python3'?'Python 3':'C++17'}</span>
    <Button label="复制模板" onClick={()=>copy(current.code)}>{copied?<Check size={17}/>:<Copy size={17}/>}</Button>
    {current.builtin?<Button label="另存为我的模板" onClick={()=>create(current)}><FilePlus2 size={17}/></Button>:<><Button label="保存模板" disabled={busy||!current.title.trim()||!current.code.trim()} onClick={()=>save(false)}>{busy?<LoaderCircle className="spin" size={17}/>:<Save size={17}/>}</Button>{current.id&&<Button label="删除模板" disabled={busy} onClick={event=>setDeleting(event.currentTarget)}><Trash2 size={17}/></Button>}</>}
    {onUse&&<Button label="插入到文件开头" disabled={!current.code.trim()||Boolean(language&&language!==current.language)} onClick={()=>onUse(current)}><Plus size={17}/></Button>}
   </header>
   {own&&<div className="template-fields"><input aria-label="模板名称" maxLength={120} value={current.title} onChange={event=>update('title',event.target.value)} placeholder="模板名称"/><input aria-label="模板分类" maxLength={40} value={current.category} onChange={event=>update('category',event.target.value)} placeholder="模板分类"/><ThemedSelect aria-label="模板语言" value={current.language} onChange={event=>update('language',event.target.value)}><option value="cpp17">C++17</option><option value="python3">Python 3</option></ThemedSelect></div>}
   {current.builtin?<p className="template-notes">{current.notes}</p>:<textarea aria-label="模板说明" maxLength={16384} value={current.notes} onChange={event=>update('notes',event.target.value)} placeholder="适用条件与复杂度"/>}
   <div className="template-code"><CodeEditor ref={editor} value={current.code} docKey={`${selected}:${current.language}`} language={current.language} readOnly={current.builtin} shortcuts={shortcuts} onChange={value=>update('code',value)} onCommand={command=>{if(command==='save'&&own)save(false);}} ariaLabel="模板代码"/></div>
   {current.example&&<Markdown text={'```cpp\n'+current.example+'\n```'} onCopy={copy}/>}
  </div>:<div className="lab-catalog lab-multi-catalog template-catalog">
   {embedded?<div className="template-tools">{tools}</div>:<PageSearch>{tools}</PageSearch>}
   {loading?<LoaderCircle className="spin" role="status" aria-label="正在读取模板"/>:groups.map(group=><Fragment key={group}><h2 className="lab-catalog-group">{group}</h2>{matching.filter(item=>item.category===group).map(item=><section className="lab-panel" aria-label={item.title} key={item.id}><Code2 className="template-symbol" size={20}/><h3>{item.title}</h3><p className="seq-catalog-description">{item.summary||item.notes.slice(0,100)}</p><div className="lab-course-options"><Button label={`打开模板 ${item.title}`} onClick={()=>open(item)}><BookOpen size={18}/></Button><Button label={`复制模板 ${item.title}`} onClick={()=>copy(item.code)}><Copy size={18}/></Button>{onUse&&<Button label={`插入模板 ${item.title}`} onClick={()=>onUse(item)}><Plus size={18}/></Button>}</div></section>)}</Fragment>)}
  </div>}
  {deleting&&<PopConfirm anchor={deleting} title="删除这个模板？" busy={busy} onCancel={()=>setDeleting(null)} onConfirm={()=>save(true)} error={error}/>}
 </div>;
}
