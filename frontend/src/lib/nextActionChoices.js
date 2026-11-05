import {planActions} from './learningSummaryModel.js';
import {original} from './problemIdentity.js';

// One primary action and at most four alternatives in the dropdown.
export const MAX_NEXT_ACTION_CHOICES=5;

// Choices are actual unfinished work or an existing picker. No completion or
// ability evidence is inferred from opening one of these actions.
export function nextActionChoices({snapshot,items=[],rows=[],training=[],dailyTasks,availablePages=[],activeContest,now=Date.now()}){
 if(activeContest)return items.slice(0,MAX_NEXT_ACTION_CHOICES);
 const result=[],seen=new Set(),titles=new Set(),counts=new Map(),byId=new Map(rows.flatMap(row=>[row.id,...(row.aliasIds||[])].map(id=>[id,row]))),accepted=new Set([...rows,...training].filter(row=>row.accepted).map(row=>original(byId.get(row.id)||row)));
 const problemKinds=new Set(['problem','stretch','review','template-problem','knowledge-review','random']);
 const push=item=>{
  if(!item||item.completed)return;
  // Both replay entries open the same picker. Count the primary choice too,
  // after removing repeated originals and indistinguishable labels.
  const key=problemKinds.has(item.kind)?'problem:'+original(byId.get(item.id)||item):item.kind==='replay'?'replay-picker':item.kind+':'+item.id;
  const title=String(item.title||'').normalize('NFKC').trim().replace(/\s+/g,' ').toLowerCase(),label=title?item.kind+':'+title:null;
  if(seen.has(key)||label&&titles.has(label)||(counts.get(item.kind)||0)>=2)return;
  seen.add(key);if(label)titles.add(label);counts.set(item.kind,(counts.get(item.kind)||0)+1);result.push(item);
 };
 const planned=planActions(snapshot,now)||[];
 for(const task of planned)push(task);
 if(!snapshot)push(items[0]);
 if(snapshot&&!snapshot.plan)push({kind:'summary-task',id:'summary',title:snapshot.recommendation?.title||'安排今天的学习',reason:snapshot.recommendation?.reason||'按当前记录接着学',summaryTask:true});
 const unfinished=(dailyTasks?.tasks||[]).filter(task=>!task.completed&&!task.claimed),unclaimed=(dailyTasks?.tasks||[]).filter(task=>task.completed&&!task.claimed);
 if(availablePages.includes('tasks')&&(unfinished.length||unclaimed.length))push({kind:'daily',page:'tasks',id:'daily',title:unfinished.length?'每日任务 · '+unfinished.length+' 项待完成':'领取每日任务奖励',reason:unfinished.length?'继续今天尚未完成的每日任务':'已有任务完成，可以领取奖励',taskView:'overview'});
 if(availablePages.includes('mine'))for(const task of training){if((counts.get('problem')||0)>=2)break;const row={...byId.get(task.id),...task};if(row.accepted||accepted.has(original(row))||['review','check'].includes(row.queue)||row.catalogHidden||row.locked||row.catalogContentReady!==true)continue;push({kind:'problem',page:'mine',id:row.id,title:row.title||'继续训练题',reason:'我的训练中尚未完成的题目'});}
 for(const item of items)push(item);
 if(availablePages.includes('mock'))push({kind:'replay',page:'mock',id:'replay-picker',title:'选择一场重现赛',reason:'从现有完整试卷中选择一场限时训练，按自己的可用时间安排；本轮任务完成后也可以继续。'});
 return result.slice(0,MAX_NEXT_ACTION_CHOICES);
}
