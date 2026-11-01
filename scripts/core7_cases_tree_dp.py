"""Definition-level tree oracles, literal games, colorings and frontier probabilities."""
from collections import deque
from functools import lru_cache
from fractions import Fraction
from itertools import combinations,permutations,product
from math import comb
import heapq
import random

IDS={'B4016','P11249','P15801','P1131','P2458','P2986','P4084','P9584','P13020','CF337D','CF1416C','P1453','P3554','P5958','P8916','P10767','UVA1218','CF1540B'}

def children_order(parents):
 n=len(parents);children=[[] for _ in parents];depth=[0]*n
 for i in range(1,n):children[parents[i]].append(i);depth[i]=depth[parents[i]]+1
 return children,depth

def morale_literal(parents,weights):
 children,depth=children_order(parents);n=len(parents);sub=[{u} for u in range(n)]
 for u in range(n-1,-1,-1):
  for v in children[u]:sub[u] |= sub[v]
 best=-10**30
 for colors in range(1<<n):
  value=sum(weights)
  for u in range(n):
   color=colors>>u&1
   for v in children[u]:
    if colors>>v&1==color:value+=sum(weights[x] for x in sub[v] if colors>>x&1==color)
  best=max(best,value)
 return best

def arch_literal(parents):
 n=len(parents)
 if n==1:return 0
 graph=[[] for _ in range(n)]
 for i in range(1,n):graph[i].append(parents[i]);graph[parents[i]].append(i)
 full=(1<<n)-1
 for k in range(1,n):
  @lru_cache(None)
  def win(mask,u):
   if mask==full:return True
   white=[i for i in range(n) if not(mask>>i&1)]
   for chosen in combinations(white,min(k,len(white))):
    new=mask|sum(1<<v for v in chosen)
    if new==full:return True
    if any(not(new>>v&1) for v in graph[u]):continue
    if all(win(new,v) for v in graph[u]):return True
   return False
  if win(1,0):return k
 raise AssertionError(parents)

def sabotage_literal(parents,k):
 n=len(parents);children,depth=children_order(parents);sub=[1<<u for u in range(n)]
 for u in range(n-1,0,-1):sub[parents[u]] |= sub[u]
 descendants=[sub[u]^(1<<u) for u in range(n)];sizes=[m.bit_count() for m in descendants]
 def worst(x):
  answer=1
  for start in range(n):
   infected=1<<start
   while True:
    old=infected
    for u in range(n):
     if sizes[u] and Fraction((infected&descendants[u]).bit_count(),sizes[u])>x:infected |= sub[u]
    if old==infected:break
   answer=max(answer,infected.bit_count())
  return answer
 candidates=sorted({Fraction(a,b) for b in range(1,n+1) for a in range(b+1)})
 for threshold in candidates:
  if worst(threshold)<=k:return threshold
 raise AssertionError(parents)

def tournament_literal(n,rules):
 total=1<<n;sets=[set() for _ in range(n+1)]
 for perm in permutations(range(1,total+1)):
  winner=[0]*total+list(perm);sets[0].update(perm)
  for u in range(total-1,0,-1):winner[u]=max(winner[2*u],winner[2*u+1]) if rules[u]==1 else min(winner[2*u],winner[2*u+1])
  for h in range(1,n+1):
   for u in range(total>>h,total>>(h-1)):sets[h].add(winner[u])
 return sets

def expectation_literal(parents):
 n=len(parents);adj=[0]*n
 for v in range(1,n):adj[v] |= 1<<parents[v];adj[parents[v]] |= 1<<v
 full=(1<<n)-1
 @lru_cache(None)
 def later(mask):
  if mask==full:return Fraction(0)
  frontier=0
  for u in range(n):
   if mask>>u&1:frontier |= adj[u]
  frontier &= full^mask;choices=[v for v in range(n) if frontier>>v&1]
  return sum((Fraction((mask>>(v+1)).bit_count())+later(mask|1<<v) for v in choices),Fraction(0))/len(choices)
 return sum((later(1<<r) for r in range(n)),Fraction(0))/n


def tree_edges(parents):return [(parents[v],v) for v in range(1,len(parents))]


def graph_for(n,edges):
    graph=[[] for _ in range(n)]
    for edge in edges:
        u,v=edge[:2];w=edge[2] if len(edge)>2 else 1
        graph[u].append((v,w));graph[v].append((u,w))
    return graph


