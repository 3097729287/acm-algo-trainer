import {trainingDay} from './trainingDate.js';

export function currentLearningTask(snapshot,tasks=[],now=Date.now()) {
 const today=trainingDay(now),ready=tasks.filter(task=>task.status!=='done'&&(!task.date||task.date<=today)&&(!task.minimumAt||Date.parse(task.minimumAt)<=now)&&
  (task.kind!=='calendar-contest'||task.availability==='live'));
 const current=ready.find(task=>task.kind==='calendar-contest')||ready[0];
 if(current||snapshot.plan)return current;
 // A calendar by itself is not an adopted learning plan. Offer real content
 // from the recommended mainline without inventing a plan or completion record.
 const topic=snapshot.availableTopics?.find(item=>item.id===snapshot.recommendation?.tracks?.[0]);
 if(topic?.lectures?.[0])return {kind:'lecture',id:topic.lectures[0],title:'阅读：'+topic.title,minutes:15,suggested:true};
 if(topic?.course)return {kind:'course',id:topic.course,title:'实验与跟做：'+topic.title,minutes:20,suggested:true};
 return undefined;
}

// The last interaction starts an uncommitted tail. Only a following real
// interaction within five minutes commits it; an idle tail never becomes study.
export function studyClock() {
 let last=null;
 return {
  reset(){last=null;},
  interact(now,enabled=true){
   if(!enabled){last=null;return null;}
   const before=last;last=now;
   return before!==null&&now>before&&now-before<300?[before,now]:null;
  }
 };
}
export function planActions(snapshot,now=Date.now()) {
 const plan=snapshot?.plan;if(!plan)return null;
 const day=new Date(now+8*3600000).toISOString().slice(0,10);
 return plan.tasks.filter(task=>task.status!=='done'&&task.date<=day).map(task=>({
  ...task,taskId:task.key,taskKind:task.kind,kind:task.kind==='course'?'course':task.kind==='quiz'||task.kind==='reflection'?'summary-task':task.kind,
  page:task.kind==='lecture'?'lectures':task.kind==='course'?'paths':task.kind==='mixed'?'mock':'mine',
  reason:task.condition,summaryTask:true,
 }));
}
export function changedParagraphs(article=[],seen={}) {return article.filter(p=>seen[p.id]!==p.hash).map(p=>p.id);}
