import {useEffect,useRef,useState} from 'react';
import {RotateCcw,SlidersHorizontal,X} from 'lucide-react';
import RankingMedal from './RankingMedal.jsx';
import Tooltip from './Tooltip.jsx';

const periods=[['daily','每日'],['weekly','本周'],['total','累计']];
const key=owner=>'tb.admin.ranking-preview.v1.'+owner;
export function useAdminDominancePreview(owner){
 const [state,setState]=useState({owner:null,days:null});
 useEffect(()=>{
  let days=null;
  if(window.__tbAdmin&&owner)try{const saved=JSON.parse(localStorage.getItem(key(owner))||'null');if(saved?.owner===owner&&saved.version===1){days={};for(const [period] of periods)if(Number.isInteger(saved.days?.[period])&&saved.days[period]>=0&&saved.days[period]<=100000)days[period]=saved.days[period];}}catch{}
  setState({owner,days});
 },[owner]);
 const change=days=>{
  if(!window.__tbAdmin||!owner)return;
  setState({owner,days});
  try{if(days==null)localStorage.removeItem(key(owner));else localStorage.setItem(key(owner),JSON.stringify({version:1,owner,days}));}catch{}
 };
 return [window.__tbAdmin&&state.owner===owner?state.days:null,change];
}
function PreviewDialog({days,actualDays,onChange,onClose}){
 const ref=useRef(null);
 useEffect(()=>{ref.current.showModal();return()=>ref.current?.close();},[]);
 return <dialog ref={ref} className="admin-dominance-dialog" aria-labelledby="dominance-preview-title" onCancel={event=>{event.preventDefault();onClose();}}>
  <header><h3 id="dominance-preview-title">霸榜预览</h3><Tooltip text="恢复真实记录"><button type="button" className="icon-button" aria-label="恢复真实霸榜天数" onClick={()=>onChange(null)}><RotateCcw size={17}/></button></Tooltip><button type="button" className="icon-button" aria-label="关闭霸榜预览" onClick={onClose}><X size={17}/></button></header>
  {periods.map(([period,label])=>{const value=days?.[period]??actualDays?.[period]??0;return <label key={period} className="admin-dominance-row"><RankingMedal period={period} rank={1} dominance={{days:value}}/><span>{label}</span><input aria-label={label+'霸榜天数'} type="number" min="0" max="100000" step="1" value={value} onChange={event=>onChange({...days,[period]:Math.max(0,Math.min(100000,Math.floor(Number(event.target.value)||0)))})}/></label>;})}
 </dialog>;
}
export default function AdminDominancePreview({owner,days,actualDays,onChange}){
 const [open,setOpen]=useState(false);
 if(!window.__tbAdmin)return null;
 return <><Tooltip text="本机霸榜预览，不改变真实记录"><button type="button" className="progress-button" aria-label="调整霸榜天数" disabled={!owner} onClick={()=>setOpen(true)}><SlidersHorizontal size={16}/></button></Tooltip>{open&&owner&&<PreviewDialog key={owner} days={days} actualDays={actualDays} onChange={onChange} onClose={()=>setOpen(false)}/>}</>;
}
