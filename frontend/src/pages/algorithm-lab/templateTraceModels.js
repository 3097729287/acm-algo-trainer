// Deterministic algorithm traces. Rewinding restores a frame, never an inverse
// queue mutation; the C++ programs are independently compiled and exercised.
export function binaryBoundaryTrace(values,target,upper=false){
 if(values.some((v,i)=>i&&v<values[i-1]))return {error:'二分需要非递减数组；请先核对原条件。',frames:[]};
 let left=0,right=values.length;const frames=[];
 const push=(action,explanation,middle=null)=>frames.push({left,right,middle,action,explanation});
 push('initialize',`候选边界在 [0,${right}]，${right} 是未找到的哨兵，不读取 a[${right}]。`);
 while(left<right){
  const middle=left+Math.floor((right-left)/2),good=upper?values[middle]>target:values[middle]>=target;
  push('compare',`a[${middle}]=${values[middle]} ${upper?'>':'≥'} ${target} 为${good?'真':'假'}。`,middle);
  if(good){right=middle;push('right',`mid 已成立，保留 mid=${middle}，将右边界缩到 ${right}。`,middle);}
  else{left=middle+1;push('left',`mid 不成立，排除到 ${middle} 为止的位置，新左边界为 ${left}。`,middle);}
 }
 push('return',`两端重合，返回 ${left}。${left===values.length?'这是哨兵，不可访问数组该位置。':`这是第一个 ${upper?'>':'≥'} ${target} 的位置。`}`);
 return {frames,result:left};
}

export function windowExtremaTrace(values,width,mode='minimum'){
 if(!Number.isInteger(width)||width<1||width>values.length)return {error:'当前没有有效窗口；宽度须在 1 到数组长度之间。',frames:[],result:[]};
 const queue=[],result=[],frames=[];let right=-1;
 const push=(action,explanation,changed=null)=>frames.push({right,left:Math.max(0,right-width+1),queue:[...queue],result:[...result],action,explanation,changed});
 push('initialize','队列存原数组下标，开始为空；最值与下标分别读取。');
 for(right=0;right<values.length;++right){
  push('iterate',`加入原下标 ${right} 以前，先检查窗口 [${Math.max(0,right-width+1)},${right}] 的过期候选。`);
  while(queue.length&&queue[0]<=right-width){const removed=queue.shift();push('expire',`下标 ${removed}≤${right-width}，已经离开当前窗口，移出队首。`,removed);}
  const dominated=()=>mode==='maximum'?values[queue.at(-1)]<=values[right]:mode==='earliest'?values[queue.at(-1)]>values[right]:values[queue.at(-1)]>=values[right];
  while(queue.length&&dominated()){
   const removed=queue.pop();push('dominate',`旧候选 ${removed}:${values[removed]} 被新候选 ${right}:${values[right]} 支配；按本变种的平局规则移出队尾。`,removed);
  }
  queue.push(right);push('insert',`压入下标 ${right}；候选下标按进入顺序递增。`,right);
  if(right+1>=width){
   result.push(mode==='earliest'?queue[0]:values[queue[0]]);
   push('output',`窗口已经有 ${width} 项，队首为 ${queue[0]}:${values[queue[0]]}；本次输出${mode==='earliest'?'下标':'值'} ${result.at(-1)}。`,queue[0]);
  }
 }
 --right;push('return',`扫描结束，共得到 ${result.length} 个完整窗口的答案。`);
 return {frames,result};
}

export function parseTraceValues(text){
 const tokens=text.trim().split(/[\s,，]+/).filter(Boolean),values=tokens.map(Number);
 return tokens.length<=16&&tokens.every(t=>/^-?\d+$/.test(t))&&values.every(v=>Number.isSafeInteger(v)&&Math.abs(v)<=1000000)?{values}:{error:'输入至多 16 个绝对值不超过 1000000 的整数；留空表示空数组。'};
}

export function bruteTraceResult(kind,values,parameter,mode){
 if(kind==='binary-search'){
  const index=values.findIndex(v=>mode==='upper'?v>parameter:v>=parameter);return index<0?values.length:index;
 }
 if(parameter<1||parameter>values.length)return [];
 return Array.from({length:values.length-parameter+1},(_,i)=>{
  const part=values.slice(i,i+parameter);
  return mode==='maximum'?Math.max(...part):mode==='earliest'?i+part.indexOf(Math.min(...part)):Math.min(...part);
 });
}
