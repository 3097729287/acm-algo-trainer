import './startup.css';

export default function StartupScreen({ restoring = false, error = '', onRetry }) {
  return <main className="startup-screen" aria-busy={!error} aria-label="TB 启动">
    <section className="startup-content">
      <div className="startup-logo" aria-hidden="true">TB</div>
      <h1>正在加载 TB</h1>
      <p role="status">{restoring ? '正在恢复登录与学习记录…' : '正在准备训练工作台…'}</p>
      {!error && <div className="startup-progress" role="progressbar" aria-label="正在加载"><span/></div>}
      {error && <div className="startup-issue"><p role="alert">{error}</p><button type="button" onClick={onRetry}>重新连接</button></div>}
    </section>
  </main>;
}
