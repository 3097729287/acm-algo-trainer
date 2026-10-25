import PagePagination from '@/components/PagePagination.jsx';
import PageSearch from '@/components/PageSearch.jsx';
import FolderSelect from '@/components/FolderSelect.jsx';
import PopConfirm from '@/components/PopConfirm.jsx';
import SortDirection from '@/components/SortDirection.jsx';
import {useEffect,useLayoutEffect,useMemo,useRef,useState} from 'react';
import InlineTitle from '@/components/InlineTitle.jsx';
import {ChevronLeft,ChevronRight,Code2,Flag,Search,Trash2} from 'lucide-react';
import {groupSubmissionsByDay,verdictLabel,verdictTone} from '@/models/workspaceModel.js';
import {trainingDateLabel,trainingTime} from '@/lib/trainingDate.js';

const dateText=value=>value?new Date(value).toLocaleString('zh-CN',{month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'}):'—';
const RESULT_OPTIONS=['AC','WA','CE','TLE','MLE','RE','OLE','ERROR','QUEUED','RUNNING'].map(value=>({value,label:verdictLabel(value)}));
export default function SubmissionRecords({api,revision,rows=[],onSelect,onOpenProblem}) {
 const [query,setQuery]=useState(''),[search,setSearch]=useState(''),[result,setResult]=useState(''),[descending,setDescending]=useState(true);
 const [offsets,setOffsets]=useState([0]),[visibleCount,setVisibleCount]=useState(1),[snapshot,setSnapshot]=useState(null),[loading,setLoading]=useState(true),[error,setError]=useState(''),[attempt,setAttempt]=useState(0);
 const requestId=useRef(0),panel=useRef(null);
 const offset=offsets.at(-1),page=offsets.length;
 const setPage=()=>setOffsets([0]);
 const requestKey=new URLSearchParams({resultsOnly:'1',limit:'100',offset:String(offset),q:search,verdict:result,order:descending?'desc':'asc'}).toString();
 const pending=loading||!error&&snapshot?.requestKey!==requestKey;
 useEffect(()=>{if(query===search)return;const timer=setTimeout(()=>{setSearch(query);setPage(1);},200);return()=>clearTimeout(timer);},[query,search]);
 useEffect(()=>{
  const seq=++requestId.current;
  setLoading(true);setError('');
  api('submissions?'+requestKey).then(value=>{if(seq!==requestId.current)return;setSnapshot({...value,requestKey});if(offset>=value.total&&offset>0)setOffsets([0]);}).catch(issue=>{if(seq===requestId.current)setError(issue.message||'读取提交记录失败');}).finally(()=>{if(seq===requestId.current)setLoading(false);});
  return()=>{requestId.current++;};
 },[api,revision,offset,search,result,descending,attempt]);
 const rowMap=useMemo(()=>{const map=new Map();for(const row of rows)for(const id of [row.id,...row.aliasIds||[]])map.set(id,row);return map;},[rows]);
 const logs=snapshot?.submissions||[],grouped=groupSubmissionsByDay(logs);
 const days=descending?grouped:[...grouped].reverse().map(group=>({...group,submissions:[...group.submissions].reverse()}));
 const total=snapshot?.total||0;
 const positions=new Map(days.flatMap(group=>group.submissions).map((row,i)=>[row.id,i]));
 useLayoutEffect(()=>{
  const node=panel.current;if(!node)return;let frame;
  const measure=()=>{cancelAnimationFrame(frame);frame=requestAnimationFrame(()=>{
   const bottom=node.getBoundingClientRect().bottom;
   const fitted=[...node.querySelectorAll('.submission-log-row')].filter(row=>row.getBoundingClientRect().bottom<=bottom+.5).length;
   setVisibleCount(Math.max(1,fitted));
  });};
  const observer=new ResizeObserver(measure);observer.observe(node);node.querySelectorAll('.submission-log-row').forEach(row=>observer.observe(row));measure();
  return()=>{cancelAnimationFrame(frame);observer.disconnect();};
 },[snapshot,descending]);
 const shown=Math.min(visibleCount,logs.length);

 return <div className="records-page records-paged" data-noselect="true">
  <PageSearch><label className="search-box"><Search size={17}/><input aria-label="搜索历史提交" maxLength={120} value={query} onChange={event=>setQuery(event.target.value)}/></label><SortDirection label="切换提交排序方向" descending={descending} normalDescending onChange={value=>{setDescending(value);setPage(1);}}/><FolderSelect iconOnly label="提交结果分类" placeholder="全部结果" options={RESULT_OPTIONS} value={result} onChange={event=>{setResult(event.target.value);setPage(1);}}/></PageSearch>
  {error&&<p role="alert" className="connection-error">{error} <button type="button" className="text-button" onClick={()=>setAttempt(value=>value+1)}>重新读取</button></p>}
  <div ref={panel} className="submission-log scroll-panel submission-fitted" aria-busy={pending} data-offset={snapshot?.offset??0}>
   {days.map(group=><section className="submission-day" key={group.day} data-day={group.day} style={positions.get(group.submissions[0]?.id)>=visibleCount?{visibility:'hidden'}:undefined} aria-hidden={positions.get(group.submissions[0]?.id)>=visibleCount||undefined} aria-label={`${trainingDateLabel(group.day)}提交`}>
    <header className="submission-day-heading"><h2><time dateTime={group.day||undefined}>{trainingDateLabel(group.day)}</time></h2></header>
    {group.submissions.map(submission=>{
     const row=rowMap.get(submission.problemId);
     const openProblem=()=>onOpenProblem?.(row?.id||submission.canonicalProblemId||submission.problemId);
     return <div className="submission-log-row" key={submission.id} style={positions.get(submission.id)>=visibleCount?{visibility:'hidden'}:undefined} aria-hidden={positions.get(submission.id)>=visibleCount||undefined} inert={positions.get(submission.id)>=visibleCount} onClick={openProblem}>
      <button type="button" className="submission-problem-link" onClick={event=>{event.stopPropagation();openProblem();}}><strong><InlineTitle>{row?.title||submission.title||submission.problemId}</InlineTitle></strong><small className="submission-record-meta"><time dateTime={submission.submittedAt}>{trainingTime(submission.submittedAt)}</time>{(row?.problem||submission.problem)&&<><span aria-hidden="true">·</span><b className="submission-problem-index">{row?.problem||submission.problem}</b></>}{(row?.contest||submission.contestName)&&<><span aria-hidden="true">·</span><span className="submission-contest-name">{row?.contest||submission.contestName}</span></>}</small></button>
      <div className="submission-record-actions"><button type="button" className="icon-button submission-code-button" aria-label="查看提交代码" title="查看本次提交代码" onClick={event=>{event.stopPropagation();onSelect({...submission,title:row?.title||submission.title||submission.problemId,contestName:row?.contest});}}><Code2 size={18}/></button><span className={'verdict '+verdictTone(submission.verdict)}><span/>{verdictLabel(submission.verdict)}</span>{submission.timeMs!=null&&<span className="submission-runtime">{submission.timeMs} ms</span>}</div>
     </div>;
    })}
   </section>)}
   {!logs.length&&!loading&&<div className="empty"><Code2 size={26}/><h2>{search||result?'没有匹配的提交':'还没有提交记录'}</h2></div>}
   {loading&&!snapshot&&<p role="status" className="progress-muted">正在读取提交记录…</p>}
  </div>
  <PagePagination label="提交记录分页" count={`共 ${total} 条`} page={page} previousLabel="上一页提交" nextLabel="下一页提交" previousDisabled={pending} nextDisabled={pending||offset+shown>=total||!shown} onPrevious={()=>setOffsets(value=>value.slice(0,-1))} onNext={()=>setOffsets(value=>[...value,offset+shown])}/>
 </div>;
}

export function MockHistory({contests=[],onSelect,onResume,onCreate,onDelete,embedded=false,query=''}) {
 const [target,setTarget]=useState(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const finished=contests.filter(item=>item.status!=='running');
 const tokens=query.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
 const matches=contests.filter(contest=>tokens.every(token=>`${contest.name} ${dateText(contest.startedAt)} ${contest.status==='running'?'进行中':'已结束'} ${(contest.slots||[]).map(slot=>slot.title||'').join(' ')}`.toLocaleLowerCase().includes(token)));
 const sorted=[...matches].sort((a,b)=>(Date.parse(b.startedAt)||0)-(Date.parse(a.startedAt)||0));
 async function remove(){if(busy)return;setBusy(true);setError('');try{await onDelete(target.value==='all'?{all:true}:{id:target.value.id});setTarget(null);}catch(issue){setError(issue.message||'删除失败');}finally{setBusy(false);}}
 return <section className={`records-page${embedded?' mock-history':''}`} aria-label="模拟赛记录" data-noselect="true"><header className="table-toolbar"><h2 id="mock-history-heading" tabIndex={-1}>模拟赛记录 <small>{query.trim()?`${matches.length} / ${contests.length}`:contests.length} 场</small></h2><button type="button" className="icon-button" aria-label="删除全部记录" disabled={!finished.length||busy} onClick={event=>setTarget({value:'all',anchor:event.currentTarget})}><Trash2 size={17}/></button></header>
 {target&&<PopConfirm anchor={target.anchor} title={target.value==='all'?`删除全部 ${finished.length} 场记录？`:`删除“${target.value.name}”？`} error={error} busy={busy} onCancel={()=>setTarget(null)} onConfirm={remove}/>}
 <div className="records-list scroll-panel">{sorted.map(contest=><div className="mock-record" key={contest.id}><button type="button" className="record-row" onClick={()=>contest.status==='running'?onResume(contest):onSelect(contest)}><span className="record-symbol"><Flag size={21}/></span><div><strong>{contest.name}</strong><small>{dateText(contest.startedAt)} · {contest.duration} 分钟 · {contest.total} 题</small></div><span className="record-score">{contest.accepted}<small> / {contest.total}</small></span><ChevronRight size={18}/></button><button type="button" className="mock-record-delete icon-button" aria-label={`删除模拟赛 ${contest.name}`} disabled={contest.status==='running'||busy} onClick={event=>setTarget({value:contest,anchor:event.currentTarget})}><Trash2 size={17}/></button></div>)}{!sorted.length&&<div className="empty"><Flag size={27}/>{query.trim()?<p>没有匹配的模拟赛记录</p>:embedded?<p>暂无模拟赛记录</p>:<button className="primary" onClick={onCreate}>创建模拟赛</button>}</div>}</div></section>;
}
