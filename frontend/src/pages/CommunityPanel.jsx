import { useCallback, useEffect, useRef, useState } from 'react';
import { Award, Check, LogOut, LockKeyhole, RefreshCw, ShieldCheck, Sparkles, Trash2, Trophy, UserRound } from 'lucide-react';
import RankingMedal from '../components/RankingMedal.jsx';
import './Rankings.css';

const saveBeforeLogout = async () => (await import('../app/Workbench.jsx')).saveBeforeLogout();

export function ProfileSettings({ api, onError, onChanged, initialAccount, initialProfileSnapshot }) {
  const [snapshot, setSnapshot] = useState(initialProfileSnapshot || null), [account, setAccount] = useState(initialAccount || null), [nickname, setNickname] = useState(initialProfileSnapshot?.profile?.nickname || '');
  const [busy, setBusy] = useState(false), [error, setError] = useState(''), [message, setMessage] = useState('');
  const onChangedRef = useRef(onChanged);
  onChangedRef.current = onChanged;
  const [oldPassword, setOldPassword] = useState(''), [newPassword, setNewPassword] = useState(''), [confirmation, setConfirmation] = useState('');
  useEffect(() => { let alive = true; Promise.all([initialProfileSnapshot || api('profile'), initialAccount ? { account: initialAccount } : api('account')]).then(([value, login]) => { if (!alive) return; setSnapshot(value); setNickname(value.profile?.nickname || ''); setAccount(login.account); if (!initialProfileSnapshot) onChangedRef.current?.(value); }).catch(issue => { if (alive) setError(issue.message); }); return () => { alive = false; }; }, [api, initialAccount, initialProfileSnapshot]);
  async function save(event) {
    event.preventDefault(); if (busy) return; setBusy(true); setError(''); setMessage('');
    try { const value = await api('profile', { nickname: nickname.trim() }); setSnapshot(value); setNickname(value.profile?.nickname || ''); setMessage('昵称已保存。'); onChanged?.(value); }
    catch (issue) { setError(issue.message); onError?.(issue.message); } finally { setBusy(false); }
  }
  async function changePassword(event) {
    event.preventDefault(); if (busy) return; setError(''); setMessage('');
    if (newPassword !== confirmation) { setError('两次输入的新密码不一致'); return; }
    setBusy(true);
    try { await api('account/password', { oldPassword, newPassword }); setOldPassword(''); setNewPassword(''); setConfirmation(''); setMessage('密码已修改，其他设备需要重新登录。'); }
    catch (issue) { setError(issue.message); } finally { setBusy(false); }
  }
  async function logout() {
    if (busy) return; setBusy(true); setError('');
    try { await saveBeforeLogout(); await api('account/logout', {}); window.dispatchEvent(new Event('tb:account-change')); }
    catch (issue) { setError(issue.message); setBusy(false); }
  }
  return <section className="profile-settings" aria-label="TB 账号设置"><div className="progress-section-heading"><h2><UserRound size={18} />我的账号</h2><span>{snapshot?.leaderboard?.configured ? '排行榜已连接' : '账号设置'}</span></div>
    {!snapshot && !error && <p className="progress-muted" role="status">正在读取已同步的账号信息…</p>}
    {snapshot?.profile && <div className="profile-identity"><strong>{snapshot.profile.nickname || '用户'}</strong>{account && <span>登录号：{account.loginId}</span>}</div>}
    <details className="profile-edit"><summary>管理账号</summary><p className="progress-small">排行榜显示昵称。修改昵称会保留你的成绩和训练记录。</p>
    <form onSubmit={save} className="profile-form"><label>昵称<input aria-label="用户昵称" maxLength={32} value={nickname} onChange={event => setNickname(event.target.value)} placeholder="设置你的昵称" required disabled={busy || !snapshot} /></label><button className="progress-button progress-primary" disabled={busy || !snapshot}><Check size={14} />保存昵称</button></form>
    <p className="progress-small">{snapshot?.leaderboard?.notice || '共享排行榜尚未连接。连接后同步 ID、昵称与过题统计。'}</p>{error && <p className="connection-error" role="alert">{error}</p>}{message && <p className="connection-message" role="status">{message}</p>}
    {account && <div className="account-settings"><h3><LockKeyhole size={16}/> 修改密码</h3><form onSubmit={changePassword}>
      <label>原密码<input type="password" autoComplete="current-password" minLength={8} maxLength={128} value={oldPassword} onChange={event => setOldPassword(event.target.value)} required disabled={busy}/></label>
      <label>新密码<input type="password" autoComplete="new-password" minLength={8} maxLength={128} value={newPassword} onChange={event => setNewPassword(event.target.value)} required disabled={busy}/></label>
      <label>确认新密码<input type="password" autoComplete="new-password" minLength={8} maxLength={128} value={confirmation} onChange={event => setConfirmation(event.target.value)} required disabled={busy}/></label>
      <button className="progress-button progress-primary" disabled={busy}>修改密码</button></form>
      <button className="progress-button account-logout" onClick={logout} disabled={busy}><LogOut size={15}/>退出账号</button>
    </div>}</details>
  </section>;
}

