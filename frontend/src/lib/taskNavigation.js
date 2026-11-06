import {trainingDay} from './trainingDate.js';
export function todayTaskSequence(plan,now=Date.now()){
 const today=trainingDay(now);
 return (plan?.tasks||[]).filter(task=>task?.key&&(!task.date||task.date===today||task.date<today&&task.status!=='done'||task.completedAt?.startsWith(today)));
}
export function taskNeighbours(flow,plan,now=Date.now()){
 if(!flow?.planId||!flow?.taskKey)return {managed:false};
 if(flow.planId!==plan?.id)return {managed:true,stale:true,tasks:[],index:-1,previous:null,next:null,label:'下一项'};
 const tasks=todayTaskSequence(plan,now),index=tasks.findIndex(task=>task.key===flow.taskKey),allDone=tasks.length>0&&tasks.every(task=>task.status==='done');
 return {managed:true,tasks,index,allDone,previous:tasks[index-1]||(allDone&&index===0?tasks.at(-1):null),next:index<0?tasks.find(task=>task.status!=='done')||tasks[0]:tasks[index+1]||(allDone?tasks[0]:null),label:allDone&&index===tasks.length-1?'已完成':'下一项'};
}
