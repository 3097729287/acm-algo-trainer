import {useFittedPageSize} from '@/lib/useFittedPageSize.js';
import { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import { ArrowLeftRight, ChevronLeft, ChevronRight, ExternalLink, FileText, Folder, House, Search, X } from 'lucide-react';
import PageSearch from '@/components/PageSearch.jsx';
import InlineTitle from '@/components/InlineTitle.jsx';
import { difficultyBand, difficultyDescription, difficultyLabel } from '@/lib/practiceMetadata.js';
import { matchesTrainingProblem, startsWithPath, trainingIndex } from '@/lib/trainingLists.js';
import { organizeTrainingLists, compareTrainingLists, compareCategoryNames } from '@/lib/trainingListCatalog.js';
import '@/components/CatalogExplorer.css';
import './TrainingListsPage.css';

const INITIAL = { mode: 'algorithm', folder: [], trail: [], sections: [], flat: false, query: '', status: '', page: 1 };
const source = 'https://www.luogu.com.cn/training/list';

export default function TrainingListsPage({ api, rows = [], onTrain, visit, pageSize = 50, busy = false }) {
  const fallback = useRef({}), session = visit || fallback.current;
  const [state, setState] = useState(() => ({ ...INITIAL, ...session.state, status: '' }));
  const [lists, setLists] = useState(session.lists || null), [error, setError] = useState(''), [attempt, setAttempt] = useState(0);
  const panel = useRef(null), navigation = useRef(null);
  const patch = value => setState(previous => ({ ...previous, page: 1, ...value }));
  useEffect(() => {
    let alive = true;
    if (session.lists && !attempt) return;
    setError('');
    api('training-lists').then(value => {
      if (alive) { session.lists = value.lists; setLists(value.lists); }
    }).catch(issue => { if (alive) setError(issue.message || '题单读取失败'); });
    return () => { alive = false; };
  }, [api, attempt]);
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
      if (event.key !== 'Escape' || event.defaultPrevented || !canBack || event.target.closest?.('input,textarea,select,[contenteditable=true]') || document.querySelector('.tb-select-menu,dialog[open]')) return;
      event.preventDefault(); back();
    };
    window.addEventListener('keydown', key);
    return () => window.removeEventListener('keydown', key);
  }, [state, canBack]);

  const organized = useMemo(() => organizeTrainingLists(lists || []), [lists]);
  const index = useMemo(() => trainingIndex(organized, rows), [organized, rows]);
  const active = index.byList.get(state.trail.at(-1));
  const search = state.query.trim().toLocaleLowerCase();
  const size=useFittedPageSize(panel,`${state.mode}:${state.trail.join('/')}:${state.folder.join('/')}:${Boolean(lists)}`,'.training-list-table tbody tr, .catalog-folder-row');
  const all = active ? index.all(active.id) : [];
  const own = active ? index.own.get(active.id) || [] : [];
  const scoped = own.filter(item => startsWithPath(item.sections || [], state.sections));
  const sectionNames = [...new Set(scoped.map(item => item.sections?.[state.sections.length]).filter(Boolean))];
  const searchingProblems = Boolean(search || state.status);
  const showAll = state.flat || searchingProblems;
  const problems = (showAll ? state.sections.length ? scoped : all : scoped.filter(item => (item.sections || []).length === state.sections.length)).filter(item => matchesTrainingProblem(item, state.query, state.status));

  const folders = new Map(), entries = [];
  let scopeLists = organized;
  if (!active) {
    const base = organized.filter(list => state.mode !== 'source' || (list.categories || []).some(category => !state.folder.length || category.id === state.folder[0]));
    const selected = base.filter(list => state.mode !== 'algorithm' || startsWithPath(list.topicPath, state.folder));
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
  const open = list => patch({ trail: [...state.trail, list.id], sections: [], flat: false, query: '' });
  const listStats = index.stats(active ? [active.id] : scopeLists.map(list => list.id));
  const readableLists = scopeLists.filter(list => list.available).length;
  const children = active && !showAll && !state.sections.length ? (active.children || []).filter(id => !state.trail.includes(id)).map(id => index.byList.get(id)).filter(Boolean) : [];
  const folderRows = active ? (showAll ? [] : sectionNames.map(name => ({ id: name, title: name, count: scoped.filter(item => item.sections?.[state.sections.length] === name).length, action: () => patch({ sections: [...state.sections, name] }) }))) : [...folders].map(([id, ids]) => ({ id, title: state.mode === 'source' ? index.categories.find(c => c.id === id)?.name || id : id, count: ids.length, unit: '个题单', action: () => patch({ folder: [...state.folder, id] }) }));
  if (!active && state.mode === 'algorithm') folderRows.sort((a, b) => compareCategoryNames(a.title, b.title, state.folder[0]));
  const listEntries = active ? children : entries;
  const browsingFolders=!!active&&!showAll&&(folderRows.length>0||listEntries.length>0);
  const count = active&&!browsingFolders ? problems.length : folderRows.length + listEntries.length + (browsingFolders?1:0);
  const pages = Math.max(1, Math.ceil(count / size)), page = Math.min(state.page, pages), start = (page - 1) * size;
  const directoryEntries = [...(browsingFolders?[{all:true}]:[]),...folderRows.map(folder => ({ folder })), ...listEntries.map(list => ({ list }))];
  const displayedEntries = directoryEntries.slice(start, start + size);
  const problemIds = problems.filter(item => item.row).map(item => item.row.id);
  const title = active?.displayTitle || (state.mode === 'source' ? index.categories.find(c => c.id === state.folder.at(-1))?.name : state.folder.at(-1)) || '题单';
  const clear = () => patch({ query: '', status: '' });

  return <section className="training-lists-page" aria-label="题单训练">
    <PageSearch>
      <label className="search-box"><Search size={17}/><input aria-label="搜索题单或题目" value={state.query} maxLength={120} onChange={event => patch({ query: event.target.value })}/>{state.query && <button className="icon-button" aria-label="清空题单搜索" onClick={() => patch({ query: '' })}><X size={14}/></button>}</label>
      <button type="button" className="training-list-mode" aria-label="题单目录方式" data-mode={state.mode} title={state.mode === 'source' ? '点击切换为按类别' : '点击切换为按来源'} onClick={() => patch({ ...INITIAL, mode: state.mode === 'source' ? 'algorithm' : 'source' })}><ArrowLeftRight size={16}/>{state.mode === 'source' ? '按来源' : '按类别'}</button>
    </PageSearch>
    <div className="training-list-directory"><nav className="catalog-path training-list-path" aria-label="题单浏览路径">
      <button aria-label="全部题单" onClick={() => patch({ folder: [], trail: [], sections: [], flat: false, query: '' })}><House size={16}/></button>
      {state.folder.map((part, i) => <span key={part}><ChevronRight size={13}/><button onClick={() => patch({ folder: state.folder.slice(0, i + 1), trail: [], sections: [], flat: false, query: '' })}>{state.mode === 'source' ? index.categories.find(c => c.id === part)?.name || part : part}</button></span>)}
      {state.trail.map((id, i) => <span key={id}><ChevronRight size={13}/><button onClick={() => patch({ trail: state.trail.slice(0, i + 1), sections: [], flat: false, query: '' })}>{index.byList.get(id)?.displayTitle || '题单'}</button></span>)}
      {state.sections.map((part, i) => <span key={i}><ChevronRight size={13}/><button onClick={() => patch({ sections: state.sections.slice(0, i + 1), flat: false })}>{part}</button></span>)}
      {state.flat && <span aria-current="page">全部题目</span>}
    </nav>
    <div className="training-list-summary"><span className="training-list-stats">{active ? `${listStats.accepted} / ${listStats.total} 题已通过` : `${scopeLists.length} 个题单${readableLists < scopeLists.length ? `（${readableLists} 个可读取）` : ''} · ${listStats.total} 道题 · ${listStats.accepted} 题已通过`}</span><a className="text-button training-list-source" href={active?.url || source} target="_blank" rel="noreferrer"><ExternalLink size={15}/><span>洛谷原题单</span></a></div></div>
    {error && <p role="alert" className="connection-error">{error} <button className="text-button" onClick={() => setAttempt(value => value + 1)}>重新读取</button></p>}
    <div className="catalog-explorer training-list-content" ref={panel} onScroll={event => { session.scrollTop = event.currentTarget.scrollTop; }} aria-busy={!lists && !error}>
      {!lists && !error && <p className="progress-muted" role="status">正在读取题单…</p>}
      {active && !active.available && <p role="status" className="progress-muted">原站题单暂不可读取，可从右上角前往洛谷查看。</p>}
      {displayedEntries.map(({ folder, list, all:allEntry }) => {
        if(allEntry)return <button key="all" className="catalog-folder-row" onClick={() => patch({ flat: true, sections: [] })}><FileText size={20}/><strong>全部题目</strong><span>{all.length} 题</span><ChevronRight size={16}/></button>;
        const stats = list ? index.stats([list.id]) : null;
        return <button className="catalog-folder-row" key={folder ? 'folder:' + folder.id : list.id} onClick={folder ? folder.action : () => open(list)}>
          <Folder size={20}/><strong title={list?.originalTitle}>{folder?.title || list.displayTitle}{list && <small>{list.sourceLabel}{search ? ` · ${list.topicPath.join(' / ')}` : ''}</small>}</strong>
          <span>{folder ? `${folder.count} ${folder.unit || '题'}` : list.available ? `${stats.accepted} / ${stats.total} 题` : '暂不可用'}</span><ChevronRight size={16}/>
        </button>;
      })}
      {active && !browsingFolders && problems.length > 0 && <table className="problem-table training-list-table"><thead><tr><th>题目</th><th>难度</th><th>训练状态</th></tr></thead><tbody>{problems.slice(start, start + size).map((item, offset) => <tr key={item.row?.id || item.pid} data-id={item.row?.id}>
        <td><div className="training-list-title"><span className="training-list-number">{start + offset + 1}</span><div><button className="problem-title" disabled={!item.row || busy} onClick={() => onTrain(item.row.id, { problemIds })}><InlineTitle>{item.row?.title || item.pid}</InlineTitle></button><small>{item.pid}{item.row?.platform && item.row.platform !== '洛谷' ? ` · ${item.row.platform}` : ''}</small></div></div></td>
        <td><span className={'difficulty band-' + difficultyBand(item.row?.difficultyHidden ? null : item.row?.difficulty)} title={item.row ? difficultyDescription(item.row) : ''}>{item.row ? difficultyLabel(item.row) : '—'}</span></td>
        <td><span className={'verdict ' + (item.row?.accepted ? 'success' : item.row?.active ? 'pending' : '')}>{!item.row ? '暂不可用' : item.row.accepted ? '已通过' : item.row.active ? '练习中' : '未开始'}</span></td>
      </tr>)}</tbody></table>}
      {lists && !displayedEntries.length && !problems.length && <div className="empty"><Search size={26}/><h3>{searchingProblems ? '没有匹配的题单或题目' : active ? '此目录暂无可用题目' : '暂无题单'}</h3>{searchingProblems && <button className="secondary" onClick={clear}>清除筛选</button>}</div>}
    </div>
    {lists && count > 0 && <nav className="library-pagination" aria-label="题单分页"><span>{active ? `${problems.length} 道题` : `${count} 项`}</span><div className="pagination-actions"><button aria-label="题单上一页" disabled={page <= 1} onClick={() => patch({ page: page - 1 })}><ChevronLeft size={15}/>上一页</button><span>第 {page} / {pages} 页</span><button aria-label="题单下一页" disabled={page >= pages} onClick={() => patch({ page: page + 1 })}>下一页<ChevronRight size={15}/></button></div></nav>}
  </section>;
}
