import {useEffect,useLayoutEffect,useMemo,useRef,useState} from 'react';
import {CalendarDays,ChevronLeft,ChevronRight} from 'lucide-react';
import Tooltip from '@/components/Tooltip.jsx';
import {trainingDay} from '@/lib/trainingDate.js';

const levelOf = count => count <= 0 ? 0 : count === 1 ? 1 : count <= 3 ? 2 : count <= 6 ? 3 : 4;
const toKey = date => date.toISOString().slice(0,10);
export function monthDays(month) {
  if (!/^\d{4}-(0[1-9]|1[0-2])$/.test(month)) return [];
  const [year,index]=month.split('-').map(Number),count=new Date(Date.UTC(year,index,0)).getUTCDate();
  return Array.from({length:count},(_,i)=>`${month}-${String(i+1).padStart(2,'0')}`);
}

export default function ActivityPage({insights}) {
  const [now,setNow]=useState(Date.now),today=trainingDay(now),[month,setMonth]=useState(()=>trainingDay().slice(0,7));
  const [selected,setSelected]=useState(today),[page,setPage]=useState(1),[pageSize,setPageSize]=useState(5);
  const detail=useRef(null),head=useRef(null),foot=useRef(null),rowHeight=useRef(44),buttons=useRef(new Map());
  useEffect(()=>{const timer=setInterval(()=>setNow(Date.now()),30000);return()=>clearInterval(timer);},[]);
  const activity=useMemo(()=>new Map((insights?.activity||[]).map(item=>[item.date,item])),[insights?.activity]);
  const days=useMemo(()=>monthDays(month),[month]),available=useMemo(()=>days.filter(day=>day<=today),[days,today]);
  const offset=days.length?(new Date(days[0]+'T00:00:00Z').getUTCDay()+6)%7:0;
  const records=useMemo(()=>days.filter(day=>activity.has(day)&&day<=today).reverse(),[days,activity,today]);
  const pages=Math.max(1,Math.ceil(records.length/pageSize)),currentPage=Math.min(page,pages);
  const visible=records.slice((currentPage-1)*pageSize,currentPage*pageSize);
  const firstMonth=[...activity.keys(),today].sort()[0]?.slice(0,7)||today.slice(0,7);
  const pick=day=>{setSelected(day);requestAnimationFrame(()=>buttons.current.get(day)?.focus({preventScroll:true}));};
  useEffect(()=>{
    const move=event=>{
      if(event.defaultPrevented||event.altKey||event.ctrlKey||event.metaKey||!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(event.key)||event.target.closest?.('input,textarea,select,[contenteditable=true],dialog,.tb-select-menu'))return;
      if(!available.length)return;
      const index=Math.max(0,available.indexOf(selected)),delta={ArrowLeft:-1,ArrowRight:1,ArrowUp:-7,ArrowDown:7}[event.key];
      event.preventDefault();pick(available[Math.max(0,Math.min(available.length-1,index+delta))]);
    };
    window.addEventListener('keydown',move);return()=>window.removeEventListener('keydown',move);
  },[available,selected]);
  useLayoutEffect(()=>{
    if(!detail.current)return;
    const resize=()=>{
      const measured=detail.current.querySelector('tbody tr')?.getBoundingClientRect().height;
      if(measured>20)rowHeight.current=measured;
      const size=detail.current.clientHeight-(head.current?.offsetHeight||42)-(foot.current?.offsetHeight||38)-(detail.current.querySelector('thead')?.getBoundingClientRect().height||34)-24;
      setPageSize(Math.max(1,Math.floor(size/rowHeight.current)));
    };
    const observer=new ResizeObserver(resize);observer.observe(detail.current);resize();return()=>observer.disconnect();
  },[records.length,month]);
  useEffect(()=>{setPage(1);},[month,pageSize]);
  const changeMonth=next=>{if(!monthDays(next).length)return;setMonth(next);setSelected(next===today.slice(0,7)?today:next+'-01');setPage(1);};
  if(!insights)return <p role="status">正在读取活动记录…</p>;
  return <div className="activity-page activity-month-page" aria-label="训练活动">
    <section className="progress-section activity-month-panel" aria-label="月度训练日历">
      <header className="activity-month-heading"><h2><CalendarDays size={18}/><time dateTime={selected}>{selected.replaceAll('-','/')}</time><span className="activity-selected-count">AC<span className="metric-separator">:</span><b>{activity.get(selected)?.officialAccepted||0}</b></span><Tooltip label="训练日历说明" text="按北京时间统计原站 AC，同题同日计一次。直接按方向键切换日期，移动后立即显示当天记录。"/></h2><label className="activity-month-picker"><span>时间</span><input type="month" aria-label="活动时间" value={month} min={firstMonth} max={today.slice(0,7)} onChange={event=>changeMonth(event.target.value)}/></label></header>
      <div className="activity-month-grid" role="grid" aria-label={`${month}月训练日历，方向键切换日期`}>
        {['一','二','三','四','五','六','日'].map(day=><span key={day} className="activity-weekday" role="columnheader">{day}</span>)}
        {Array.from({length:offset},(_,index)=><span key={'pad'+index} className="activity-month-padding" role="presentation"/>)}
        {days.map(day=>{const count=activity.get(day)?.officialAccepted||0;return <button type="button" role="gridcell" key={day} ref={node=>{if(node)buttons.current.set(day,node);else buttons.current.delete(day);}} className={`activity-day activity-level-${levelOf(count)}${selected===day?' activity-selected':''}`} disabled={day>today} tabIndex={day===selected?0:-1} aria-label={`${day}，${count} 题通过`} aria-selected={day===selected} title={`${day} · AC : ${count}`} onFocus={()=>setSelected(day)} onClick={()=>pick(day)}><span>{Number(day.slice(-2))}</span>{count>0&&<b>{count}</b>}</button>;})}
      </div>
    </section>
    <section ref={detail} className="progress-section activity-month-details" aria-label="日期明细">
      <header ref={head} className="activity-detail-heading"><h2>日期明细</h2><span>{month.replace('-','年')}月 · {records.length} 天</span></header>
      <div className="activity-detail-table"><table><thead><tr><th>日期</th><th>AC</th></tr></thead><tbody>{visible.map(day=><tr key={day} data-selected={day===selected}><td><button type="button" className="progress-text-button" onClick={()=>pick(day)}>{day.replaceAll('-','/')}</button></td><td>{activity.get(day)?.officialAccepted||0}</td></tr>)}</tbody></table>{!records.length&&<p className="progress-muted">本月还没有活动记录。</p>}</div>
      <footer ref={foot} className="activity-pagination"><span>每页 {pageSize} 行</span><button type="button" className="icon-button" aria-label="上一页日期明细" disabled={currentPage<=1} onClick={()=>setPage(value=>value-1)}><ChevronLeft size={16}/></button><span>{currentPage} / {pages}</span><button type="button" className="icon-button" aria-label="下一页日期明细" disabled={currentPage>=pages} onClick={()=>setPage(value=>value+1)}><ChevronRight size={16}/></button></footer>
    </section>
  </div>;
}
