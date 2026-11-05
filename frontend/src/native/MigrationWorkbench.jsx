import { useEffect, useState } from 'react';
import { request } from '../api/client.js';
import './migration.css';

// A development-only diagnostic entrypoint. The regular React application and
// every product page stay in place until the native compatibility gate passes.
export default function MigrationWorkbench() {
  const [capabilities, setCapabilities] = useState(null), [catalog, setCatalog] = useState(null);
  const [statement, setStatement] = useState(null), [error, setError] = useState('');
  useEffect(() => {
    let active = true;
    Promise.all([request('api/capabilities'), request('library/page?limit=30')])
      .then(([report, library]) => { if (active) { setCapabilities(report); setCatalog(library); } })
      .catch(issue => { if (active) setError(issue.message); });
    return () => { active = false; };
  }, []);
  const open = id => request(`library/statement?id=${encodeURIComponent(id)}`).then(value => { setStatement(value); setError(''); }).catch(issue => setError(issue.message));
  return <main className="native-migration">
    <header><span className="native-brand">ToBe</span><div><h1>Rust 迁移验证</h1><p>React → Tauri IPC → Rust → SQLite</p></div></header>
    {error && <p role="alert">{error}</p>}
    <section className="native-progress" aria-label="迁移状态">
      <strong>{capabilities ? `${capabilities.legacyImplemented} / ${capabilities.legacyTotal}` : '读取中'}</strong>
      <div><p>已接入的原有接口</p><p>仅供本地测试；正式更新继续使用原有架构。</p></div>
      <button className="native-open-workspace" onClick={() => { location.hash = 'native-workspace'; }}>打开本地测试工作区</button>
    </section>
    <div className="native-columns">
      <section className="native-catalog"><h2>现有题库 <small>{catalog?.total?.toLocaleString()} 道</small></h2>
        <div role="list">{catalog?.rows.map(row => <button key={row.id} role="listitem" onClick={() => open(row.id)}><span>{row.title}</span><small>{row.contest} {row.problem}</small></button>)}</div>
      </section>
      <section className="native-reading" aria-label="题面读取"><h2>{statement?.title || '点击题目验证原有内容'}</h2>
        {statement && <><pre>{statement.markdown || statement.statementError}</pre><p>{statement.samples?.length || 0} 组原始样例</p></>}
        {!statement && <ul>{capabilities?.pendingDomains.map(domain => <li key={domain}>{domain}</li>)}</ul>}
      </section>
    </div>
  </main>;
}
