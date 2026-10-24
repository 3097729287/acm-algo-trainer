import {DEFAULT_MODEL,estimateMastery,rated,sigmoid} from './masteryScale.js';

export function combineKnowledgeEvidence(ids,evidence,model={},children=[]) {
 const p={...DEFAULT_MODEL,...model},items=[...new Set(ids)].map(id=>evidence.get(id)).filter(Boolean);
 if(!children.length)return {...estimateMastery(items,p),childWeights:[],coverage:null};
 const frequency=new Map();
 const available=children.map(child=>[...new Set(child.availableIds||child.ids||[])]);
 for(const ids of available)for(const id of ids)frequency.set(id,(frequency.get(id)||0)+1);
 const masses=children.map((child,i)=>Math.sqrt(available[i].reduce((sum,id)=>{
  const d=child.difficulties?.[id];
  const relevance=Number.isFinite(d)&&d>0?sigmoid((p.benchmark-d)/p.difficultyScale):1;
  return sum+relevance/frequency.get(id);
 },0)));
 const mass=masses.reduce((sum,value)=>sum+value,0);
 const estimates=children.map(child=>estimateMastery((child.ids||[]).map(id=>evidence.get(id)).filter(Boolean),p));
 const childWeights=children.map((child,i)=>({name:child.name,weight:mass?masses[i]/mass:0,observed:estimates[i].value!==null,value:estimates[i].value}));
 const coverage=childWeights.reduce((sum,child)=>sum+(child.observed?child.weight:0),0);
 const base={value:null,rawValue:null,interval:null,intervalKind:'coverage',participated:items.length,rated:items.filter(rated).length,officialAccepted:items.filter(item=>item.solved).length,childWeights,coverage};
 if(!mass||!coverage)return {...base,reason:'子知识点尚无有效定级证据；大类作答不会凭空分配到未练的子知识点。'};
 // Keep every child's weight in the denominator. Unobserved domains earn no
 // demonstrated credit, but remain unknown (0–100) in the reference range.
 const rawValue=estimates.reduce((sum,result,i)=>sum+childWeights[i].weight*(result.rawValue??0),0),value=Math.round(rawValue);
 const interval=[0,1].map(bound=>Math.round(estimates.reduce((sum,result,i)=>sum+childWeights[i].weight*(result.interval?.[bound]??(bound?100:0)),0)));
 const breakdown=childWeights.map(child=>`${child.name} ${(child.weight*100).toFixed(1)}%${child.observed?'':'（未练）'}`).join('；');
 const reason=`CF 2300 基准达标指数 ${value}%；逐个子知识点加权，权重合计 100%，已练范围 ${Math.round(coverage*100)}%。未练部分暂不贡献已证实掌握分，也不作为失败样本。权重按题库分布、目标难度相关性计算；范围 ${interval[0]}–${interval[1]}% 包含未练部分，并非父项联合置信区间。子项权重：${breakdown}。`;
 return {...base,value,rawValue,interval,reason};
}
