// Small, directly enumerated teaching oracles. The fast C++ implementations
// are checked separately; these deliberately expose the mathematical objects.
export function guidedMini(kind,values,parameter,extra=[]){
 const n=values.length,k=parameter;
 if(kind==='wave'){
  if(!Number.isInteger(k)||k<1||k>80)return {error:'波段小实验使用 1～80 的项号。原题大范围由参考程序另行核验。'};
  const sequence=[];let segment=0;
  while(sequence.length<k){
   const i=segment++;
   for(let t=0;t<=4*i;++t)sequence.push(t<=i?t:t<=3*i?2*i-t:t-4*i);
  }
  return {values:sequence,result:sequence[k-1],selected:[k-1],state:`第 ${k} 项；波段从 0 开始编号为 ${segment-1}。`,label:'按原规则逐项生成的波段'};
 }
 if(!n)return {error:'这道原题的小实验至少需要一个元素。'};
 if(kind==='lookup'){
  if(values.some((x,i)=>x<0||i&&x<values[i-1]))return {error:'原题保证非负、非递减；修改数据时也要保持这个前提。'};
  const p=values.findIndex(x=>x>=k),hit=p>=0&&values[p]===k;
  return {values,result:hit?p+1:-1,selected:p<0?[]:[p],state:`第一个 ≥${k} 的 0 开始位置为 ${p<0?n:p}；${hit?'命中后转为 1 开始编号。':'仍需核对相等，未命中返回 -1。'}`,label:'原数组'};
 }
 if(kind==='cuts'){
  if(values.some(x=>x<1)||extra.some(x=>x<1))return {error:'原题元素与切割值均为正整数。'};
  const cut=new Set(extra);let inSegment=false,result=0;const removed=[];
  values.forEach((x,i)=>{if(cut.has(x)){inSegment=false;removed.push(i);}else{if(!inSegment)result++;inSegment=true;}});
  return {values,result,selected:values.map((_,i)=>i).filter(i=>!removed.includes(i)),state:`切割值 {${[...cut].join(',')}}；保留段数 ${result}，删除点之间的空隙不计数。`,label:'保持原相邻关系'};
 }
 if(kind==='nearest'){
  if(values.some(x=>x<0)||k<0)return {error:'学校与学生分数均为非负。'};
  const sorted=[...values].sort((a,b)=>a-b),best=Math.min(...sorted.map(x=>Math.abs(x-k))),selected=sorted.map((x,i)=>Math.abs(x-k)===best?i:-1).filter(i=>i>=0);
  return {values:sorted,result:best,selected,state:`学生分数 ${k}，最近分数差 ${best}；检查分界两侧，不能只选右侧。`,label:'学校分数排序副本'};
 }
 if(kind==='schedule'){
  if(values.length!==extra.length||values.some(x=>x<=0)||extra.some(x=>x<=0))return {error:'每项工作需要一个正时长和一个正截止时间，两组数量须一致。'};
  const jobs=values.map((duration,i)=>({duration,deadline:extra[i]})).sort((a,b)=>a.deadline-b.deadline);let elapsed=0,latest=Infinity;const detail=[];
  for(const job of jobs){elapsed+=job.duration;latest=Math.min(latest,job.deadline-elapsed);detail.push(`${job.deadline}−${elapsed}=${job.deadline-elapsed}`);}
  return {values:jobs.map(j=>j.duration),result:latest<0?-1:latest,selected:[],state:`按截止时间排序后的前缀余量：${detail.join('，')}。取最小余量。`,label:'按截止时间排序的工作时长'};
 }
 if(!Number.isInteger(k)||k<1||k>n)return {error:'原题宽度须在 1 到数组长度之间。'};
 if(kind==='previous'){
  const result=values.map((_,i)=>i?Math.min(...values.slice(Math.max(0,i-k),i)):0);
  return {values:result,result,selected:[],state:'第 i 项只看它之前至多 m 项；第一个结果为 0。',label:'每个位置在插入自身以前的查询结果'};
 }
 if(kind==='bounded-sum'){
  let result=-Infinity,selected=[];
  for(let l=0;l<n;l++){let sum=0;for(let r=l;r<n&&r-l+1<=k;r++){sum+=values[r];if(sum>result){result=sum;selected=values.map((_,i)=>i).filter(i=>i>=l&&i<=r);}}}
  return {values,result,selected,state:`枚举所有长度 1..${k} 的非空连续段；最优下标 ${selected.join(',')}，和 ${result}。`,label:'原数组，亮色为一个最优非空段'};
 }
 if(kind==='all-widths'){
  if(values.some(x=>x<=0))return {error:'这道原题要求正整数；完整算法的其它值域需要重新检查初值。'};
  const result=Array.from({length:n},(_,index)=>{
   const width=index+1;return Math.max(...Array.from({length:n-width+1},(_,l)=>Math.min(...values.slice(l,l+width))));
  });
  return {values:result,result,selected:[k-1],state:`宽度 ${k} 的“窗口最小值中的最大值”为 ${result[k-1]}。每格对应一种宽度。`,label:'逐个枚举窗口得到的宽度答案'};
 }
 if(kind==='quality'||kind==='extrema'){
  const minima=Array.from({length:n-k+1},(_,i)=>Math.min(...values.slice(i,i+k))),maxima=Array.from({length:n-k+1},(_,i)=>Math.max(...values.slice(i,i+k)));
  return {values:minima,result:kind==='quality'?minima:[minima,maxima],selected:[],state:`共有 ${minima.length} 个完整窗口。${kind==='extrema'?`最大值一行为 ${maxima.join(' ')}。`:'每个答案应单独输出一行。'}`,label:'完整窗口的最小值'};
 }
 return {error:'没有这个实验模型。'};
}
