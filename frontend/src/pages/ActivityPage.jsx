import PagePagination from '@/components/PagePagination.jsx';
import {useEffect,useLayoutEffect,useMemo,useRef,useState} from 'react';
import {CalendarDays,Search} from 'lucide-react';
import Tooltip from '@/components/Tooltip.jsx';
import ThemedSelect from '@/components/ThemedSelect.jsx';
import './ActivityPage.css';
import PageSearch from '@/components/PageSearch.jsx';
import ActivityProgress from '@/components/ActivityProgress.jsx';
import {trainingDay} from '@/lib/trainingDate.js';
import {parseActivityDate,monthDays,yearDays,activityYearCells,activityTone,fitCompactActivityGrid,activitySegmentSize} from '@/lib/activityDate.js';

export {monthDays} from '@/lib/activityDate.js';
const monthLabel=month=>`${month.slice(0,4)}年${Number(month.slice(5))}月`;
export default function ActivityPage({insights}) {
 const [now,setNow]=useState(Date.now),today=trainingDay(now);
 const [year,setYear]=useState(()=>trainingDay().slice(0,4)),[selected,setSelected]=useState(today),[query,setQuery]=useState('');
 const [page,setPage]=useState(1),[pageSize,setPageSize]=useState(5),[grid,setGrid]=useState({columns:25,rows:5,size:24});
 const gridRef=useRef(null),tableRef=useRef(null),buttons=useRef(new Map());
 useEffect(()=>{const timer=setInterval(()=>setNow(Date.now()),30000);return()=>clearInterval(timer);},[]);
 const activity=useMemo(()=>new Map((insights?.activity||[]).map(item=>[item.date,item])),[insights?.activity]);
 const allDays=useMemo(()=>yearDays(year),[year]);
 const cells=useMemo(()=>activityYearCells(allDays,grid.rows),[allDays,grid.rows]);
 const years=useMemo(()=>[...new Set([year,...Array.from({length:6},(_,i)=>String(Number(today.slice(0,4))-i)),...[...activity.keys()].map(day=>day.slice(0,4))])].sort().reverse(),[year,today,activity]);
 const month=selected.slice(0,7),days=useMemo(()=>monthDays(month),[month]);
 const searchedDate=parseActivityDate(query),invalid=Boolean(query.trim())&&!searchedDate;
 const records=useMemo(()=>days.filter(day=>activity.has(day)&&day<=today&&(!searchedDate||day===searchedDate)).reverse(),[days,activity,today,searchedDate]);
 const step=activitySegmentSize(Math.max(0,...allDays.map(day=>activity.get(day)?.officialAccepted||0)));
 const pages=Math.max(1,Math.ceil(records.length/pageSize)),currentPage=Math.min(page,pages),visible=records.slice((currentPage-1)*pageSize,currentPage*pageSize);
 const pick=(day,focus=true)=>{setQuery('');setSelected(day);if(focus)requestAnimationFrame(()=>buttons.current.get(day)?.focus({preventScroll:true}));};
 useEffect(()=>{
  if(!searchedDate)return;
  setYear(searchedDate.slice(0,4));
  setSelected(searchedDate);setPage(1);
 },[searchedDate]);
 useEffect(()=>{
  const move=event=>{
   if(event.defaultPrevented||event.altKey||event.ctrlKey||event.metaKey||!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(event.key)||event.target.closest?.('input,textarea,select,[contenteditable=true],dialog,.tb-select-menu'))return;
   if(!allDays.length||!event.target.closest?.('.activity-continuous-grid'))return;
   const index=cells.indexOf(selected),delta={ArrowLeft:-grid.rows,ArrowRight:grid.rows,ArrowUp:-1,ArrowDown:1}[event.key];
   let next=Math.max(0,Math.min(cells.length-1,index+delta));
   while(!cells[next]&&next>=0&&next<cells.length)next+=Math.sign(delta);
   event.preventDefault();pick(cells[next]||allDays.at(-1));
  };
  window.addEventListener('keydown',move);return()=>window.removeEventListener('keydown',move);
 },[allDays,cells,selected,grid.rows]);
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
 const changeYear=next=>{
  if(!yearDays(next).length)return;
  setQuery('');setYear(next);setSelected(next===today.slice(0,4)?today:next+'-01-01');setPage(1);
 };
 if(!insights)return <p role="status">正在读取活动记录…</p>;
 const count=activity.get(selected)?.officialAccepted||0;
 return <div className="activity-page activity-month-page" aria-label="训练活动">
  <PageSearch><label className="search-box"><Search size={17}/><input aria-label="搜索活动日期" value={query} aria-invalid={invalid||undefined} onChange={event=>setQuery(event.target.value)}/></label></PageSearch>
  <section className="progress-section activity-month-panel" aria-label="全年训练日历">
   <header className="activity-month-heading"><h2><CalendarDays size={18}/>训练日历<Tooltip label="训练日历说明" text="所选年份的 1 月 1 日至 12 月 31 日，日期从上到下、再向右排列。月初以短线和月份数字标记。按北京时间统计每道题第一次原站 AC，重做不增加过题数。五种颜色与下方进度条对应，同一颜色越深表示题数越多。点击查看当天，方向键切换日期；下方明细随所选日期切换月份。"/></h2><label className="activity-month-picker"><span>年份</span><ThemedSelect aria-label="活动年份" value={year} onChange={event=>changeYear(event.target.value)}>{years.map(value=><option key={value} value={value}>{value}年</option>)}</ThemedSelect></label></header>
   <div ref={gridRef} className="activity-square-viewport"><div className="activity-month-grid activity-continuous-grid" role="grid" aria-colcount={grid.columns} aria-rowcount={grid.rows} aria-label="全年连续训练日历，方向键切换日期" style={{gridTemplateColumns:`repeat(${grid.columns},${grid.size}px)`,gridTemplateRows:`repeat(${grid.rows},${grid.size}px)`,gridAutoFlow:'column','--activity-cell-size':`${grid.size}px`}}>
    {cells.map((day,index)=>{if(!day)return <span key={`gap-${index}`} aria-hidden="true"/>;const amount=activity.get(day)?.officialAccepted||0,{band,shade}=activityTone(amount,step),monthStart=day.endsWith('-01');return <button type="button" role="gridcell" key={day} ref={node=>{if(node)buttons.current.set(day,node);else buttons.current.delete(day);}} className={`activity-day${selected===day?' activity-selected':''}${monthStart?' activity-month-start':''}`} data-band={band} data-shade={shade} data-future={day>today||undefined} tabIndex={day===selected?0:-1} aria-rowindex={index%grid.rows+1} aria-colindex={Math.floor(index/grid.rows)+1} aria-label={`${day}，${amount} 题通过`} aria-selected={day===selected} title={`${day} · 首次 AC : ${amount}`} onFocus={()=>setSelected(day)} onClick={()=>pick(day)}>{monthStart&&<span className="activity-month-marker" aria-hidden="true">{Number(day.slice(5,7))}</span>}</button>;})}
   </div></div>
   <div className="activity-selected-summary"><time dateTime={selected}>{selected.replaceAll('-','/')}</time><span className="activity-selected-count">AC<span className="metric-separator">:</span><b>{count}</b></span><ActivityProgress count={count} step={step}/></div>
  </section>
  <section className="progress-section activity-month-details" aria-label="日期明细">
   <header className="activity-detail-heading"><h2>日期明细</h2><span>{invalid?'日期格式无效':monthLabel(month)}</span></header>
   <div ref={tableRef} className="activity-detail-table" data-full={visible.length===pageSize}><table style={{'--activity-row-count':Math.max(1,visible.length)}}><thead><tr><th>日期</th><th>AC</th></tr></thead><tbody>{visible.map(day=><tr key={day} data-selected={day===selected}><td><button type="button" className="progress-text-button" onClick={()=>pick(day)}>{day.replaceAll('-','/')}</button></td><td><span className="activity-detail-progress"><ActivityProgress count={activity.get(day)?.officialAccepted||0} step={step}/><b>{activity.get(day)?.officialAccepted||0}</b></span></td></tr>)}</tbody></table>{!records.length&&<p className="progress-muted">{searchedDate?'这一天没有已保存的活动记录。':'本月还没有活动记录。'}</p>}</div>
   <PagePagination label="日期明细分页" count={`共 ${records.length} 天`} page={currentPage} pages={pages} previousLabel="上一页日期明细" nextLabel="下一页日期明细" onPrevious={()=>setPage(currentPage-1)} onNext={()=>setPage(currentPage+1)}/>
  </section>
 </div>;
}
