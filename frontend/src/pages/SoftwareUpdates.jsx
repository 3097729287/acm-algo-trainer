import { useCallback, useEffect, useState } from 'react';
import './SoftwareUpdates.css';

export function useSoftwareUpdates(api, enabled) {
  const [state, setState] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [dismissed, setDismissed] = useState('');
  useEffect(() => {
    if (!enabled) return;
    let alive = true, timer;
    const poll = async () => {
      try {
        const value = await api('software-update');
        if (alive) {
          setState(value);
          timer = setTimeout(poll, ['checking', 'downloading', 'installing'].includes(value.status) ? 1000 : 10000);
        }
      } catch { if (alive) timer = setTimeout(poll, 30000); }
    };
    poll();
    return () => { alive = false; clearTimeout(timer); };
  }, [api, enabled]);
  const action = useCallback(async (name, body = {}) => {
    setBusy(true); setError('');
    try {
      if (name === 'install') {
        const pending = [];
        window.dispatchEvent(new CustomEvent('tb-before-update', { detail: { waitUntil: promise => pending.push(promise) } }));
        const saved = await Promise.all(pending);
        if (saved.some(value => value === false)) throw new Error('草稿尚未保存，请保存成功后再安装更新。');
      }
      setState(await api('software-update/' + name, body));
      if (name === 'check') setDismissed('');
    } catch (problem) { setError(problem.message || '更新未完成，请重试'); }
    finally { setBusy(false); }
  }, [api]);
  return { state, error, busy, action, dismissed, dismiss: () => setDismissed(state?.latestVersion || '') };
}

function UpdateAction({ update }) {
  const { state, action, busy } = update;
  if (state.status === 'installing') return <span role="status">正在关闭 TB 并安装，完成后将自动重新打开…</span>;
  if (state.status === 'downloading') return <div role="status"><progress max={state.totalBytes || 1} value={state.downloadedBytes || 0} aria-label="安装包下载进度" /> {Math.floor(100 * (state.downloadedBytes || 0) / (state.totalBytes || 1))}%</div>;
  if (state.status === 'ready') return <button className="primary" disabled={busy || !state.canInstall} onClick={() => action('install')}>保存并安装更新</button>;
  if (state.latestVersion) return state.canInstall
    ? <button className="primary" disabled={busy} onClick={() => action('download')}>下载更新 v{state.latestVersion}</button>
    : <a href={state.releaseUrl} target="_blank" rel="noreferrer">下载 Windows 安装版</a>;
  return null;
}

export function SoftwareUpdatePanel({ update }) {
  const { state, error, busy, action } = update;
  if (!state) return <section className="software-update"><h3>软件版本更新</h3><p>正在读取软件更新状态…</p></section>;
  return <section className="software-update" aria-label="软件版本更新">
    <h3>软件版本更新</h3>
    <p>当前版本 v{state.currentVersion}{state.latestVersion ? ` · 新版本 v${state.latestVersion}` : state.status === 'current' ? ' · 已是最新正式版' : ''}</p>
    <label><input type="checkbox" checked={state.autoCheck} onChange={event => action('settings', { autoCheck: event.target.checked })} disabled={busy} />启动时自动检查更新（运行期间每天检查一次）</label>
    <div className="software-update-actions"><button disabled={busy || ['checking', 'downloading', 'installing'].includes(state.status)} onClick={() => action('check')}>{state.status === 'checking' ? '正在检查…' : '检查软件更新'}</button><UpdateAction update={update} /></div>
    {state.latestVersion && <p>安装前会保存当前草稿并备份个人数据，安装完成后自动重新打开 TB。</p>}
    {(error || state.error) && <p className="software-update-error" role="alert">{error || state.error}</p>}
    {state.notes && <details><summary>本次更新内容</summary><pre>{state.notes}</pre></details>}
    <a href={state.releaseUrl} target="_blank" rel="noreferrer">在 GitHub 查看正式发布</a>
  </section>;
}

export function SoftwareUpdateNotice({ update, onDetails }) {
  const { state, dismissed, dismiss, error } = update;
  if (!state?.latestVersion || dismissed === state.latestVersion) return null;
  return <aside className="software-update-notice" aria-label="软件更新提示" aria-live="polite">
    <strong>TB v{state.latestVersion} 可更新</strong>
    <UpdateAction update={update} />
    <button onClick={onDetails}>查看更新</button>
    {state.status !== 'installing' && <button aria-label="稍后更新" onClick={dismiss}>稍后</button>}
    {(error || state.error) && <span role="alert">{error || state.error}</span>}
  </aside>;
}
