import { useCallback, useEffect, useState } from 'react';
import { Bell, Check, Play, RefreshCw, Target } from 'lucide-react';
import InlineTitle from '@/components/InlineTitle.jsx';
import { difficultyLabel } from '@/lib/practiceMetadata.js';
import '@/pages/GoalsPanel.css';

function useGoals(api) {
  const [data,setData]=useState({goals:[]}),[error,setError]=useState('');
  const reload=useCallback(()=>api('goals').then(value=>{setData(value);setError('');}).catch(issue=>setError(issue.message)),[api]);
  useEffect(()=>{reload();const visible=()=>{if(!document.hidden)reload();};const timer=setInterval(visible,60000);document.addEventListener('visibilitychange',visible);return()=>{clearInterval(timer);document.removeEventListener('visibilitychange',visible);};},[reload]);
  return {data,setData,error,setError,reload};
}

export function GoalReminder({api,onOpen}) {
  const {data}=useGoals(api);
  const incomplete=data.goals.filter(goal=>!goal.workloadCompleted&&(!goal.dailyTask.completed||goal.warnings.length));
  return incomplete.length>0&&<button className="goal-reminder topbar-status-chip" aria-label="目标任务提醒" onClick={onOpen}><Bell size={15}/><span>待办目标</span><b>{incomplete.length}</b></button>;
}

