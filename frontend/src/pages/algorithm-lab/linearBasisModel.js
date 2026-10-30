const LIMIT = (1n << 64n) - 1n;
export function parseXorInput(text) {
 const words=text.trim().split(/[\s,，]+/).filter(Boolean);
 if(!words.length||words.length>10)throw Error('输入 1 至 10 个无符号 64 位整数。');
 return words.map(word=>{
  if(!/^\d+$/.test(word)||BigInt(word)>LIMIT)throw Error('每个数须在 0 至 18446744073709551615 之间。');
  return BigInt(word);
 });
}
export function xorBasis(values) {
 const p=Array(64).fill(0n),frames=[];
 let rank=0;
 values.forEach((original,index)=>{
  let x=BigInt(original);
  if(x<0n||x>LIMIT)throw Error('数值超出 uint64_t 范围');
  frames.push({index,original,x,basis:[...p],rank,action:'开始插入'});
  for(let bit=63;bit>=0;bit--){
   if(!((x>>BigInt(bit))&1n))continue;
   if(p[bit]){
    const before=x;x^=p[bit];
    frames.push({index,original,x,before,pivot:p[bit],bit,basis:[...p],rank,action:'消元'});
   }else{
    p[bit]=x;rank++;
    frames.push({index,original,x,bit,basis:[...p],rank,action:'新增主元'});
    return;
   }
  }
  frames.push({index,original,x,basis:[...p],rank,action:'没有新增方向'});
 });
 return {p,rank,frames};
}
export function xorQuery(p,seed=0n,minimize=false) {
 let answer=BigInt(seed);const steps=[];
 for(let bit=63;bit>=0;bit--)if(p[bit]){
  const before=answer,candidate=answer^p[bit],take=minimize?candidate<answer:candidate>answer;
  if(take)answer=candidate;
  steps.push({bit,before,pivot:p[bit],candidate,take,answer});
 }
 return {answer,steps};
}
export function xorContains(p,target) {
 let x=BigInt(target);
 for(let bit=63;bit>=0;bit--)if((x>>BigInt(bit))&1n)x^=p[bit];
 return x===0n;
}
export function xorKth(p,k) {
 k=BigInt(k);const q=[...p],ordered=[];
 for(let i=0;i<64;i++)if(q[i]){
  for(let j=0;j<i;j++)if((q[i]>>BigInt(j))&1n)q[i]^=q[j];
  ordered.push(q[i]);
 }
 if(k<0n||k>=(1n<<BigInt(ordered.length)))return null;
 return ordered.reduce((value,x,i)=>((k>>BigInt(i))&1n)?value^x:value,0n);
}
export function subsetXors(values) {
 let results=[0n];for(const x of values)results=results.concat(results.map(value=>value^BigInt(x)));
 return [...new Set(results)].sort((a,b)=>a<b?-1:a>b?1:0);
}
