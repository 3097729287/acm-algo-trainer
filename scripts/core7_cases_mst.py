"""Definition-level trees, purchasing schedules, partitions and edge subsets."""
from collections import deque
from decimal import Decimal,localcontext,ROUND_HALF_UP
from functools import lru_cache
from itertools import combinations,permutations,product
import heapq
import math
import random

IDS={'P1194','P1195','P1546','P1547','P2212','P2330','P2872','P17016','CF1687B',
     'P1340','P2700','P5425','P12375','CF1184E1','CF545E','CF1184E2','P2245','P14362'}
INF=10**80


class Sets:
    def __init__(self,n):self.p=list(range(n))
    def root(self,u):
        while self.p[u]!=u:u=self.p[u]
        return u
    def join(self,u,v):
        u,v=self.root(u),self.root(v)
        if u==v:return False
        self.p[u]=v;return True


def trees(n,edges):
    for ids in combinations(range(len(edges)),n-1):
        groups=Sets(n);total=largest=mask=0;valid=True
        for i in ids:
            u,v,w=edges[i]
            if not groups.join(u,v):valid=False;break
            total+=w;largest=max(largest,w);mask|=1<<i
        if valid:yield total,largest,mask


def brute_tree_cost(n,edges):
    return min((value for value,largest,mask in trees(n,edges)),default=None)


@lru_cache(None)
def labelled_trees(n):
    if n==1:return ((),)
    result=[]
    for sequence in product(range(n),repeat=n-2):
        degree=[1]*n
        for v in sequence:degree[v]+=1
        leaves=[v for v in range(n) if degree[v]==1];heapq.heapify(leaves);edges=[]
        for v in sequence:
            u=heapq.heappop(leaves);edges.append((u,v));degree[v]-=1
            if degree[v]==1:heapq.heappush(leaves,v)
        edges.append(tuple(leaves));result.append(tuple(edges))
    return tuple(result)


def random_connected(rng,n,max_edges=11,distinct=False):
    pairs={tuple(sorted((i,rng.randrange(i)))) for i in range(1,n)}
    available=[p for p in combinations(range(n),2) if p not in pairs];rng.shuffle(available)
    extra=rng.randint(0,max(0,min(len(available),max_edges-len(pairs))))
    pairs=sorted(pairs|set(available[:extra]));rng.shuffle(pairs)
    weights=rng.sample(range(100),len(pairs)) if distinct else [rng.randint(1,30) for _ in pairs]
    return [(u,v,w) for (u,v),w in zip(pairs,weights)]


def edge_text(n,edges):return f'{n} {len(edges)}\n'+''.join(f'{u+1} {v+1} {w}\n' for u,v,w in edges)


def euclidean_cost(points,free=(),maximum=None,minimum=None,squared=False):
    n=len(points);free={tuple(sorted(p)) for p in free}
    with localcontext() as context:
        context.prec=65;weight={}
        for u,v in combinations(range(n),2):
            dx=points[u][0]-points[v][0];dy=points[u][1]-points[v][1];w=dx*dx+dy*dy
            if (maximum is not None and w>maximum**2) or (minimum is not None and w<minimum):continue
            weight[u,v]=0 if (u,v) in free else w if squared else Decimal(w).sqrt()
        best=None
        for tree in labelled_trees(n):
            if not all(tuple(sorted(e)) in weight for e in tree):continue
            value=sum(weight[tuple(sorted(e))] for e in tree)
            if best is None or value<best:best=value
        return best


def cents(value):
    with localcontext() as context:
        context.prec=65
        return format(Decimal(value).quantize(Decimal('.01'),rounding=ROUND_HALF_UP),'.2f')


def all_distances(n,edges):
    d=[[0 if u==v else INF for v in range(n)] for u in range(n)]
    for u,v,w in edges:d[u][v]=d[v][u]=min(d[u][v],w)
    for k in range(n):
        for u in range(n):
            for v in range(n):d[u][v]=min(d[u][v],d[u][k]+d[k][v])
    return d


