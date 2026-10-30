// Deterministic teaching traces; inputs are data, never executable source.
export function operationTrace(kind,values,operations) {
 const frames=[],log=[],active=[];
 const push=state=>frames.push({...structuredClone(state),log:[...log],active:[...active]});
 if(kind==='dsu'){
  const parent=values.map((_,i)=>i),size=values.map(()=>1);let components=values.length;
  const find=v=>parent[v]===v?v:(parent[v]=find(parent[v]));
  push({parent,size,components});
  for(const [op,a,b] of operations){
   active.splice(0,active.length,a,...(b==null?[]:[b]));
   if(op==='unite'){
    let u=find(a),v=find(b);
    if(u===v)log.push(`unite(${a},${b}) → false；同组，大小不变`);
    else{if(size[u]<size[v])[u,v]=[v,u];parent[v]=u;size[u]+=size[v];components--;log.push(`unite(${a},${b}) → true；根 ${v} 并入根 ${u}`);}
   }else if(op==='same')log.push(`same(${a},${b}) → ${find(a)===find(b)}`);
   else log.push(`component_size(${a}) → ${size[find(a)]}`);
   push({parent,size,components});
  }
 }else if(kind==='fenwick'){
  const a=[...values],tree=Array(a.length+1).fill(0);
  const add=(index,delta)=>{for(let i=index+1;i<tree.length;i+=i&-i){tree[i]+=delta;active.push(i);}};
  const prefix=end=>{let sum=0;for(let i=end;i>0;i-=i&-i){sum+=tree[i];active.push(i);}return sum;};
  a.forEach((x,i)=>add(i,x));active.length=0;push({a,tree});
  for(const [op,x,y] of operations){
   active.length=0;
   if(op==='add'){a[x]+=y;add(x,y);log.push(`add(${x},${y})；外部位置 ${x} 变为 ${a[x]}`);}
   else if(op==='prefix')log.push(`prefix_sum(${x}) = ${prefix(x)}`);
   else log.push(`range_sum(${x},${y}) = ${prefix(y)-prefix(x)}`);
   push({a,tree});
  }
 }else if(kind==='segment-tree'){
  const a=[...values],tree=[];
  const build=(p,l,r)=>{tree[p]={p,l,r,sum:0,lazy:0};if(r-l===1)tree[p].sum=a[l];else{const m=(l+r)>>1;build(p*2,l,m);build(p*2+1,m,r);tree[p].sum=tree[p*2].sum+tree[p*2+1].sum;}};
  const apply=(p,d)=>{tree[p].sum+=(tree[p].r-tree[p].l)*d;tree[p].lazy+=d;};
  const visit=(p,l,r,d)=>{
   const node=tree[p];if(r<=node.l||node.r<=l)return 0;
   active.push(p);if(l<=node.l&&node.r<=r){if(d!=null)apply(p,d);return node.sum;}
   if(node.lazy){apply(p*2,node.lazy);apply(p*2+1,node.lazy);node.lazy=0;}
   const result=visit(p*2,l,r,d)+visit(p*2+1,l,r,d);
   if(d!=null)node.sum=tree[p*2].sum+tree[p*2+1].sum;
   return result;
  };
  if(a.length)build(1,0,a.length);push({a,tree});
  for(const [op,l,r,d] of operations){active.length=0;if(op==='addRange'){visit(1,l,r,d);for(let i=l;i<r;i++)a[i]+=d;log.push(`add(${l},${r},${d})；每项加 ${d}`);}else log.push(`range_sum(${l},${r}) = ${visit(1,l,r,null)}`);push({a,tree});}
 }else if(kind==='trie'){
  const words=[],nodes=[{path:'',pass:0,end:0,next:{}}];
  const locate=word=>{let v=0;for(const c of word){if(nodes[v].next[c]==null)return -1;v=nodes[v].next[c];}return v;};
  push({words,nodes});
  for(const [op,word] of operations){active.length=0;let v=locate(word);
   if(op==='insert'){
    words.push(word);v=0;nodes[0].pass++;active.push(0);
    for(const c of word){if(nodes[v].next[c]==null){nodes[v].next[c]=nodes.length;nodes.push({path:nodes[v].path+c,pass:0,end:0,next:{}});}v=nodes[v].next[c];nodes[v].pass++;active.push(v);}nodes[v].end++;log.push(`insert("${word}")`);
   }else if(op==='erase'){
    if(v<0||!nodes[v].end)log.push(`erase("${word}") → false`);
    else{words.splice(words.indexOf(word),1);v=0;nodes[0].pass--;for(const c of word){v=nodes[v].next[c];nodes[v].pass--;active.push(v);}nodes[v].end--;log.push(`erase("${word}") → true，只删除一份`);}
   }else log.push(`${op==='count'?'count':'prefix_count'}("${word}") = ${v<0?0:nodes[v][op==='count'?'end':'pass']}`);
   push({words,nodes});
  }
 }else if(kind==='binary-lifting'){
  const up=values.map(x=>[x]);for(let j=1;j<64;j++)for(let v=0;v<values.length;v++)up[v][j]=up[up[v][j-1]][j-1];
  push({up});for(const [,start,k] of operations){let v=start;active.length=0;for(let j=0;j<64;j++)if((BigInt(k)>>BigInt(j))&1n){active.push(j);v=up[v][j];}log.push(`jump(${start},${k}) = ${v}；拼接 ${active.map(j=>'2^'+j).join(' + ')||'0'} 步`);push({up,start,target:v});}
 }else if(kind==='li-chao'){
  const lines=[];push({lines,results:values.map(x=>[x,null])});
  for(const [op,k,b] of operations){if(op==='line'){lines.push([k,b]);log.push(`加入 y = ${k}x + ${b}`);}else{const answer=lines.length&&values.includes(k)?Math.min(...lines.map(([s,t])=>s*k+t)):null;log.push(`query(${k}) = ${answer??'空值'}`);}push({lines,results:values.map(x=>[x,lines.length?Math.min(...lines.map(([s,t])=>s*x+t)):null])});}
 }else if(kind==='dinic'){
  const n=1+Math.max(...values.flatMap(([u,v])=>[u,v])),capacity=Array.from({length:n},()=>Array(n).fill(0)),residual=Array.from({length:n},()=>Array(n).fill(0));
  for(const [u,v,c] of values)capacity[u][v]+=c;
  capacity.forEach((row,i)=>row.forEach((c,j)=>residual[i][j]=c));let flow=0;push({capacity,residual,flow,path:[]});
  const [,s,t]=operations[0]||['flow',0,n-1];
  while(true){const parent=Array(n).fill(-1),q=[s];parent[s]=s;for(let h=0;h<q.length;h++)for(let v=0;v<n;v++)if(parent[v]<0&&residual[q[h]][v]>0){parent[v]=q[h];q.push(v);}
   if(parent[t]<0){log.push(`再无增广路；最大流 ${flow}，源侧 {${q.join(', ')}}`);push({capacity,residual,flow,path:[],cut:q});break;}
   let amount=Infinity,path=[];for(let v=t;v!==s;v=parent[v]){path.unshift([parent[v],v]);amount=Math.min(amount,residual[parent[v]][v]);}
   for(const [u,v] of path){residual[u][v]-=amount;residual[v][u]+=amount;}flow+=amount;log.push(`路径 ${[s,...path.map(([,v])=>v)].join(' → ')}，增加 ${amount}，总流量 ${flow}`);push({capacity,residual,flow,path});
  }
 }
 return frames;
}
