// Rasch/EAP quadrature mirrored in backend/knowledge_mastery.py.
// This provisional practice index is not a calibrated mastery probability.
const DEFAULT_MODEL={difficultyCenter:1600,difficultyScale:400,priorSd:1.5,gridMin:-8,gridMax:8,gridStep:.05,referenceDifficulty:1600};
const rated=item=>item.rated&&Number.isFinite(item.difficulty)&&item.difficulty>0;
const sigmoid=value=>1/(1+Math.exp(-value));
export function combineKnowledgeEvidence(ids,evidence,model={},children=[]) {
 const items=[...new Set(ids)].map(id=>evidence.get(id)).filter(Boolean).sort((a,b)=>a.id<b.id?-1:a.id>b.id?1:0);
 const known=items.filter(rated),p={...DEFAULT_MODEL,...model};
 const result={value:null,interval:null,participated:items.length,rated:known.length,officialAccepted:items.filter(item=>item.solved).length};
 const frequency=new Map();
 for(const child of children)for(const id of new Set(child.availableIds||child.ids||[]))frequency.set(id,(frequency.get(id)||0)+1);
 const masses=children.map(child=>[...new Set(child.availableIds||child.ids||[])].reduce((sum,id)=>sum+1/frequency.get(id),0));
 const totalMass=masses.reduce((sum,mass)=>sum+mass,0);
 result.childWeights=children.map((child,index)=>({name:child.name,weight:totalMass?masses[index]/totalMass:0,observed:(child.ids||[]).some(id=>rated(evidence.get(id)||{}))}));
 result.coverage=totalMass?result.childWeights.reduce((sum,child)=>sum+(child.observed?child.weight:0),0):null;
 if(!known.length)return {...result,reason:'尚无已定级题目的有效作答；未知难度不补造分数。'};
 const histogram=new Map();
 for(const item of known){const pair=histogram.get(item.difficulty)||[0,0],weight=Math.max(0,Math.min(1,item.weight??1));pair[0]+=weight;if(item.solved)pair[1]+=weight;histogram.set(item.difficulty,pair);}
 const factors=[...histogram].sort((a,b)=>a[0]-b[0]).map(([difficulty,[weight,successes]])=>[(difficulty-p.difficultyCenter)/p.difficultyScale,weight,successes]);
 const points=[],size=Math.round((p.gridMax-p.gridMin)/p.gridStep)+1,reference=(p.referenceDifficulty-p.difficultyCenter)/p.difficultyScale;
 for(let index=0;index<size;index++) {
  const theta=p.gridMin+index*p.gridStep;
  let logDensity=-.5*(theta/p.priorSd)**2;
  for(const [beta,weight,successes] of factors) {
   const delta=theta-beta;
   const softplus=Math.max(delta,0)+Math.log1p(Math.exp(-Math.abs(delta)));
   logDensity+=successes*delta-weight*softplus;
  }
  points.push({logDensity,score:sigmoid(theta-reference)});
 }
 const peak=Math.max(...points.map(point=>point.logDensity));
 const weights=points.map(point=>Math.exp(point.logDensity-peak)),total=weights.reduce((sum,value)=>sum+value,0);
 const value=Math.round(100*points.reduce((sum,point,index)=>sum+weights[index]*point.score,0)/total);
 const interval=[];let cumulative=0;
 points.forEach((point,index)=>{cumulative+=weights[index]/total;while(interval.length<2&&cumulative>=(interval.length ? .975 : .025))interval.push(Math.round(100*point.score));});
 while(interval.length<2)interval.push(100);
 const coverage=result.coverage===null?'':`已练子项按题库频率加权覆盖 ${Math.round(result.coverage*100)}%；未练子项未按失败计入。`;
 const reason=`Rasch 估计指数 ${value}%，95% 模型区间 ${interval[0]}–${interval[1]}%；${known.length} 道不同的已定级题。${coverage}统一参照难度 1600；参数尚未经群体标定，区间不含模型误差，不代表考试通过率。`;
 return {...result,value,interval,reason};
}
