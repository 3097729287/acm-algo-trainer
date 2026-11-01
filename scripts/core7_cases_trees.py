"""Definition-level walks, folds, permutations and connected-subset oracles."""
from collections import deque
from functools import lru_cache
from itertools import combinations,permutations
import random

IDS={'P1030','P4715','P1351','P3379','P10113','P1185','P5536','UVA11987','CF77C',
     'CF455C','CF540E','P1099','P9433','CF196C','CF538E','CF765E','CF980E','CF1278E'}


def adjacency(n,edges):
    g=[[] for _ in range(n)]
    for u,v,*weight in edges:
        w=weight[0] if weight else 1;g[u].append((v,w));g[v].append((u,w))
    return g


def random_tree(rng,n,weighted=False):
    label=list(range(n));rng.shuffle(label)
    edges=[(label[i],label[rng.randrange(i)]) for i in range(1,n)]
    rng.shuffle(edges)
    return [(u,v,rng.randint(0,9)) for u,v in edges] if weighted else edges


def edge_text(edges,weighted=False):
    return ''.join(f'{u+1} {v+1}'+(f' {w[0]}' if weighted else '')+'\n' for u,v,*w in edges)


def all_paths(n,edges):
    g=adjacency(n,edges);distance=[];paths=[]
    for source in range(n):
        d=[None]*n;route=[None]*n;d[source]=0;route[source]=(source,);queue=[source]
        for u in queue:
            for v,w in g[u]:
                if d[v] is None:d[v]=d[u]+w;route[v]=route[u]+(v,);queue.append(v)
        distance.append(d);paths.append(route)
    return distance,paths


def parents(n,edges,root):
    g=adjacency(n,edges);p=[None]*n;p[root]=root;order=[root]
    for u in order:
        for v,w in g[u]:
            if p[v] is None:p[v]=u;order.append(v)
    return p


def ancestors(p,u):
    answer={u}
    while p[u]!=u:u=p[u];answer.add(u)
    return answer


def connected_subset(n,edges,subset):
    if not subset:return False
    g=adjacency(n,edges);reached={next(iter(subset))};todo=list(reached)
    for u in todo:
        for v,w in g[u]:
            if v in subset and v not in reached:reached.add(v);todo.append(v)
    return reached==subset


@lru_cache(None)
def shapes(n):
    if n==0:return (None,)
    return tuple((left,right) for k in range(n) for left in shapes(k) for right in shapes(n-1-k))


def traversals(shape,letters):
    it=iter(letters)
    def visit(s):
        if s is None:return '','',''
        root=next(it);a,b,c=visit(s[0]);d,e,f=visit(s[1])
        return a+root+d,b+e+root,root+c+f
    return visit(shape)


