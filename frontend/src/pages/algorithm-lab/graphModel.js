// Small deterministic traces for teaching. These do not submit or award progress.
export const GRAPH_NODES = ['A','B','C','D','E','F'];
export const GRAPH_EDGES = [[0,1,4],[0,2,1],[1,2,2],[1,3,1],[2,4,5],[3,4,1],[4,5,2]];
export function graphTrace(kind, edges=GRAPH_EDGES, start=0, count=6) {
  const adj=Array.from({length:count},()=>[]);
  for(const [a,b,w] of edges){adj[a].push([b,w]);adj[b].push([a,w]);}
  adj.forEach(neighbors=>neighbors.sort((a,b)=>a[0]-b[0]));
  const dist=Array(count).fill(Infinity),parent=Array(count).fill(-1),seen=new Set(),order=[],frames=[];
  const save=(active,frontier,note,changed=[])=>frames.push({active,frontier:[...frontier],dist:[...dist],parent:[...parent],seen:[...seen],order:[...order],note,changed});
  if(kind==='dsu') {
    const size=Array(count).fill(1);parent.forEach((_,i)=>parent[i]=i);
    const root=x=>{while(parent[x]!==x){parent[x]=parent[parent[x]];x=parent[x];}return x;};
    const record=(note,changed=[])=>frames.push({active:-1,frontier:[],dist:[],parent:[...parent],size:[...size],roots:parent.map((_,i)=>root(i)),seen:[],order:[],note,changed});
    record('每个点自成一个集合：parent[x]=x，size[x]=1。');
    for(const [u,v] of edges){let a=root(u),b=root(v);if(a===b){record(`${GRAPH_NODES[u]} 与 ${GRAPH_NODES[v]} 已连通，不能再次累加集合大小。`);continue;}if(size[a]<size[b])[a,b]=[b,a];parent[b]=a;size[a]+=size[b];record(`连接 ${GRAPH_NODES[u]}—${GRAPH_NODES[v]}：把较小集合的根 ${GRAPH_NODES[b]} 接到 ${GRAPH_NODES[a]}，新集合大小 ${size[a]}。`,[u,v]);}
    return frames;
  }
  dist[start]=0;
  if(kind==='dijkstra'){
    const queue=[[0,start]];
    save(-1,[start],'起点距离 0，其他点暂不可达。小根堆保存（候选距离，点）。');
    while(queue.length){queue.sort((a,b)=>a[0]-b[0]||a[1]-b[1]);const [d,u]=queue.shift();if(d!==dist[u]){save(u,queue.map(x=>x[1]),`跳过 ${GRAPH_NODES[u]} 的旧候选 ${d}；最新距离是 ${dist[u]}。`);continue;}seen.add(u);order.push(u);const changed=[];for(const [v,w] of adj[u])if(d+w<dist[v]){dist[v]=d+w;parent[v]=u;queue.push([dist[v],v]);changed.push(v);}save(u,queue.slice().sort((a,b)=>a[0]-b[0]||a[1]-b[1]).map(x=>x[1]),`取出最短候选 ${GRAPH_NODES[u]}（${d}），检查它的邻边；${changed.length?changed.map(v=>GRAPH_NODES[v]).join('、')+' 的距离变小':'没有距离需要更新'}。`,changed);}
  } else if(kind==='bfs'){
    const queue=[start];seen.add(start);save(-1,queue,'起点入队时就标记，避免同一层的多个父亲重复加入它。');
    while(queue.length){const u=queue.shift(),changed=[];order.push(u);for(const [v] of adj[u])if(!seen.has(v)){seen.add(v);parent[v]=u;dist[v]=dist[u]+1;queue.push(v);changed.push(v);}save(u,queue,`队首先出 ${GRAPH_NODES[u]}，新发现的邻点排到队尾；距离是边数，不使用图中的权值。`,changed);}
  } else {
    // Explicit recursion frames preserve recursive DFS order without call-stack overflow.
    const stack=[[start,0]];seen.add(start);order.push(start);save(start,[start],`进入 ${GRAPH_NODES[start]}；栈记录每层接下来要检查哪条边。`);
    while(stack.length){const frame=stack[stack.length-1],u=frame[0];if(frame[1]===adj[u].length){stack.pop();save(u,stack.map(x=>x[0]),`${GRAPH_NODES[u]} 的邻边已处理完，返回上一层。`);continue;}const [v]=adj[u][frame[1]++];if(seen.has(v))continue;seen.add(v);parent[v]=u;dist[v]=dist[u]+1;order.push(v);stack.push([v,0]);save(v,stack.map(x=>x[0]),`沿 ${GRAPH_NODES[u]}—${GRAPH_NODES[v]} 深入；这里的深度不保证是最短路。`,[v]);}
  }
  return frames;
}
export function matchesGraphProblem(row,problem){
  const key=url=>String(url||'').replace('http:','https:').replace('www.codeforces.com','codeforces.com').replace(/\/problemset\/problem\/(\d+)\/([A-Z]\d?)/,'/contest/$1/problem/$2').replace(/\/$/,'').split('?')[0];
  return key(row.url)===key(problem.url);
}
