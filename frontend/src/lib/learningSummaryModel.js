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
