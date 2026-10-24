import {useEffect,useLayoutEffect,useMemo,useRef,useState} from 'react';
import {CalendarDays,ChevronLeft,ChevronRight,Search} from 'lucide-react';
import Tooltip from '@/components/Tooltip.jsx';
import PageSearch from '@/components/PageSearch.jsx';
import ActivityProgress from '@/components/ActivityProgress.jsx';
import {trainingDay} from '@/lib/trainingDate.js';
import {parseActivityDate,fitActivityGrid,activitySegmentSize} from '@/lib/activityDate.js';

const levelOf=count=>count<=0?0:count===1?1:count<=3?2:count<=6?3:4;
export function monthDays(month) {
 if(!/^\d{4}-(0[1-9]|1[0-2])$/.test(month))return [];
 const [year,index]=month.split('-').map(Number),count=new Date(Date.UTC(year,index,0)).getUTCDate();
 return Array.from({length:count},(_,i)=>`${month}-${String(i+1).padStart(2,'0')}`);
}
export default function ActivityPage({insights}) {
 const [now,setNow]=useState(Date.now),today=trainingDay(now);
 const [month,setMonth]=useState(()=>trainingDay().slice(0,7)),[selected,setSelected]=useState(today),[query,setQuery]=useState('');
 const [page,setPage]=useState(1),[pageSize,setPageSize]=useState(5),[grid,setGrid]=useState({columns:16,size:40});
 const gridRef=useRef(null),tableRef=useRef(null),buttons=useRef(new Map());
 useEffect(()=>{const timer=setInterval(()=>setNow(Date.now()),30000);return()=>clearInterval(timer);},[]);
 const activity=useMemo(()=>new Map((insights?.activity||[]).map(item=>[item.date,item])),[insights?.activity]);
 const days=useMemo(()=>monthDays(month),[month]),available=useMemo(()=>days.filter(day=>day<=today),[days,today]);
 const searchedDate=parseActivityDate(query),invalid=Boolean(query.trim())&&!searchedDate;
 const records=useMemo(()=>days.filter(day=>activity.has(day)&&day<=today&&(!searchedDate||day===searchedDate)).reverse(),[days,activity,today,searchedDate]);
 const step=activitySegmentSize(Math.max(0,...days.map(day=>activity.get(day)?.officialAccepted||0)));
 const pages=Math.max(1,Math.ceil(records.length/pageSize)),currentPage=Math.min(page,pages);
 const visible=records.slice((currentPage-1)*pageSize,currentPage*pageSize);
 const pick=(day,focus=true)=>{setSelected(day);if(focus)requestAnimationFrame(()=>buttons.current.get(day)?.focus({preventScroll:true}));};
 useEffect(()=>{
  if(!searchedDate)return;
  setMonth(searchedDate.slice(0,7));setSelected(searchedDate);setPage(1);
 },[searchedDate]);
 useEffect(()=>{
  const move=event=>{
   if(event.defaultPrevented||event.altKey||event.ctrlKey||event.metaKey||!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(event.key)||event.target.closest?.('input,textarea,select,[contenteditable=true],dialog,.tb-select-menu'))return;
   if(!available.length)return;
   const index=Math.max(0,days.indexOf(selected)),delta={ArrowLeft:-1,ArrowRight:1,ArrowUp:-grid.columns,ArrowDown:grid.columns}[event.key];
   event.preventDefault();pick(available[Math.max(0,Math.min(available.length-1,index+delta))]);
  };
  window.addEventListener('keydown',move);return()=>window.removeEventListener('keydown',move);
 },[available,days,selected,grid.columns]);
 useLayoutEffect(()=>{
  if(!gridRef.current||!tableRef.current)return;
  const resize=()=>{
   const area=gridRef.current;
   const next=fitActivityGrid(area.clientWidth,area.clientHeight,days.length);
   setGrid(old=>old.columns===next.columns&&old.size===next.size?old:next);
   const head=tableRef.current.querySelector('thead')?.getBoundingClientRect().height||30;
   const fontSize=parseFloat(getComputedStyle(tableRef.current).fontSize)||14;
   setPageSize(Math.max(1,Math.floor((tableRef.current.clientHeight-head)/Math.max(42,fontSize*3))));
  };
  const observer=new ResizeObserver(resize);observer.observe(gridRef.current);observer.observe(tableRef.current);resize();
  return()=>observer.disconnect();
 },[days.length,insights]);
 useEffect(()=>{setPage(1);},[month,pageSize,searchedDate]);
 const changeMonth=next=>{
  if(!monthDays(next).length)return;
  setQuery('');setMonth(next);setSelected(next===today.slice(0,7)?today:next+'-01');setPage(1);
 };
 if(!insights)return <p role="status">正在读取活动记录…</p>;
 const count=activity.get(selected)?.officialAccepted||0;
 return <div className="activity-page activity-month-page" aria-label="训练活动">
  <PageSearch><label className="search-box"><Search size={17}/><input aria-label="搜索活动日期" value={query} aria-invalid={invalid||undefined} onChange={event=>setQuery(event.target.value)}/></label></PageSearch>
  <section className="progress-section activity-month-panel" aria-label="月度训练日历">
   <header className="activity-month-heading"><h2><CalendarDays size={18}/>训练日历<Tooltip label="训练日历说明" text="按北京时间统计原站 AC，同题同日计一次。方向键按格子的位置切换日期；下方五段进度逐段填满，每种颜色占独立的一段。"/></h2><label className="activity-month-picker"><span>时间</span><input type="month" aria-label="活动时间" value={month} max={today.slice(0,7)} onChange={event=>changeMonth(event.target.value)}/></label></header>
   <div ref={gridRef} className="activity-square-viewport"><div className="activity-month-grid" role="grid" aria-colcount={grid.columns} aria-rowcount={Math.ceil(days.length/grid.columns)} aria-label={`${month}月训练日历，方向键切换日期`} style={{gridTemplateColumns:`repeat(${grid.columns},${grid.size}px)`,gridAutoRows:`${grid.size}px`}}>
    {days.map(day=>{const amount=activity.get(day)?.officialAccepted||0;return <button type="button" role="gridcell" key={day} ref={node=>{if(node)buttons.current.set(day,node);else buttons.current.delete(day);}} className={`activity-day activity-level-${levelOf(amount)}${selected===day?' activity-selected':''}`} disabled={day>today} tabIndex={day===selected?0:-1} aria-label={`${day}，${amount} 题通过`} aria-selected={day===selected} title={`${day} · AC : ${amount}`} onFocus={()=>setSelected(day)} onClick={()=>pick(day)}/>;})}
   </div></div>
   <div className="activity-selected-summary"><time dateTime={selected}>{selected.replaceAll('-','/')}</time><span className="activity-selected-count">AC<span className="metric-separator">:</span><b>{count}</b></span><ActivityProgress count={count} step={step}/></div>
  </section>
  <section className="progress-section activity-month-details" aria-label="日期明细">
   <header className="activity-detail-heading"><h2>日期明细</h2><span>{invalid?'日期格式无效':`${month.replace('-','年')}月 · ${records.length} 天`}</span></header>
   <div ref={tableRef} className="activity-detail-table" data-full={visible.length===pageSize}><table style={{'--activity-row-count':Math.max(1,visible.length)}}><thead><tr><th>日期</th><th>AC</th></tr></thead><tbody>{visible.map(day=><tr key={day} data-selected={day===selected}><td><button type="button" className="progress-text-button" onClick={()=>pick(day)}>{day.replaceAll('-','/')}</button></td><td><span className="activity-detail-progress"><ActivityProgress count={activity.get(day)?.officialAccepted||0} step={step}/><b>{activity.get(day)?.officialAccepted||0}</b></span></td></tr>)}</tbody></table>{!records.length&&<p className="progress-muted">{searchedDate?'这一天没有已保存的活动记录。':'本月还没有活动记录。'}</p>}</div>
   <footer className="activity-pagination"><span>共 {records.length} 天 · 每页 {pageSize} 行</span><button type="button" className="icon-button" aria-label="上一页日期明细" disabled={currentPage<=1} onClick={()=>setPage(value=>value-1)}><ChevronLeft size={16}/></button><span>{currentPage} / {pages}</span><button type="button" className="icon-button" aria-label="下一页日期明细" disabled={currentPage>=pages} onClick={()=>setPage(value=>value+1)}><ChevronRight size={16}/></button></footer>
  </section>
 </div>;
}
