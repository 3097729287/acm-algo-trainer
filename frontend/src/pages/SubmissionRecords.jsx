import { useState } from 'react';
import InlineTitle from '@/components/InlineTitle.jsx';
import { ChevronRight, Code2, Flag, Search } from 'lucide-react';
import { groupSubmissionsByDay, verdictLabel, verdictTone } from '@/models/workspaceModel.js';
import { trainingDateLabel, trainingTime } from '@/lib/trainingDate.js';

const dateText = value => value ? new Date(value).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) : '—';
export default function SubmissionRecords({ submissions = [], total = submissions.length, hasMore = false, loading = false, onLoadMore, rows, onSelect }) {
  const [query, setQuery] = useState(''), [result, setResult] = useState('');
  const rowMap = new Map(rows.map(row => [row.id, row]));
  const logs = submissions.filter(submission => {
    const row = rowMap.get(submission.problemId);
    return (!result || submission.verdict === result) && `${row?.title || submission.problemId} ${row?.contest || ''} ${verdictLabel(submission.verdict)}`.toLowerCase().includes(query.trim().toLowerCase());
  });
  const days = groupSubmissionsByDay(logs);
  return <div className="records-page">
    <div className="table-toolbar">
      <label className="search-box"><Search size={16} /><input aria-label="搜索历史提交" placeholder="搜索题名、比赛或提交结果" value={query} onChange={event => setQuery(event.target.value)} /></label>
      <select aria-label="历史提交结果" value={result} onChange={event => setResult(event.target.value)}><option value="">全部提交结果</option>{['AC', 'SAMPLE_PASS', 'WA', 'CE', 'TLE', 'MLE', 'RE', 'OLE', 'ERROR'].map(value => <option key={value} value={value}>{verdictLabel(value)}</option>)}</select>
      <span className="toolbar-count">{logs.length} 条记录{hasMore ? ` · 已读取 ${submissions.length}/${total}` : ''}</span>
    </div>
    <div className="submission-log scroll-panel">
      {days.map(group => <section className="submission-day" key={group.day} data-day={group.day} aria-label={`${trainingDateLabel(group.day)}提交`}>
        <header className="submission-day-heading">
          <h2><time dateTime={group.day || undefined}>{trainingDateLabel(group.day)}</time> 提交</h2>
          <span>{group.problems.size} 题 · {group.submissions.length} 条记录 · <b>{group.accepted.size} 题 AC</b></span>
        </header>
        {group.submissions.map(submission => {
          const row = rowMap.get(submission.problemId);
          return <button className="submission-log-row" key={submission.id} onClick={() => onSelect({ ...submission, title: row?.title || submission.problemId, contestName: row?.contest })}>
            <span><strong><InlineTitle>{row?.title || submission.problemId}</InlineTitle></strong><small>{trainingTime(submission.submittedAt)} · {submission.mode === 'run' ? '运行' : '提交'}{submission.scope === 'official' ? ' · 平台回执' : submission.contestId ? ' · 模拟赛' : ' · 单题练习'}{row?.contest ? ` · ${row.contest}` : ''}</small></span>
            <span className={'verdict ' + verdictTone(submission.verdict)}><span />{verdictLabel(submission.verdict)}</span>
            <span>{submission.timeMs != null ? submission.timeMs + ' ms' : '—'}</span><ChevronRight size={15} />
          </button>;
        })}
      </section>)}
      {!logs.length && !loading && <div className="empty"><Code2 size={26} /><h2>{submissions.length ? '没有匹配的提交' : '还没有提交记录'}</h2><p>{submissions.length ? '试试调整搜索或结果筛选。' : '写好代码后提交，每次结果与代码都会保存在这里。'}</p></div>}
      {(hasMore || loading) && <div className="submission-pagination"><span>{hasMore ? '搜索、筛选与每日统计针对已读取的记录；加载更早提交可补全当天和此前的记录。' : '正在读取提交记录…'}</span>{hasMore && <button className="secondary" onClick={onLoadMore} disabled={loading}>{loading ? '正在读取…' : '加载更早提交'}</button>}</div>}
    </div>
  </div>;
}

export function MockHistory({ contests = [], onSelect, onResume, onCreate }) {
  return <div className="records-page"><div className="records-list scroll-panel">{contests.map(contest => <button className="record-row" key={contest.id} onClick={() => contest.status === 'running' ? onResume(contest) : onSelect(contest)}><span className={'record-symbol ' + (contest.accepted === contest.total ? 'complete' : '')}><Flag size={20} /></span><div><strong>{contest.name}</strong><small>{dateText(contest.startedAt)} · {contest.duration} 分钟 · {contest.total} 题</small></div><span className="record-score">{contest.accepted}<small> / {contest.total}</small><em>本地 AC</em></span><span className="record-status">{contest.status === 'running' ? '进行中' : '查看复盘'}</span><ChevronRight size={17} /></button>)}{!contests.length && <div className="empty"><Flag size={26} /><h2>还没有模拟赛记录</h2><p>完成模拟赛后，这里保留每题提交与复盘。</p><button className="primary" onClick={onCreate}>创建模拟赛</button></div>}</div></div>;
}
