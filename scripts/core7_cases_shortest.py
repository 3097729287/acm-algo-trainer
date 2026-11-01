"""Independent physical/state models and bounded exhaustive path oracles."""
from collections import Counter,deque
from decimal import Decimal,localcontext
from itertools import product
from math import gcd
import bisect
import random

IDS={'CF910A','P1339','P1828','P3905','P11966','AT_arc064_c','P1608','P2737','P5195',
     'P7100','P10726','UVA658','CF938D','CF912D','P2371','P3831','P6096','UVA11997'}
INF=10**60


def floyd(n,edges,directed=False):
    d=[[0 if i==j else INF for j in range(n)] for i in range(n)]
    for u,v,w in edges:
        d[u][v]=min(d[u][v],w)
        if not directed:d[v][u]=min(d[v][u],w)
    for k in range(n):
        for i in range(n):
            for j in range(n):d[i][j]=min(d[i][j],d[i][k]+d[k][j])
    return d


def graph_text(n,edges,header=None):
    return (header or f'{n} {len(edges)}')+'\n'+''.join(f'{u+1} {v+1} {w}\n' for u,v,w in edges)


def connected_graph(rng,n,limit=100):
    edges=[(i,rng.randrange(i),rng.randint(1,limit)) for i in range(1,n)]
    for _ in range(n):
        u,v=rng.sample(range(n),2) if n>1 else (0,0)
        if u!=v:edges.append((u,v,rng.randint(1,limit)))
    return edges


def packing(b):
    g=0
    for v in b:g=gcd(g,v)
    if g!=1:return 0
    # A run of min(b) reachable consecutive totals proves every later total.
    m=min(b);reachable=[True];last=0;run=0
    for value in range(1,m*max(b)+m+1):
        yes=any(value>=coin and reachable[value-coin] for coin in b)
        reachable.append(yes);run=run+1 if yes else 0
        if not yes:last=value
        if run>=m:return last
    raise AssertionError('The finite packaging oracle did not close')


def knight_map(land,W,H):
    start=land.index('2');target=land.index('3');q=deque([(start,False)]);d={(start,False):0}
    while q:
        u,held=q.popleft()
        if u==target and held:return d[u,held]
        for dr,dc in [(0,1),(0,-1),(1,0),(-1,0)]:
            nr,nc=u//W+dr,u%W+dc
            if not(0<=nr<H and 0<=nc<W):continue
            v=nr*W+nc
            if land[v]=='1' or (land[v]=='3' and not held):continue
            state=(v,held or land[v]=='4')
            if state not in d:d[state]=d[u,held]+1;q.append(state)
    return -1


def platform_walk(boards,s,t):
    points=[(i,x) for i,(l,r,h) in enumerate(boards) for x in range(l,r+1)]
    index={p:i for i,p in enumerate(points)};edges=[]
    for u,(i,x) in enumerate(points):
        l,r,h=boards[i]
        for nx in [x-1,x+1]:
            if l<=nx<=r:edges.append((u,index[i,nx],1))
        if x not in (l,r):continue
        below=[(b[2],j) for j,b in enumerate(boards) if j!=i and b[0]<=x<=b[1] and b[2]<=h]
        if below:
            top=max(y for y,j in below)
            for y,j in below:
                if y==top:edges.append((u,index[j,x],h-y))
    dist=[INF]*len(points);dist[index[s,boards[s][0]]]=0
    for _ in points:
        changed=False
        for u,v,w in edges:
            if dist[u]+w<dist[v]:dist[v]=dist[u]+w;changed=True
        if not changed:break
    answer=min(dist[u] for u,(i,x) in enumerate(points) if i==t)
    return -1 if answer==INF else answer


def bug_answer(n,patches):
    states=list(product([False,True],repeat=n));d={state:INF for state in states};d[(True,)*n]=0
    for _ in range(len(states)):
        changed=False
        for state in states:
            if d[state]==INF:continue
            for cost,before,after in patches:
                if any(c=='+' and not x or c=='-' and x for c,x in zip(before,state)):continue
                nxt=tuple(True if c=='+' else False if c=='-' else x for c,x in zip(after,state))
                if d[state]+cost<d[nxt]:d[nxt]=d[state]+cost;changed=True
        if not changed:break
    return d[(False,)*n]