def picture(m,deleted):
    # Build all coordinates bottom-up from the required leaf spacing.
    count=1<<(m-1);levels=[None]*m
    width=6*(1<<(m-2))-1;bottom=(width-1)//2
    levels[-1]=[(6*(j//2)+4*(j%2),bottom) for j in range(count)]
    for d in range(m-2,-1,-1):
        levels[d]=[]
        for j in range(1<<d):
            a,b=levels[d+1][2*j:2*j+2];x=(a[0]+b[0])//2;y=a[1]-(b[0]-a[0])//2
            levels[d].append((x,y))
    alive=[[(d,j) not in deleted for j in range(1<<d)] for d in range(m)]
    for d in range(1,m):
        for j in range(1<<d):alive[d][j]&=alive[d-1][j//2]
    canvas=[[' ']*width for _ in range(bottom+1)]
    for d in range(m):
        for j,(x,y) in enumerate(levels[d]):
            if not alive[d][j]:continue
            canvas[y][x]='o'
            if d:
                px,py=levels[d-1][j//2];sign=1 if x>px else -1
                for row in range(py+1,y):canvas[row][px+sign*(row-py)]='\\' if sign>0 else '/'
    return '\n'.join(''.join(row) for row in canvas)+'\n'


def closed_walk(g,capacity,source):
    @lru_cache(None)
    def visit(u,spent):
        best=0 if u==source else -10**9
        for v,w in g[u]:
            if spent[v]<capacity[v]:
                nxt=list(spent);nxt[v]+=1;best=max(best,1+visit(v,tuple(nxt)))
        return best
    return visit(source,(0,)*len(g))


def fold_by_operations(n,edges):
    g=adjacency(n,edges)
    @lru_cache(None)
    def visit(mask):
        verts=[u for u in range(n) if mask>>u&1]
        degree={u:sum(mask>>v&1 for v,w in g[u]) for u in verts}
        answer=len(verts)-1 if all(d<=2 for d in degree.values()) else n+1
        for u in verts:
            arms=[]
            for v,w in g[u]:
                if not(mask>>v&1):continue
                p=u;bits=0;length=0
                while True:
                    bits|=1<<v;length+=1
                    if degree[v]==1:arms.append((length,bits));break
                    if degree[v]!=2:break
                    nxt=next(x for x,w in g[v] if x!=p and mask>>x&1);p,v=v,nxt
            for length,bits in arms:
                if any(other!=bits and length==other_length for other_length,other in arms):answer=min(answer,visit(mask^bits))
        return answer
    result=visit((1<<n)-1);return -1 if result==n+1 else result


def repeated_label_oracle(n,edges,queries):
    g=adjacency(n,edges);answer=[]
    def component(s):
        reached={s};queue=[s]
        for u in queue:
            for v,w in g[u]:
                if v not in reached:reached.add(v);queue.append(v)
        return reached
    def diameter(vertices,extra=None):
        result=0
        for s in vertices:
            d={s:0};queue=[s]
            for u in queue:
                adj=[v for v,w in g[u]]
                if extra and u==extra[0]:adj.append(extra[1])
                if extra and u==extra[1]:adj.append(extra[0])
                for v in adj:
                    if v not in d:d[v]=d[u]+1;queue.append(v)
            result=max(result,max(d.values()))
        return result
    for query in queries:
        typ,u,*rest=query;a=component(u)
        if typ==1:answer.append(diameter(a));continue
        v=rest[0]
        if v in a:continue
        b=component(v)
        _,x,y=min((diameter(a|b,(x,y)),x,y) for x in a for y in b)
        g[x].append((y,1));g[y].append((x,1))
    return answer


def key_visit_oracle(n,edges,keys,s,t):
    # Shortest walk in the literal (vertex, collected-key-mask) state graph.
    import heapq
    g=adjacency(n,edges);key={u:1<<i for i,u in enumerate(keys)};end=(1<<len(keys))-1
    start=(s,key.get(s,0));d={start:0};heap=[(0,*start)]
    while heap:
        cost,u,mask=heapq.heappop(heap)
        if d[(u,mask)]!=cost:continue
        if u==t and mask==end:return cost
        for v,w in g[u]:
            state=(v,mask|key.get(v,0));value=cost+w
            if value<d.get(state,10**20):d[state]=value;heapq.heappush(heap,(value,*state))


def cases_for(pid):
    rng=random.Random(2026103017);result=[]
    def put(inp,out):result.append((f'树独立基准 {len(result)+1}',str(inp),str(out)))
    if pid=='P1030':
        for n in range(1,7):
            for shape in shapes(n):
                labels=rng.sample(list('ABCDEFGHIJKLMNOPQRSTUVWXYZ'),n);a,b,c=traversals(shape,labels);put(a+'\n'+b+'\n',c+'\n')
        for _ in range(180):
            n=rng.randint(7,8);a,b,c=traversals(rng.choice(shapes(n)),rng.sample(list('ABCDEFGHIJKLMNOPQRSTUVWXYZ'),n));put(a+'\n'+b+'\n',c+'\n')
    elif pid=='P4715':
        for exponent in range(1,8):
            for _ in range(30):
                a=rng.sample(range(-10**9,10**9),1<<exponent);teams=list(enumerate(a))
                while len(teams)>2:teams=[max(teams[i:i+2],key=lambda p:p[1]) for i in range(0,len(teams),2)]
                runner=min(teams,key=lambda p:p[1])[0]+1;put(str(exponent)+'\n'+' '.join(map(str,a))+'\n',runner)
    elif pid=='P1351':
        for _ in range(240):
            n=rng.randint(3,16);edges=random_tree(rng,n);d,_=all_paths(n,edges);weights=[rng.randint(1,10000) for _ in range(n)]
            products=[weights[u]*weights[v] for u in range(n) for v in range(n) if d[u][v]==2]
            put(f'{n}\n'+edge_text(edges)+' '.join(map(str,weights))+'\n',f'{max(products)} {sum(products)%10007}')
        n=200000;put(f'{n}\n'+''.join(f'1 {i}\n' for i in range(2,n+1))+' '.join(['10000']*n)+'\n',f'100000000 {((n-1)*(n-2)*10**8)%10007}')
    elif pid=='P3379':
        for _ in range(210):
            n=rng.randint(1,18);root=rng.randrange(n);edges=random_tree(rng,n);p=parents(n,edges,root)
            queries=list(combinations(range(n),2))+[(u,u) for u in range(n)];rng.shuffle(queries);answers=[]
            depth=[len(ancestors(p,u)) for u in range(n)]
            for u,v in queries:answers.append(max(ancestors(p,u)&ancestors(p,v),key=lambda z:depth[z])+1)
            put(f'{n} {len(queries)} {root+1}\n'+edge_text(edges)+''.join(f'{u+1} {v+1}\n' for u,v in queries),'\n'.join(map(str,answers)))
        n=q=500000;root=251113;queries=[(i%n+1,(i*7919+7)%n+1) for i in range(q)]
        def answer(a,b):return max(a,b) if max(a,b)<=root else min(a,b) if min(a,b)>=root else root
        put(f'{n} {q} {root}\n'+''.join(f'{i} {i+1}\n' for i in range(1,n))+''.join(f'{a} {b}\n' for a,b in queries),'\n'.join(str(answer(a,b)) for a,b in queries))
    elif pid=='P10113':
        for _ in range(230):
            n=rng.randint(3,20);edges=random_tree(rng,n);p=parents(n,edges,0);queries=[rng.sample(range(n),rng.randint(2,min(n,10))) for _ in range(25)];answers=[]
            for row in queries:answers.append(max(set.intersection(*(ancestors(p,u) for u in row))))
            put(f'{n}\n'+' '.join(str(p[u]) for u in range(1,n))+f'\n{len(queries)}\n'+''.join(str(len(row))+' '+' '.join(map(str,row))+'\n' for row in queries),'\n'.join(map(str,answers)))
        n=100000;q=100;m=10000;p=[u+1 for u in range(1,n-1)]+[0]
        put(f'{n}\n'+' '.join(map(str,p))+f'\n{q}\n'+(str(m)+' '+' '.join(map(str,range(1,m+1)))+'\n')*q,'\n'.join([str(n-1)]*q))
    elif pid=='P1185':
        for m in range(2,7):
            for _ in range(30):
                options=[(d,j) for d in range(1,m) for j in range(1<<d)];deleted=set(rng.sample(options,rng.randint(0,min(10,len(options)))))
                put(f'{m} {len(deleted)}\n'+''.join(f'{d+1} {j+1}\n' for d,j in sorted(deleted)),picture(m,deleted))
        for deleted in [set(),{(1,0),(2,1),(9,511)}]:put(f'10 {len(deleted)}\n'+''.join(f'{d+1} {j+1}\n' for d,j in deleted),picture(10,deleted))
    elif pid=='P5536':
        from core7_cases_mst import labelled_trees
        for n in range(2,6):
            for edges in labelled_trees(n):
                d,_=all_paths(n,edges)
                for k in range(1,n):
                    best=min(max(min(d[u][v] for v in chosen) for u in range(n)) for row in combinations(range(n),k) if connected_subset(n,edges,chosen:=set(row)))
                    put(f'{n} {k}\n'+edge_text(edges),best)
        for _ in range(160):
            n=rng.randint(6,11);k=rng.randint(1,n-1);edges=random_tree(rng,n);d,_=all_paths(n,edges)
            best=min(max(min(d[u][v] for v in chosen) for u in range(n)) for row in combinations(range(n),k) if connected_subset(n,edges,chosen:=set(row)))
            put(f'{n} {k}\n'+edge_text(edges),best)
        n=100000;k=37411;put(f'{n} {k}\n'+''.join(f'{i} {i+1}\n' for i in range(1,n)),(n-k+1)//2)
    elif pid=='UVA11987':
        for _ in range(100):
            inputs=[];answers=[]
            for case in range(rng.randint(2,5)):
                n=rng.randint(1,25);m=100;groups=[{u} for u in range(n+1)];where=list(range(n+1));commands=[]
                for __ in range(m):
                    typ=rng.randint(1,3);p,q=rng.randint(1,n),rng.randint(1,n);a,b=where[p],where[q]
                    if typ==3:commands.append(f'3 {p}');answers.append(f'{len(groups[a])} {sum(groups[a])}')
                    elif typ==1:
                        commands.append(f'1 {p} {q}')
                        if a!=b:
                            for x in groups[a]:where[x]=b
                            groups[b]|=groups[a];groups[a]=set()
                    else:
                        commands.append(f'2 {p} {q}')
                        if a!=b:groups[a].remove(p);groups[b].add(p);where[p]=b
                inputs.append(f'{n} {m}\n'+'\n'.join(commands)+'\n')
            put(''.join(inputs),'\n'.join(answers))
        n=100000;put(f'{n} {n}\n'+''.join(f'1 1 {i}\n' for i in range(2,n+1))+'3 1\n',f'{n} {n*(n+1)//2}')
    elif pid=='CF77C':
        for _ in range(700):
            n=rng.randint(1,7);edges=random_tree(rng,n);k=[rng.randint(1,3) for _ in range(n)];s=rng.randrange(n)
            put(f'{n}\n'+' '.join(map(str,k))+'\n'+edge_text(edges)+str(s+1)+'\n',closed_walk(adjacency(n,edges),k,s))
        n=100000;put(f'{n}\n'+' '.join(['100000']*n)+'\n'+''.join(f'1 {i}\n' for i in range(2,n+1))+'1\n',200000)
        put(f'{n}\n'+' '.join(['100000']*n)+'\n'+''.join(f'{i} {i+1}\n' for i in range(1,n))+'1\n',9999999998)
    elif pid=='CF455C':
        for _ in range(210):
            n=rng.randint(1,9);edges=[e for e in random_tree(rng,n) if rng.randrange(2)];queries=[]
            for __ in range(35):queries.append((1,rng.randrange(n)) if rng.randrange(2) else (2,rng.randrange(n),rng.randrange(n)))
            answer=repeated_label_oracle(n,edges,queries)
            put(f'{n} {len(edges)} {len(queries)}\n'+edge_text(edges)+''.join(' '.join([str(row[0])]+[str(v+1) for v in row[1:]])+'\n' for row in queries),'\n'.join(map(str,answer)))
        n=300000;q=300000;commands=[f'2 1 {u}\n' for u in range(2,n+1)]+['1 1\n'];put(f'{n} 0 {q}\n'+''.join(commands),2)
        put(f'{n} {n-1} 1\n'+''.join(f'{u} {u+1}\n' for u in range(1,n))+'1 1\n',n-1)
    elif pid=='CF540E':
        for _ in range(300):
            length=rng.randint(2,45);swaps=[tuple(rng.sample(range(1,length+1),2)) for _ in range(rng.randint(1,30))];a=list(range(length+1))
            for u,v in swaps:a[u],a[v]=a[v],a[u]
            inv=sum(a[i]>a[j] for i in range(1,length+1) for j in range(i+1,length+1))
            put(str(len(swaps))+'\n'+''.join(f'{u} {v}\n' for u,v in swaps),inv)
        put('1\n1 1000000000\n',1999999997)
        count=100000;length=10**9;put(str(count)+'\n'+''.join(f'{i} {length-i+1}\n' for i in range(1,count+1)),2*count*length-2*count*count-count)
    elif pid=='P1099':
        for _ in range(280):
            n=rng.randint(2,12);edges=random_tree(rng,n,True);s=rng.randint(0,35);d,path=all_paths(n,edges);diameter=max(map(max,d));candidates=[]
            for a in range(n):
                for b in range(a,n):
                    if d[a][b]!=diameter:continue
                    row=path[a][b]
                    for i in range(len(row)):
                        for j in range(i,len(row)):
                            u,v=row[i],row[j]
                            if d[u][v]<=s:candidates.append(max(min(d[x][z] for z in row[i:j+1]) for x in range(n)))
            put(f'{n} {s}\n'+edge_text(edges,True),min(candidates))
        n=300;s=1000;put(f'{n} {s}\n'+''.join(f'{i} {i+1} 1000\n' for i in range(1,n)),149000)
        put(f'{n} 0\n'+''.join(f'1 {i} 0\n' for i in range(2,n+1)),0)
    elif pid=='P9433':
        for _ in range(230):
            n=rng.randint(1,9);edges=[(u,v,rng.randint(1,9)) for u,v in random_tree(rng,n)];keys=rng.sample(range(n),rng.randint(1,min(n,5)))
            queries=list(combinations(range(n),2))+[(u,u) for u in range(n)];rng.shuffle(queries)
            answers=[key_visit_oracle(n,edges,keys,s,t) for s,t in queries]
            put(f'{n} {len(queries)} {len(keys)}\n'+edge_text(edges,True)+' '.join(str(v+1) for v in keys)+'\n'+''.join(f'{s+1} {t+1}\n' for s,t in queries),'\n'.join(map(str,answers)))
        n=q=100000;queries=[(i+1,(i*7919)%n+1) for i in range(q)];weight=10000
        put(f'{n} {q} {n}\n'+''.join(f'{i} {i+1} {weight}\n' for i in range(1,n))+' '.join(map(str,range(1,n+1)))+'\n'+''.join(f'{s} {t}\n' for s,t in queries),'\n'.join(str((2*(n-1)-abs(s-t))*weight) for s,t in queries))
    elif pid=='CF196C':
        for _ in range(220):
            n=rng.randint(1,14);edges=random_tree(rng,n);xs=rng.sample(range(-100,101),n);points=[(x,x*x) for x in xs];rng.shuffle(points)
            put(str(n)+'\n'+edge_text(edges)+''.join(f'{x} {y}\n' for x,y in points),'valid')
        points=[(-10**9,-10**9),(10**9,-999999999),(999999997,10**9),(-999999995,999999993),(5,7)]
        put('5\n1 2\n2 3\n3 4\n4 5\n'+''.join(f'{x} {y}\n' for x,y in points),'valid')
        n=1500;xs=list(range(-750,750));rng.shuffle(xs)
        put(f'{n}\n'+''.join(f'{u} {u+1}\n' for u in range(1,n))+''.join(f'{x} {x*x}\n' for x in xs),'valid')
        put(f'{n}\n'+''.join(f'1 {u}\n' for u in range(2,n+1))+''.join(f'{x} {x*x}\n' for x in xs),'valid')
    elif pid=='CF538E':
        for _ in range(260):
            n=rng.randint(1,10);undirected=random_tree(rng,n);p=parents(n,undirected,0);child=[[] for _ in range(n)]
            edges=[]
            for u in range(1,n):child[p[u]].append(u);edges.append((p[u],u))
            rng.shuffle(edges);leaves=[u for u in range(n) if not child[u]]
            if len(leaves)>8:continue
            outcomes=[]
            for perm in permutations(range(1,len(leaves)+1)):
                assigned=dict(zip(leaves,perm))
                def minimax(u,turn):
                    if not child[u]:return assigned[u]
                    values=[minimax(v,1-turn) for v in child[u]]
                    return max(values) if turn==0 else min(values)
                outcomes.append(minimax(0,0))
            put(f'{n}\n'+edge_text(edges),f'{max(outcomes)} {min(outcomes)}')
        n=200000;put(f'{n}\n'+''.join(f'{i} {i+1}\n' for i in range(1,n)),'1 1')
        put(f'{n}\n'+''.join(f'1 {i}\n' for i in range(2,n+1)),f'{n-1} {n-1}')
    elif pid=='CF765E':
        from core7_cases_mst import labelled_trees
        for n in range(2,7):
            for edges in labelled_trees(n):put(f'{n}\n'+edge_text(edges),fold_by_operations(n,edges))
        for _ in range(400):
            n=rng.randint(7,12);edges=random_tree(rng,n);put(f'{n}\n'+edge_text(edges),fold_by_operations(n,edges))
        n=200000;put(f'{n}\n'+''.join(f'{i} {i+1}\n' for i in range(1,n)),n-1)
        put(f'{n}\n'+''.join(f'1 {i}\n' for i in range(2,n+1)),1)
        n=131073;put(f'{n}\n'+''.join(f'{i} {i+1}\n' for i in range(1,n)),1)
    elif pid=='CF980E':
        for _ in range(270):
            n=rng.randint(2,12);k=rng.randint(1,n-1);edges=random_tree(rng,n)
            kept=max((set(row) for row in combinations(range(n),n-k) if connected_subset(n,edges,set(row))),key=lambda row:sum(1<<u for u in row))
            put(f'{n} {k}\n'+edge_text(edges),' '.join(str(u+1) for u in range(n) if u not in kept))
        n=1000000;k=333333;put(f'{n} {k}\n'+''.join(f'{i} {i+1}\n' for i in range(1,n)),' '.join(map(str,range(1,k+1))))
        n=200000;k=126379;put(f'{n} {k}\n'+''.join(f'1 {i}\n' for i in range(2,n+1)),' '.join(map(str,range(2,k+2))))
    elif pid=='CF1278E':
        for _ in range(280):
            n=rng.randint(1,40);edges=random_tree(rng,n);put(str(n)+'\n'+edge_text(edges),'valid')
        n=500000;put(f'{n}\n'+''.join(f'{i} {i+1}\n' for i in range(1,n)),'valid')
        put(f'{n}\n'+''.join(f'1 {i}\n' for i in range(2,n+1)),'valid')
    else:raise KeyError(pid)
    return result
