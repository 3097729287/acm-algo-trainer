import BrandWordmark from '../components/BrandWordmark.jsx';
import {BookOpen,ChartNoAxesCombined,Clock,Flag,FolderOpen,History,Library,LoaderCircle,Settings,Target} from 'lucide-react';
import './startup.css';

export default function StartupScreen({ restoring = false, error = '', onRetry }) {
  return <main className="startup-screen" aria-busy={!error} aria-label="ToBe 启动">
    <aside className="startup-navigation" aria-hidden="true"><div className="startup-brand"><BrandWordmark/></div>{[[Target,'我的训练'],[Library,'题库'],[FolderOpen,'题单'],[Flag,'比赛'],[Clock,'模拟赛'],[ChartNoAxesCombined,'成长'],[History,'提交记录'],[BookOpen,'从零讲']].map(([Icon,label])=><span key={label}><Icon size={18}/>{label}</span>)}<span className="startup-settings"><Settings size={18}/>设置</span></aside>
    <header className="startup-topbar" aria-hidden="true"><span className="startup-search"/></header>
    <section className="startup-content">
      <div className="startup-logo" aria-hidden="true"><BrandWordmark/></div>
      <h1>正在加载 ToBe</h1>
      <p role="status">{restoring ? '正在恢复登录与学习记录…' : '正在准备训练工作台…'}</p>
      {!error && <div className="startup-progress" role="progressbar" aria-label="正在加载"><span/></div>}
      {error && <div className="startup-issue"><p role="alert">{error}</p><button type="button" onClick={onRetry}>重新连接</button></div>}
    </section>
  </main>;
}