def actual_shortest_tree_cost(n,edges,s):
    target=all_distances(n,edges)[s];best=None
    for total,largest,mask in trees(n,edges):
        selected=[e for i,e in enumerate(edges) if mask>>i&1]
        if all_distances(n,selected)[s]==target and (best is None or total<best):best=total
    assert best is not None
    return best


def partition_value(n,k):
    # Enumerate every set partition; use the original distance expression.
    weight=[[0]*n for _ in range(n)]
    for u,v in combinations(range(n),2):weight[u][v]=weight[v][u]=(2019201913*(u+1)+2019201949*(v+1))%2019201997
    groups=[0]*n;best=0
    def visit(at,count):
        nonlocal best
        if at==n:
            if count==k:best=max(best,min(weight[u][v] for u,v in combinations(range(n),2) if groups[u]!=groups[v]))
            return
        for value in range(min(count+1,k)):
            groups[at]=value;visit(at+1,max(count,value+1))
    visit(1,1);return best


@lru_cache(None)
def exhaustive_mst_assignment(n,m):
    # Every ordered placement of the labels 1..m on distinct unordered pairs.
    best=0;count=0
    for ordered in permutations(list(combinations(range(n),2)),m):
        count+=1;groups=Sets(n);accepted=total=0
        for w,(u,v) in enumerate(ordered,1):
            if groups.join(u,v):
                accepted+=1;total+=w
                if accepted==n-1:break
        if accepted==n-1:best=max(best,total)
    return best,count


