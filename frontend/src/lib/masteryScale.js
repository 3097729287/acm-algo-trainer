// Numerical mirror of backend/mastery_scale.py; no personal records are changed.
export const DEFAULT_MODEL={version:5,method:'rasch-cf2300-coverage',benchmark:2300,baselineMin:800,baselineStep:100,difficultyScale:400/Math.log(10),priorMean:1200,priorSd:600,gridMin:0,gridMax:4000,gridStep:10,scoreQuantile:.1,interval:.95,calibrated:false};
export const rated=item=>item?.rated&&Number.isFinite(item.difficulty)&&item.difficulty>0;
export const sigmoid=value=>1/(1+Math.exp(-value));
export function benchmarkScore(ability,model={}) {
 const p={...DEFAULT_MODEL,...model};let numerator=0,denominator=0;
 if(ability>=p.benchmark)return 100;
 for(let d=p.baselineMin;d<=p.benchmark;d+=p.baselineStep){numerator+=sigmoid((ability-d)/p.difficultyScale);denominator+=sigmoid((p.benchmark-d)/p.difficultyScale);}
 return Math.min(100,100*numerator/denominator);
}
const grids=new Map();
export function estimateMastery(evidence,model={}) {
 const p={...DEFAULT_MODEL,...model},items=[...new Map(evidence.map(item=>[item.id,item])).values()].sort((a,b)=>a.id<b.id?-1:a.id>b.id?1:0),known=items.filter(rated);
 const base={value:null,rawValue:null,interval:null,intervalKind:'model',participated:items.length,rated:known.length,officialAccepted:items.filter(item=>item.solved).length};
 if(!known.length)return {...base,reason:'尚无已定级题目的有效作答；未练与未知难度均不补造掌握分。'};
 const histogram=new Map();
 for(const item of known){const pair=histogram.get(item.difficulty)||[0,0],weight=Math.max(0,Math.min(1,item.weight??1));pair[0]+=weight;if(item.solved)pair[1]+=weight;histogram.set(item.difficulty,pair);}
 const factors=[...histogram].sort((a,b)=>a[0]-b[0]),key=JSON.stringify(p);
 let grid=grids.get(key);
 if(!grid){grid=Array.from({length:Math.round((p.gridMax-p.gridMin)/p.gridStep)+1},(_,i)=>{const ability=p.gridMin+i*p.gridStep;return [ability,-.5*((ability-p.priorMean)/p.priorSd)**2,benchmarkScore(ability,p)];});if(grids.size>=8)grids.clear();grids.set(key,grid);}
 const densities=grid.map(([ability,prior])=>{
  let density=prior;for(const [difficulty,[weight,successes]] of factors){const delta=(ability-difficulty)/p.difficultyScale;density+=successes*delta-weight*(Math.max(delta,0)+Math.log1p(Math.exp(-Math.abs(delta))));}return density;
 });
 const peak=Math.max(...densities),weights=densities.map(value=>Math.exp(value-peak)),total=weights.reduce((a,b)=>a+b,0),quantiles=[.025,p.scoreQuantile,.975],scores=[];
 let cumulative=0;
 weights.forEach((weight,i)=>{cumulative+=weight/total;while(scores.length<3&&cumulative>=quantiles[scores.length])scores.push(grid[i][2]);});
 while(scores.length<3)scores.push(100);
 const rawValue=scores[1],value=Math.round(rawValue),interval=[Math.round(scores[0]),Math.round(scores[2])];
 const reason=`CF 2300 基准达标指数 ${value}%；以 800–2300 整百难度层的参考答题能力为尺度，CF 2300 参考能力为 100%。取能力后验的 90% 单侧下界，避免少量简单题高估；95% 模型区间 ${interval[0]}–${interval[1]}%，有效已定级原题 ${known.length} 道。这是练习参考指数，非官方 CF rating 或经标定的考试通过率。`;
 return {...base,value,rawValue,interval,reason};
}
