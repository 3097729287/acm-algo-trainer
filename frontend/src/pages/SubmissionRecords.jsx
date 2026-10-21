import PageSearch from '@/components/PageSearch.jsx';
import FilterMenu from '@/components/FilterMenu.jsx';
import PopConfirm from '@/components/PopConfirm.jsx';
import ThemedSelect from '@/components/ThemedSelect.jsx';
import SortDirection from '@/components/SortDirection.jsx';
import { useState } from 'react';
import InlineTitle from '@/components/InlineTitle.jsx';
import { ChevronRight, Code2, Flag, Search, Trash2 } from 'lucide-react';
import { groupSubmissionsByDay, verdictLabel, verdictTone } from '@/models/workspaceModel.js';
import { trainingDateLabel, trainingTime } from '@/lib/trainingDate.js';

const dateText = value => value ? new Date(value).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) : '—';
export default function SubmissionRecords({ submissions = [], total = submissions.length, hasMore = false, loading = false, onLoadMore, rows, onSelect }) {
  const [query, setQuery] = useState(''), [result, setResult] = useState(''),[descending,setDescending]=useState(true);
  const rowMap = new Map(rows.map(row => [row.id, row]));
  const logs = submissions.filter(submission => {
    if (submission.mode === 'run' || submission.verdict === 'SAMPLE_PASS') return false;
    const row = rowMap.get(submission.problemId);
    return (!result || submission.verdict === result) && `${row?.title || submission.problemId} ${row?.contest || ''} ${verdictLabel(submission.verdict)}`.toLowerCase().includes(query.trim().toLowerCase());
  });
  const grouped = groupSubmissionsByDay(logs);
  const days = descending?grouped:[...grouped].reverse().map(day=>({...day,submissions:[...day.submissions].reverse()}));
  return <div className="records-page" data-noselect="true">
    <PageSearch><label className="search-box"><Search size={17}/><input aria-label="搜索历史提交" value={query} onChange={event=>setQuery(event.target.value)}/></label><FilterMenu label="筛选提交" active={!!result}><label className="filter-field"><span>结果</span><ThemedSelect aria-label="历史提交结果" value={result} onChange={event=>setResult(event.target.value)}><option value="">全部结果</option>{['AC','WA','CE','TLE','MLE','RE','OLE','ERROR'].map(value=><option key={value} value={value}>{verdictLabel(value)}</option>)}</ThemedSelect></label><span className="filter-result-count">{logs.length} 条</span></FilterMenu><SortDirection label="切换提交排序方向" descending={descending} onChange={setDescending}/></PageSearch>
    <div className="submission-log scroll-panel">
      {days.map(group => <section className="submission-day" key={group.day} data-day={group.day} aria-label={`${trainingDateLabel(group.day)}提交`}>
        <header className="submission-day-heading">
          <h2><time dateTime={group.day || undefined}>{trainingDateLabel(group.day)}</time></h2>
        </header>
        {group.submissions.map(submission => {
          const row = rowMap.get(submission.problemId);
          return <button className="submission-log-row" key={submission.id} onClick={() => onSelect({ ...submission, title: row?.title || submission.problemId, contestName: row?.contest })}>
            <span><strong><InlineTitle>{row?.title || submission.problemId}</InlineTitle></strong><small>{trainingTime(submission.submittedAt)}{row?.contest ? ` · ${row.contest}` : ''}</small></span>
            <span className={'verdict ' + verdictTone(submission.verdict)}><span />{verdictLabel(submission.verdict)}</span>
            {submission.timeMs != null && <span className="submission-runtime">{submission.timeMs} ms</span>}
          </button>;
        })}
      </section>)}
      {!logs.length && !loading && <div className="empty"><Code2 size={26} /><h2>{submissions.length ? '没有匹配的提交' : '还没有提交记录'}</h2><p>{submissions.length ? '试试调整搜索或结果筛选。' : '写好代码后提交，每次结果与代码都会保存在这里。'}</p></div>}
      {(hasMore || loading) && <div className="submission-pagination"><span>{hasMore ? '搜索、筛选与每日统计针对已读取的记录；加载更早提交可补全当天和此前的记录。' : '正在读取提交记录…'}</span>{hasMore && <button className="secondary" onClick={onLoadMore} disabled={loading}>{loading ? '正在读取…' : '加载更早提交'}</button>}</div>}
    </div>
  </div>;
}

export function MockHistory({contests=[],onSelect,onResume,onCreate,onDelete,embedded=false}) {
 const [target,setTarget]=useState(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const finished=contests.filter(item=>item.status!=='running');
 const sorted=[...contests].sort((a,b)=>(Date.parse(b.startedAt)||0)-(Date.parse(a.startedAt)||0));
 async function remove(){if(busy)return;setBusy(true);setError('');try{await onDelete(target.value==='all'?{all:true}:{id:target.value.id});setTarget(null);}catch(issue){setError(issue.message||'删除失败');}finally{setBusy(false);}}
 return <section className={`records-page${embedded?' mock-history':''}`} aria-label="模拟赛记录" data-noselect="true"><header className="table-toolbar"><h2 id="mock-history-heading" tabIndex={-1}>模拟赛记录 <small>{contests.length} 场</small></h2><button type="button" className="icon-button" aria-label="删除全部记录" disabled={!finished.length||busy} onClick={event=>setTarget({value:'all',anchor:event.currentTarget})}><Trash2 size={17}/></button></header>
 {target&&<PopConfirm anchor={target.anchor} title={target.value==='all'?`删除全部 ${finished.length} 场记录？`:`删除“${target.value.name}”？`} error={error} busy={busy} onCancel={()=>setTarget(null)} onConfirm={remove}/>}
 <div className="records-list scroll-panel">{sorted.map(contest=><div className="mock-record" key={contest.id}><button type="button" className="record-row" onClick={()=>contest.status==='running'?onResume(contest):onSelect(contest)}><span className="record-symbol"><Flag size={21}/></span><div><strong>{contest.name}</strong><small>{dateText(contest.startedAt)} · {contest.duration} 分钟 · {contest.total} 题</small></div><span className="record-score">{contest.accepted}<small> / {contest.total}</small></span><ChevronRight size={18}/></button><button type="button" className="mock-record-delete icon-button" aria-label={`删除模拟赛 ${contest.name}`} disabled={contest.status==='running'||busy} onClick={event=>setTarget({value:contest,anchor:event.currentTarget})}><Trash2 size={17}/></button></div>)}{!contests.length&&<div className="empty"><Flag size={27}/>{embedded?<p>完成训练后，记录会显示在这里。</p>:<button className="primary" onClick={onCreate}>创建模拟赛</button>}</div>}</div></section>;
}