def all_distances(n,edges):
    graph=graph_for(n,edges);result=[]
    for root in range(n):
        distance=[None]*n;distance[root]=0;todo=[root]
        for u in todo:
            for v,w in graph[u]:
                if distance[v] is None:distance[v]=distance[u]+w;todo.append(v)
        result.append(distance)
    return result


def path_masks(n,edges):
    graph=graph_for(n,edges);result=[]
    for root in range(n):
        parent=[-1]*n;parent[root]=root;todo=[root]
        for u in todo:
            for v,w in graph[u]:
                if parent[v]<0:parent[v]=u;todo.append(v)
        for endpoint in range(root,n):
            u=endpoint;mask=1<<u
            while u!=root:u=parent[u];mask |= 1<<u
            result.append(mask)
    return result


def treasure_paths(n,edges,marked):
    required=sum(1<<u for u in marked)
    return any(mask&required==required for mask in path_masks(n,edges))


def complete_subtrees(left,right):
    answer=0
    for root in range(len(left)):
        queue=deque([root]);gap=False;valid=True
        while queue:
            u=queue.popleft()
            if u<0:gap=True;continue
            if gap:valid=False;break
            queue.append(left[u]);queue.append(right[u])
        answer+=valid
    return answer


def delay_assignments(n,edges,root):
    graph=[[] for _ in range(n)]
    for i,(u,v,w) in enumerate(edges):graph[u].append((v,w,i));graph[v].append((u,w,i))
    parent=[-1]*n;parent[root]=root;distance=[0]*n;path=[0]*n;todo=[root]
    for u in todo:
        for v,w,i in graph[u]:
            if parent[v]<0:parent[v]=u;distance[v]=distance[u]+w;path[v]=path[u]|1<<i;todo.append(v)
    leaves=[u for u in range(n) if all(v==parent[u] for v,w,i in graph[u])]
    maximum=max(distance[u] for u in leaves);deficit=tuple(maximum-distance[u] for u in leaves)
    effects={tuple(j for j,u in enumerate(leaves) if path[u]>>i&1) for i in range(n-1)};effects.discard(())
    @lru_cache(None)
    def add_units(remaining):
        if not any(remaining):return 0
        best=10**30
        for affected in effects:
            if all(remaining[j]>0 for j in affected):
                nxt=list(remaining)
                for j in affected:nxt[j]-=1
                best=min(best,1+add_units(tuple(nxt)))
        return best
    return add_units(deficit)


def dominating_sets(n,edges,cost,perfect=False):
    graph=graph_for(n,edges);best=10**30
    for mask in range(1<<n):
        value=sum(cost[u] for u in range(n) if mask>>u&1)
        if value>=best:continue
        valid=True
        for u in range(n):
            if mask>>u&1:continue
            servers=sum(bool(mask>>v&1) for v,w in graph[u])
            if (servers!=1 if perfect else servers==0):valid=False;break
        if valid:best=value
    return best


def paint_assignments(n,edges,fixed):
    count=0
    for colors in product(range(3),repeat=n):
        if any(colors[u]!=color for u,color in fixed.items()):continue
        count+=all(colors[u]!=colors[v] for u,v in edges)
    return count


def actual_dfs_orders(n,edges):
    graph=graph_for(n,edges);orders=set()
    def walk(sequence,stack,seen):
        if len(sequence)==n:orders.add(tuple(sequence));return
        while stack and all(seen>>v&1 for v,w in graph[stack[-1]]):stack=stack[:-1]
        assert stack
        for v,w in graph[stack[-1]]:
            if not(seen>>v&1):walk(sequence+[v],stack+[v],seen|1<<v)
    for root in range(n):walk([root],[root],1<<root)
    return len(orders)


def xor_choices(a):
    bound=1<<max(1,max(a).bit_length())
    return min((sum((a[i]^x)>(a[j]^x) for i in range(len(a)) for j in range(i+1,len(a))),x) for x in range(bound))


def independent_subsets(weights,edges):
    best=0
    for mask in range(1<<len(weights)):
        if any(mask>>u&1 and mask>>v&1 for u,v in edges):continue
        best=max(best,sum(w for u,w in enumerate(weights) if mask>>u&1))
    return best


def rooted_parents(n,edges):
    graph=graph_for(n,edges);parent=[-1]*n;parent[0]=0;todo=[0]
    for u in todo:
        for v,w in graph[u]:
            if parent[v]<0:parent[v]=u;todo.append(v)
    parent[0]=-1
    return parent


