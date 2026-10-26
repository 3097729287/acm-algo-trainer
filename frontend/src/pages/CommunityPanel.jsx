import usePublicAvatar from '@/lib/usePublicAvatar.js';
import ProfileBadge from '@/components/ProfileBadge.jsx';
import PageSearch from '@/components/PageSearch.jsx';
import {Search} from 'lucide-react';
import PopConfirm from '@/components/PopConfirm.jsx';
import MedalEmblem, {titleMedalIndex} from '@/components/MedalEmblem.jsx';
import { useCallback, useEffect, useRef, useState } from 'react';
import { Award, Check, CircleCheckBig, LogOut, LockKeyhole, MessageCircle, RefreshCw, ShieldCheck, Sparkles, Trash2, Trophy, UserRound, UserRoundCheck, UsersRound } from 'lucide-react';
import { LikeBurst, CommentDialog, SocialActivity, useSocial } from '../components/Social.jsx';
import RankingMedal from '../components/RankingMedal.jsx';
import TierIcon, { TIER_NAMES } from '../components/TierIcon.jsx';
import {rankIndex} from '@/lib/rankTiers.js';
import Tooltip from '../components/Tooltip.jsx';
import './Rankings.css';

const saveBeforeLogout = async () => (await import('../app/Workbench.jsx')).saveBeforeLogout();

export function ProfileSettings({ api, onError, onChanged, initialAccount, initialProfileSnapshot }) {
  const [snapshot, setSnapshot] = useState(initialProfileSnapshot || (initialAccount ? {profile:initialAccount}:null)), [account, setAccount] = useState(initialAccount || null), [nickname, setNickname] = useState(initialProfileSnapshot?.profile?.nickname || initialAccount?.nickname || '');
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
  return <section className="profile-settings" aria-label="ToBe 账号设置"><div className="progress-section-heading"><h2><UserRound size={18} />我的账号</h2><span/></div>
    {!snapshot && !error && <p className="progress-muted" role="status">正在读取已同步的账号信息…</p>}
    {snapshot?.profile && <div className="profile-identity"><strong>{snapshot.profile.nickname || '用户'}</strong>{account && <span>登录号：{account.loginId}</span>}</div>}
    <details className="profile-edit"><summary>管理账号</summary>
    <form onSubmit={save} className="profile-form"><label>昵称<input aria-label="用户昵称" maxLength={32} value={nickname} onChange={event => setNickname(event.target.value)} placeholder="设置你的昵称" required disabled={busy || !snapshot} /></label><button className="progress-button progress-primary" disabled={busy || !snapshot}><Check size={14} />保存昵称</button></form>
    {error && <p className="connection-error" role="alert">{error}</p>}{message && <p className="connection-message" role="status">{message}</p>}
    {account && !window.__tbAdmin && <div className="account-settings"><h3><LockKeyhole size={16}/> 修改密码</h3><form onSubmit={changePassword}>
      <label>原密码<input type="password" autoComplete="current-password" minLength={8} maxLength={128} value={oldPassword} onChange={event => setOldPassword(event.target.value)} required disabled={busy}/></label>
      <label>新密码<input type="password" autoComplete="new-password" minLength={8} maxLength={128} value={newPassword} onChange={event => setNewPassword(event.target.value)} required disabled={busy}/></label>
      <label>确认新密码<input type="password" autoComplete="new-password" minLength={8} maxLength={128} value={confirmation} onChange={event => setConfirmation(event.target.value)} required disabled={busy}/></label>
      <button className="progress-button progress-primary" disabled={busy}>修改密码</button></form>
      <button className="progress-button account-logout" onClick={logout} disabled={busy}><LogOut size={15}/>退出账号</button>
    </div>}</details>
  </section>;
}

const rankingCache=new WeakMap();
const rankingDate=()=>new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Shanghai'}).format(new Date());
const periods = [['daily', '每日过题'], ['weekly', '本周过题'], ['total', '累计过题']];

