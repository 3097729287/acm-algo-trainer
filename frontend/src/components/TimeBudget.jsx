import {Minus,Plus} from 'lucide-react';
import {useEffect,useState} from 'react';
import './TimeBudget.css';
export const studyMinutes=value=>Math.min(720,Math.max(60,Number.isFinite(Number(value))?Math.round(Number(value)):60));
export default function TimeBudget({value=60,onChange,label='每日可用时间',compact=false}){
 const minutes=studyMinutes(value),[draft,setDraft]=useState(String(minutes));
 useEffect(()=>setDraft(String(minutes)),[minutes]);
 const commit=()=>{const next=studyMinutes(draft);setDraft(String(next));onChange(next);};
 return <div className={'time-budget'+(compact?' time-budget-compact':'')} role="group" aria-label={label}><div className="time-budget-stepper"><button type="button" aria-label={label+'减少30分钟'} disabled={minutes<=60} onClick={()=>onChange(studyMinutes(minutes-30))}><Minus size={16}/></button><label><input type="number" aria-label={label} min="60" max="720" step="1" value={draft} onChange={event=>{setDraft(event.target.value);const next=Number(event.target.value);if(next>=60&&next<=720)onChange(Math.round(next));}} onBlur={commit}/><span>分钟</span></label><button type="button" aria-label={label+'增加30分钟'} disabled={minutes>=720} onClick={()=>onChange(studyMinutes(minutes+30))}><Plus size={15}/>30</button><button type="button" aria-label={label+'增加60分钟'} disabled={minutes>=720} onClick={()=>onChange(studyMinutes(minutes+60))}><Plus size={15}/>60</button></div>{!compact&&<div className="time-budget-presets">{[60,90,120,180,240,360].map(value=><button type="button" key={value} aria-pressed={minutes===value} onClick={()=>onChange(value)}>{value}<small>分钟</small></button>)}</div>}</div>;
}
