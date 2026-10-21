import BoundedNumber from '@/components/BoundedNumber.jsx';
import ThemedSelect from '@/components/ThemedSelect.jsx';
import { useCallback, useEffect, useRef, useState } from 'react';
import { Plus, Settings2, Target, X } from 'lucide-react';
import '@/pages/GoalsPanel.css';

const blank = () => ({title:'CF 2200',kind:'cf',deadline:'',currentRating:1000,targetRating:2200,dailyMinutes:90,totalProblems:100});

export default function GoalsPanel({api, overview, onChanged}) {
  const [data,setData] = useState(overview || {goals:[]});
  const [form,setForm] = useState(null), [error,setError] = useState(''), [busy,setBusy] = useState(false), [archiving,setArchiving] = useState(false);
  const editor = useRef(null), returnFocus = useRef(null);
  const reload = useCallback(async () => {
    try { const value=await api('goals'); setData(value); return value; }
    catch (issue) { setError(issue.message); }
  }, [api]);
  useEffect(() => { if (overview) setData(overview); else reload(); }, [overview,reload]);
  useEffect(() => {
    if (!form) return;
    editor.current?.querySelector('input,select')?.focus();
    return () => returnFocus.current?.focus();
  }, [Boolean(form)]);
  const change = patch => setForm(previous=>({...previous,...patch}));
  const open = goal => { returnFocus.current=document.activeElement; setError(''); setArchiving(false); setForm(goal ? {...goal} : blank()); };
  const close = () => { if (!busy) { setForm(null); setError(''); } };
  async function save(event) {
    event.preventDefault(); setBusy(true); setError('');
    try { setData(await api('goals/save',form)); setForm(null); await onChanged?.(); }
    catch(issue) { setError(issue.message); }
    finally { setBusy(false); }
  }
  async function archive() {
    setBusy(true); setError('');
    try { setData(await api('goals/archive',{id:form.id})); setForm(null); await onChanged?.(); }
    catch(issue) { setError(issue.message); }
    finally { setBusy(false); }
  }
  function keydown(event) {
    if(event.key==='Escape') {event.stopPropagation(); close();}
    if(event.key==='Tab') {
      const fields=[...editor.current.querySelectorAll('button:not(:disabled),input,select')];
      if(event.shiftKey && document.activeElement===fields[0]) {event.preventDefault();fields.at(-1)?.focus();}
      else if(!event.shiftKey && document.activeElement===fields.at(-1)) {event.preventDefault();fields[0]?.focus();}
    }
  }
  return <div className="goal-manager" aria-label="目标管理">
    <div className="goal-management-bar"><span><Target size={17}/><strong>目标计划</strong>{data.goals.length>0&&<small>{data.goals.length} 个</small>}</span><div><button className="progress-text-button" onClick={()=>open()}><Plus size={15}/>新建目标</button><button className="progress-text-button" disabled={!data.goals.length} onClick={()=>open(data.goals[0])}><Settings2 size={15}/>调整目标</button></div></div>
    {form && <div className="goal-editor-backdrop" onMouseDown={event=>{if(event.target===event.currentTarget)close();}}><section ref={editor} className="goal-editor" role="dialog" aria-modal="true" aria-label={form.id?'调整目标':'新建目标'} onKeyDown={keydown}>
      <header><h2><Target size={19}/>{form.id?'调整目标':'新建目标'}</h2><button className="icon-button" aria-label="关闭目标设置" disabled={busy} onClick={close}><X size={18}/></button></header>
      {form.id&&data.goals.length>1&&<label className="goal-selector">选择目标<ThemedSelect aria-label="选择要调整的目标" value={form.id} onChange={event=>{setForm({...data.goals.find(goal=>goal.id===event.target.value)});setArchiving(false);}}>{data.goals.map(goal=><option key={goal.id} value={goal.id}>{goal.title}</option>)}</ThemedSelect></label>}
      <form className="goal-form" onSubmit={save}>
        <label>目标类型<ThemedSelect aria-label="目标类型" value={form.kind} onChange={event=>{const kind=event.target.value;change({kind,title:{cf:'CF 2200',xcpc:'区域赛银牌',lanqiao:'蓝桥杯国一',custom:''}[kind],targetRating:{cf:2200,xcpc:2000,lanqiao:1800,custom:1800}[kind]});}}><option value="cf">Codeforces 评级</option><option value="xcpc">XCPC 区域赛</option><option value="lanqiao">蓝桥杯</option><option value="custom">自定义目标</option></ThemedSelect></label>
        <label>目标名称<input aria-label="具体目标" value={form.title} onChange={event=>change({title:event.target.value})} maxLength={160} required/></label>
        <label>截止日期<input aria-label="目标截止日期" type="date" value={form.deadline} onChange={event=>change({deadline:event.target.value})} required/></label>
        <label>当前练习难度<BoundedNumber aria-label="当前练习难度" type="number" min={0} max={4000} value={form.currentRating} onChange={event=>change({currentRating:event.target.value})} required/></label>
        {form.kind==='custom'?<label>新题总数<BoundedNumber aria-label="目标新题总数" type="number" min={1} max={10000} value={form.totalProblems} onChange={event=>change({totalProblems:event.target.value})} required/></label>:<label>目标参考值<BoundedNumber aria-label="目标练习难度" type="number" min={200} max={4000} value={form.targetRating} onChange={event=>change({targetRating:event.target.value})} required/></label>}
        <label>每日时间（分钟）<BoundedNumber aria-label="每日可用分钟" type="number" min={15} max={720} value={form.dailyMinutes} onChange={event=>change({dailyMinutes:event.target.value})} required/></label>
        <p className="goal-editor-note">题目会加入每日任务及训练列表的“今日目标”。新比赛按目标要求补充，已确认 AC 自动完成。</p>
        {error&&<p className="inline-error" role="alert">{error}</p>}
        {archiving&&<div className="goal-archive-confirm" role="alertdialog" aria-label="归档目标确认"><span>停止此目标的后续安排，保留训练记录。</span><button type="button" className="secondary" disabled={busy} onClick={()=>setArchiving(false)}>返回</button><button type="button" className="primary" disabled={busy} onClick={archive}>归档目标</button></div>}
        <footer className="progress-actions">{form.id&&<button type="button" className="progress-text-button" disabled={busy} onClick={()=>setArchiving(true)}>归档</button>}<span/><button type="button" className="secondary" disabled={busy} onClick={close}>取消</button><button className="primary" disabled={busy} type="submit">{busy?'保存中…':'保存目标'}</button></footer>
      </form>
    </section></div>}
    {!form&&error&&<p className="inline-error" role="alert">{error}</p>}
  </div>;
}
