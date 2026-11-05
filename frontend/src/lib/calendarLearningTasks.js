import {trainingDay} from './trainingDate.js';

const officialResults=new Set(['AC','WA','TLE','MLE','RE','CE','OLE','PARTIAL']);
const valid=event=>event?.id&&event.url&&Number.isFinite(Date.parse(event.startAt))&&Date.parse(event.endAt)>Date.parse(event.startAt);

// Schedule entries and trusted calendar contest receipts already persist in
// the application. Derive extra tasks without changing the adopted study plan.
export function calendarLearningTasks(events=[],records=[],now=Date.now()){
 const today=trainingDay(now),day=new Date(today+'T00:00:00Z'),weekday=(day.getUTCDay()+6)%7;
 day.setUTCDate(day.getUTCDate()-weekday);const monday=day.toISOString().slice(0,10);
 day.setUTCDate(day.getUTCDate()+7);const nextMonday=day.toISOString().slice(0,10);
 const entries=new Map();
 for(const event of events)if(valid(event))entries.set(event.id,event);
 for(const record of records){const event=record.constraints?.calendarEvent;if(valid(event)&&!entries.has(event.id))entries.set(event.id,{...event,title:record.name});}
 return [...entries.values()].filter(event=>{const date=trainingDay(event.startAt);return date>=monday&&date<nextMonday;}).sort((a,b)=>Date.parse(a.startAt)-Date.parse(b.startAt)||a.id.localeCompare(b.id)).map((event,index)=>{
  const attempts=records.filter(record=>{
   const receipt=record.constraints?.calendarEvent;
   return receipt?.id===event.id&&receipt.url===event.url&&Date.parse(receipt.startAt)===Date.parse(event.startAt)&&Date.parse(receipt.endAt)===Date.parse(event.endAt)&&Date.parse(record.startedAt)>=Date.parse(event.startAt)&&Date.parse(record.startedAt)<Date.parse(event.endAt)&&record.status!=='cancelled';
  });
  const completed=attempts.find(record=>record.status==='finished'&&Date.parse(record.finishedAt)>=Date.parse(record.startedAt)&&Date.parse(record.finishedAt)<=now&&record.slots?.some(slot=>slot.judgeScope==='official'&&slot.attempts>0&&officialResults.has(slot.verdict)));
  const record=completed||attempts.find(record=>record.status==='running')||attempts[0];
  return {key:'calendar:'+event.id,id:event.id,kind:'calendar-contest',title:event.title,date:trainingDay(event.startAt),minutes:Math.round((Date.parse(event.endAt)-Date.parse(event.startAt))/60000),order:index+1,
   condition:'在比赛时段参加赛事，完成原站正式提交并交卷',status:completed?'done':'pending',completedAt:completed?.finishedAt,contestId:record?.id,event,
   availability:now<Date.parse(event.startAt)?'upcoming':now<Date.parse(event.endAt)?'live':'ended'};
 });
}

export function addCalendarLearningTasks(plan,events,records,now){
 const extra=calendarLearningTasks(events,records,now),tasks=plan?.tasks||[];
 if(!extra.length)return plan;
 const max=Math.max(0,...tasks.map(task=>Number(task.order)||0));
 return {...plan,tasks:[...tasks,...extra.map((task,index)=>({...task,order:max+index+1}))]};
}