const blank=()=>({title:'CF 2200',kind:'cf',deadline:'',currentRating:1000,targetRating:2200,dailyMinutes:90,totalProblems:100});
export default function GoalsPanel({api,onTrain,onManage,dailyOnly=false,onChanged}) {
  const {data,setData,error,setError,reload}=useGoals(api);
  const [form,setForm]=useState(blank),[busy,setBusy]=useState(false),[confirm,setConfirm]=useState(null),[editing,setEditing]=useState(false);
  const change=patch=>setForm(value=>({...value,...patch}));
  async function save(event){event.preventDefault();setBusy(true);try{setData(await api('goals/save',form));setForm(blank());setEditing(false);setError('');await onChanged?.();}catch(issue){setError(issue.message);}finally{setBusy(false);}}
  async function archive(){setBusy(true);try{setData(await api('goals/archive',{id:confirm.id}));setConfirm(null);}catch(issue){setError(issue.message);}finally{setBusy(false);}}
  if (dailyOnly) {
    if (!data.goals.length && !error) return null;
    return <section className="training-goals" aria-label="目标每日任务">
      <div className="training-goals-heading"><span><Target size={15}/>今日目标</span><div><button className="text-button" aria-label="刷新目标进度" onClick={reload}><RefreshCw size={13}/></button>{onManage&&<button className="text-button" onClick={onManage}>管理目标</button>}</div></div>
      {error&&<p className="inline-error" role="alert">{error}</p>}
      {data.goals.map(goal=><article className="training-goal" key={goal.id}>
        <div className="training-goal-summary"><strong>{goal.title}</strong><span className={'training-goal-today'+(goal.dailyTask.completed?' completed':'')}>{goal.dailyTask.completed&&<Check size={13}/>}今日 <b>{goal.dailyTask.progress}/{goal.dailyTask.target}</b> 题{goal.dailyTask.completed?' · 已完成':''}</span><span>新题 <b>{goal.progress}/{goal.totalProblems}</b></span><span className="training-goal-schedule">本周 {goal.weeklyTarget} 题 · 剩余 {goal.remainingDays} 天</span><span className="training-goal-deadline">截止 {goal.deadline}</span></div>
        {(goal.warnings.length>0||(!goal.dailyTask.completed&&goal.dailyTask.problems.length>0))&&<details className="training-goal-details"><summary>{goal.warnings.length>0?'查看计划提醒':'推荐新题'}{!goal.dailyTask.completed&&goal.dailyTask.problems.length>0?` · ${goal.dailyTask.problems.length} 题`:''}</summary>{goal.warnings.map(warning=><p key={warning} className="goal-pressure" role="alert">{warning}</p>)}{!goal.dailyTask.completed&&<div className="goal-problems">{goal.dailyTask.problems.map(problem=><button className="secondary" key={problem.id} onClick={()=>onTrain(problem.id)}><Play size={13}/><InlineTitle>{problem.title}</InlineTitle><small>{problem.difficulty??'未评级'}</small></button>)}</div>}</details>}
      </article>)}
    </section>;
  }
  return <div className={'goals-page'+(dailyOnly?' goals-daily':'')} aria-label={dailyOnly?'目标每日任务':'目标计划'}>
    <div className="progress-section-heading"><h2><Target size={18}/>目标计划</h2><div><button className="text-button" onClick={reload}>刷新进度</button><button className="secondary" onClick={()=>{setForm(blank());setEditing(true);}}>新建目标</button></div></div>
    {(editing||!data.goals.length)&&<form className="goal-form" onSubmit={save}>
      <label>目标类型<select aria-label="目标类型" value={form.kind} onChange={event=>{const kind=event.target.value;change({kind,title:{cf:'CF 2200',xcpc:'区域赛银牌',lanqiao:'蓝桥杯国一',custom:''}[kind],targetRating:{cf:2200,xcpc:2000,lanqiao:1800,custom:1800}[kind]});}}><option value="cf">Codeforces 评级</option><option value="xcpc">XCPC 区域赛</option><option value="lanqiao">蓝桥杯</option><option value="custom">自定义目标</option></select></label>
      <label>具体目标<input aria-label="具体目标" value={form.title} onChange={event=>change({title:event.target.value})} maxLength={160} required/></label>
      <label>截止日期<input aria-label="目标截止日期" type="date" value={form.deadline} onChange={event=>change({deadline:event.target.value})} required/></label>
      <label>当前练习难度<input aria-label="当前练习难度" type="number" min={0} max={4000} value={form.currentRating} onChange={event=>change({currentRating:event.target.value})} required/></label>
      {form.kind==='custom'?<label>计划新题总数<input aria-label="目标新题总数" type="number" min={1} max={10000} value={form.totalProblems} onChange={event=>change({totalProblems:event.target.value})} required/></label>:<label>{form.kind==='cf'?'目标 CF 评级':'目标练习难度'}<input aria-label="目标练习难度" type="number" min={200} max={4000} value={form.targetRating} onChange={event=>change({targetRating:event.target.value})} required/></label>}
      <label>每日可用时间（分钟）<input aria-label="每日可用分钟" type="number" min={15} max={720} value={form.dailyMinutes} onChange={event=>change({dailyMinutes:event.target.value})} required/></label>
      <div className="progress-actions"><button className="primary" type="submit" disabled={busy}>{form.id?'保存目标调整':'生成目标计划'}</button>{data.goals.length>0&&<button className="secondary" type="button" onClick={()=>{setForm(blank());setEditing(false);}}>取消</button>}</div>
    </form>}
    {error&&<p className="inline-error" role="alert">{error}</p>}
    {confirm&&<div className="goal-archive-confirm" role="alertdialog" aria-label="归档目标确认"><p>归档“{confirm.title}”后停止每日提醒，保留计划和训练记录。</p><button className="secondary" disabled={busy} onClick={()=>setConfirm(null)}>取消</button><button className="primary" disabled={busy} onClick={archive}>确认归档</button></div>}
    {!data.goals.length&&<p className="progress-muted">填写目标和截止日期后，今日题目会自动加入我的训练。</p>}
    {data.contestPlan?.contests?.length > 0 && <section className="goal-card shared-contest-plan" aria-label="本周比赛题量">
      <div className="progress-section-heading"><h3>本周比赛与补题</h3><span>共 {data.contestPlan.total} 题</span></div>
      <p className="progress-small">合并 {data.contestPlan.goalCount} 个目标，同类比赛取最高题量与最高练习范围。</p>
      <div className="goal-contest-grid">{data.contestPlan.contests.map(item=><div key={item.contest}><strong>{item.contest}</strong><span>{item.problems} · <b>{item.target} 题 / 周</b></span>{item.questions?.length>0&&<details><summary>本周建议题目 · {item.questions.length} 题</summary><div className="goal-problems">{item.questions.map(problem=><button className="secondary" key={problem.id} onClick={()=>onTrain(problem.id)}><Play size={13}/><InlineTitle>{problem.title}</InlineTitle><small>{difficultyLabel(problem)}</small></button>)}</div></details>}</div>)}</div>
    </section>}
    {data.goals.map(goal=><section className="goal-card" key={goal.id}>
      <div className="progress-section-heading"><h3>{goal.title}</h3><span>截止 {goal.deadline}</span></div>
      <p>新题进度 <b>{goal.progress}/{goal.totalProblems}</b> · 剩余 {goal.remainingDays} 天 · 本周安排 <b>{goal.weeklyTarget}</b> 题{goal.workloadCompleted&&' · 已完成'}</p>
      {goal.warnings.map(warning=><p key={warning} className="goal-pressure" role="alert">{warning}</p>)}
      <div className="goal-daily-task"><strong>{goal.dailyTask.date} · 今日目标任务</strong><span>{goal.dailyTask.progress}/{goal.dailyTask.target} 道新题通过 · {goal.dailyTask.completed?'今日已完成':'尚未完成，请安排训练时间'}</span></div>
      <div className="goal-problems">{!goal.dailyTask.completed&&goal.dailyTask.problems.map(problem=><button className="secondary" key={problem.id} onClick={()=>onTrain(problem.id)}><Play size={13}/><InlineTitle>{problem.title}</InlineTitle><small>{problem.difficulty??'未评级'}</small></button>)}</div>
      <div className="progress-actions"><button className="text-button" onClick={()=>{setForm(goal);setEditing(true);setConfirm(null);document.getElementById('growth-goals')?.scrollIntoView({behavior:'smooth'});}}>调整目标</button><button className="text-button" onClick={()=>setConfirm(goal)}>归档目标</button></div>
    </section>)}
  </div>;
}