def physical_metro(n,transfers,start,finish):
    # All n*n physical stations, independently of compressed event stations.
    edges=[]
    at=lambda x,y,axis:2*(x*n+y)+axis
    for x in range(n):
        for y in range(n):
            for dy in [-1,1]:
                if 0<=y+dy<n:edges.append((at(x,y,0),at(x,y+dy,0),2))
            for dx in [-1,1]:
                if 0<=x+dx<n:edges.append((at(x,y,1),at(x+dx,y,1),2))
            if (x,y) in transfers:
                edges.extend([(at(x,y,0),at(x,y,1),1),(at(x,y,1),at(x,y,0),1)])
    dist=[INF]*(2*n*n);dist[at(*start,0)]=dist[at(*start,1)]=0
    for _ in dist:
        changed=False
        for u,v,w in edges:
            if dist[u]+w<dist[v]:dist[v]=dist[u]+w;changed=True
        if not changed:break
    answer=min(dist[at(*finish,0)],dist[at(*finish,1)])
    return -1 if answer==INF else answer


def fare_time(S,lines,A,B):
    # Enumerate every boarding/alighting occurrence pair, including repeats.
    edges=[]
    for line in lines:
        edges.extend((u,v,abs(i-j)) for i,u in enumerate(line) for j,v in enumerate(line))
    d=[-1]*S;d[A]=0;q=deque([A])
    while q:
        u=q.popleft()
        for a,b,w in edges:
            if a==u and d[b]==-1:d[b]=d[u]+1;q.append(b)
    if d[B]==-1:return '-1\n0'
    best=[-INF]*S;best[A]=0
    # Do not use shortest-distance filtering: enumerate exactly C boardings.
    for step in range(d[B]):
        nxt=[-INF]*S
        for u,v,w in edges:
            if best[u]!=-INF:nxt[v]=max(nxt[v],best[u]+w)
        best=nxt
    return f'{d[B]}\n{best[B]}'


