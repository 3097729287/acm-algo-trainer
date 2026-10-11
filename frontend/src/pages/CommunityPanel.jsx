import { useCallback, useEffect, useRef, useState } from 'react';
import { Check, Copy, RefreshCw, ShieldCheck, Sparkles, Trash2, Trophy, UserRound } from 'lucide-react';
import RankingMedal from '../components/RankingMedal.jsx';
import './Rankings.css';

export function ProfileSettings({ api, onError, onChanged }) {
  const [snapshot, setSnapshot] = useState(null), [nickname, setNickname] = useState(''), [endpoint, setEndpoint] = useState('');
  const [busy, setBusy] = useState(false), [error, setError] = useState(''), [message, setMessage] = useState('');
  useEffect(() => { let alive = true; api('profile').then(value => { if (!alive) return; setSnapshot(value); setNickname(value.profile?.nickname || ''); setEndpoint(value.leaderboard?.endpoint || ''); }).catch(issue => { if (alive) setError(issue.message); }); return () => { alive = false; }; }, [api]);
  async function save(event) {
    event.preventDefault(); if (busy) return; setBusy(true); setError(''); setMessage('');
    try { const value = await api('profile', { nickname: nickname.trim(), endpoint: endpoint.trim() }); setSnapshot(value); setNickname(value.profile?.nickname || ''); setEndpoint(value.leaderboard?.endpoint || ''); setMessage('昵称与排行榜连接已保存。'); onChanged?.(value); }
    catch (issue) { setError(issue.message); onError?.(issue.message); } finally { setBusy(false); }
  }
  return <section className="profile-settings" aria-label="用户身份与排行榜连接"><div className="progress-section-heading"><h2><UserRound size={18} />用户身份</h2><span>{snapshot?.leaderboard?.configured ? '排行榜已连接' : '本地身份'}</span></div>
    {snapshot?.profile && <div className="profile-identity"><strong>{snapshot.profile.nickname || '用户'}</strong><code className="copyable-id">#{snapshot.profile.userId}</code><button className="text-button" aria-label="复制用户 ID" onClick={() => navigator.clipboard.writeText(snapshot.profile.userId).then(() => setMessage('用户 ID 已复制。')).catch(() => setError('请选中 ID 后按 Ctrl+C 复制。'))}><Copy size={14} /></button></div>}
    <p className="progress-small">ID 是你的固定标识，修改昵称后保留。连接共享服务后，排行榜显示昵称和 ID。</p>
    <form onSubmit={save} className="profile-form"><label>昵称<input aria-label="用户昵称" maxLength={24} value={nickname} onChange={event => setNickname(event.target.value)} placeholder="设置你的昵称" required /></label><label>排行榜服务地址<input aria-label="排行榜服务地址" type="url" value={endpoint} onChange={event => setEndpoint(event.target.value)} placeholder="https://your-service.example" /></label><button className="progress-button progress-primary" disabled={busy || !snapshot}><Check size={14} />保存身份</button></form>
    <p className="progress-small">{snapshot?.leaderboard?.notice || '共享排行榜尚未连接。连接后同步 ID、昵称与过题统计。'}</p>{error && <p className="connection-error" role="alert">{error}</p>}{message && <p className="connection-message" role="status">{message}</p>}
  </section>;
}

const periods = [['daily', '每日过题'], ['weekly', '本周过题'], ['total', '累计过题']];

function DeleteConfirmation({ target, busy, onCancel, onConfirm }) {
  const dialog = useRef(null), cancel = useRef(null);
  useEffect(() => {
    const element = dialog.current;
    element.showModal(); cancel.current.focus();
    return () => element.close();
  }, []);
  return <dialog ref={dialog} className="ranking-confirm" aria-labelledby="ranking-delete-title" onCancel={event => { event.preventDefault(); if (!busy) onCancel(); }}>
    <h3 id="ranking-delete-title">{target.userId ? `删除 ${target.nickname} 的${target.label}成绩？` : `清空${target.label}成绩？`}</h3>
    <p>{target.userId ? `用户 ID：${target.userId}` : '将删除当前统计周期内所有用户的排行榜成绩。'}</p>
    <p>对应题目的日榜、周榜和总榜计数都会更新，再次同步也不会恢复这些成绩。已发放的经验保留，本机训练记录和代码保留。</p>
    <div className="ranking-confirm-actions"><button ref={cancel} className="progress-button" disabled={busy} onClick={onCancel}>取消</button><button className="progress-button ranking-delete-button" disabled={busy} onClick={onConfirm}><Trash2 size={14}/>{busy ? '正在删除…' : '确认删除'}</button></div>
  </dialog>;
}

export default function RankingsPage({ api, onConfigure, onError }) {
  const [period, setPeriod] = useState('daily'), [snapshot, setSnapshot] = useState(null), [busy, setBusy] = useState(false), [error, setError] = useState('');
  const [confirmation, setConfirmation] = useState(null), [deleting, setDeleting] = useState(false), [message, setMessage] = useState('');
  const generation = useRef(0);
  const load = useCallback(async () => {
    const request = ++generation.current;
    setBusy(true); setError('');
    try { const value = await api('leaderboard?period=' + period); if (request === generation.current) setSnapshot(value); }
    catch (issue) { if (request === generation.current) { setError(issue.message); onError?.(issue.message); } }
    finally { if (request === generation.current) setBusy(false); }
  }, [api, period]);
  useEffect(() => { setSnapshot(null); setMessage(''); load(); return () => { generation.current++; }; }, [load]);
  async function sync() {
    if (busy || deleting) return;
    setBusy(true); setError('');
    try { await api('leaderboard/sync', {}); await load(); }
    catch (issue) { setError(issue.message); onError?.(issue.message); setBusy(false); }
  }
  useEffect(() => {
    if (!snapshot?.configured || deleting) return;
    const request = generation.current;
    const timer = setTimeout(() => {
      api('leaderboard?period=' + period).then(value => { if (request === generation.current) setSnapshot(value); }).catch(issue => { if (request === generation.current) setError(issue.message); });
    }, snapshot.status === 'syncing' ? 1000 : 60000);
    return () => clearTimeout(timer);
  }, [api, period, snapshot, deleting]);
  const entries = Array.isArray(snapshot?.entries) ? snapshot.entries : [];
  const label = periods.find(([key]) => key === period)[1];
  const ready = snapshot?.configured && snapshot.status !== 'offline' && snapshot.status !== 'error';
  const awards = snapshot?.rewardPolicy?.[period] || (period === 'daily' ? [100, 60, 30] : [500, 300, 150]);
  function askDelete(item = null) { setConfirmation({ userId: item?.userId || null, nickname: item?.nickname || '用户', period, label }); }
  async function remove() {
    if (deleting || !confirmation) return;
    setDeleting(true); setError('');
    try {
      const value = await api('leaderboard/admin/delete', { userId: confirmation.userId, period: confirmation.period, confirmation: 'delete' });
      setConfirmation(null); setMessage(`已删除 ${value.removed || 0} 条排行榜成绩。`); await load();
    } catch (issue) { setError(issue.message); onError?.(issue.message); }
    finally { setDeleting(false); }
  }
  return <div className="rankings-page scroll-panel" aria-label="用户过题排行榜"><section className="progress-section">
    <div className="progress-section-heading"><h2><Trophy size={20}/>过题排行榜</h2><div className="ranking-controls">
      {snapshot?.isAdmin && <><span className="ranking-admin-label"><ShieldCheck size={14}/>管理员</span><button className="progress-button ranking-delete-button" onClick={() => askDelete()} disabled={busy || deleting || !ready || !entries.length}><Trash2 size={14}/>清空当前榜单</button></>}
      <button className="progress-button" onClick={snapshot?.configured ? sync : load} disabled={busy || deleting}><RefreshCw size={14} className={busy ? 'spin' : ''}/>{snapshot?.configured ? '同步与刷新' : '刷新'}</button>
    </div></div>
    <div className="ranking-tabs" role="tablist" aria-label="排行榜时间范围">{periods.map(([value, title]) => <button role="tab" disabled={deleting} aria-selected={period === value} className={period === value ? 'active' : ''} key={value} onClick={() => setPeriod(value)}>{title}</button>)}</div>
    <p className="progress-small">按不同题目的首次官方 AC 数排名，同分按完成时间先后排序。{snapshot?.date ? `统计日期：${snapshot.date}。` : ''}</p>
    <div className="ranking-reward-rule"><Sparkles size={16}/>{period === 'total' ? <><b>累计荣誉</b>前三名佩戴专属冠饰徽章<span>九种奖牌，累计榜高于周榜，周榜高于日榜</span></> : <><b>{period === 'daily' ? '每日奖励' : '每周奖励'}</b>第一名 +{awards[0]} · 第二名 +{awards[1]} · 第三名 +{awards[2]} XP<span>{period === 'daily' ? '北京时间每天 0 点结算前一日' : '北京时间每周日 0 点结算前一周'} · 自动到账</span></>}</div>
    {message && <p className="ranking-operation-message" role="status">{message}</p>}
    {error && <p className="connection-error" role="alert">{error}</p>}
    {!snapshot ? <p className="progress-muted" role="status">正在读取排行榜…</p> : !snapshot.configured || snapshot.status === 'offline' || snapshot.status === 'error' && !entries.length ? <div className="ranking-empty"><Trophy size={32}/><h3>{snapshot.configured ? '排行榜暂时无法连接' : '共享排行榜尚未连接'}</h3><p>{snapshot.error || snapshot.notice || '在偏好设置中填写排行榜服务地址，连接后查看所有用户的排名。'}</p><button className="progress-button progress-primary" onClick={onConfigure}>设置昵称与连接</button></div> : entries.length ? <div className="progress-table-scroll"><table className="ranking-table"><thead><tr><th>排名</th><th>用户 · ID</th><th>过题数</th>{snapshot.isAdmin && <th>管理</th>}</tr></thead><tbody>{entries.map(item => <tr key={item.userId} className={snapshot.self?.userId === item.userId ? 'ranking-self' : ''}><td>{item.rank}</td><td><span className="ranking-user-name">{item.rank <= 3 && <RankingMedal period={period} rank={item.rank}/>}<strong>{item.nickname || item.displayName || '用户'}</strong></span><code className="copyable-id">{item.userId}</code>{snapshot.self?.userId === item.userId && <span className="tag">我</span>}</td><td><b>{item.count}</b></td>{snapshot.isAdmin && <td><button className="text-button ranking-delete-button" aria-label={`删除 ${item.nickname || '用户'} 的${label}成绩`} disabled={busy || deleting || !ready} onClick={() => askDelete(item)}><Trash2 size={14}/>删除</button></td>}</tr>)}</tbody></table></div> : <div className="ranking-empty" role="status">{snapshot.status === 'syncing' ? <p><RefreshCw size={18} className="spin"/>正在同步过题记录…</p> : <><h3>服务已连接</h3><p>这个统计周期还没有首次官方 AC 记录。</p>{snapshot.self && <p>我的过题数：{snapshot.self.count || 0}</p>}</>}</div>}
    {confirmation && <DeleteConfirmation target={confirmation} busy={deleting} onCancel={() => setConfirmation(null)} onConfirm={remove}/>}
  </section></div>;
}
