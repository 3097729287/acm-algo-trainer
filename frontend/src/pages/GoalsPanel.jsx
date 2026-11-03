import BoundedNumber from '@/components/BoundedNumber.jsx';
import {DifficultySlider} from '@/components/DifficultyRange.jsx';
import ThemedSelect from '@/components/ThemedSelect.jsx';
import { useCallback, useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { Plus, Target, X } from 'lucide-react';
import '@/pages/GoalsPanel.css';

const blank = () => ({title:'CF 2200',kind:'cf',deadline:'',currentRating:1000,targetRating:2200,dailyMinutes:90,totalProblems:100});

export default function GoalsPanel({api, overview, onChanged, onClose}) {
  const [data,setData] = useState(overview || {goals:[]});
  const [form,setForm] = useState(()=>overview?.goals?.[0]?{...overview.goals[0]}:blank()), [error,setError] = useState(''), [busy,setBusy] = useState(false), [archiving,setArchiving] = useState(false);
  const editor = useRef(null), returnFocus = useRef(document.activeElement), initialized=useRef(Boolean(overview)), edited=useRef(false);
  const reload = useCallback(async () => {
    try { const value=await api('goals'); setData(value); if(!initialized.current&&!edited.current&&value.goals?.[0])setForm({...value.goals[0]});initialized.current=true;return value; }
    catch (issue) { setError(issue.message); }
  }, [api]);
  useEffect(() => { if (overview) setData(overview); else reload(); }, [overview,reload]);
  useEffect(() => {
    if (!form) return;
    editor.current?.querySelector('input,select')?.focus();
    return () => returnFocus.current?.focus();
  }, [Boolean(form)]);
  const change = patch => {edited.current=true;setForm(previous=>({...previous,...patch}));};
  const open = goal => { edited.current=true;setError(''); setArchiving(false); setForm(goal ? {...goal} : blank()); };
  const close = () => { if (!busy) onClose?.(); };
  async function save(event) {
    event.preventDefault(); setBusy(true); setError('');
    try { setData(await api('goals/save',form)); await onChanged?.(); onClose?.(); }
    catch(issue) { setError(issue.message); }
    finally { setBusy(false); }
  }
  async function archive() {
    setBusy(true); setError('');
    try { setData(await api('goals/archive',{id:form.id})); await onChanged?.(); onClose?.(); }
    catch(issue) { setError(issue.message); }
    finally { setBusy(false); }
  }
  function keydown(event) {
    if(event.key==='Escape') {event.stopPropagation(); close();}
    if(event.key==='Tab') {
      const fields=[...editor.current.querySelectorAll('button:not(:disabled),input:not(:disabled),select:not(:disabled)')].filter(node=>node.getClientRects().length);
      if(event.shiftKey && document.activeElement===fields[0]) {event.preventDefault();fields.at(-1)?.focus();}
      else if(!event.shiftKey && document.activeElement===fields.at(-1)) {event.preventDefault();fields[0]?.focus();}
    }
  }
  return createPortal(<div className="goal-editor-backdrop" onMouseDown={event=>{if(event.target===event.currentTarget)close();}}><section ref={editor} className="goal-editor" role="dialog" aria-modal="true" aria-label={form.id?'调整目标':'新建目标'} onKeyDown={keydown}>
      <header><h2><Target size={19}/>{form.id?'调整目标':'新建目标'}</h2><div className="goal-dialog-actions"><button type="button" className="icon-button" aria-label="新建目标" title="新建目标" disabled={busy||!form.id} onClick={()=>open()}><Plus size={18}/></button><button type="button" className="icon-button" aria-label="关闭目标设置" disabled={busy} onClick={close}><X size={18}/></button></div></header>
      {data.goals.length>0&&<label className="goal-selector">选择目标<ThemedSelect aria-label="选择要调整的目标" disabled={busy} value={form.id||''} onChange={event=>open(data.goals.find(goal=>goal.id===event.target.value))}>{!form.id&&<option value="">新建目标</option>}{data.goals.map(goal=><option key={goal.id} value={goal.id}>{goal.title}</option>)}</ThemedSelect></label>}
      <form className="goal-form" onSubmit={save}>
        <label>目标类型<ThemedSelect aria-label="目标类型" value={form.kind} onChange={event=>{const kind=event.target.value;change({kind,title:{cf:'CF 2200',xcpc:'区域赛银牌',lanqiao:'蓝桥杯国一',custom:''}[kind],targetRating:{cf:2200,xcpc:2000,lanqiao:1800,custom:1800}[kind]});}}><option value="cf">Codeforces 评级</option><option value="xcpc">XCPC 区域赛</option><option value="lanqiao">蓝桥杯</option><option value="custom">自定义目标</option></ThemedSelect></label>
        <label>目标名称<input aria-label="具体目标" value={form.title} onChange={event=>change({title:event.target.value})} maxLength={160} required/></label>
        <label>截止日期<input aria-label="目标截止日期" type="date" value={form.deadline} onChange={event=>change({deadline:event.target.value})} required/></label>
        <label>当前练习难度<DifficultySlider label="当前练习难度" value={form.currentRating} onChange={event=>change({currentRating:event.target.value})}/></label>
        {form.kind==='custom'?<label>新题总数<BoundedNumber aria-label="目标新题总数" type="number" min={1} max={10000} value={form.totalProblems} onChange={event=>change({totalProblems:event.target.value})} required/></label>:<label>目标参考值<DifficultySlider label="目标练习难度" min={200} value={form.targetRating} onChange={event=>change({targetRating:event.target.value})}/></label>}
        <label>每日时间（分钟）<BoundedNumber aria-label="每日可用分钟" type="number" min={15} max={720} value={form.dailyMinutes} onChange={event=>change({dailyMinutes:event.target.value})} required/></label>

        {error&&<p className="inline-error" role="alert">{error}</p>}
        {archiving&&<div className="goal-archive-confirm" role="alertdialog" aria-label="归档目标确认"><span>停止此目标的后续安排，保留训练记录。</span><button type="button" className="secondary" disabled={busy} onClick={()=>setArchiving(false)}>返回</button><button type="button" className="primary" disabled={busy} onClick={archive}>归档目标</button></div>}
        <footer className="progress-actions">{form.id&&<button type="button" className="progress-text-button" disabled={busy} onClick={()=>setArchiving(true)}>归档</button>}<span/><button type="button" className="secondary" disabled={busy} onClick={close}>取消</button><button className="primary" disabled={busy} type="submit">{busy?'保存中…':'保存目标'}</button></footer>
      </form>
    </section></div>,document.body);
}
