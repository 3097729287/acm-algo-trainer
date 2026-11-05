// Plan tasks share the existing training rows; a problem keeps one identity and one row.
export function mergeLearningTasks(index,plan){
 const tasks=Array.isArray(plan?.tasks)?plan.tasks:[],byKey=new Map();
 const kind=task=>['problem','review','template-problem'].includes(task.kind)?'problem':task.kind==='course'?'lab':['lecture','template'].includes(task.kind)?task.kind:'task';
 for(const task of tasks){if(!task?.title||!task.id&&!task.key)continue;const key=kind(task)+':'+(task.id||task.key),old=byKey.get(key);if(!old||old.status==='done'&&task.status!=='done')byKey.set(key,task);}
 const decorate=(entry,task)=>({...entry,summaryTask:task,trainingGroup:entry.trainingGroup||'plan',trainingLabel:task.status==='done'?'已完成':task.kind==='calendar-contest'&&task.availability==='upcoming'?'尚未开始':'待完成',trainingOrder:5000+(task.order||0),search:(entry.search||entry.title)+' '+task.title});
 const seen=new Set(),result=index.map(entry=>{const task=byKey.get(entry.key);if(!task)return entry;seen.add(entry.key);return decorate(entry,task);});
 for(const [key,task]of byKey)if(!seen.has(key))result.push(decorate({key,kind:kind(task),id:task.id||task.key,title:task.title,source:'任务',category:''},task));
 return result;
}