function RankingIdentity({item,self,avatarData,ownGrowth,api}) {
 const sharedAvatar=usePublicAvatar(api,item.userId,self?null:item.avatarHash);
 const progress=item.publicProgress||{},index=rankIndex(progress),growth=self&&ownGrowth?ownGrowth:{level:progress.level,currentLevelXp:progress.currentLevelXp,nextLevelXp:progress.nextLevelXp,ranked:{tier:TIER_NAMES[index],badge:`tier-${index}`,qualified:progress.rankTier!=null,abilityScore:progress.rankScore}};
 return <div className="ranking-identity"><ProfileBadge compact={false} showXp={Number.isFinite(growth.currentLevelXp)&&Number.isFinite(growth.nextLevelXp)} avatar={self?avatarData:sharedAvatar} growth={growth} nickname={item.nickname||item.displayName||'用户'}/><div className="ranking-title-list">{progress.titles?.map(title=><span className="ranking-title-badge" key={title.id}><MedalEmblem size={20} index={titleMedalIndex(title)} variant={title.category==='streak'?'streak':'ac'}/>{title.name}</span>)}</div></div>;
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

export default function RankingsPage({ api, onConfigure, onError, socialState, avatarData, ownGrowth }) {
  const [query,setQuery]=useState('');
  const [period, setPeriod] = useState('daily'), [snapshot, setSnapshot] = useState(()=>{const cached=rankingCache.get(api)?.daily;return cached?.date===rankingDate()?cached.value:null;}), [busy, setBusy] = useState(false), [error, setError] = useState('');
  const [confirmation, setConfirmation] = useState(null), [deleting, setDeleting] = useState(false), [message, setMessage] = useState('');
  const generation = useRef(0);
  const confirmedLikes = useRef(new Map());
  const [commentTarget,setCommentTarget] = useState(null);
  const ownSocial=useSocial(api,!socialState&&Boolean(snapshot?.socialAvailable));
  const social=socialState||ownSocial;
  const load = useCallback(async () => {
    const request = ++generation.current;
    setBusy(true); setError('');
    try { const value = await api('leaderboard?period=' + period); if(request===generation.current){setSnapshot(value);rankingCache.set(api,{...rankingCache.get(api),[period]:{date:rankingDate(),value}});} }
    catch (issue) { if (request === generation.current) { setError(issue.message); onError?.(issue.message); } }
    finally { if (request === generation.current) setBusy(false); }
  }, [api, period]);
  useEffect(() => { setSnapshot(previous=>{const cached=rankingCache.get(api)?.[period];return cached?.date===rankingDate()?cached.value:previous?.period===period?previous:null;});setMessage('');load(); return () => { generation.current++; }; }, [load]);
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
      api('leaderboard?period=' + period).then(value => { if(request===generation.current){setSnapshot(value);rankingCache.set(api,{...rankingCache.get(api),[period]:{date:rankingDate(),value}});} }).catch(issue => { if (request === generation.current) setError(issue.message); });
    }, snapshot.status === 'syncing' ? 1000 : 60000);
    return () => clearTimeout(timer);
  }, [api, period, snapshot, deleting]);
  const entries = Array.isArray(snapshot?.entries) ? snapshot.entries.map(item=>{
    const likes=confirmedLikes.current.get(snapshot.date+':'+item.userId);
    return likes ? {...item,likes:{total:Math.max(likes.counts?.[period]??(likes.countPeriod===period?likes.total:0),item.likes?.total || 0),likedToday:true}} : item;
  }) : [];
  const shownEntries=entries.filter(item=>String(item.nickname||'').toLocaleLowerCase().includes(query.trim().toLocaleLowerCase()));
  const label = periods.find(([key]) => key === period)[1];
  const ready = snapshot?.configured && snapshot.status !== 'offline' && snapshot.status !== 'error';
  const canManage = Boolean(window.__tbAdmin && snapshot?.isAdmin);
  const awards = snapshot?.rewardPolicy?.[period] || (period === 'daily' ? [100, 60, 30] : [500, 300, 150]);
  function askDelete(item = null, anchor) { setConfirmation({anchor, userId: item?.userId || null, nickname: item?.nickname || '用户', period, label }); }
  async function remove() {
    if (deleting || !confirmation || !canManage) return;
    setDeleting(true); setError('');
    try {
      const value = await api('leaderboard/admin/delete', { userId: confirmation.userId, period: confirmation.period, confirmation: 'delete' });
      setConfirmation(null); setMessage(`已删除 ${value.removed || 0} 条排行榜成绩。`); await load();
    } catch (issue) { setError(issue.message); onError?.(issue.message); }
    finally { setDeleting(false); }
  }
  return <div className="rankings-page scroll-panel" aria-label="用户过题排行榜"><PageSearch><label className="search-box"><Search size={17}/><input aria-label="搜索排行榜用户昵称" value={query} onChange={event=>setQuery(event.target.value)}/></label></PageSearch><section className="progress-section">
    <div className="ranking-header">
      <div className="ranking-period-controls">
      <Tooltip text="按不同题目的首次官方 AC 数排名，同分按完成时间排序。"><Trophy size={20} aria-label="过题排行榜"/></Tooltip>
      <div className="ranking-tabs" role="tablist" aria-label="排行榜时间范围">{periods.map(([value,title])=><button role="tab" disabled={deleting} aria-selected={period===value} className={period===value?'active':''} key={value} onClick={()=>setPeriod(value)}>{title.replace('过题','')}</button>)}</div>
      <Tooltip text={`${period==='total'?'累计榜前三名佩戴专属冠饰徽章。':`前三名奖励 ${awards.join(' / ')} XP，按北京时间结算，自动到账。`}统计日期：${snapshot?.date || '读取中'}`}><button className="hint-icon" aria-label="排名与奖励说明"><Sparkles size={16}/></button></Tooltip>
      </div><div className="ranking-overview-controls">
      {snapshot&&<div className="ranking-board-summary"><Tooltip text="本榜训练者"><span><UsersRound size={18}/><b>{entries.length}</b></span></Tooltip><Tooltip text="本榜通过"><span><CircleCheckBig size={18}/><b>{entries.reduce((sum,item)=>sum+Number(item.count||0),0)}</b></span></Tooltip><Tooltip text="我的过题"><span><UserRoundCheck size={18}/><b>{entries.find(item=>item.userId===snapshot.self?.userId)?.count ?? snapshot.self?.count ?? 0}</b></span></Tooltip></div>}
      <div className="ranking-controls">{canManage&&<Tooltip text="清空当前榜单"><button aria-label="清空当前榜单" className="progress-button ranking-delete-button" onClick={event=>askDelete(null,event.currentTarget)} disabled={busy||deleting||!ready||!entries.length}><Trash2 size={16}/></button></Tooltip>}<Tooltip text="同步与刷新"><button aria-label="同步与刷新" className="progress-button" onClick={snapshot?.configured?sync:load} disabled={busy||deleting}><RefreshCw size={16} className={busy?'spin':''}/></button></Tooltip></div>
      </div>
    </div>
    {message && <p className="ranking-operation-message" role="status">{message}</p>}
    {error && <p className="connection-error" role="alert">{error}</p>}
    {snapshot?.hasSnapshot && snapshot.status === 'error' && <p className="connection-error" role="status">部分数据刷新未完成，后台将重试。{snapshot.error}</p>}
    {!snapshot ? <p className="progress-muted" role="status">正在读取排行榜…</p> : !snapshot.configured || snapshot.status === 'offline' || snapshot.status === 'error' && !snapshot.hasSnapshot && !entries.length ? <div className="ranking-empty"><Trophy size={32}/><h3>{snapshot.configured ? '排行榜暂时无法连接' : '共享排行榜尚未连接'}</h3><p>{snapshot.error || snapshot.notice || '在成长与能力中登录账号，连接后查看所有用户的排名。'}</p><button className="progress-button progress-primary" disabled={busy} onClick={snapshot.configured ? sync : onConfigure}>{snapshot.configured ? '重试连接' : '设置昵称与连接'}</button></div> : shownEntries.length ? <div className="progress-table-scroll"><table className="ranking-table"><colgroup><col className="ranking-column-place"/><col/>{snapshot.socialAvailable&&<col className="ranking-column-social"/>}<col className="ranking-column-count"/>{canManage&&<col className="ranking-column-admin"/>}</colgroup><thead className="sr-only"><tr><th>排名</th><th>用户</th>{snapshot.socialAvailable&&<th>互动</th>}<th>AC</th>{canManage&&<th>管理</th>}</tr></thead><tbody>{shownEntries.map(item=>{const self=snapshot.self?.userId===item.userId;return <tr key={item.userId} className={self?'ranking-self':''}><td className="ranking-place">{item.count>0&&item.rank<=3?<RankingMedal period={period} rank={item.rank}/>:item.rank}</td><td><RankingIdentity item={item} self={self} avatarData={avatarData} ownGrowth={ownGrowth} api={api}/></td>{snapshot.socialAvailable&&<td className="ranking-social-cell"><div className="ranking-social">{self?<span className="ranking-message-slot" aria-hidden="true"/>:<button type="button" className="ranking-message" title={`给 ${item.nickname} 留言`} disabled={!ready} aria-label={`给 ${item.nickname} 留言`} onClick={()=>setCommentTarget(item)}><MessageCircle size={18}/></button>}<LikeBurst key={snapshot.date+':'+period+':'+item.userId} period={period} self={self} targetId={item.userId} nickname={item.nickname} likes={item.likes} disabled={!ready||self} api={api} onError={message=>setError(message)} onLiked={result=>{confirmedLikes.current.set(snapshot.date+':'+item.userId,{...result.likes,countPeriod:period});setSnapshot(previous=>({...previous}));}}/></div></td>}<td className="ranking-count"><b>{item.count}</b></td>{canManage&&<td className="ranking-admin-cell"><button type="button" className="text-button ranking-delete-button" aria-label={`删除 ${item.nickname||'用户'} 的${label}成绩`} disabled={busy||deleting||!ready} onClick={event=>askDelete(item,event.currentTarget)}><Trash2 size={16}/></button></td>}</tr>;})}</tbody></table></div> : <div className="ranking-empty" role="status">{query.trim()?<p>没有找到昵称匹配的用户。</p>:snapshot.status === 'syncing' && !snapshot.hasSnapshot ? <p><RefreshCw size={18} className="spin"/>正在同步过题记录…</p> : <p>暂无过题记录</p>}</div>}
    <SocialActivity items={social.snapshot?.activity||[]}/>{commentTarget && <CommentDialog target={commentTarget} api={api} onClose={()=>setCommentTarget(null)} onSent={()=>setMessage('留言已发送。')}/> }
    {confirmation && <PopConfirm anchor={confirmation.anchor} title={confirmation.userId?`删除 ${confirmation.nickname} 的${confirmation.label}成绩？`:`清空${confirmation.label}成绩？`} busy={deleting} error={error} onCancel={()=>setConfirmation(null)} onConfirm={remove}/>}
  </section></div>;
}
