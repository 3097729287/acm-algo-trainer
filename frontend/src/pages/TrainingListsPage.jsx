import {ProblemCells,ProblemTableHead} from '@/components/ProblemTableParts.jsx';
import PagePagination from '@/components/PagePagination.jsx';
import {useFittedPageSize} from '@/lib/useFittedPageSize.js';
import { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import { ArrowLeftRight, ChevronLeft, ChevronRight, ExternalLink, FileText, Folder, Heart, House, Pencil, Plus, RotateCw, Search, Trash2, X } from 'lucide-react';
import {LikeBurst} from '@/components/Social.jsx';
import TrainingListEditor from './TrainingListEditor.jsx';
import PopConfirm from '@/components/PopConfirm.jsx';
import {buildTrainingCurriculum} from '@/lib/trainingCurriculum.js';
import SortDirection from '@/components/SortDirection.jsx';
import {compareProblemDifficulty} from '@/lib/problemOrder.js';
import PageSearch from '@/components/PageSearch.jsx';
import { matchesTrainingProblem, startsWithPath, trainingIndex } from '@/lib/trainingLists.js';
import { organizeTrainingLists, compareTrainingLists, compareCategoryNames } from '@/lib/trainingListCatalog.js';
import '@/components/CatalogExplorer.css';
import './TrainingListsPage.css';

const INITIAL = { curriculumVersion:1, mode: 'algorithm', folder: [], trail: [], sections: [], flat: false, query: '', status: '', descending: false, page: 1 };
const source = 'https://www.luogu.com.cn/training/list';
const leaf=list=>list && !list.children?.length && !list.problems?.some(item=>item.sections?.length);
const cardTitle=list=>String(list.displayTitle||list.title).replace(/^(?:【[^】]*】|\[[^\]]*\])\s*/,'');

