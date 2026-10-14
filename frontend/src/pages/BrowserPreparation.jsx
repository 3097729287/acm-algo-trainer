import { useCallback, useEffect, useRef, useState } from 'react';
import { ExternalLink, FolderOpen, Plug, RefreshCw, X } from 'lucide-react';
import './BrowserPreparation.css';

const labels = {logged_in:'已登录',logged_out:'未登录或登录已失效',not_synced:'尚未同步登录',unknown:'登录状态待确认'};

export default function BrowserPreparation({ api, enabled }) {
  const [snapshot, setSnapshot] = useState(null), [open, setOpen] = useState(false);
  const [browser, setBrowser] = useState('edge'), [busy, setBusy] = useState(false);
  const [error, setError] = useState(''), [message, setMessage] = useState(''), [context, setContext] = useState(null);
  const dialog = useRef(null), close = useRef(null), restore = useRef(null);
  const generation = useRef(0), pending = useRef(null), selectedBrowser = useRef(false);
  const refresh = useCallback(() => {
    if (pending.current) return pending.current;
    const current = ++generation.current;
    pending.current = api('browser-preparation').then(value => {
      if (current !== generation.current) return;
      setSnapshot(value); setError('');
      if (!selectedBrowser.current) {
        const available = value.browsers?.find(item => item.available);
        if (available) setBrowser(available.id);
      }
    }).catch(issue => { if (current === generation.current) setError(issue.message); })
      .finally(() => { if (current === generation.current) pending.current = null; });
    return pending.current;
  }, [api]);
  useEffect(() => {
    if (!enabled) return;
    refresh();
    const show = async event => {
      const detail = event.detail || null;
      try {
        const value = await api('browser-preparation');
        setSnapshot(value);
        const state = value.platforms?.find(item => item.platform === detail?.platform)?.state;
        // A connected browser's stale job status must not reopen setup.
        if (value.extension?.installed && detail?.status === 'needs_browser' && state === 'logged_in') return;
      } catch {}
      setContext(detail); setOpen(true); refresh();
    };
    window.addEventListener('tb:browser-preparation', show);
    window.addEventListener('focus', refresh);
    return () => { generation.current++; pending.current = null; window.removeEventListener('tb:browser-preparation', show); window.removeEventListener('focus', refresh); };
  }, [enabled, refresh]);
  useEffect(() => {
    if (!enabled || !snapshot?.available) return;
    const timer = setInterval(() => { if (!document.hidden) refresh(); }, open || !snapshot.ready ? 3000 : 30000);
    return () => clearInterval(timer);
  }, [enabled, snapshot?.available, snapshot?.ready, open, refresh]);
  useEffect(() => {
    const node = dialog.current;
    if (!node) return;
    if (open && !node.open) { restore.current = document.activeElement; node.showModal(); close.current?.focus(); }
    else if (!open && node.open) { node.close(); if (restore.current?.isConnected) restore.current.focus(); }
  }, [open, snapshot?.available]);
  async function action(action, platform) {
    if (busy) return;
    setBusy(true); setError(''); setMessage('');
    try {
      const value = await api('browser-preparation', {action, browser, ...(platform ? {platform} : {})});
      if (action === 'refresh') { setSnapshot(value); setMessage('正在后台同步四个平台的登录状态，无需打开原站页面。完成后可直接提交。'); }
      else setMessage(action === 'open-folder' ? '请选择这个包含 manifest.json 的文件夹。' : '请在打开的浏览器中完成操作，再回 TB 点击重新检测。');
    } catch (issue) { setError(issue.message); }
    finally { setBusy(false); }
  }
  async function copyPath() {
    try { await navigator.clipboard.writeText(snapshot.extensionPath); setMessage('扩展文件夹路径已复制。'); }
    catch { setMessage('请选中扩展文件夹路径后按 Ctrl+C 复制。'); }
  }
  if (!snapshot?.available) return null;
  const extension = snapshot.extension || {}, platforms = snapshot.platforms || [];
  const missing = platforms.filter(item => item.state !== 'logged_in');
  const status = !extension.installed ? '尚未安装或启用 TB 浏览器连接扩展'
    : !extension.connected ? '扩展已安装，浏览器当前未连接' : 'TB 浏览器连接扩展已连接';
  return <>
    {!snapshot.ready && <section className="browser-preparation-notice" aria-label="浏览器提交准备" role="status">
      <Plug size={16}/>
      <span>{!extension.installed ? '原站提交前，请先安装浏览器连接扩展，再登录原站账号。' : `原站提交准备：${missing.map(item => item.platform).join('、') || '浏览器连接'}还需检查。`}</span>
      <button className="browser-guide-button" onClick={() => { setContext(null); setOpen(true); refresh(); }}>查看准备说明</button>
    </section>}
    <dialog className="browser-preparation-dialog" ref={dialog} aria-labelledby="browser-preparation-title" onCancel={event => { event.preventDefault(); setOpen(false); }}>
      <header><div><h2 id="browser-preparation-title">浏览器提交准备</h2><p>按顺序完成一次，之后即可在 TB 提交题目。</p></div><button ref={close} className="browser-guide-button" aria-label="关闭浏览器准备说明" onClick={() => setOpen(false)}><X size={18}/></button></header>
      <div className="browser-guide-body">
        {context?.message && <p className="browser-guide-context" role="status">{context.message}</p>}
        <p>TB 账号和原站账号分别登录。请在<strong>同一个浏览器、同一个用户配置</strong>中安装扩展并登录，不使用无痕窗口。</p>
        <label className="browser-guide-browser">使用的浏览器<select aria-label="准备使用的浏览器" value={browser} onChange={event => { selectedBrowser.current = true; setBrowser(event.target.value); }}><option value="edge">Microsoft Edge</option><option value="chrome">Google Chrome</option></select></label>
        <ol className="browser-guide-steps">
          <li><h3>安装并启用 TB 浏览器连接</h3><p>{status}</p><p>打开扩展管理，开启“开发人员模式”（Chrome 为“开发者模式”），点击“加载解压缩的扩展程序”，选择下方文件夹。</p>
            <code>{browser === 'edge' ? 'edge://extensions' : 'chrome://extensions'}</code>
            <div className="browser-guide-actions"><button className="browser-guide-button" disabled={busy} onClick={() => action('open-extensions')}><ExternalLink size={14}/>打开扩展管理</button><button className="browser-guide-button" disabled={busy} onClick={() => action('open-folder')}><FolderOpen size={14}/>打开扩展文件夹</button></div>
            <label>扩展文件夹<input aria-label="扩展文件夹路径" readOnly value={snapshot.extensionPath || ''}/></label><button className="browser-guide-button" onClick={copyPath}>复制文件夹路径</button>
            <p>确认“TB 浏览器连接”已启用。已装过旧版时，点击扩展卡片上的“重新加载”，再刷新原站页面。</p>
          </li>
          <li><h3>在浏览器登录原站账号</h3><p>点击对应平台，在上面选择的浏览器登录。只使用某个平台时，先完成该平台即可。</p>
            <div className="browser-guide-platforms">{platforms.map(item => <div className={context?.platform === item.platform ? 'browser-guide-selected' : ''} key={item.platform}><strong>{item.platform === 'Codeforces' ? 'Codeforces（CF）' : item.platform}</strong><span className={item.state === 'logged_in' ? 'browser-login-ready' : ''}>{labels[item.state] || labels.unknown}</span><button className="browser-guide-button" disabled={busy} onClick={() => action('open-login', item.platform)}>打开{item.platform}登录</button><code>{item.loginUrl}</code></div>)}</div>
            <p>如果原站要求验证码或安全验证，请在原站完成。遇到提交页验证时，回到题目点击“在浏览器查看”。</p>
          </li>
          <li><h3>回到 TB 提交</h3><p>已安装扩展且在浏览器登录后，可直接回到题目点击“提交”。四个平台会自动同步，无需打开原站标签页或重复登录；提交时会再次检查实际会话。</p><button className="browser-guide-button" disabled={busy} onClick={() => action('refresh')}><RefreshCw size={14}/>{busy ? '正在操作…' : '重新检测浏览器准备'}</button><p>关闭浏览器后仍可使用已同步的有效会话，必要时 TB 会在后台唤醒扩展。检测不会发送代码；原站明确要求登录或验证时再按提示处理。</p></li>
        </ol>
        {error && <p className="browser-guide-error" role="alert">{error}</p>}{message && <p role="status">{message}</p>}
      </div>
      <footer><span>{snapshot.ready ? '准备完成，可以返回题目提交。' : '完成后再提交，训练和代码会保留。'}</span><button className="browser-guide-button" onClick={() => setOpen(false)}>返回工作台</button></footer>
    </dialog>
  </>;
}