const periods = [['daily', '每日过题'], ['weekly', '本周过题'], ['total', '累计过题']];

function RankingIdentity({ item, period, self }) {
  const progress = item.publicProgress;
  const identity = item.publicId || (item.userId ? 'TB-' + item.userId.replaceAll('-', '').toUpperCase() : '');
  return <div className="ranking-identity"><div className="ranking-identity-heading"><span className="ranking-user-name">{item.count > 0 && item.rank > 0 && item.rank <= 3 && <RankingMedal period={period} rank={item.rank}/>}<strong>{item.nickname || item.displayName || '用户'}</strong></span>{self && <span className="tag">我</span>}
    {progress?.titles?.map(title => <span className="ranking-title-badge" key={title.id} title={`${title.category === 'streak' ? '连续训练' : 'AC'} ${title.target}${title.category === 'streak' ? ' 天' : ' 题'}`}><Award size={14}/>{title.name}</span>)}
    {identity && <span className="ranking-public-id" title={identity}>ID：{identity}</span>}</div>
    {progress ? <div className="ranking-public-progress"><span>Lv.{progress.level}</span><span>{progress.tier}</span><span>{progress.rankTier ? `排位 ${progress.rankTier} · ${Number(progress.rankScore).toLocaleString('zh-CN')} 分` : '排位未解锁'}</span></div> : <span className="ranking-public-progress ranking-progress-pending">成长资料待同步</span>}
  </div>;
}

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
    {snapshot && <div className="ranking-board-summary"><div><UserRound size={17}/><span>本榜训练者</span><b>{entries.length}</b></div><div><Check size={17}/><span>本榜通过</span><b>{entries.reduce((sum,item)=>sum+Number(item.count||0),0)}</b></div><div><Trophy size={17}/><span>我的过题</span><b>{entries.find(item=>item.userId===snapshot.self?.userId)?.count ?? snapshot.self?.count ?? 0}</b></div></div>}
    <p className="progress-small">按不同题目的首次官方 AC 数排名，同分按完成时间先后排序。{snapshot?.date ? `统计日期：${snapshot.date}。` : ''}</p>
    <div className="ranking-reward-rule"><Sparkles size={16}/>{period === 'total' ? <><b>累计荣誉</b>前三名佩戴专属冠饰徽章<span>九种奖牌，累计榜高于周榜，周榜高于日榜</span></> : <><b>{period === 'daily' ? '每日奖励' : '每周奖励'}</b>第一名 +{awards[0]} · 第二名 +{awards[1]} · 第三名 +{awards[2]} XP<span>{period === 'daily' ? '北京时间每天 0 点结算前一日' : '北京时间每周日 0 点结算前一周'} · 自动到账</span></>}</div>
    {message && <p className="ranking-operation-message" role="status">{message}</p>}
    {error && <p className="connection-error" role="alert">{error}</p>}
    {snapshot?.hasSnapshot && snapshot.status === 'error' && <p className="connection-error" role="status">部分数据刷新未完成，后台将重试。{snapshot.error}</p>}
    {!snapshot ? <p className="progress-muted" role="status">正在读取排行榜…</p> : !snapshot.configured || snapshot.status === 'offline' || snapshot.status === 'error' && !snapshot.hasSnapshot && !entries.length ? <div className="ranking-empty"><Trophy size={32}/><h3>{snapshot.configured ? '排行榜暂时无法连接' : '共享排行榜尚未连接'}</h3><p>{snapshot.error || snapshot.notice || '在成长与能力中登录账号，连接后查看所有用户的排名。'}</p><button className="progress-button progress-primary" disabled={busy} onClick={snapshot.configured ? sync : onConfigure}>{snapshot.configured ? '重试连接' : '设置昵称与连接'}</button></div> : entries.length ? <div className="progress-table-scroll"><table className="ranking-table"><thead><tr><th>排名</th><th>用户与成长</th><th>过题数</th>{snapshot.isAdmin && <th>管理</th>}</tr></thead><tbody>{entries.map(item => <tr key={item.userId} className={snapshot.self?.userId === item.userId ? 'ranking-self' : ''}><td>{item.rank}</td><td><RankingIdentity item={item} period={period} self={snapshot.self?.userId === item.userId}/></td><td><b>{item.count}</b></td>{snapshot.isAdmin && <td><button className="text-button ranking-delete-button" aria-label={`删除 ${item.nickname || '用户'} 的${label}成绩`} disabled={busy || deleting || !ready} onClick={() => askDelete(item)}><Trash2 size={14}/>删除</button></td>}</tr>)}</tbody></table></div> : <div className="ranking-empty" role="status">{snapshot.status === 'syncing' && !snapshot.hasSnapshot ? <p><RefreshCw size={18} className="spin"/>正在同步过题记录…</p> : <><h3>{snapshot.status === 'error' ? '榜单已读取' : '服务已连接'}</h3><p>这个统计周期还没有首次官方 AC 记录。</p>{snapshot.self && <p>我的过题数：{snapshot.self.count || 0}</p>}</>}</div>}
    {confirmation && <DeleteConfirmation target={confirmation} busy={deleting} onCancel={() => setConfirmation(null)} onConfirm={remove}/>}
  </section></div>;
}
