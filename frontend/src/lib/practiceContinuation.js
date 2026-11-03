import {original} from './problemIdentity.js';

const singleKinds=new Set(['problem','random','stretch','template-problem','knowledge-review']);
export function practiceContinuation(tab,{workspace={},recommendations=[],rows=[]}={}){
 const flow=tab.visit?.practiceFlow,review=Boolean(tab.reviewTask||flow?.stage==='review');
 if(!review&&flow?.stage!=='recommendation')return {managed:false,disabled:false};
 const training=workspace.training||[],catalog=new Map(rows.map(row=>[row.id,row]));
 for(const row of training)catalog.set(row.id,{...catalog.get(row.id),...row});
 const key=id=>original(catalog.get(id)||{id}),currentKey=key(tab.id),current=training.find(row=>key(row.id)===currentKey);
 if(review){
  const tasks=workspace.reviews?.tasks||training.filter(row=>row.reviewTask&&['review','check'].includes(row.queue)).map(row=>({problemId:row.id}));
  const pending=tasks.map(task=>task.problemId||task.id),at=pending.findIndex(id=>key(id)===currentKey);
  const following=at<0?pending:[...pending.slice(at+1),...pending.slice(0,at)];
  const next=following.find(id=>key(id)!==currentKey);
  if(next)return {managed:true,disabled:false,next:{id:next,kind:'review'}};
  if(at>=0)return {managed:true,disabled:true};
 }else{
  const stamp=Date.parse(current?.lastSubmittedAt),baseline=Date.parse(flow.baselineSubmittedAt),opened=Date.parse(flow.openedAt);
  const completed=current?.accepted===true&&current.verdict==='AC'&&['official','template'].includes(current.scope)
   &&Number.isFinite(stamp)&&Number.isFinite(opened)&&stamp>=opened&&(!Number.isFinite(baseline)||stamp>baseline);
  if(!completed)return {managed:true,disabled:true};
 }
 const accepted=new Set(training.filter(row=>row.accepted).map(row=>key(row.id)));
 const next=recommendations.find(item=>singleKinds.has(item.kind)&&key(item.id)!==currentKey&&!accepted.has(key(item.id)));
 return {managed:true,disabled:!next,next};
}