def prufer_edges(n,sequence):
    degree=[1]*n
    for u in sequence:degree[u]+=1
    leaves=[u for u in range(n) if degree[u]==1];heapq.heapify(leaves);edges=[]
    for u in sequence:
        v=heapq.heappop(leaves);edges.append((u,v));degree[u]-=1
        if degree[u]==1:heapq.heappush(leaves,u)
    edges.append(tuple(leaves));return edges


def relabel(n,edges,rng,keep_root=False):
    if keep_root:
        rest=list(range(1,n));rng.shuffle(rest);permutation=[0]+rest
    else:permutation=list(range(n));rng.shuffle(permutation)
    result=[]
    for edge in edges:
        u,v=edge[:2]
        if rng.randrange(2):u,v=v,u
        result.append((permutation[u],permutation[v],*edge[2:]))
    rng.shuffle(result)
    return permutation,result


def remap(values,permutation):
    result=[0]*len(values)
    for old,new in enumerate(permutation):result[new]=values[old]
    return result


def cases_for(pid):
    rng=random.Random(20261102+sum(map(ord,pid)));result=[]
    def put(inp,out):result.append((f'{pid}-literal-{len(result)+1}',inp,str(out).rstrip()+'\n'))
    def row(values):return ' '.join(map(str,values))+'\n'
    def lines(edges,one_based=True):
        shift=int(one_based)
        return ''.join(f'{e[0]+shift} {e[1]+shift}'+(' '+str(e[2]) if len(e)>2 else '')+'\n' for e in edges)
    def parents(n):return [-1]+[rng.randrange(v) for v in range(1,n)]
    if pid=='B4016':
        for _ in range(300):
            n=rng.randint(1,13);edges=tree_edges(parents(n));answer=max(map(max,all_distances(n,edges)));perm,edges=relabel(n,edges,rng)
            put(f'{n}\n'+lines(edges),answer)
        put('100000\n'+''.join(f'{u} {u+1}\n' for u in range(1,100000)),99999)
        put('100000\n'+''.join(f'1 {v}\n' for v in range(2,100001)),2)
    elif pid=='P11249':
        for _ in range(40):
            cases=[];answers=[]
            for case in range(10):
                n=rng.randint(1,12);edges=tree_edges(parents(n));marked={u for u in range(n) if rng.randrange(3)==0}
                if not marked:marked.add(rng.randrange(n))
                answer=treasure_paths(n,edges,marked);perm,edges=relabel(n,edges,rng)
                flags=[0]*n
                for u in marked:flags[perm[u]]=1
                cases.append(f'{n}\n'+row(flags)+lines(edges));answers.append('Yes' if answer else 'No')
            put('10\n'+''.join(cases),'\n'.join(answers))
        n=100000;chain=''.join(f'{u} {u+1}\n' for u in range(1,n));star=''.join(f'1 {v}\n' for v in range(2,n+1));one=[0]*n;one[-1]=1
        put('3\n'+f'{n}\n'+row([1]*n)+chain+f'{n}\n'+row([1]*n)+star+f'{n}\n'+row(one)+star,'Yes\nNo\nYes')
    elif pid=='P15801':
        for _ in range(260):
            n=rng.randint(1,15);left=[-1]*n;right=[-1]*n;slots=[(0,0),(0,1)]
            for v in range(1,n):
                at=rng.randrange(len(slots));u,side=slots.pop(at)
                (right if side else left)[u]=v;slots += [(v,0),(v,1)]
            expected=complete_subtrees(left,right);perm,_=relabel(n,[],rng,True);l=[0]*n;r=[0]*n
            for u in range(n):l[perm[u]]=perm[left[u]]+1 if left[u]>=0 else 0;r[perm[u]]=perm[right[u]]+1 if right[u]>=0 else 0
            put(f'{n}\n'+''.join(f'{x} {y}\n' for x,y in zip(l,r)),expected)
        n=100000
        put(f'{n}\n'+''.join(f'{2*u if 2*u<=n else 0} {2*u+1 if 2*u+1<=n else 0}\n' for u in range(1,n+1)),n)
        put(f'{n}\n'+''.join(f'{u+1} 0\n' for u in range(1,n))+'0 0\n',2)
        put(f'{n}\n'+''.join(f'0 {u+1}\n' for u in range(1,n))+'0 0\n',1)
    elif pid=='P1131':
        for _ in range(220):
            n=rng.randint(1,7);edges=[(u,v,rng.randint(1,5)) for u,v in tree_edges(parents(n))];root=rng.randrange(n);expected=delay_assignments(n,edges,root);perm,edges=relabel(n,edges,rng)
            put(f'{n}\n{perm[root]+1}\n'+lines(edges),expected)
        n=500000
        put(f'{n}\n1\n'+''.join(f'{u} {u+1} 1000000\n' for u in range(1,n)),0)
        put(f'{n}\n1\n'+''.join(f'1 {v+1} {1 if v%2 else 1000000}\n' for v in range(1,n)),250000*999999)
    elif pid=='P2458':
        def encode(parent,cost,perm=None):
            n=len(parent);perm=perm if perm is not None else list(range(n));child=[[] for _ in range(n)]
            for v in range(1,n):child[parent[v]].append(v)
            order=list(range(n));rng.shuffle(order)
            return f'{n}\n'+''.join(f'{perm[u]+1} {cost[u]} {len(child[u])}'+(' '+ ' '.join(str(perm[v]+1) for v in child[u]) if child[u] else '')+'\n' for u in order)
        for _ in range(260):
            n=rng.randint(1,13);parent=parents(n);cost=[rng.randint(1,10000) for u in range(n)];expected=dominating_sets(n,tree_edges(parent),cost);perm=list(range(n));rng.shuffle(perm)
            put(encode(parent,cost,perm),expected)
        n=1500;put(encode([-1]+list(range(n-1)),[10000]*n),5000000)
        put(encode([-1]+[0]*(n-1),[10000]+[1]*(n-1),list(reversed(range(n)))),1499)
    elif pid=='P2986':
        for _ in range(260):
            n=rng.randint(1,12);edges=[(u,v,rng.randint(0,1000)) for u,v in tree_edges(parents(n))];cows=[rng.randint(0,1000) for u in range(n)];distance=all_distances(n,edges);expected=min(sum(cows[v]*distance[u][v] for v in range(n)) for u in range(n));perm,edges=relabel(n,edges,rng)
            edges=[(min(u,v),max(u,v),w) for u,v,w in edges]
            put(f'{n}\n'+row(remap(cows,perm))+lines(edges),expected)
        n=100000;edges=''.join(f'{u} {u+1} 1000\n' for u in range(1,n))
        put(f'{n}\n'+row([1000]*n)+edges,2500000000000000)
        put(f'{n}\n'+row([0]*n)+edges,0)
    elif pid=='P4084':
        for _ in range(220):
            n=rng.randint(1,9);edges=tree_edges(parents(n));fixed={u:rng.randrange(3) for u in rng.sample(range(n),rng.randrange(n+1))};expected=paint_assignments(n,edges,fixed);perm,edges=relabel(n,edges,rng)
            put(f'{n} {len(fixed)}\n'+lines(edges)+''.join(f'{perm[u]+1} {c+1}\n' for u,c in fixed.items()),expected)
        n=100000
        put(f'{n} 0\n'+''.join(f'{u} {u+1}\n' for u in range(1,n)),3*pow(2,n-1,1000000007)%1000000007)
        put(f'{n} 2\n'+''.join(f'1 {v}\n' for v in range(2,n+1))+'2 1\n3 2\n',pow(2,n-3,1000000007))
        put('2 2\n1 2\n1 1\n2 1\n',0)
    elif pid=='P9584':
        mod=998244353
        for _ in range(220):
            n=rng.randint(2,11);edges=[(u,v,rng.randint(1,1000000)) for u,v in tree_edges(parents(n))];queries=[(rng.randrange(n),rng.randint(1,1000000)) for q in range(rng.randint(1,10))];answers=[]
            for k,w in queries:answers.append(sum(map(sum,all_distances(n+1,edges+[(k,n,w)])))%mod)
            perm,edges=relabel(n,edges,rng)
            put(f'{n} {len(queries)}\n'+lines(edges)+''.join(f'{perm[k]+1} {w}\n' for k,w in queries),'\n'.join(map(str,answers)))
        n=200000;q=200000;w=1000000;answer=w*(n+1)*((n+1)**2-1)//3%mod
        put(f'{n} {q}\n'+''.join(f'{u} {u+1} {w}\n' for u in range(1,n))+''.join(f'{1 if i%2 else n} {w}\n' for i in range(q)),'\n'.join([str(answer)]*q))
        put(f'{n} 2\n'+''.join(f'1 {v} {w}\n' for v in range(2,n+1))+f'1 {w}\n2 {w}\n',f'{2*n*n*w%mod}\n{2*(n-1)*(n+2)*w%mod}')
    elif pid=='P13020':
        for _ in range(220):
            n=rng.randint(1,8);edges=tree_edges(parents(n));expected=actual_dfs_orders(n,edges);perm,edges=relabel(n,edges,rng)
            put(f'{n}\n'+lines(edges),expected)
        n=100000
        put(f'{n}\n'+''.join(f'{u} {u+1}\n' for u in range(1,n)),2*(n-1))
        put(f'{n}\n'+''.join(f'1 {v}\n' for v in range(2,n+1)),0)
        put('12\n'+''.join(f'1 {v}\n' for v in range(2,13)),79833600)
    elif pid=='CF337D':
        for _ in range(260):
            n=rng.randint(1,15);edges=tree_edges(parents(n));marked=rng.sample(range(n),rng.randint(1,n));limit=rng.randrange(n)
            distance=all_distances(n,edges);expected=sum(all(distance[u][v]<=limit for v in marked) for u in range(n));perm,edges=relabel(n,edges,rng)
            put(f'{n} {len(marked)} {limit}\n'+row([perm[u]+1 for u in marked])+lines(edges),expected)
        n=100000;chain=''.join(f'{u} {u+1}\n' for u in range(1,n));star=''.join(f'1 {v}\n' for v in range(2,n+1))
        put(f'{n} 2 49999\n1 {n}\n'+chain,0)
        put(f'{n} 2 50000\n1 {n}\n'+chain,2)
        put(f'{n} 1 100\n50000\n'+chain,201)
        for limit,answer in [(1,1),(2,n)]:put(f'{n} {n-1} {limit}\n'+row(range(2,n+1))+star,answer)
    elif pid=='CF1416C':
        for _ in range(300):
            n=rng.randint(1,13);a=[rng.randrange(64) for _ in range(n)];count,x=xor_choices(a)
            put(f'{n}\n'+row(a),f'{count} {x}')
        n=300000
        put(f'{n}\n'+row(range(n-1,-1,-1)),f'0 {(1<<(n-1).bit_length())-1}')
        put(f'{n}\n'+row([1000000000]*n),'0 0')
        put(f'{n}\n'+row([0,1]*(n//2)),f'{(n//2)*(n//2-1)//2} 0')
        put(f'{n}\n'+row([1000000000]*(n//2)+[0]*(n//2)),f'0 {1<<29}')
    elif pid=='P1453':
        multipliers=['0','0.15','0.25','0.35','0.45','9999.999999','10000']
        for index in range(260):
            n=rng.randint(3,13);edges=tree_edges(parents(n));used={tuple(sorted(e)) for e in edges};extra=rng.choice([e for e in combinations(range(n),2) if e not in used]);edges.append(extra)
            weights=[rng.randint(1,10000) for _ in range(n)];expected=independent_subsets(weights,edges);perm,edges=relabel(n,edges,rng)
            multiplier=multipliers[index%len(multipliers)] if index<70 else f'{rng.randrange(10000000001)/1000000:.6f}'
            put(f'{n}\n'+row(remap(weights,perm))+lines(edges,False)+multiplier+'\n',format(expected*float(multiplier),'.1f'))
        n=100000;weights=row([10000]*n)
        put(f'{n}\n'+weights+''.join(f'{u} {(u+1)%n}\n' for u in range(n))+'10000\n','5000000000000.0')
        put(f'{n}\n'+weights+'0 1\n1 2\n2 0\n'+''.join(f'{u-1} {u}\n' for u in range(3,n))+'0\n','0.0')
    elif pid=='P3554':
        for _ in range(220):
            n=rng.randint(1,9);parent=parents(n);expected=arch_literal(parent);perm,edges=relabel(n,tree_edges(parent),rng,True)
            put(f'{n}\n'+lines(edges),expected)
        n=300000
        put(f'{n}\n'+''.join(f'{u} {u+1}\n' for u in range(1,n)),1)
        put(f'{n}\n'+''.join(f'1 {v}\n' for v in range(2,n+1)),n-1)
        put(f'{n}\n1 2\n'+''.join(f'2 {v}\n' for v in range(3,n+1)),n//2)
    elif pid=='P5958':
        for _ in range(180):
            n=rng.randint(1,10);parent=parents(n);k=rng.randint(1,n);expected=sabotage_literal(parent,k)
            put(f'{n} {k}\n'+row([parent[v]+1 for v in range(1,n)]),expected)
        n=500000
        put(f'{n} 1\n'+row(range(1,n)),1)
        put(f'{n} 1\n'+row([1]*(n-1)),Fraction(1,n-1))
        put(f'{n} {n}\n'+row([1]*(n-1)),0)
        # One large chain child and many root leaves: ignore critical values of
        # smaller subtrees that cannot themselves exceed k.
        chain_size=n//2;parent=[1]+list(range(2,chain_size+1))+[1]*(n-chain_size-1)
        assert len(parent)==n-1
        put(f'{n} {chain_size}\n'+row(parent),Fraction(chain_size,n-1))
    elif pid=='P8916':
        for _ in range(240):
            n=rng.randint(1,12);parent=parents(n);weights=[rng.randint(-1000,1000) for _ in range(n)];expected=morale_literal(parent,weights);perm,edges=relabel(n,tree_edges(parent),rng,True)
            put(f'{n}\n'+lines(edges)+row(remap(weights,perm)),expected)
        n=300;chain=''.join(f'{u} {u+1}\n' for u in range(1,n))
        put(f'{n}\n'+chain+row([1000]*n),1000*n*(n+1)//2)
        put(f'{n}\n'+chain+row([-1000]*n),-1000*n)
        weights=[7]+[1000 if v%2 else -1000 for v in range(1,n)]
        put(f'{n}\n'+''.join(f'1 {v}\n' for v in range(2,n+1))+row(weights),7+sum(2*w if w>0 else w for w in weights[1:]))
    elif pid=='P10767':
        def rule_lines(n,rules):return ''.join(row(rules[1<<level:1<<(level+1)]) for level in range(n))
        put('0 1\n1 1\n','Yes')
        for n in range(1,4):
            total=1<<n
            for rules_tuple in product([1,2],repeat=total-1):
                rules=[0]+list(rules_tuple);possible=tournament_literal(n,rules);queries=[(a,h+1) for h in range(n+1) for a in range(1,total+1)]
                put(f'{n} {len(queries)}\n'+rule_lines(n,rules)+''.join(f'{a} {b}\n' for a,b in queries),'\n'.join('Yes' if a in possible[b-1] else 'No' for a,b in queries))
        n=19;total=1<<n;q=1000000;queries=[(i%total+1,i%(n+1)+1) for i in range(q)]
        put(f'{n} {q}\n'+rule_lines(n,[0]+[1]*(total-1))+''.join(f'{a} {b}\n' for a,b in queries),'\n'.join('Yes' if a>=1<<(b-1) else 'No' for a,b in queries))
        queries=queries[:1000]
        put(f'{n} {len(queries)}\n'+rule_lines(n,[0]+[2]*(total-1))+''.join(f'{a} {b}\n' for a,b in queries),'\n'.join('Yes' if a<=total-(1<<(b-1))+1 else 'No' for a,b in queries))
    elif pid=='UVA1218':
        for _ in range(25):
            cases=[];answers=[]
            for case in range(10):
                n=rng.randint(1,13);edges=tree_edges(parents(n));expected=dominating_sets(n,edges,[1]*n,True);perm,edges=relabel(n,edges,rng)
                cases.append(f'{n}\n'+lines(edges));answers.append(expected)
            put('0\n'.join(cases)+'-1\n','\n'.join(map(str,answers)))
        n=10000
        put(f'{n}\n'+''.join(f'{u} {u+1}\n' for u in range(1,n))+'0\n'+f'{n}\n'+''.join(f'1 {v}\n' for v in range(2,n+1))+'-1\n',f'{(n+2)//3}\n1')
        # Adjacent servers 3 and 4 are valid in the original six-node tree.
        put('6\n1 3\n2 3\n3 4\n4 5\n4 6\n-1\n',2)
    elif pid=='CF1540B':
        mod=1000000007
        def probability_case(n,edges):
            expected=expectation_literal(rooted_parents(n,edges));value=expected.numerator*pow(expected.denominator,-1,mod)%mod
            put(f'{n}\n'+lines(edges),value)
        for n in range(2,6):
            for sequence in product(range(n),repeat=n-2):probability_case(n,prufer_edges(n,sequence))
        for _ in range(200):
            n=rng.randint(2,9);perm,edges=relabel(n,tree_edges(parents(n)),rng);probability_case(n,edges)
        n=200
        put(f'{n}\n'+''.join(f'{u} {u+1}\n' for u in range(1,n)),n*(n-1)*pow(4,-1,mod)%mod)
        expected=Fraction((n-1)*(n*n-2*n+4),4*n)
        put(f'{n}\n'+''.join(f'1 {v}\n' for v in range(2,n+1)),expected.numerator*pow(expected.denominator,-1,mod)%mod)
    else:raise KeyError(pid)
    return result