def fish_threshold(n,m,r,k):
    a=Counter(min(i,r,n-i+1,n-r+1) for i in range(1,n+1))
    b=sorted(min(i,r,m-i+1,m-r+1) for i in range(1,m+1));prefix=[0]
    for v in b:prefix.append(prefix[-1]+v)
    def above(threshold):
        count=total=0
        for value,multiplicity in a.items():
            j=bisect.bisect_left(b,(threshold+value-1)//value)
            count+=multiplicity*(m-j);total+=multiplicity*value*(prefix[-1]-prefix[j])
        return count,total
    lo,hi=1,max(a)*b[-1]
    while lo<hi:
        mid=(lo+hi+1)//2
        if above(mid)[0]>=k:lo=mid
        else:hi=mid-1
    count,total=above(lo+1)
    return Decimal(total+(k-count)*lo)/Decimal((n-r+1)*(m-r+1))


def cases_for(pid):
    rng=random.Random(20261030+sum(map(ord,pid)));cases=[]
    def put(inp,expected,label='独立校验'):
        cases.append((f'{label} {len(cases)+1}',str(inp),str(expected)))
    if pid=='CF910A':
        for n in range(2,9):
            for middle in product('01',repeat=n-2):
                s='1'+''.join(middle)+'1'
                for jump in range(1,n):
                    d=[-1]*n;d[0]=0;q=deque([0])
                    while q:
                        u=q.popleft()
                        for v in range(u+1,min(n,u+jump+1)):
                            if s[v]=='1' and d[v]==-1:d[v]=d[u]+1;q.append(v)
                    put(f'{n} {jump}\n{s}\n',d[-1],'全位串 BFS')
    elif pid=='P1339':
        for _ in range(100):
            n=rng.randint(1,13);edges=connected_graph(rng,n,1000);s,t=rng.randrange(n),rng.randrange(n)
            if edges:edges+=rng.choices(edges,k=3)
            put(graph_text(n,edges,f'{n} {len(edges)} {s+1} {t+1}'),floyd(n,edges)[s][t])
        n=2500;edges=[(i,i+1,1000) for i in range(n-1)]
        put(graph_text(n,edges,f'{n} {len(edges)} 1 {n}'),(n-1)*1000,'最大点数长链')
    elif pid=='P1828':
        for _ in range(90):
            P=rng.randint(2,11);edges=connected_graph(rng,P,255);N=rng.randint(1,30);cows=[rng.randrange(P) for _ in range(N)];d=floyd(P,edges)
            ans=min(sum(d[c][v] for c in cows) for v in range(P))
            put(f'{N} {P} {len(edges)}\n'+''.join(f'{v+1}\n' for v in cows)+''.join(f'{u+1} {v+1} {w}\n' for u,v,w in edges),ans)
        P=800;N=500;cows=[(17*i)%P for i in range(N)];edges=[(i,i+1,1) for i in range(P-1)]
        put(f'{N} {P} {len(edges)}\n'+''.join(f'{v+1}\n' for v in cows)+''.join(f'{u+1} {v+1} {w}\n' for u,v,w in edges),min(sum(abs(c-v) for c in cows) for v in range(P)),'最大牧场逐牛距离')
    elif pid=='P3905':
        for _ in range(85):
            n=rng.randint(3,6);allpairs=[(u,v) for u in range(n) for v in range(u+1,n)];rng.shuffle(allpairs)
            edges=[(u,v,rng.randint(1,100)) for u,v in allpairs[:rng.randint(n-1,min(9,len(allpairs)))]]
            # Require an original connection; all roads damaged makes the
            # requested pair genuinely disconnected before rebuilding.
            if floyd(n,edges)[0][-1]==INF:continue
            answer=INF
            for mask in range(1<<len(edges)):
                parent=list(range(n));cost=0
                def find(u):
                    while parent[u]!=u:u=parent[u]
                    return u
                for i,(u,v,w) in enumerate(edges):
                    if mask>>i&1:parent[find(u)]=find(v);cost+=w
                if find(0)==find(n-1):answer=min(answer,cost)
            text=f'{n}\n{len(edges)}\n'+''.join(f'{u+1} {v+1} {w}\n' for u,v,w in edges)+f'{len(edges)}\n'+''.join(f'{u+1} {v+1}\n' for u,v,w in edges)+f'1 {n}\n'
            put(text,answer,'枚举全部修复子集')
        put('4\n4\n1 2 100\n2 4 100\n1 3 3\n3 4 4\n2\n2 4\n3 4\n1 4\n',4,'完好长路免费')
    elif pid=='P11966':
        for _ in range(95):
            n=rng.randint(1,12);edges=connected_graph(rng,n,10**6);school=rng.randrange(n);homes=list(range(n))+[rng.randrange(n) for _ in range(6)];d=floyd(n,edges)
            put(graph_text(n,edges,f'{n} {len(edges)} {school+1} {len(homes)}')+''.join(f'{v+1}\n' for v in homes),'\n'.join(str(d[v][school]) for v in homes))
        n=200000;homes=[0,n-1,n//2,0,n-1];edges=[(i,i+1,10**6) for i in range(n-1)]
        put(graph_text(n,edges,f'{n} {n-1} 1 {len(homes)}')+''.join(f'{v+1}\n' for v in homes),'\n'.join(str(v*10**6) for v in homes),'最大图与长整数')
    elif pid=='AT_arc064_c':
        for _ in range(95):
            n=rng.randint(1,6);sx,sy,tx,ty=[rng.randint(-15,15) for _ in range(4)]
            if (sx,sy)==(tx,ty):tx+=1
            circles=[(rng.randint(-15,15),rng.randint(-15,15),rng.randint(1,12)) for _ in range(n)]
            with localcontext() as context:
                context.prec=55;p=[(sx,sy,0)]+circles+[(tx,ty,0)];size=n+2;edges=[]
                for i,(x,y,r) in enumerate(p):
                    for j in range(i):
                        X,Y,R=p[j];squared=(x-X)**2+(y-Y)**2
                        gap=Decimal(0) if squared<=(r+R)**2 else Decimal(squared).sqrt()-r-R
                        edges.append((i,j,gap))
                answer=floyd(size,edges)[0][-1]
            put(f'{sx} {sy} {tx} {ty}\n{n}\n'+''.join(f'{x} {y} {r}\n' for x,y,r in circles),answer,'高精度 Floyd')
        put('-1 0 1999 0\n1000\n'+''.join(f'{2*i} 0 1\n' for i in range(1000)),0,'最大相切屏障链')
        with localcontext() as c:
            c.prec=55;v=Decimal(2)*Decimal(2).sqrt()*10**9-2
        put('-1000000000 -1000000000 1000000000 1000000000\n1\n0 0 1\n',v,'极端坐标与辐射间隙')
    elif pid=='P1608':
        for _ in range(100):
            n=rng.randint(1,8);edges=[]
            for u in range(n):
                for v in range(n):
                    if u!=v and rng.randrange(4)==0:
                        w=rng.randint(1,10);edges.extend([(u,v,w)]*rng.randint(1,3))
                        if rng.randrange(2):edges.append((u,v,rng.randint(1,10)))
            graph=[{} for _ in range(n)]
            for u,v,w in edges:graph[u][v]=min(w,graph[u].get(v,INF))
            results=[]
            def walk(u,seen,cost):
                if u==n-1:results.append(cost);return
                for v,w in graph[u].items():
                    if v not in seen:walk(v,seen|{v},cost+w)
            walk(0,{0},0)
            ans='No answer' if not results else f'{min(results)} {results.count(min(results))}'
            put(graph_text(n,edges),ans,'枚举简单点序列')
        for layers,dead in [(30,False),(90,True)]:
            edges=[];last=[0]
            for layer in range(layers):
                current=[2*layer+1,2*layer+2];edges.extend((u,v,1) for u in last for v in current);last=current
            target=2*layers+1
            edges.extend([(0,target,1)] if dead else [(u,target,1) for u in last])
            put(graph_text(target+1,edges),'1 1' if dead else f'{layers+1} {1<<layers}','无关大计数' if dead else '计数恰等于二的三十次方')
        n=2000;edges=[(i,i+1,10) for i in range(n-1)]
        put(graph_text(n,edges),f'{10*(n-1)} 1','最大点数正权链')
    elif pid=='P2737':
        for _ in range(150):
            b=rng.sample(range(1,40),rng.randint(1,10));put(str(len(b))+'\n'+'\n'.join(map(str,b))+'\n',packing(b),'逐总量完全背包')
        for b in [[255,256],[256],[1],[2,4,6],[6,10,15]]:
            put(str(len(b))+'\n'+'\n'.join(map(str,b))+'\n',packing(b),'包装边界')
    elif pid=='P5195':
        made=0
        while made<110:
            W,H=rng.randint(2,7),rng.randint(2,7);land=['1' if rng.randrange(4)==0 else '0' for _ in range(W*H)]
            start,knight,bush=rng.sample(range(W*H),3);land[start]='2';land[knight]='3';land[bush]='4'
            for i in range(W*H):
                if land[i]=='0' and rng.randrange(9)==0:land[i]='4'
            answer=knight_map(land,W,H)
            if answer<0:continue
            sep='' if made%2 else ' '
            put(f'{W} {H}\n'+'\n'.join(sep.join(land[row*W:(row+1)*W]) for row in range(H))+'\n',answer,'持灌木标记的完整状态 BFS');made+=1
        W=H=1000;land=['0']*(W*H);land[0]='2';land[1]='3';land[-1]='4'
        put(f'{W} {H}\n'+'\n'.join(''.join(land[row*W:(row+1)*W]) for row in range(H))+'\n',2*(W+H-2)-1,'最大地图先绕开骑士')
    elif pid=='P7100':
        for _ in range(120):
            n=rng.randint(1,10);groups=[];edges=[]
            for i in range(rng.randint(1,9)):
                group=[(u,rng.choice([0,1,7,10**9])) for u in rng.sample(range(n),rng.randint(1,n))];groups.append(group)
                for a,(u,w) in enumerate(group):
                    for v,W in group[a+1:]:edges.append((u,v,w+W))
            d=floyd(n,edges)[0]
            text=f'{n} {len(groups)}\n'+''.join(str(len(group))+'\n'+''.join(f'{u+1} {w}\n' for u,w in group) for group in groups)
            put(text,' '.join(str(4557430888798830399 if v==INF else v) for v in d),'显式团全点对最短路')
        n=200000;put(f'{n} 1\n{n}\n'+''.join(f'{i+1} 1000000000\n' for i in range(n)),'0 '+' '.join(['2000000000']*(n-1)),'大团线性输入')
    elif pid=='P10726':
        boards_cases=[([(1,3,3),(3,5,3)],0,1),([(1,5,4),(2,3,1)],0,1),([(1,2,3),(2,2,1)],0,1),([(1,4,10),(3,5,6),(5,6,3)],0,2)]
        for _ in range(130):
            n=rng.randint(1,7);heights=rng.sample(range(1,20),n);boards=[]
            for h in heights:
                l=rng.randint(1,8);boards.append((l,rng.randint(l,10),h))
            boards_cases.append((boards,rng.randrange(n),rng.randrange(n)))
        for boards,s,t in boards_cases:
            put(f'{len(boards)}\n{s+1} {t+1}\n'+''.join(f'{l} {r} {h}\n' for l,r,h in boards),platform_walk(boards,s,t),'所有板上整数位置 Bellman-Ford')
        n=1000;put(f'{n}\n{n} 1\n'+''.join(f'1 2 {h}\n' for h in range(1,n+1)),n-1,'最大挡板下落链')
    elif pid=='UVA658':
        inputs=[];answers=[]
        for case in range(100):
            n=rng.randint(1,6);patches=[(rng.randint(1,10),''.join(rng.choices('0+-',k=n)),''.join(rng.choices('0+-',k=n))) for _ in range(rng.randint(1,10))]
            answer=bug_answer(n,patches);inputs.append(f'{n} {len(patches)}\n'+''.join(f'{cost} {before} {after}\n' for cost,before,after in patches))
            result='Bugs cannot be fixed.' if answer==INF else f'Fastest sequence takes {answer} seconds.';answers.append(f'Product {case+1}\n{result}\n\n')
        put(''.join(inputs)+'0 0\n',''.join(answers),'布尔元组状态 Bellman-Ford 多产品')
        n=20;patches=[(1,'0'*n,'0'*i+'-'+'0'*(n-i-1)) for i in range(n)]
        put(f'{n} {n}\n'+''.join(f'{c} {b} {a}\n' for c,b,a in patches)+'0 0\n','Product 1\nFastest sequence takes 20 seconds.\n\n','最大缺陷集合全部清位')
    elif pid=='CF938D':
        for _ in range(110):
            n=rng.randint(2,13);edges=[]
            for u in range(n):
                for v in range(u):
                    if rng.randrange(4)==0:edges.append((u,v,rng.choice([1,10,10**12])))
            if not edges:edges=[(0,1,10**12)]
            a=[rng.randint(1,10**12) for _ in range(n)];d=floyd(n,edges)
            put(graph_text(n,edges)+' '.join(map(str,a))+'\n',' '.join(str(min(a[j]+2*d[i][j] for j in range(n))) for i in range(n)),'显式枚举演出城市')
        n=200000;edges=[(i,i+1,1) for i in range(n-1)];a=[10**12]*(n-1)+[1]
        put(graph_text(n,edges)+' '.join(map(str,a))+'\n',' '.join(str(2*(n-1-i)+1) for i in range(n)),'大图廉价演出传播')
    elif pid=='CF912D':
        for _ in range(200):
            n,m=rng.randint(1,7),rng.randint(1,7);r=rng.randint(1,min(n,m));k=rng.randint(1,n*m);cover=[[0]*m for _ in range(n)]
            for x in range(n-r+1):
                for y in range(m-r+1):
                    for i in range(x,x+r):
                        for j in range(y,y+r):cover[i][j]+=1
            values=sorted((v for row in cover for v in row),reverse=True)
            ans=Decimal(sum(values[:k]))/Decimal((n-r+1)*(m-r+1));put(f'{n} {m} {r} {k}\n',ans,'逐网位置统计覆盖')
        for n,m,r,k in [(100000,100000,50000,100000),(100000,100000,1,100000),(100000,100000,100000,100000)]:
            put(f'{n} {m} {r} {k}\n',fish_threshold(n,m,r,k),'独立乘积阈值计数')
    elif pid=='P2371':
        for _ in range(150):
            n=rng.randint(1,12);a=[rng.randint(0,25) for _ in range(n)];l,r=sorted(rng.sample(range(1,351),2));reach=[True]+[False]*r
            for value in range(1,r+1):reach[value]=any(x>0 and value>=x and reach[value-x] for x in a)
            put(f'{n} {l} {r}\n'+' '.join(map(str,a))+'\n',sum(reach[l:r+1]),'逐整数可表示性')
        a,b=499999,500000;R=10**12
        answer=sum((R-x*b)//a+1 for x in range(a) if x*b<=R)-1
        put(f'2 1 {R}\n{a} {b}\n',answer,'大模数规范系数枚举')
        put('12 1 1000000000000\n'+' '.join(['0']*12)+'\n',0,'全部零系数')
        put('2 1 1000000000000\n0 500000\n',2000000,'大模数单系数')
    elif pid=='P3831':
        for _ in range(110):
            n=rng.randint(1,6);allpoints=list(product(range(n),repeat=2));transfers=set(rng.sample(allpoints,rng.randint(0,len(allpoints))));start=rng.choice(allpoints);finish=rng.choice(allpoints)
            text=f'{n} {len(transfers)}\n'+''.join(f'{x+1} {y+1}\n' for x,y in transfers)+f'{start[0]+1} {start[1]+1} {finish[0]+1} {finish[1]+1}\n'
            put(text,physical_metro(n,transfers,start,finish),'全网格方向状态 Bellman-Ford')
        n=20000;m=100000;put(f'{n} {m}\n'+''.join(f'{x} {y}\n' for x in range(1,6) for y in range(1,n+1))+f'1 1 {n} {n}\n',4*(n-1)+1,'最大坐标与换乘站')
    elif pid=='P6096':
        for _ in range(180):
            S=rng.randint(2,8);lines=[[rng.randrange(S) for j in range(rng.randint(1,8))] for i in range(rng.randint(2,7))];A,B=rng.sample(range(S),2)
            text=f'{len(lines)} {S}\n'+' '.join(f'v{i}' for i in range(S))+'\n'+''.join(str(len(line))+' '+' '.join(f'v{i}' for i in line)+'\n' for line in lines)+f'v{A} v{B}\n'
            put(text,fare_time(S,lines,A,B),'逐上车次数枚举全部出现位置')
        lines=[[0,1],[0,2,2,2,1],[1,3]]
        put('3 4\nA X Q B\n2 A X\n5 A Q Q Q X\n2 X B\nA B\n',fare_time(4,lines,0,3),'同层后来发现的更长前缀')
        N,S=400000,300000;text=f'{N} {S}\n'+' '.join(f'v{i}' for i in range(S))+'\n'+''.join(f'2 v{i} v{i+1}\n' for i in range(S-1))+'2 v0 v1\n'*(N-S+1)+f'v0 v{S-1}\n'
        put(text,f'{S-1}\n{S-1}','最大线路数站数与成员数')
    elif pid=='UVA11997':
        inputs=[];answers=[]
        for _ in range(100):
            k=rng.randint(2,5);a=[[rng.randint(1,15) for j in range(k)] for i in range(k)];ans=sorted(map(sum,product(*a)))[:k]
            inputs.append(str(k)+'\n'+''.join(' '.join(map(str,row))+'\n' for row in a));answers.append(' '.join(map(str,ans)))
        put(''.join(inputs),'\n'.join(answers),'全部组合排序与多组 EOF')
        k=750;put(str(k)+'\n'+(' '.join(['1000000']*k)+'\n')*k,' '.join(['750000000']*k),'最大矩阵重复选择')
    else:raise KeyError(pid)
    return cases
