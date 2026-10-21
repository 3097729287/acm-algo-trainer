import FilterMenu from '@/components/FilterMenu.jsx';
import { CONTEST_SHELVES } from '@/components/ContestTabs.jsx';
import { matchesShelf } from '@/lib/contestShelves.js';
import Tooltip from '@/components/Tooltip.jsx';
import BoundedNumber from '@/components/BoundedNumber.jsx';
import ThemedSelect from '@/components/ThemedSelect.jsx';
import { useEffect, useMemo, useRef, useState } from 'react';
import { Clock, Flag, LoaderCircle, Play, RefreshCw, Search } from 'lucide-react';

export default function MockSetup({ api, onStarted, onError, activeContest, onResume, categories = [], platforms = [] }) {
  const [config, setConfig] = useState({ mode: 'comprehensive', count: 6, duration: 120, min: 0, max: 10000, tags: [], platform: '', excludeSolved: true, reviewedOnly: false, rules: 'acm', wrongPenalty: 20, compilePenalty: false, contest: '' });
  const [events, setEvents] = useState([]);
  const [eventQuery, setEventQuery] = useState('');
  const shownEvents = useMemo(() => events.filter(item => (config.platform ? matchesShelf(item,config.platform) : true) && (Number(config.min)===0 && Number(config.max)===10000 || item.difficulty != null && item.difficulty>=Number(config.min) && item.difficulty<=Number(config.max))).filter(item => eventQuery.trim().toLowerCase().split(/\s+/).every(word => `${item.displayName || item.name} ${item.name}`.toLowerCase().includes(word))).sort((a,b) => (b.displayName || b.name).localeCompare(a.displayName || a.name, 'zh-CN', {numeric:true})), [events, eventQuery, config.platform, config.min, config.max]);
  const replay = config.mode === 'replay';
  useEffect(() => { if (!replay) return; let alive = true; api('contests/events').then(result => { if (alive) setEvents(result.events || []); }).catch(issue => { if (alive) setError(issue.message); }); return () => { alive = false; }; }, [replay, api]);
  const [plan, setPlan] = useState(null), [busy, setBusy] = useState(false), [name, setName] = useState(''), [error, setError] = useState(''), [topic, setTopic] = useState('');
  const sequence = useRef(0);
  const topics = useMemo(() => { const result = []; const walk = (nodes, depth = 0) => nodes.forEach(node => { result.push({ ...node, depth }); walk(node.children || [], depth + 1); }); walk(categories); return result; }, [categories]);
  const change = patch => { setConfig(previous => ({ ...previous, ...patch })); setPlan(null); setError(''); sequence.current++; };
  const valid = [config.min, config.max, config.duration].every(value => String(value).trim() !== '' && Number.isFinite(Number(value))) && Number(config.min) <= Number(config.max) && Number(config.duration) >= 1 && Number(config.duration) <= 1440 && (config.mode !== 'topic' || config.tags.length > 0) && (!replay || !!config.contest);
  async function generate() {
    const seq = ++sequence.current; setBusy(true); setError('');
    try { const result = await api('contests/preview', { ...config, wrongPenalty: Number(config.wrongPenalty), count: config.mode === 'single' ? 1 : Number(config.count), duration: Number(config.duration), min: Number(config.min), max: Number(config.max), tags: config.mode === 'topic' ? config.tags : [] }); if (sequence.current === seq) setPlan(result.plan); }
    catch (issue) { if (sequence.current === seq) setError(issue.message); }
    finally { if (sequence.current === seq) setBusy(false); }
  }
  async function start() {
    if (!plan || busy) return; setBusy(true); setError('');
    try { const result = await api('contests/start', { previewId: plan.previewId, ids: plan.slots.map(slot => slot.id), duration: Number(config.duration), name: name.trim() || plan.name }); onStarted(result); }
    catch (issue) { setError(issue.message); onError?.(issue.message, 'error'); setBusy(false); }
  }
  return <div className="mock-create"><section className="create-main">
    {activeContest && <div className="active-notice"><Clock size={17} /><span>你有一场进行中的模拟赛</span><button className="primary" onClick={onResume}>继续比赛</button></div>}
    <div className="mock-config">
      <div className="mock-mode-options" role="group" aria-label="组题方式">{[['comprehensive', '综合训练', '多种知识点，逐步增加难度'], ['topic', '专项训练', '指定某个领域或知识点'], ['single', '随机单题', '抽取一道适合难度的题'], ['replay', '重现赛', '保留已收录比赛全部题序']].map(([mode, title, description]) => <Tooltip text={description} key={mode}><button aria-pressed={config.mode === mode} className={config.mode === mode ? 'active' : ''} disabled={busy} onClick={() => change({ mode })}><strong>{title}</strong></button></Tooltip>)}</div>
      <div className="mock-difficulty-row"><span>难度</span><div className="difficulty-presets" role="radiogroup" aria-label="训练难度">{[['简单',0,1600,'easy'],['普通',1600,2200,'normal'],['困难',2200,10000,'hard']].map(([label,min,max,tone])=><button type="button" key={label} className={`difficulty-${tone}`} role="radio" aria-checked={Number(config.min)===min&&Number(config.max)===max} disabled={busy} onClick={()=>change({min,max})}><i/>{label}</button>)}</div><span className="difficulty-range-label">{config.min}–{config.max}</span>
      <FilterMenu label="训练筛选" active={config.mode==='topic'?!!config.tags.length:replay?!!config.contest:!!config.platform}>
        {replay&&<><label className="filter-field"><span>比赛</span><input aria-label="搜索重现赛比赛" placeholder="搜索比赛" value={eventQuery} onChange={event=>setEventQuery(event.target.value)}/></label><ThemedSelect aria-label="重现赛比赛" value={config.contest} disabled={busy} onChange={event=>{const item=events.find(item=>item.name===event.target.value);change({contest:event.target.value,...(item?{duration:item.duration,rules:item.rules}:{})});}}><option value="">选择比赛</option>{config.contest&&!shownEvents.some(item=>item.name===config.contest)&&<option value={config.contest}>{events.find(item=>item.name===config.contest)?.displayName||config.contest}</option>}{shownEvents.map(item=><option key={item.name} value={item.name}>{item.displayName||item.name} · {item.count} 题</option>)}</ThemedSelect><Tooltip text="难度用于筛选整场比赛的中位难度；保留原赛全部题序。未定级比赛只在 0–10000 范围内展示。" label="重现赛难度说明"/></>}
        {config.mode==='topic'&&<label className="filter-field"><span>知识点</span><ThemedSelect aria-label="专项训练知识点" value={topic} disabled={busy} onChange={event=>{setTopic(event.target.value);const node=topics.find(item=>item.name===event.target.value);change({tags:node?.tags||[event.target.value]});}}><option value="">选择知识点</option>{topics.map((item,index)=><option key={item.name+index} value={item.name}>{'　'.repeat(item.depth)}{item.name}</option>)}</ThemedSelect></label>}
        <details className="filter-submenu"><summary>比赛分类</summary><div className="filter-choice-grid">{CONTEST_SHELVES.map(([id,label])=><button type="button" key={id} aria-pressed={(config.platform||'all')===id} disabled={busy} onClick={()=>change({platform:id==='all'?'':id})}>{label}</button>)}</div></details>
        <label className="filter-field"><span>最低难度</span><BoundedNumber aria-label="模拟赛最低难度" min={0} max={10000} step={100} value={config.min} disabled={busy} onChange={event=>change({min:Number(event.target.value)})}/></label><label className="filter-field"><span>最高难度</span><BoundedNumber aria-label="模拟赛最高难度" min={0} max={10000} step={100} value={config.max} disabled={busy} onChange={event=>change({max:Number(event.target.value)})}/></label>
        {!replay&&<><label className="filter-field"><span>题目数</span><BoundedNumber aria-label="模拟赛题目数" min={1} max={20} required value={config.mode==='single'?1:config.count} disabled={busy||config.mode==='single'} onChange={event=>change({count:Number(event.target.value)})}/></label><label className="filter-field"><span>排除已通过</span><input type="checkbox" aria-label="排除已通过题目" checked={config.excludeSolved} onChange={event=>change({excludeSolved:event.target.checked})}/></label><label className="filter-field"><span>完整本地评测</span><input type="checkbox" aria-label="只选本地完整评测题" checked={config.reviewedOnly} onChange={event=>change({reviewedOnly:event.target.checked})}/></label></>}
        <label className="filter-field"><span>赛制</span><ThemedSelect aria-label="模拟赛赛制" value={config.rules} disabled={busy} onChange={event=>change({rules:event.target.value,wrongPenalty:20,compilePenalty:false,...(event.target.value==='xcpc'?{duration:300}:{})})}><option value="acm">ACM</option><option value="xcpc">XCPC</option></ThemedSelect></label><label className="filter-field"><span>错误罚时</span><BoundedNumber aria-label="错误罚时" min={0} max={120} unit="分钟" value={config.wrongPenalty} onChange={event=>change({wrongPenalty:Number(event.target.value)})}/></label><label className="filter-field"><span>编译错误计罚</span><input type="checkbox" aria-label="编译错误计罚时" checked={config.compilePenalty} onChange={event=>change({compilePenalty:event.target.checked})}/></label>
        <label className="filter-field"><span>时长</span><BoundedNumber aria-label="模拟赛时长" min={1} max={1440} unit="分钟" value={config.duration} disabled={busy} onChange={event=>change({duration:Number(event.target.value)})}/></label><label className="filter-field"><span>名称</span><input aria-label="试卷名称" value={name} onChange={event=>setName(event.target.value)} maxLength={80}/></label>
      </FilterMenu></div>
      {config.mode==='topic'&&<button className="training-selection-chip" disabled type="button">{topic||'从筛选中选择知识点'}</button>}{replay&&<button className="training-selection-chip" disabled type="button">{events.find(item=>item.name===config.contest)?.displayName||config.contest||'从筛选中选择比赛'}</button>}

    </div>
    {error && <div className="inline-error" role="alert">{error}</div>}
    <div className="create-buttons"><button className={plan ? 'secondary' : 'primary'} onClick={generate} disabled={busy || !!activeContest || !valid}>{busy ? <LoaderCircle size={16} className="spin" /> : <RefreshCw size={16} />}{plan ? '重新组题' : replay ? '预览重现赛' : config.mode === 'single' ? '抽取单题' : '生成试卷'}</button>{plan && <button className="primary" onClick={start} disabled={busy || !!activeContest}><Play size={16} />开始 {config.duration} 分钟训练</button>}</div>
    {plan && <div className="paper-preview" aria-label="训练试卷预览"><div className="paper-preview-title"><span>{config.mode === 'topic' ? `专项训练 · ${topic}` : config.mode === 'single' ? '随机单题' : replay ? `重现赛 · ${plan.event?.displayName || plan.event?.name || config.contest}` : '综合训练'}</span><span>{plan.slots.length} 题 · {config.duration} 分钟</span></div>{plan.slots.map((slot, index) => <div className="paper-slot" key={slot.id}><strong>{slot.letter || String.fromCharCode(65 + index)}</strong><div><span>{slot.judgeScope === 'local' ? '本地完整评测' : '官方样例评测'}</span><small>考点在训练结束后显示</small></div></div>)}{plan.selectionNotice && <p className="selection-notice" role="status">{plan.selectionNotice}</p>}{plan.event && <p>{plan.event.durationSource}{plan.event.complete == null ? '；按已收录题单重现，原赛完整性尚未核验。' : '；已核对题数。'}</p>}<p>代码按题自动保存；离开页面后倒计时继续。</p></div>}

  </section></div>;
}
