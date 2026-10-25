import {useEffect,useLayoutEffect,useMemo,useRef,useState} from 'react';
import {CalendarDays,ChevronLeft,ChevronRight,Search} from 'lucide-react';
import Tooltip from '@/components/Tooltip.jsx';
import PageSearch from '@/components/PageSearch.jsx';
import ActivityProgress from '@/components/ActivityProgress.jsx';
import {trainingDay} from '@/lib/trainingDate.js';
import {parseActivityDate,monthDays,activityMonths,fitCompactActivityGrid,activitySegmentSize} from '@/lib/activityDate.js';

export {monthDays} from '@/lib/activityDate.js';
const levelOf=count=>count<=0?0:count===1?1:count<=3?2:count<=6?3:4;
const monthLabel=month=>`${month.slice(0,4)}年${Number(month.slice(5))}月`;
export default function ActivityPage({insights}) {
 const [now,setNow]=useState(Date.now),today=trainingDay(now);
 const [endingMonth,setEndingMonth]=useState(()=>trainingDay().slice(0,7)),[selected,setSelected]=useState(today),[query,setQuery]=useState('');
 const [page,setPage]=useState(1),[pageSize,setPageSize]=useState(5),[grid,setGrid]=useState({columns:25,rows:5,size:24});
 const gridRef=useRef(null),tableRef=useRef(null),buttons=useRef(new Map());
 useEffect(()=>{const timer=setInterval(()=>setNow(Date.now()),30000);return()=>clearInterval(timer);},[]);
 const activity=useMemo(()=>new Map((insights?.activity||[]).map(item=>[item.date,item])),[insights?.activity]);
 const months=useMemo(()=>activityMonths(endingMonth),[endingMonth]);
 const allDays=useMemo(()=>months.flatMap(monthDays),[months]);
 const available=useMemo(()=>allDays.filter(day=>day<=today),[allDays,today]);
 const month=selected.slice(0,7),days=useMemo(()=>monthDays(month),[month]);
 const searchedDate=parseActivityDate(query),invalid=Boolean(query.trim())&&!searchedDate;
 const records=useMemo(()=>days.filter(day=>activity.has(day)&&day<=today&&(!searchedDate||day===searchedDate)).reverse(),[days,activity,today,searchedDate]);
 const step=activitySegmentSize(Math.max(0,...allDays.map(day=>activity.get(day)?.officialAccepted||0)));
 const pages=Math.max(1,Math.ceil(records.length/pageSize)),currentPage=Math.min(page,pages),visible=records.slice((currentPage-1)*pageSize,currentPage*pageSize);
 const pick=(day,focus=true)=>{setQuery('');setSelected(day);if(focus)requestAnimationFrame(()=>buttons.current.get(day)?.focus({preventScroll:true}));};
 useEffect(()=>{
  if(!searchedDate)return;
  setEndingMonth(previous=>activityMonths(previous).includes(searchedDate.slice(0,7))?previous:searchedDate.slice(0,7));
  setSelected(searchedDate);setPage(1);
 },[searchedDate]);
 useEffect(()=>{
  const move=event=>{
   if(event.defaultPrevented||event.altKey||event.ctrlKey||event.metaKey||!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(event.key)||event.target.closest?.('input,textarea,select,[contenteditable=true],dialog,.tb-select-menu'))return;
   if(!available.length)return;
   const index=Math.max(0,available.indexOf(selected)),delta={ArrowLeft:-grid.rows,ArrowRight:grid.rows,ArrowUp:-1,ArrowDown:1}[event.key];
   event.preventDefault();pick(available[Math.max(0,Math.min(available.length-1,index+delta))]);
  };
  window.addEventListener('keydown',move);return()=>window.removeEventListener('keydown',move);
 },[available,selected,grid.rows]);
 useLayoutEffect(()=>{
  if(!gridRef.current||!tableRef.current)return;
  const resize=()=>{
   const area=gridRef.current,style=getComputedStyle(area);
   const width=area.clientWidth-parseFloat(style.paddingLeft)-parseFloat(style.paddingRight);
   const height=area.clientHeight-parseFloat(style.paddingTop)-parseFloat(style.paddingBottom);
   const next=fitCompactActivityGrid(width,height,allDays.length);
   setGrid(old=>old.columns===next.columns&&old.rows===next.rows&&old.size===next.size?old:next);
   const head=tableRef.current.querySelector('thead')?.getBoundingClientRect().height||30,fontSize=parseFloat(getComputedStyle(tableRef.current).fontSize)||14;
   setPageSize(Math.max(1,Math.floor((tableRef.current.clientHeight-head)/Math.max(42,fontSize*3))));
  };
  const observer=new ResizeObserver(resize);observer.observe(gridRef.current);observer.observe(tableRef.current);resize();
  return()=>observer.disconnect();
 },[insights,allDays.length]);
 useEffect(()=>{setPage(1);},[month,pageSize,searchedDate]);
 const changeMonth=next=>{
  if(!monthDays(next).length)return;
  setQuery('');setEndingMonth(next);setSelected(next===today.slice(0,7)?today:next+'-01');setPage(1);
 };
 if(!insights)return <p role="status">正在读取活动记录…</p>;
 const count=activity.get(selected)?.officialAccepted||0;
 return <div className="activity-page activity-month-page" aria-label="训练活动">
  <PageSearch><label className="search-box"><Search size={17}/><input aria-label="搜索活动日期" value={query} aria-invalid={invalid||undefined} onChange={event=>setQuery(event.target.value)}/></label></PageSearch>
  <section className="progress-section activity-month-panel" aria-label="四个月训练日历">
   <header className="activity-month-heading"><h2><CalendarDays size={18}/>训练日历<Tooltip label="训练日历说明" text="所选月份及之前三个月按日期连续排列。按北京时间统计原站 AC，同题同日计一次。悬停或点击查看当天，上下键切换相邻日期，左右键切换相邻列；下方明细随所选日期切换月份。"/></h2><label className="activity-month-picker"><span>截至</span><input type="month" aria-label="活动时间" value={endingMonth} max={today.slice(0,7)} onChange={event=>changeMonth(event.target.value)}/></label></header>
   <div ref={gridRef} className="activity-square-viewport"><div className="activity-month-grid activity-continuous-grid" role="grid" aria-colcount={grid.columns} aria-rowcount={grid.rows} aria-label="四个月连续训练日历，方向键切换日期" style={{gridTemplateColumns:`repeat(${grid.columns},${grid.size}px)`,gridTemplateRows:`repeat(${grid.rows},${grid.size}px)`,gridAutoFlow:'column'}}>
    {allDays.map(day=>{const amount=activity.get(day)?.officialAccepted||0;return <button type="button" role="gridcell" key={day} ref={node=>{if(node)buttons.current.set(day,node);else buttons.current.delete(day);}} className={`activity-day activity-level-${levelOf(amount)}${selected===day?' activity-selected':''}`} disabled={day>today} tabIndex={day===selected?0:-1} aria-label={`${day}，${amount} 题通过`} aria-selected={day===selected} title={`${day} · AC : ${amount}`} onFocus={()=>setSelected(day)} onClick={()=>pick(day)}/>;})}
   </div></div>
   <div className="activity-selected-summary"><time dateTime={selected}>{selected.replaceAll('-','/')}</time><span className="activity-selected-count">AC<span className="metric-separator">:</span><b>{count}</b></span><ActivityProgress count={count} step={step}/></div>
  </section>
  <section className="progress-section activity-month-details" aria-label="日期明细">
   <header className="activity-detail-heading"><h2>日期明细</h2><span>{invalid?'日期格式无效':`${monthLabel(month)} · ${records.length} 天`}</span></header>
   <div ref={tableRef} className="activity-detail-table" data-full={visible.length===pageSize}><table style={{'--activity-row-count':Math.max(1,visible.length)}}><thead><tr><th>日期</th><th>AC</th></tr></thead><tbody>{visible.map(day=><tr key={day} data-selected={day===selected}><td><button type="button" className="progress-text-button" onClick={()=>pick(day)}>{day.replaceAll('-','/')}</button></td><td><span className="activity-detail-progress"><ActivityProgress count={activity.get(day)?.officialAccepted||0} step={step}/><b>{activity.get(day)?.officialAccepted||0}</b></span></td></tr>)}</tbody></table>{!records.length&&<p className="progress-muted">{searchedDate?'这一天没有已保存的活动记录。':'本月还没有活动记录。'}</p>}</div>
   <footer className="activity-pagination"><span>共 {records.length} 天 · 每页 {pageSize} 行</span><button type="button" className="icon-button" aria-label="上一页日期明细" disabled={currentPage<=1} onClick={()=>setPage(value=>value-1)}><ChevronLeft size={16}/></button><span>{currentPage} / {pages}</span><button type="button" className="icon-button" aria-label="下一页日期明细" disabled={currentPage>=pages} onClick={()=>setPage(value=>value+1)}><ChevronRight size={16}/></button></footer>
  </section>
 </div>;
}
