import BrandWordmark from '../components/BrandWordmark.jsx';
import { useCallback, useEffect, useRef, useState } from 'react';
import { Eye, EyeOff, LoaderCircle, LockKeyhole, LogIn, UserRoundPlus } from 'lucide-react';
import { request } from '../api/client.js';
import { SoftwareUpdateNotice, useSoftwareUpdates } from '../pages/SoftwareUpdates.jsx';
import StartupScreen from './StartupScreen.jsx';
import './Accounts.css';

export default function AccountGate({ children }) {
  const [session, setSession] = useState(null), [booting, setBooting] = useState(true);
  const [mode, setMode] = useState('login'), [loginId, setLoginId] = useState(''), [nickname, setNickname] = useState('');
  const [password, setPassword] = useState(''), [confirmation, setConfirmation] = useState(''), [visible, setVisible] = useState(false);
  const [busy, setBusy] = useState(false), [error, setError] = useState(''), [message, setMessage] = useState('');
  const [syncBusy, setSyncBusy] = useState(false);
  const generation = useRef(0);
  const submitting = useRef(false);
  const refreshing = useRef(false);
  const mounted = useRef(false);
  const seeded = useRef(false);
  const registeredLogin = useRef('');
  const updateApi = useCallback((path, body) => request(path, body, session?.token), [session?.token]);
  const softwareUpdate = useSoftwareUpdates(updateApi, Boolean(session?.token && !session.authenticated));
  const refresh = useCallback(async (retry = false) => {
    if (submitting.current || refreshing.current) return;
    refreshing.current = true;
    const current = ++generation.current;
    try {
      const value = await request(`account?background=1${retry === true ? '&retry=1' : ''}`);
      if (current !== generation.current || !mounted.current) return;
      setSession(value);
      if (!value.authenticated) {
        if (!seeded.current) { setLoginId(value.lastLoginId || ''); seeded.current = true; }
        setError(value.error || '');
      }
    } catch (issue) { if (current === generation.current) setError(issue.message); }
    finally {
      refreshing.current = false;
      if (mounted.current && current === generation.current) setBooting(false);
      else if (mounted.current && !submitting.current) queueMicrotask(refresh);
    }
  }, []);
  useEffect(() => {
    mounted.current = true;
    refresh();
    const changed = () => { generation.current++; setSession(null); setBooting(true); setError(''); seeded.current = false; setPassword(''); setConfirmation(''); setMode('login'); refresh(); };
    const visible = () => { if (!document.hidden) refresh(); };
    window.addEventListener('tb:account-change', changed);
    window.addEventListener('focus', refresh);
    document.addEventListener('visibilitychange', visible);
    return () => { mounted.current = false; window.removeEventListener('tb:account-change', changed); window.removeEventListener('focus', refresh); document.removeEventListener('visibilitychange', visible); };
  }, [refresh]);
  useEffect(() => {
    // Saved-session validation runs in the backend. Show its completed result
    // promptly; steady signed-in polling keeps the original lower frequency.
    const interval = setInterval(() => { if (!document.hidden) refresh(); }, session?.restoring ? 250 : 3000);
    return () => clearInterval(interval);
  }, [refresh, session?.restoring]);
  async function submit(event) {
    event.preventDefault(); if (busy) return;
    setError(''); setMessage('');
    if (!session?.token) { await refresh(); return; }
    if (mode === 'register' && password !== confirmation) { setError('两次输入的密码不一致'); return; }
    generation.current++;
    submitting.current = true;
    setBusy(true);
    try {
      if (mode === 'register') {
        const result = await request('account/register', { nickname: nickname.trim(), loginId: loginId.trim(), password }, session.token);
        registeredLogin.current = result.loginId.toLowerCase();
        try { sessionStorage.setItem(`tb.onboarding.pending.${registeredLogin.current}`, '1'); } catch { /* Optional device hint. */ }
        setLoginId(result.loginId); setMode('login'); setPassword(''); setConfirmation(''); setVisible(false);
        setMessage('注册成功，请用登录号和密码登录。');
        const authenticated = await request('account/login', { loginId: result.loginId, password }, session.token);
        window.__tbNewAccount = true;
        setMessage(''); setSession(authenticated);
      } else {
        const result = await request('account/login', { loginId: loginId.trim(), password }, session.token);
        window.__tbNewAccount = registeredLogin.current === loginId.trim().toLowerCase();
        try { window.__tbNewAccount ||= sessionStorage.getItem(`tb.onboarding.pending.${loginId.trim().toLowerCase()}`) === '1'; } catch { /* The in-memory registration hint still works. */ }
        setPassword(''); setConfirmation(''); setSession(result);
      }
    } catch (issue) { setError(issue.message); }
    finally { submitting.current = false; setBusy(false); }
  }
  function changeMode(next) {
    setMode(next); setError(''); setMessage(''); setPassword(''); setConfirmation(''); setVisible(false);
  }
  window.__tbAdmin = Boolean(session?.admin);
  window.__tbAccountUserId = session?.account?.userId || '';
  window.__tbAccount = session?.account || null;
  window.__tbOriginalWorkspace = Boolean(session?.usesOriginalWorkspace);
  window.__tbAccountSync = session?.authenticated ? session.sync : null;
  useEffect(() => {
    window.dispatchEvent(new CustomEvent('tb:sync-status', { detail: session?.authenticated ? session.sync : null }));
    window.dispatchEvent(new CustomEvent('tb:account-state', { detail: session?.account || null }));
  }, [session]);
  async function retrySync() {
    if (syncBusy) return;
    setSyncBusy(true);
    try { await request('account/sync', {}, session.token); }
    catch (issue) { setError(issue.message); }
    finally { setSyncBusy(false); refresh(); }
  }
  if (session?.authenticated) return <div className="account-session" key={`${session.account?.userId || 'fixture'}:${session.token}`}>
    {session.sync?.status === 'error' && <aside className="account-sync-alert" role="status"><span>{session.sync.error || '云端同步暂未完成，本机数据已保留。'}</span><button type="button" onClick={retrySync} disabled={syncBusy}>{syncBusy ? '正在同步…' : '重试同步'}</button></aside>}
    <div className="account-session-content">{children}</div>
  </div>;
  if (booting || session?.restoring) return <><StartupScreen restoring={session?.restoring} error={error} onRetry={() => refresh(true)}/><SoftwareUpdateNotice update={softwareUpdate} onDetails={() => window.open(softwareUpdate.state.releaseUrl, '_blank', 'noopener,noreferrer')}/></>;
  const registering = mode === 'register';
  return <main className="account-screen">
    <div className="account-brand"><span className="account-logo"><BrandWordmark/></span><span>ToBe <small>训练工作台</small></span></div>
    <section className="account-card" aria-label="ToBe 账号登录">
      <div className="account-symbol"><LockKeyhole size={24}/></div>
      <h1>{registering ? '创建你的 ToBe 账号' : '登录 ToBe'}</h1>
      <p className="account-intro">{registering ? '注册账号，记录训练进步，参与过题排行榜。' : '登录后继续训练，排行榜使用你的昵称。'}</p>
        <div className="account-tabs" role="tablist" aria-label="账号操作">
          <button type="button" role="tab" aria-selected={!registering} disabled={busy} onClick={() => changeMode('login')}>登录</button>
          <button type="button" role="tab" aria-selected={registering} disabled={busy} onClick={() => changeMode('register')}>注册</button>
        </div>
        <form onSubmit={submit} className="account-form">
          {registering && <label>昵称<input name="nickname" autoComplete="nickname" maxLength={32} value={nickname} onChange={event => setNickname(event.target.value)} placeholder="排行榜上显示的名字" required disabled={busy}/></label>}
          <label>登录号<input name="username" autoComplete="username" minLength={4} maxLength={32} pattern="[A-Za-z0-9_]{4,32}" value={loginId} onChange={event => setLoginId(event.target.value)} placeholder="4–32 位字母、数字或下划线" autoCapitalize="none" spellCheck={false} required disabled={busy}/></label>
          <label>密码<div className="account-password"><input name="password" type={visible ? 'text' : 'password'} autoComplete={registering ? 'new-password' : 'current-password'} minLength={8} maxLength={128} value={password} onChange={event => setPassword(event.target.value)} placeholder="至少 8 个字符" required disabled={busy}/><button type="button" aria-label={visible ? '隐藏密码' : '显示密码'} aria-pressed={visible} onClick={() => setVisible(value => !value)}>{visible ? <EyeOff size={18}/> : <Eye size={18}/>}</button></div></label>
          {registering && <label>确认密码<input name="passwordConfirmation" type={visible ? 'text' : 'password'} autoComplete="new-password" minLength={8} maxLength={128} value={confirmation} onChange={event => setConfirmation(event.target.value)} placeholder="再次输入密码" required disabled={busy}/></label>}
          {error && <p className="account-error" role="alert">{error}</p>}
          {message && <p className="account-message" role="status">{message}</p>}
          <button type="submit" className="account-submit" disabled={busy || session?.restoring || !session?.token}>{busy ? <LoaderCircle className="spin" size={18}/> : registering ? <UserRoundPlus size={18}/> : <LogIn size={18}/>} {busy ? registering ? '正在注册…' : '正在登录并同步数据…' : registering ? '注册账号' : '登录'}</button>
        </form>
        {(!session?.token || error && !session?.restoring) && <button className="account-retry" onClick={() => refresh(true)}>重新连接</button>}
    </section>
    <p className="account-footer">ToBe · 每一步训练，都留下进步</p>
    <SoftwareUpdateNotice update={softwareUpdate} onDetails={() => window.open(softwareUpdate.state.releaseUrl, '_blank', 'noopener,noreferrer')} />
  </main>;
}