def rank_bound_sum(n,m):
    # Arithmetic-boundary oracle uses exact binary search, never float roots.
    lo,hi=1,n-1;D=m-n
    while lo<hi:
        middle=(lo+hi+1)//2
        if middle*(middle-3)<=2*D:lo=middle
        else:hi=middle-1
    p=lo;t=n-1-p
    return (p*(p-1)*(p+1)//6+p+t*(2*D+p+n+2)//2)%998244353


def activated_network(n,roads,costs,attachment):
    k=len(costs);edges=[(*e,0) for e in roads]
    for town in range(k):edges.extend((n+town,v,w,1<<town) for v,w in enumerate(attachment[town]))
    best=INF
    # A nonnegative optimum has an acyclic subset with at most n+k-1 edges.
    for size in range(n-1,min(len(edges),n+k-1)+1):
        for ids in combinations(range(len(edges)),size):
            groups=Sets(n+k);total=active=0
            for i in ids:
                u,v,w,bit=edges[i]
                if not groups.join(u,v):break
                total+=w;active|=bit
            else:
                if all(groups.root(v)==groups.root(0) for v in range(n)):
                    total+=sum(c for j,c in enumerate(costs) if active>>j&1);best=min(best,total)
    assert best!=INF;return best


def cases_for(pid):
    rng=random.Random(20261030+sum(map(ord,pid)));cases=[]
    def put(inp,expected,label='独立校验'):cases.append((f'{label} {len(cases)+1}',str(inp),str(expected)))
    if pid=='P1194':
        for _ in range(110):
            n=rng.randint(1,8);A=rng.randint(0,20);price=[[0]*n for _ in range(n)]
            for u,v in combinations(range(n),2):price[u][v]=price[v][u]=rng.randint(0,30)
            best=[INF]*(1<<n);best[0]=0
            for mask in range(1<<n):
                for v in range(n):
                    if not mask>>v&1:
                        cost=min([A]+[price[u][v] for u in range(n) if mask>>u&1 and price[u][v]>0])
                        best[mask|1<<v]=min(best[mask|1<<v],best[mask]+cost)
            put(f'{A} {n}\n'+''.join(' '.join(map(str,row))+'\n' for row in price),best[-1],'枚举所有购买集合')
        for A,promo,ans in [(1000,0,500000),(1000,1,1499),(0,1000,0)]:
            n=500;put(f'{A} {n}\n'+''.join(' '.join(str(0 if u==v else promo) for v in range(n))+'\n' for u in range(n)),ans,'最大商品矩阵')
    elif pid=='P1195':
        for _ in range(110):
            n=rng.randint(1,8);k=rng.randint(1,min(n+2,10));edges=[]
            for u,v in rng.sample(list(combinations(range(n),2)),rng.randint(0,min(10,n*(n-1)//2))):edges.append((u,v,rng.randint(0,20)))
            if not edges:edges=[(0,0,0)]
            best=None
            if k<=n:
                for ids in combinations(range(len(edges)),n-k):
                    groups=Sets(n);total=0
                    for i in ids:
                        u,v,w=edges[i]
                        if not groups.join(u,v):break
                        total+=w
                    else:
                        if best is None or total<best:best=total
            put(f'{n} {len(edges)} {k}\n'+''.join(f'{u+1} {v+1} {w}\n' for u,v,w in edges),'No Answer' if best is None else best,'枚举固定秩森林')
        n=1000;k=10;edges=[(i,i+1,1) for i in range(n-1)]+[(0,i,9999) for i in range(2,n)]
        put(f'{n} {len(edges)} {k}\n'+''.join(f'{u+1} {v+1} {w}\n' for u,v,w in edges),n-k,'最大点数K块')
    elif pid=='P1546':
        for _ in range(100):
            n=rng.randint(3,6);matrix=[[0]*n for _ in range(n)]
            for u,v in combinations(range(n),2):matrix[u][v]=matrix[v][u]=rng.randint(0,100000)
            answer=min(sum(matrix[u][v] for u,v in tree) for tree in labelled_trees(n))
            flat=[str(value) for row in matrix for value in row]
            put(str(n)+'\n'+'\n'.join(' '.join(flat[i:i+7]) for i in range(0,len(flat),7))+'\n',answer,'全部Pruefer树及折行输入')
        n=100;put(str(n)+'\n'+''.join(' '.join(str(0 if u==v else 100000) for v in range(n))+'\n' for u in range(n)),(n-1)*100000,'最大矩阵')
    elif pid in {'P1547','P2330'}:
        for _ in range(110):
            n=rng.randint(2,7);edges=random_connected(rng,n);bottleneck=min(largest for total,largest,mask in trees(n,edges))
            if pid=='P1547' and edges:edges+=rng.choices(edges,k=2)
            put(edge_text(n,edges),bottleneck if pid=='P1547' else f'{n-1} {bottleneck}','枚举全部生成树瓶颈')
        n=2000 if pid=='P1547' else 300;m=10000 if pid=='P1547' else 8000
        edges=[(i,i+1,1) for i in range(n-1)];seen={tuple(sorted((u,v))) for u,v,w in edges}
        while len(edges)<m:
            u,v=rng.sample(range(n),2)
            pair=tuple(sorted((u,v)))
            if pid=='P2330' and pair in seen:continue
            seen.add(pair);edges.append((u,v,9999))
        put(edge_text(n,edges),1 if pid=='P1547' else f'{n-1} 1','最大道路数')
    elif pid=='P2212':
        for _ in range(100):
            n=rng.randint(1,6);points=[(rng.randint(0,10),rng.randint(0,10)) for i in range(n)];c=rng.randint(1,100)
            answer=euclidean_cost(points,minimum=c,squared=True)
            put(f'{n} {c}\n'+''.join(f'{x} {y}\n' for x,y in points),-1 if answer is None else answer,'枚举几何生成树')
        for c in [25,26]:put(f'2 {c}\n0 0\n3 4\n',25 if c==25 else -1,'距离平方门槛相等')
        n=2000;put(f'{n} 1\n'+''.join(f'{i%1000} {i//1000}\n' for i in range(n)),n-1,'最大二维格点')
    elif pid=='P2872':
        for _ in range(100):
            n=rng.randint(1,6);points=[(rng.randint(1,20),rng.randint(1,20)) for i in range(n)];pairs=list(combinations(range(n),2));rng.shuffle(pairs);old=pairs[:rng.randint(1,len(pairs))] if pairs else [(0,0)]
            answer=euclidean_cost(points,free=old)
            put(f'{n} {len(old)}\n'+''.join(f'{x} {y}\n' for x,y in points)+''.join(f'{u+1} {v+1}\n' for u,v in old),cents(answer),'全部Pruefer树高精度长度')
        n=1000;old=[(i,i+1) for i in range(499)];put(f'{n} {len(old)}\n'+''.join(f'{i+1} 1\n' for i in range(n))+''.join(f'{u+1} {v+1}\n' for u,v in old),'500.00','最大点数已有半段链')
        old=[(i,i+1) for i in range(n-1)];put(f'{n} {len(old)}\n'+''.join(f'{i+1} 1\n' for i in range(n))+''.join(f'{u+1} {v+1}\n' for u,v in old),'0.00','已有网络全部连通')
    elif pid=='P17016':
        for _ in range(100):
            n=rng.randint(1,6);points=[(rng.randint(-10,10),rng.randint(-10,10)) for i in range(n)];limit=rng.randint(1,20);answer=euclidean_cost(points,maximum=limit)
            put(f'{n} {limit}\n'+''.join(f'{x} {y}\n' for x,y in points),'Impossible' if answer is None else cents(answer),'枚举全部受限几何树')
        for limit in [4,5]:put(f'2 {limit}\n0 0\n3 4\n','Impossible' if limit==4 else '5.00','长度上限相等')
        n=500;put(f'{n} 1\n'+''.join(f'{i%25-10} {i//25-10}\n' for i in range(n)),'499.00','最大基站格点')
    elif pid=='P1340':
        for _ in range(80):
            n=rng.randint(2,7);weeks=rng.randint(1,12);edges=[];answers=[]
            for week in range(weeks):
                u,v=rng.sample(range(n),2);edges.append((u,v,rng.randint(1,30)));value=brute_tree_cost(n,edges);answers.append(-1 if value is None else value)
            put(f'{n} {weeks}\n'+''.join(f'{u+1} {v+1} {w}\n' for u,v,w in edges),'\n'.join(map(str,answers)),'每个完整历史前缀枚举生成树')
        n=200;edges=[(i,i+1,10000) for i in range(n-1)];answers=[-1]*(n-2)+[10000*(n-1)]
        for i in range(1,n):edges.append((0,i,1));answers.append(i+10000*(n-1-i))
        while len(edges)<6000:
            u,v=rng.sample(range(n),2);edges.append((u,v,10000));answers.append(n-1)
        put(f'{n} {len(edges)}\n'+''.join(f'{u+1} {v+1} {w}\n' for u,v,w in edges),'\n'.join(map(str,answers)),'最大周数插入替换')
    elif pid=='P2700':
        for _ in range(130):
            n=rng.randint(2,9);enemy=set(rng.sample(range(n),rng.randint(2,n)));edges=[(i,rng.randrange(i),rng.randint(1,30)) for i in range(1,n)];best=INF
            for mask in range(1<<(n-1)):
                groups=Sets(n);cost=0
                for i,(u,v,w) in enumerate(edges):
                    if mask>>i&1:cost+=w
                    else:groups.join(u,v)
                roots=[groups.root(u) for u in enemy]
                if len(set(roots))==len(roots):best=min(best,cost)
            put(f'{n} {len(enemy)}\n'+' '.join(map(str,sorted(enemy)))+'\n'+''.join(f'{u} {v} {w}\n' for u,v,w in edges),best,'枚举所有切边集合')
        n=100000;edges=[(i,i+1,1000000) for i in range(n-1)]
        put(f'{n} {n}\n'+' '.join(map(str,range(n)))+'\n'+''.join(f'{u} {v} {w}\n' for u,v,w in edges),(n-1)*1000000,'全部城市敌占长整数')
        edges[n//2]=(n//2,n//2+1,1)
        put(f'{n} 2\n0 {n-1}\n'+''.join(f'{u} {v} {w}\n' for u,v,w in edges),1,'两端敌占仅切最便宜边')
    elif pid=='P5425':
        for n in range(2,8):
            for k in range(2,n+1):put(f'{n} {k}\n',partition_value(n,k),'枚举全部非空分组')
        for _ in range(80):
            n=rng.randint(8,100);k=rng.randint(2,n);edges=[((2019201913*(u+1)+2019201949*(v+1))%2019201997,u,v) for u,v in combinations(range(n),2)];edges.sort();groups=Sets(n);components=n;answer=None
            for w,u,v in edges:
                if groups.root(u)==groups.root(v):continue
                if components==k:answer=w;break
                groups.join(u,v);components-=1
            assert answer is not None;put(f'{n} {k}\n',answer,'原完全图Kruskal分组门槛')
        for k in [2,3750,7500]:put(f'7500 {k}\n',2019201997-84*(k-1)-48*7500,'最大规模双算法算术边界')
    elif pid=='P12375':
        rows=[];answers=[]
        for n,m in [(4,4),(4,5),(4,6),(5,5),(5,6),(5,7)]:
            answer,count=exhaustive_mst_assignment(n,m);rows.append((n,m));answers.append(answer)
        for _ in range(240):
            n=rng.randint(4,500);m=rng.randint(n,n*(n-1)//2)
            rows.append((n,m));answers.append(sum(min(i*(i-1)//2+1,m-n+i+1) for i in range(1,n))%998244353)
        for p in [3,4,5,7,100,1000000,1000000000,1414213560]:
            D=p*(p-3)//2
            for delta in [-1,0,1]:
                d=D+delta;n=max(4,p+100)
                if d<0 or n+d>10**18:continue
                m=n+d;rows.append((n,m));answers.append(rank_bound_sum(n,m))
        for n,m in [(10**18,10**18),(4,6),(2*10**9,10**18),(10**18-1,10**18)]:rows.append((n,m));answers.append(rank_bound_sum(n,m))
        put(str(len(rows))+'\n'+''.join(f'{n} {m}\n' for n,m in rows),'\n'.join(map(str,answers)),'完整图权值排列与精确根边界')
        count=1000000;rows=[];answers=[]
        for i in range(count):
            n=10**18-i;rows.append(f'{n} {n}\n');answers.append(str((n*(n+1)//2-3)%998244353))
        put(str(count)+'\n'+''.join(rows),'\n'.join(answers),'百万组超大单环图闭式边界')
    elif pid in {'CF1184E1','CF1184E2'}:
        for _ in range(110):
            n=rng.randint(2,7);edges=random_connected(rng,n,distinct=pid=='CF1184E2');all_trees=list(trees(n,edges));base=min(cost for cost,largest,mask in all_trees)
            chosen=next(mask for cost,largest,mask in all_trees if cost==base);ids=[0] if pid=='CF1184E1' else [i for i in range(len(edges)) if not chosen>>i&1];answers=[]
            for edge in ids:
                included=min(cost-edges[edge][2] for cost,largest,mask in all_trees if mask>>edge&1)
                omitted=min((cost for cost,largest,mask in all_trees if not mask>>edge&1),default=None)
                answers.append(10**9 if omitted is None else min(10**9,omitted-included))
            put(edge_text(n,edges),'\n'.join(map(str,answers)),'枚举包含及不包含边的所有树')
        if pid=='CF1184E1':
            put('3 3\n1 2 999999999\n1 3 0\n2 3 0\n',0,'零权替代路径')
            put('2 1\n1 2 0\n',1000000000,'零权桥仍可提高到上限')
        n=100000;m=1000000;edges=[];answers=[]
        if pid=='CF1184E1':
            edges=[(0,1,7)];gap=1
            while len(edges)<m:
                for u in range(1,n-gap):
                    edges.append((u,u+gap,10));
                    if len(edges)==m:break
                gap+=1
            put(edge_text(n,edges),10**9,'百万边首边为桥')
        else:
            edges=[(i,i+1,i) for i in range(n-1)];gap=2
            while len(edges)<m:
                for u in range(n-gap):
                    v=u+gap;edges.append((u,v,len(edges)));answers.append(v-1)
                    if len(edges)==m:break
                gap+=1
            put(edge_text(n,edges),'\n'.join(map(str,answers)),'百万互异边长链查询')
    elif pid=='P2245':
        for _ in range(120):
            n=rng.randint(1,9);edges=[(rng.randrange(n),rng.randrange(n),rng.randint(0,100)) for i in range(rng.randint(1,14))];d=[[0 if u==v else INF for v in range(n)] for u in range(n)]
            for u,v,w in edges:
                if u!=v:d[u][v]=d[v][u]=min(d[u][v],w)
            for k in range(n):
                for u in range(n):
                    for v in range(n):d[u][v]=min(d[u][v],max(d[u][k],d[k][v]))
            queries=list(product(range(n),repeat=2));rng.shuffle(queries)
            put(edge_text(n,edges)+str(len(queries))+'\n'+''.join(f'{u+1} {v+1}\n' for u,v in queries),'\n'.join('impossible' if d[u][v]==INF else str(d[u][v]) for u,v in queries),'原图min-max Floyd')
        n=100000;m=300000;edges=[(i,i+1,i+1) for i in range(n-1)]+[(i,i,1) for i in range(n)]
        while len(edges)<m:
            u=rng.randrange(n-1);edges.append((u,u+1,1000000000))
        queries=[(rng.randrange(n),rng.randrange(n)) for _ in range(100000)]
        put(edge_text(n,edges)+str(len(queries))+'\n'+''.join(f'{u+1} {v+1}\n' for u,v in queries),'\n'.join(str(0 if u==v else max(u,v)) for u,v in queries),'最大森林路径表与重边自环')
    elif pid=='CF545E':
        for _ in range(90):
            n=rng.randint(1,7);edges=random_connected(rng,n);s=rng.randrange(n)
            put(edge_text(n,edges)+str(s+1)+'\n',actual_shortest_tree_cost(n,edges,s),'逐树检验全部最短距离')
        n=300000;edges=[(i,i+1,1000000000) for i in range(n-1)]
        put(edge_text(n,edges)+'1\n',(n-1)*1000000000,'最大点数长整数树')
        edges=[(i,i+1,1) for i in range(n-1)]+[(0,n-1,1000000000)]
        put(edge_text(n,edges)+str(n//2)+'\n',n-1,'最大边数不取昂贵直达边')
    elif pid=='P14362':
        for _ in range(80):
            n=rng.randint(2,4);roads=random_connected(rng,n,max_edges=5);roads=[(u,v,w%15) for u,v,w in roads];k=rng.randint(0,2);costs=[rng.randint(0,15) for _ in range(k)];attachment=[[rng.randint(0,15) for i in range(n)] for j in range(k)]
            answer=activated_network(n,roads,costs,attachment)
            text=f'{n} {len(roads)} {k}\n'+''.join(f'{u+1} {v+1} {w}\n' for u,v,w in roads)+''.join(str(c)+' '+' '.join(map(str,a))+'\n' for c,a in zip(costs,attachment))
            put(text,answer,'原始可选道路子集及一次启用费')
        put('2 1 1\n1 2 10\n5 0 0\n',5,'一次费用不能按每边重复支付')
        n=10000;m=1000000;k=10
        roads=''.join(f'{i%(n-1)+1} {i%(n-1)+2} 1\n' for i in range(m))
        town=('0 '+' '.join(['1']*n)+'\n')*k
        put(f'{n} {m} {k}\n'+roads+town,n-1,'最大道路与全子集枚举')
    elif pid=='CF1687B':return []
    else:raise KeyError(pid)
    return cases