export default function TrainingListsPage({ api, rows = [], onTrain, visit, pageSize = 50, busy = false, prefs={},onTag,onFavorite,onSolution,onAddToList,onRemove }) {
  const fallback = useRef({}), session = visit || fallback.current;
  const owner = window.__tbAccountUserId || 'local';
  const cached = session.content?.owner === owner ? session.content : null;
  const [state, setState] = useState(() => ({ ...INITIAL, ...(session.state?.curriculumVersion===1?session.state:{}), status: '' }));
  const [lists, setLists] = useState(() => cached?.lists || null), [error, setError] = useState(''), [attempt, setAttempt] = useState(0);
  const [deletion,setDeletion]=useState(null),[deleting,setDeleting]=useState(false),[deleteError,setDeleteError]=useState('');
  const panel = useRef(null), navigation = useRef(null);
  const contentVersion=useRef(0);
  const [editor,setEditor]=useState(null),[hearts,setHearts]=useState({likes:{}});
  const patch = value => setState(previous => ({ ...previous, page: 1, ...value }));
  useEffect(() => {
    let alive = true;
    const version=contentVersion.current;
    setError('');
    api('training-lists').then(value => {
      if (alive && version===contentVersion.current) { session.content={owner,lists:value.lists}; setLists(value.lists); }
    }).catch(issue => { if (alive) setError(issue.message || '题单读取失败'); });
    return () => { alive = false; };
  }, [api, attempt, owner]);
  useEffect(() => { if (lists) session.content={owner,lists}; }, [lists,owner]);
  useLayoutEffect(() => { session.state = state; }, [state]);
  useLayoutEffect(() => {
    const node = panel.current;
    if (!node) return;
    node.scrollTop = session.scrollTop || 0;
  }, [Boolean(lists)]);
  const location = JSON.stringify([state.mode, state.folder, state.trail, state.sections, state.flat, state.page, state.query, state.status]);
  useLayoutEffect(() => {
    if (navigation.current && navigation.current !== location) panel.current?.scrollTo({ top: 0 });
    navigation.current = location;
  }, [location]);
  function back() {
    if (state.sections.length) patch({ sections: state.sections.slice(0, -1), flat: false });
    else if (state.flat) patch({ flat: false });
    else if (state.trail.length) patch({ trail: state.trail.slice(0, -1), sections: [], query: '', flat: false });
    else patch({ folder: state.folder.slice(0, -1), query: '' });
  }
  const canBack = state.folder.length > 0 || state.trail.length > 0 || state.flat;
  useEffect(() => {
    const key = event => {
      if (event.key !== 'Escape' || event.defaultPrevented || !canBack || event.target.closest?.('input,textarea,select,[contenteditable=true]') || document.querySelector('.tb-select-menu,dialog[open],[data-popconfirm]')) return;
      event.preventDefault(); back();
    };
    window.addEventListener('keydown', key);
    return () => window.removeEventListener('keydown', key);
  }, [state, canBack]);

  const organized = useMemo(() => {const original=organizeTrainingLists((lists || []).filter(list=>!list.custom));return [...(state.mode==='source'?original:buildTrainingCurriculum(original,rows)),...(lists||[]).filter(list=>list.custom).map(list=>({...list,displayTitle:list.title,sourceLabel:'',topicPath:['我的题单']}))];}, [lists, rows, state.mode]);
  const index = useMemo(() => trainingIndex(organized, rows), [organized, rows]);
  const active = index.byList.get(state.trail.at(-1));
  const search = state.query.trim().toLocaleLowerCase();
  const rowSize=useFittedPageSize(panel,`${state.mode}:${state.trail.join('/')}:${state.folder.join('/')}:${Boolean(lists)}`,'.training-list-table tbody tr, .catalog-folder-row');
  const all = active ? index.all(active.id) : [];
  const own = active ? index.own.get(active.id) || [] : [];
  const scoped = own.filter(item => startsWithPath(item.sections || [], state.sections));
  const sectionNames = [...new Set(scoped.map(item => item.sections?.[state.sections.length]).filter(Boolean))];
  const searchingProblems = Boolean(search || state.status);
  const showAll = state.flat || searchingProblems;
  const problems = (showAll ? state.sections.length ? scoped : all : scoped.filter(item => (item.sections || []).length === state.sections.length)).filter(item => matchesTrainingProblem(item, state.query, state.status));
  if(!active?.custom)problems.sort((a,b)=>compareProblemDifficulty(a.row,b.row,state.descending));

  const folders = new Map(), entries = [];
  let scopeLists = organized;
  if (!active) {
    const base = organized.filter(list => state.mode !== 'source' || (list.categories || []).some(category => !state.folder.length || category.id === state.folder[0]));
    const selected = base.filter(list => (state.mode !== 'algorithm' || startsWithPath(list.topicPath, state.folder)));
    scopeLists = selected;
    for (const list of selected) {
      const searchableTitle = [list.title, list.displayTitle, list.sourceLabel, ...list.topicPath].join(' ').toLocaleLowerCase();
      const titleMatches = search && search.split(/\s+/).every(word => searchableTitle.includes(word));
      const items = index.all(list.id);
      if ((search || state.status) && !items.some(item => matchesTrainingProblem(item, titleMatches ? '' : state.query, state.status)) && !(titleMatches && !state.status)) continue;
      const next = state.mode === 'algorithm' ? list.topicPath[state.folder.length] : !state.folder.length ? list.categories?.[0]?.id : null;
      if (next && !search && !state.status) {
        const paths = state.mode === 'source' ? list.categories.map(category => category.id) : [next];
        for (const key of paths) { if (!folders.has(key)) folders.set(key, []); folders.get(key).push(list.id); }
      } else entries.push(list);
    }
    if (state.mode === 'source' && state.folder.length) entries.sort((a, b) => (a.categories.find(c => c.id === state.folder[0])?.position || 0) - (b.categories.find(c => c.id === state.folder[0])?.position || 0));
    else entries.sort(compareTrainingLists);
  }
  const open = list => {setDeletion(null);patch({ trail: [...state.trail, list.id], sections: [], flat: false, query: '' });};
  const listStats = index.stats(active ? [active.id] : scopeLists.map(list => list.id));
  const readableLists = scopeLists.filter(list => list.available).length;
  const children = active && !showAll && !state.sections.length ? (active.children || []).filter(id => !state.trail.includes(id)).map(id => index.byList.get(id)).filter(Boolean) : [];
  const folderRows = active ? (showAll ? [] : sectionNames.map(name => ({ id: name, title: name, count: scoped.filter(item => item.sections?.[state.sections.length] === name).length, action: () => patch({ sections: [...state.sections, name] }) }))) : [...folders].map(([id, ids]) => ({ id, stats:index.stats(ids), title: state.mode === 'source' ? index.categories.find(c => c.id === id)?.name || id : id, count: ids.length, unit: '个题单', action: () => patch({ folder: [...state.folder, id] }) }));
  if (!active && state.mode === 'algorithm') folderRows.sort((a, b) => compareCategoryNames(a.title, b.title, state.folder[0]));
  const listEntries = active ? children : entries;
  const browsingFolders=!!active&&!showAll&&(folderRows.length>0||listEntries.length>0);
  const cards=listEntries.some(leaf);
  const size=cards?24:rowSize;
  const count = active&&!browsingFolders ? problems.length : folderRows.length + listEntries.length + (browsingFolders?1:0);
  const pages = Math.max(1, Math.ceil(count / size)), page = Math.min(state.page, pages), start = (page - 1) * size;
  const directoryEntries = [...(browsingFolders?[{all:true}]:[]),...folderRows.map(folder => ({ folder })), ...listEntries.map(list => ({ list }))];
  const displayedEntries = directoryEntries.slice(start, start + size);
  const likeIds=JSON.stringify(displayedEntries.filter(({list})=>leaf(list)&&!list.custom).map(({list})=>list.id).sort());
  useEffect(()=>{
    let alive=true,pending=false;
    const ids=JSON.parse(likeIds);if(!ids.length)return;
    async function refresh(){if(pending||document.hidden)return;pending=true;
      try{const value=await api('training-list-likes?'+new URLSearchParams(ids.map(id=>['id',id])));if(alive)setHearts(value);}
      catch{if(alive)setHearts({likes:{}});}finally{pending=false;}
    }
    refresh();const timer=setInterval(refresh,30000);
    window.addEventListener('focus',refresh);document.addEventListener('visibilitychange',refresh);
    return()=>{alive=false;clearInterval(timer);window.removeEventListener('focus',refresh);document.removeEventListener('visibilitychange',refresh);};
  },[api,likeIds,owner]);
  const problemIds = problems.filter(item => item.row).map(item => item.row.id);
  const title = active?.displayTitle || (state.mode === 'source' ? index.categories.find(c => c.id === state.folder.at(-1))?.name : state.folder.at(-1)) || '题单';
  const clear = () => patch({ query: '', status: '' });
  function confirmDelete(event,list){
    event.preventDefault();event.stopPropagation();if(deleting)return;
    setDeleteError('');setDeletion({list,anchor:event.currentTarget});
  }
  async function deleteList(){
    if(!deletion||deleting)return;
    setDeleting(true);setDeleteError('');
    try{
      const value=await api('training-lists/save',{id:deletion.list.id,deleted:true});
      contentVersion.current++;
      setLists(previous=>[...(previous||[]).filter(list=>!list.custom),...value.customLists]);
      if(state.trail.includes(deletion.list.id))patch({trail:[],sections:[],flat:false});
      setDeletion(null);
    }catch(issue){setDeleteError(issue.message||'删除失败');}finally{setDeleting(false);}
  }

  return <section className="list-page training-lists-page" aria-label="题单训练">
    <PageSearch>
      <label className="search-box"><Search size={17}/><input aria-label="搜索题单或题目" value={state.query} maxLength={120} onChange={event => patch({ query: event.target.value })}/>{state.query && <button className="icon-button" aria-label="清空题单搜索" onClick={() => patch({ query: '' })}><X size={14}/></button>}</label>
      {active&&!active.custom&&!browsingFolders&&<SortDirection label="切换题单难度排序方向" descending={state.descending} onChange={descending=>patch({descending})}/>}
      <button type="button" className="icon-button training-list-mode" aria-label="题单目录方式" data-mode={state.mode} title={state.mode === 'source' ? '点击切换为按类别' : '点击切换为按来源'} onClick={() => patch({ ...INITIAL, mode: state.mode === 'source' ? 'algorithm' : 'source' })}><ArrowLeftRight size={16}/></button>
      <button type="button" className="icon-button" aria-label="新建题单" title="新建题单" onClick={()=>setEditor({})}><Plus size={16}/></button>
    </PageSearch>
    <div className="training-list-directory"><nav className="catalog-path training-list-path" aria-label="题单浏览路径">
      <button type="button" data-folder-up aria-label="返回上一级文件夹" title="返回上一级 · Backspace" disabled={!canBack} onClick={back}><ChevronLeft size={17}/></button>
      <button aria-label="全部题单" onClick={() => patch({ folder: [], trail: [], sections: [], flat: false, query: '' })}><House size={16}/></button>
      {state.folder.map((part, i) => <span key={part}><ChevronRight size={13}/><button onClick={() => patch({ folder: state.folder.slice(0, i + 1), trail: [], sections: [], flat: false, query: '' })}>{state.mode === 'source' ? index.categories.find(c => c.id === part)?.name || part : part}</button></span>)}
      {state.trail.map((id, i) => <span key={id}><ChevronRight size={13}/><button onClick={() => patch({ trail: state.trail.slice(0, i + 1), sections: [], flat: false, query: '' })}>{index.byList.get(id)?.displayTitle || '题单'}</button></span>)}
      {state.sections.map((part, i) => <span key={i}><ChevronRight size={13}/><button onClick={() => patch({ sections: state.sections.slice(0, i + 1), flat: false })}>{part}</button></span>)}
      {state.flat && <span aria-current="page">全部题目</span>}
    </nav>
    {active?.custom&&<div className="training-list-tools"><button type="button" className="icon-button" aria-label="编辑题单" title="编辑题单" onClick={()=>setEditor({...active,problems:index.own.get(active.id)})}><Pencil size={15}/></button><button type="button" className="icon-button" aria-label="删除题单" title="删除题单" onClick={event=>confirmDelete(event,active)}><Trash2 size={15}/></button></div>}
    <div className="training-list-summary"><span className="training-list-stats">{active ? `${listStats.accepted} / ${listStats.total} 题已通过` : `${scopeLists.length} 个题单${readableLists < scopeLists.length ? `（${readableLists} 个可读取）` : ''} · ${listStats.total} 道题 · ${listStats.accepted} 题已通过`}</span>{state.mode==='source'&&!active?.custom&&<a className="icon-button training-list-source" aria-label="洛谷原题单" href={active?.url || source} target="_blank" rel="noreferrer"><ExternalLink size={15}/></a>}</div></div>
    {error && <p role="alert" className="connection-error">{error} <button className="icon-button" aria-label="重新读取" onClick={() => setAttempt(value => value + 1)}><RotateCw size={16}/></button></p>}
    <div className="catalog-explorer training-list-content" ref={panel} onScroll={event => { session.scrollTop = event.currentTarget.scrollTop; }} aria-busy={!lists && !error}>
      {!lists && !error && <p className="progress-muted" role="status">正在读取题单…</p>}
      {active && !active.available && <p role="status" className="progress-muted">原站题单暂不可读取，可从右上角前往洛谷查看。</p>}
      <div className={cards?'training-list-card-grid':'training-list-folders'}>{displayedEntries.map(({ folder, list, all:allEntry }) => {
        if(allEntry)return <button key="all" className="catalog-folder-row" onClick={() => patch({ flat: true, sections: [] })}><FileText size={20}/><strong>全部题目</strong><span>{all.length} 题</span><ChevronRight size={16}/></button>;
        const stats = list ? index.stats([list.id]) : folder?.stats;
        if(leaf(list))return <article className="training-list-card" key={list.id} data-list-id={list.id} onContextMenu={list.custom?event=>confirmDelete(event,list):undefined}>
          <button className="training-card-open" onClick={()=>open(list)} aria-label={`打开题单：${cardTitle(list)}`}><div><strong>{cardTitle(list)}</strong></div><span className="training-card-progress" aria-label={`已通过 ${stats.accepted} / ${stats.total} 题`}><svg viewBox="0 0 64 64" aria-hidden="true"><circle cx="32" cy="32" r="28"/><circle cx="32" cy="32" r="28" pathLength="100" strokeDasharray={`${stats.total?stats.accepted/stats.total*100:0} 100`}/></svg><b>{stats.accepted}<small> / {stats.total}</small></b></span></button>
          <div className="training-card-actions">{list.custom?<button type="button" className="icon-button" aria-label={`删除题单：${list.title}`} title="删除题单" onClick={event=>confirmDelete(event,list)}><Trash2 size={16}/></button>:<>{hearts.available&&hearts.likes?.[list.id]?<LikeBurst key={`${owner}:${list.id}:${hearts.day}`} targetId={list.id} nickname={cardTitle(list)} likes={hearts.likes[list.id]} eventName="tb:training-list-like" api={(_,body)=>api('training-list-likes',{listId:body.targetId})} onLiked={result=>setHearts(previous=>({...previous,likes:{...previous.likes,[list.id]:result.likes}}))} onError={setError}/>:<button className="like-burst" disabled aria-label="题单点赞暂不可用"><Heart size={19}/><span>—</span></button>}</>}</div>
        </article>;
        return <button className="catalog-folder-row" key={folder ? 'folder:' + folder.id : list.id} onClick={folder ? folder.action : () => open(list)}>
          <Folder size={20}/><strong title={list?.originalTitle}>{folder?.title || list.displayTitle}{list && (list.sourceLabel || search) && <small>{[list.sourceLabel,search ? list.topicPath.join(' / ') : ''].filter(Boolean).join(' · ')}</small>}</strong>
          {stats&&<span className="training-folder-progress" role="progressbar" aria-label={`${folder?.title||list.displayTitle} 已 AC / 总题数`} aria-valuemin={0} aria-valuemax={Math.max(1,stats.total)} aria-valuenow={stats.accepted} aria-valuetext={`${stats.accepted} / ${stats.total}`}><span className="training-folder-progress-track"><span style={{width:`${stats.total?stats.accepted/stats.total*100:0}%`}}/></span><span className="training-folder-progress-count">{stats.accepted} / {stats.total}</span></span>}
          <span>{folder ? `${folder.count} ${folder.unit || '题'}` : list.available ? `${stats.accepted} / ${stats.total} 题` : '暂不可用'}</span><ChevronRight size={16}/>
        </button>;
      })}</div>
      {active && !browsingFolders && problems.length > 0 && <table className="problem-table training-list-table"><ProblemTableHead onSort={active.custom?undefined:()=>patch({descending:!state.descending})} sorted={!active.custom} descending={state.descending}/><tbody>{problems.slice(start, start + size).map((item, offset) => <tr key={item.row?.id || item.pid} data-id={item.row?.id} className="training-problem-row" tabIndex={item.row&&!busy?0:undefined} aria-label={item.row?`进入题目：${item.row.title}`:undefined} onKeyDown={event=>{if(event.target===event.currentTarget && item.row&&!busy&&['Enter',' '].includes(event.key)){event.preventDefault();onTrain(item.row.id,{problemIds});}}} aria-disabled={!item.row||busy} onClick={event=>{if(item.row&&!busy&&!event.target.closest('button,a,input,select'))onTrain(item.row.id,{problemIds});}}>
        <ProblemCells row={item.row||{title:item.pid,problem:item.pid,platform:'洛谷',tags:[]}} favorites={prefs.favorites} showPlatforms={prefs.showPlatforms!==false} busy={busy} onTrain={id=>onTrain(id,{problemIds})} onTag={onTag} onFavorite={onFavorite} onSolution={onSolution} onAddToList={onAddToList} onRemove={onRemove}/>
      </tr>)}</tbody></table>}
      {lists && !displayedEntries.length && !problems.length && <div className="empty"><Search size={26}/><h3>{searchingProblems ? '没有匹配的题单或题目' : active ? '此目录暂无可用题目' : '暂无题单'}</h3>{searchingProblems && <button className="icon-button" aria-label="清除筛选" onClick={clear}><X size={16}/></button>}</div>}
    </div>
    {lists && count > 0 && <PagePagination label="题单分页" count={active?`${problems.length} 道题`:`${count} 项`} page={page} pages={pages} previousLabel="题单上一页" nextLabel="题单下一页" onPrevious={()=>patch({page:page-1})} onNext={()=>patch({page:page+1})}/>}
    {deletion&&<PopConfirm anchor={deletion.anchor} title={`删除题单“${deletion.list.title}”？`} label="删除题单确认" busy={deleting} error={deleteError} cancelLabel={<X size={16}/>} cancelAriaLabel="取消" confirmLabel={<Trash2 size={16}/>} confirmAriaLabel="确认删除" busyLabel={<Trash2 size={16}/>} onCancel={()=>setDeletion(null)} onConfirm={deleteList}/>}
    {editor&&<TrainingListEditor list={editor.id?editor:null} rows={rows} api={api} onClose={()=>setEditor(null)} onSave={value=>{contentVersion.current++;setLists(previous=>[...(previous||[]).filter(list=>!list.custom),...value.customLists]);setEditor(null);patch({folder:state.mode==='source'?['personal']:['我的题单'],trail:[value.list.id],sections:[],flat:false,query:''});}}/>}
  </section>;
}
