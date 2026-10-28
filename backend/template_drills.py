"""Original template exercises, independent reference oracles and full local cases.

Only exact identities from the packaged definitions opt in. Ordinary platform
problems retain their original browser judge and official-AC boundary.
"""
import bisect,collections,heapq,json,math,random
from functools import lru_cache
from paths import resource

@lru_cache(maxsize=1)
def definitions():
    return {v['id']:v for v in json.loads(resource('template-drills.json').read_text(encoding='utf8'))['problems']}

def is_drill(identity):return identity in definitions()
def _out(values):return ' '.join(map(str,values))+'\n'
def _string(s):return s if s else '-'

def floyd(n,edges):
    inf=10**40;d=[[inf]*n for _ in range(n)]
    for i in range(n):d[i][i]=0
    for u,v,w in edges:d[u][v]=min(d[u][v],w)
    for k in range(n):
        for i in range(n):
            if d[i][k]==inf:continue
            for j in range(n):
                if d[k][j]!=inf:d[i][j]=min(d[i][j],d[i][k]+d[k][j])
    return d,inf

def _graph(key,var,rng,seed):
    n=1 if seed==0 else rng.randint(2,24);m=rng.randint(0,n*3)
    edges=[(rng.randrange(n),rng.randrange(n),rng.randrange(0,20)) for _ in range(m)]
    if key=='zero-one-bfs':edges=[(u,v,w%2) for u,v,w in edges]
    if key=='bellman-ford':edges=[(u,v,w-7) for u,v,w in edges]
    s=rng.randrange(n);lines=[f'{n} {m} {s}']+[f'{u} {v} {w}' for u,v,w in edges]
    d,inf=floyd(n,edges)
    def dist(source,v):
        if key=='bellman-ford' and any(d[source][k]<inf and d[k][k]<0 and d[k][v]<inf for k in range(n)):return '-INF'
        return '-1' if d[source][v]==inf else str(d[source][v])
    if var==1:return '\n'.join(lines)+'\n',_out([dist(s,v) for v in range(n)])
    q=8;targets=[rng.randrange(n) for _ in range(q)]
    lines+=[str(q),_out(targets).strip()]
    if key=='zero-one-bfs':return '\n'.join(lines)+'\n',_out(['-1' if d[v][s]==inf else d[v][s] for v in targets])
    if key=='bellman-ford':
        answers=[]
        for source in targets:
            vals=[dist(source,v) for v in range(n)];neg=vals.count('-INF');unreachable=sum(d[source][v]==inf for v in range(n))
            finite=sum(int(vals[v]) for v in range(n) if d[source][v]<inf and vals[v]!='-INF')
            answers.append(f'{neg} {unreachable} {finite}')
        return '\n'.join(lines)+'\n','\n'.join(answers)+'\n'
    # Any shortest path is accepted by the separate structural checker.
    graph=[[] for _ in range(n)]
    for u,v,w in edges:graph[u].append((v,w))
    distance=[inf]*n;parent=[-1]*n;distance[s]=0;queue=[(0,s)]
    while queue:
        du,u=heapq.heappop(queue)
        if du!=distance[u]:continue
        for v,w in graph[u]:
            if du+w<distance[v]:distance[v]=du+w;parent[v]=u;heapq.heappush(queue,(du+w,v))
    answers=[]
    for v in targets:
        path=[];cur=v
        if distance[v]<inf:
            while cur!=-1:path.append(cur);cur=parent[cur]
            path.reverse()
        answers.append(_out([dist(s,v),len(path),*path]).strip())
    return '\n'.join(lines)+'\n','\n'.join(answers)+'\n'

def generate(key,var,seed):
    rng=random.Random(142300+sum(map(ord,key))*31+var*101+seed)
    if key in ('dijkstra','zero-one-bfs','bellman-ford'):return _graph(key,var,rng,seed)
    if key=='dsu':
        n=5 if seed==0 else rng.randint(1,35);groups=[{i} for i in range(n)];ops=[];answers=[]
        def find(x):return next(group for group in groups if x in group)
        for i in range(60):
            u,v=rng.randrange(n),rng.randrange(n)
            if var==2:
                ops.append(f'{u} {v}');a,b=find(u),find(v);merged=a is not b
                if merged:a.update(b);groups.remove(b)
                answers.append(f'{int(merged)} {len(groups)} {len(find(u))}')
            else:
                t=rng.randrange(4)
                if t==0:
                    ops.append(f'0 {u} {v}');a,b=find(u),find(v)
                    if a is not b:a.update(b);groups.remove(b)
                elif t==1:ops.append(f'1 {u} {v}');answers.append(str(int(find(u) is find(v))))
                elif t==2:ops.append(f'2 {u}');answers.append(str(len(find(u))))
                else:ops.append('3');answers.append(str(len(groups)))
        return f'{n} {len(ops)}\n'+'\n'.join(ops)+'\n','\n'.join(answers)+'\n'
    if key in ('bfs','topological','scc','kruskal'):
        n=1 if seed==0 else rng.randint(2,25);es=[(rng.randrange(n),rng.randrange(n)) for _ in range(rng.randrange(n*3+1))];m=len(es)
        if key=='kruskal':
            es=[(u,v,rng.randint(-20,30)) for u,v in es];g=[[] for _ in range(n)]
            for u,v,w in es:g[u].append((w,v));g[v].append((w,u))
            visited=set();weight=0;count=0
            for s in range(n):
                if s in visited:continue
                count+=1;q=[(0,s)]
                while q:
                    w,u=heapq.heappop(q)
                    if u in visited:continue
                    visited.add(u);weight+=w
                    for cost,v in g[u]:
                        if v not in visited:heapq.heappush(q,(cost,v))
            text=f'{n} {m}\n'+''.join(f'{u} {v} {w}\n' for u,v,w in es)
            if var==1:return text,f'{weight} {count}\n'
            groups=[{i} for i in range(n)];ids=[]
            for idx,(u,v,w) in sorted(enumerate(es),key=lambda e:(e[1][2],e[0])):
                a=next(s for s in groups if u in s);b=next(s for s in groups if v in s)
                if a is not b:a.update(b);groups.remove(b);ids.append(idx)
            return text,_out([weight,count,len(ids),*ids])
        d,inf=floyd(n,[(u,v,1) for u,v in es])
        if key=='scc':
            groups=[];bel=[-1]*n
            for u in range(n):
                if bel[u]>=0:continue
                group=[v for v in range(n) if d[u][v]<inf and d[v][u]<inf]
                for v in group:bel[v]=len(groups)
                groups.append(group)
            text=f'{n} {m}\n'+''.join(f'{u} {v}\n' for u,v in es)
            if var==1:
                qs=[(rng.randrange(n),rng.randrange(n)) for _ in range(20)]
                return text+f'{len(qs)}\n'+''.join(f'{u} {v}\n' for u,v in qs),str(len(groups))+'\n'+''.join(f'{int(bel[u]==bel[v])}\n' for u,v in qs)
            arcs={(bel[u],bel[v]) for u,v in es if bel[u]!=bel[v]}
            return text,str(len(groups))+'\n'+''.join(f'{len(groups[bel[v]])} {sum(b==bel[v] for a,b in arcs)} {sum(a==bel[v] for a,b in arcs)}\n' for v in range(n))
        if key=='topological':
            def order(edges):
                indeg=[0]*n;g=[[] for _ in range(n)]
                for u,v in edges:indeg[v]+=1;g[u].append(v)
                q=collections.deque(u for u in range(n) if not indeg[u]);ans=[]
                while q:
                    u=q.popleft();ans.append(u)
                    for v in g[u]:
                        indeg[v]-=1
                        if not indeg[v]:q.append(v)
                return ans if len(ans)==n else None
            text=f'{n} {m}\n'+''.join(f'{u} {v}\n' for u,v in es)
            if var==1:
                ans=order(es);return text,'-1\n' if ans is None else _out(ans)
            # Repeated deletion is explicitly a no-op; q=0 when m=0.
            deletions=[rng.randrange(m) for _ in range(min(20,m*2))] if m else []
            removed=set();answers=[]
            for idx in deletions:removed.add(idx);answers.append(int(order([e for i,e in enumerate(es) if i not in removed]) is not None))
            return text+f'{len(deletions)}\n'+_out(deletions),_out(answers)
        sources=list(dict.fromkeys([rng.randrange(n) for _ in range(rng.randrange(n+1))]));distance=[min((d[s][v] for s in sources),default=inf) for v in range(n)]
        text=f'{n} {m} {len(sources)}\n'+_out(sources)+''.join(f'{u} {v}\n' for u,v in es)
        if var==1:return text,_out([-1 if x==inf else x for x in distance])
        graph=[[] for _ in range(n)]
        for u,v in es:graph[u].append(v)
        pre=[-1]*n;vis=set(sources);q=collections.deque(sources)
        while q:
            u=q.popleft()
            for v in graph[u]:
                if v not in vis:vis.add(v);pre[v]=u;q.append(v)
        targets=[rng.randrange(n) for _ in range(8)];answers=[]
        for v in targets:
            path=[];u=v
            if v in vis:
                while u!=-1:path.append(u);u=pre[u]
                path.reverse()
            answers.append(_out([-1 if distance[v]==inf else distance[v],len(path),*path]).strip())
        return text+f'{len(targets)}\n'+_out(targets),'\n'.join(answers)+'\n'
    if key=='lca':
        n=1 if seed==0 else rng.randint(2,40);es=[];p=[-1]*n;dep=[0]*n;rt=list(range(n))
        for v in range(1,n):
            if var==2 and rng.randrange(4)==0:continue
            p[v]=rng.randrange(v);dep[v]=dep[p[v]]+1;rt[v]=rt[p[v]];es.append((p[v],v))
        def lca(u,v):
            if rt[u]!=rt[v]:return -1
            while dep[u]>dep[v]:u=p[u]
            while dep[v]>dep[u]:v=p[v]
            while u!=v:u,v=p[u],p[v]
            return u
        ops=[];answers=[]
        for i in range(50):
            u,v=rng.randrange(n),rng.randrange(n);t=rng.randrange(3 if var==2 else 2)
            if t==2:
                k=rng.randrange(n+3);ops.append(f'2 {u} {k}');a=u
                for _ in range(k):a=-1 if a==-1 else p[a]
                answers.append(a)
            else:
                c=lca(u,v);ops.append(f'{t} {u} {v}');answers.append(c if t==0 or c==-1 else dep[u]+dep[v]-2*dep[c])
        return f'{n} {len(es)} {len(ops)}\n'+''.join(f'{u} {v}\n' for u,v in es)+'\n'.join(ops)+'\n',_out(answers)
    if key in ('fenwick','segment-tree'):
        n=1 if seed==0 else rng.randrange(2,40);a=[rng.randrange(12) for _ in range(n)];original=a[:];ops=[];answers=[]
        for i in range(60):
            l=rng.randrange(n+1);r=rng.randrange(l,n+1)
            if key=='fenwick':
                t=rng.randrange(3)
                if t==0:
                    pos=rng.randrange(n);x=rng.randint(-a[pos],10) if var==2 else rng.randint(-10,10);a[pos]+=x;ops.append(f'0 {pos} {x}')
                elif t==1:ops.append(f'1 {l} {r}');answers.append(sum(a[l:r]))
                elif var==1:ops.append(f'2 {r}');answers.append(sum(a[:r]))
                else:
                    k=rng.randint(-1,sum(a)+3);ops.append(f'2 {k}');total=0;idx=n
                    if k>0:
                        for j,v in enumerate(a):
                            total+=v
                            if total>=k:idx=j;break
                    answers.append(idx)
            else:
                t=rng.randrange(3 if var==2 else 2)
                if t==0:
                    x=rng.randint(-10,10);ops.append(f'0 {l} {r} {x}')
                    for j in range(l,r):a[j]+=x
                elif t==1:ops.append(f'1 {l} {r}');answers.append(sum(a[l:r]))
                else:pos=rng.randrange(n);x=rng.randint(-30,30);ops.append(f'2 {pos} {x}');a[pos]=x
        return f'{n} {len(ops)}\n'+_out(original)+'\n'.join(ops)+'\n',_out(answers)
    if key=='sparse-table':
        n=1 if seed==0 else rng.randrange(2,80);a=[rng.randint(-10**9,10**9) for _ in range(n)];qs=[(lambda l:(l,rng.randrange(l+1,n+1)))(rng.randrange(n)) for _ in range(40)]
        return f'{n} {len(qs)}\n'+_out(a)+''.join(f'{l} {r}\n' for l,r in qs),_out([min(a[l:r]) if var==1 else max(a[l:r])-min(a[l:r]) for l,r in qs])
    if key=='compression':
        n=1 if seed==0 else rng.randrange(2,60);a=[rng.choice([-10**12,-3,0,2,5,10**12]) for _ in range(n)];v=sorted(set(a))
        if var==2:return f'{n}\n'+_out(a),str(len(v))+'\n'+_out([v.index(x) for x in a])+_out(v)
        ops=[];ans=[]
        for i in range(40):
            t=i%4
            if t==0:x=rng.randrange(-10,10);ans.append(bisect.bisect_left(v,x))
            elif t==1:x=rng.randrange(-10,10);ans.append(bisect.bisect_right(v,x))
            elif t==2:x=rng.choice(a);ans.append(v.index(x))
            else:x=rng.randrange(len(v));ans.append(v[x])
            ops.append(f'{t} {x}')
        return f'{n} {len(ops)}\n'+_out(a)+'\n'.join(ops)+'\n',_out(ans)
    if key=='prefix-difference':
        n=1 if seed==0 else rng.randrange(2,60);a=[rng.randint(-1000,1000) for _ in range(n)];qs=[(lambda l:(l,rng.randrange(l,n+1)))(rng.randrange(n+1)) for _ in range(30)]
        if var==1:return f'{n} {len(qs)}\n'+_out(a)+''.join(f'{l} {r}\n' for l,r in qs),_out([sum(a[l:r]) for l,r in qs])
        updates=[(l,r,rng.randint(-1000,1000)) for l,r in qs];final=a[:]
        for l,r,x in updates:
            for j in range(l,r):final[j]+=x
        return f'{n} {len(updates)} {len(qs)}\n'+_out(a)+''.join(f'{l} {r} {x}\n' for l,r,x in updates)+''.join(f'{l} {r}\n' for l,r in qs),_out(final)+_out([sum(final[l:r]) for l,r in qs])
    if key=='window-extrema':
        n=1 if seed==0 else rng.randrange(2,100);k=rng.randrange(1,n+1);a=[rng.randint(-30,30) for _ in range(n)];mins=[min(a[i:i+k]) for i in range(n-k+1)];maxs=[max(a[i:i+k]) for i in range(n-k+1)]
        return f'{n} {k}\n'+_out(a),_out(mins)+( _out(maxs) if var==2 else '')
    if key=='binary-search':
        if var==2:
            values=[0,1,2,10**18,*[rng.randrange(10**18+1) for _ in range(36)]]
            return str(len(values))+'\n'+_out(values),_out([math.isqrt(v)+(math.isqrt(v)**2<v) for v in values])
        n=0 if seed==0 else rng.randrange(1,100);a=sorted(rng.randrange(-100,101) for _ in range(n));xs=[rng.randrange(-150,151) for _ in range(40)]
        return f'{n} {len(xs)}\n'+_out(a)+_out(xs),_out([bisect.bisect_left(a,x) for x in xs])
    if key in ('kmp','z-function'):
        s='ababa' if seed==0 else ''.join(rng.choice('abc') for _ in range(rng.randrange(0,120)))
        if key=='kmp' and var==1:
            t='aba' if seed==0 else ''.join(rng.choice('abc') for _ in range(rng.randrange(0,10)));hits=[i for i in range(len(s)+1) if s.startswith(t,i)]
            return f'{_string(s)}\n{_string(t)}\n',str(len(hits))+'\n'+_out(hits)
        if key=='kmp':
            pi=[max((k for k in range(1,i+1) if s[:k]==s[i-k+1:i+1]),default=0) for i in range(len(s))]
            period=next((k for k in range(1,len(s)+1) if len(s)%k==0 and s==s[:k]*(len(s)//k)),0)
            return _string(s)+'\n',_out(pi)+str(period)+'\n'
        z=[]
        for i in range(len(s)):
            k=0
            while i+k<len(s) and s[k]==s[i+k]:k+=1
            z.append(k)
        if var==1:return _string(s)+'\n',_out(z)
        borders=[k for k in range(1,len(s)+1) if s[:k]==s[-k:]]
        return _string(s)+'\n',str(len(borders))+'\n'+_out(borders)
    if key=='trie':
        def word():return ''.join(rng.choice('abc') for _ in range(rng.randrange(0,6)))
        counts=collections.Counter();ops=[];answers=[]
        for i in range(80):
            t=i%4;w=word()
            if t==0:counts[w]+=1;ans=1
            elif t==1:ans=int(counts[w]>0);counts[w]-=ans
            elif t==2:ans=counts[w]
            else:ans=sum(c for s,c in counts.items() if s.startswith(w))
            ops.append(f'{t} {_string(w)}');answers.append(ans)
        if var==1:return str(len(ops))+'\n'+'\n'.join(ops)+'\n',_out(answers)
        words=[word() for _ in range(40)];counts=collections.Counter(words);queries=[word() for _ in range(30)];answers=[]
        for w in queries:
            before=counts[w];removed=int(before>0);counts[w]-=removed;answers.append(f'{before} {counts[w]} {sum(c for s,c in counts.items() if s.startswith(w))}')
        return f'{len(words)} {len(queries)}\n'+'\n'.join(map(_string,words+queries))+'\n','\n'.join(answers)+'\n'
    if key=='mod-combination':
        mod=1000000007;ops=[];ans=[]
        for i in range(50):
            if var==2:
                n=rng.randrange(0,101);k=rng.randrange(-1,n+3);ops.append(f'{n} {k}');ans.append(math.comb(n,k)%mod if 0<=k<=n else 0)
            elif i%2:
                a=rng.choice([0,mod,rng.randint(-2*mod,2*mod)]);ops.append(f'1 {a}');ans.append(-1 if a%mod==0 else pow(a,-1,mod))
            else:a=rng.randint(-2*mod,2*mod);e=rng.randrange(10**12);ops.append(f'0 {a} {e}');ans.append(pow(a,e,mod))
        return (f'100 {len(ops)}\n' if var==2 else f'{len(ops)}\n')+'\n'.join(ops)+'\n',_out(ans)
    if key=='linear-sieve':
        n=100 if seed==0 else rng.randrange(2,600);xs=[1,n,*[rng.randrange(1,n+1) for _ in range(38)]];lines=[];answers=[]
        for i,x in enumerate(xs):
            remain=x;factors=[];p=2
            while p*p<=remain:
                if remain%p==0:
                    e=0
                    while remain%p==0:remain//=p;e+=1
                    factors.append((p,e))
                p+=1
            if remain>1:factors.append((remain,1))
            if var==1:
                t=i%3;lines.append(f'{t} {x}')
                if t==0:answers.append(str(int(x>1 and factors==[(x,1)])))
                elif t==1:answers.append(str(factors[0][0] if factors else 0))
                else:answers.append(_out([len(factors),*[v for pair in factors for v in pair]]).strip())
            else:
                phi=x;divisors=1
                for p,e in factors:phi=phi//p*(p-1);divisors*=e+1
                lines.append(str(x));answers.append(f'{divisors} {phi}')
        return f'{n} {len(xs)}\n'+'\n'.join(lines)+'\n','\n'.join(answers)+'\n'
    if key=='extended-gcd':
        pairs=[(0,0),(0,1),(1,0),(30,18)] if var==1 else [(0,2),(3,10),(2,10),(-3,10)]
        pairs += [(rng.randrange(10**12),rng.randrange(10**12)) for _ in range(30)] if var==1 else [(rng.randrange(-10**12,10**12),rng.randrange(2,10**12)) for _ in range(30)]
        answers=[]
        for a,b in pairs:
            if var==2:answers.append(str(pow(a,-1,b) if math.gcd(a,b)==1 else -1));continue
            r,s=a,b;x,y,xx,yy=1,0,0,1
            while s:q,r,s=r//s,s,r%s;x,xx=xx,x-q*xx;y,yy=yy,y-q*yy
            answers.append(f'{r} {x} {y}')
        return f'{len(pairs)}\n'+''.join(f'{a} {b}\n' for a,b in pairs),'\n'.join(answers)+'\n'
    if key=='knapsack':
        n=1 if seed==0 else rng.randrange(1,6);cap=rng.randrange(0,25);exact=seed%2;items=[(rng.randrange(1,12),rng.randrange(-5,16)) for _ in range(n)];best=[None]*(cap+1)
        def enumerate_items(i,w,v):
            if i==n:best[w]=v if best[w] is None else max(best[w],v);return
            weight,value=items[i]
            for k in range((cap-w)//weight+1 if var==2 else min(1,(cap-w)//weight)+1):enumerate_items(i+1,w+k*weight,v+k*value)
        enumerate_items(0,0,0)
        if not exact:
            for i in range(1,cap+1):best[i]=max(best[i-1],best[i] if best[i] is not None else best[i-1])
        return f'{n} {cap} {exact}\n'+''.join(f'{w} {v}\n' for w,v in items),_out(['X' if v is None else v for v in best])
    if key=='lis':
        n=0 if seed==0 else rng.randrange(1,100);a=[rng.randrange(-12,13) for _ in range(n)]
        def path(strict):
            dp=[1]*n;p=[-1]*n
            for i in range(n):
                for j in range(i):
                    if (a[j]<a[i] if strict else a[j]<=a[i]) and dp[j]+1>dp[i]:dp[i]=dp[j]+1;p[i]=j
            u=max(range(n),key=lambda i:dp[i],default=-1);ans=[]
            while u!=-1:ans.append(u);u=p[u]
            return ans[::-1]
        if var==1:indices=path(True);return f'{n}\n'+_out(a),str(len(indices))+'\n'+_out(indices)
        return f'{n}\n'+_out(a),f'{len(path(True))} {len(path(False))}\n'
    raise ValueError('Unknown template exercise')

def check(identity,input_text,actual,expected):
    item=definitions()[identity];key,var=item['templateKey'],item['variant']
    if (key,var) not in {('extended-gcd',1),('lis',1),('topological',1),('kruskal',2),('dijkstra',2),('bfs',2)}:
        return actual.split()==expected.split()
    try:
        got=list(map(int,actual.split()));tokens=list(map(int,input_text.split()))
        if key=='extended-gcd' and var==1:
            count=tokens[0]
            if len(got)!=3*count:return False
            return all(got[3*i]==math.gcd(tokens[1+2*i],tokens[2+2*i]) and tokens[1+2*i]*got[3*i+1]+tokens[2+2*i]*got[3*i+2]==got[3*i] for i in range(count))
        if key=='lis' and var==1:
            n=tokens[0];a=tokens[1:];length=int(expected.split()[0])
            return bool(got) and got[0]==length and len(got)==length+1 and all(0<=p<n for p in got[1:]) and all(u<v and a[u]<a[v] for u,v in zip(got[1:],got[2:]))
        if key=='topological' and var==1:
            n,m=tokens[:2];es=list(zip(tokens[2::2],tokens[3::2]))
            if expected.strip()=='-1':return got==[-1]
            if len(got)!=n or set(got)!=set(range(n)):return False
            pos={v:i for i,v in enumerate(got)};return all(pos[u]<pos[v] for u,v in es)
        if key=='kruskal' and var==2:
            n,m=tokens[:2];es=[tuple(tokens[2+3*i:5+3*i]) for i in range(m)];summary=list(map(int,expected.split()[:3]))
            if len(got)<3 or got[:3]!=summary or len(got)!=3+summary[2] or len(set(got[3:]))!=summary[2]:return False
            groups=[{i} for i in range(n)];total=0
            for idx in got[3:]:
                if not 0<=idx<m:return False
                u,v,w=es[idx];a=next(s for s in groups if u in s);b=next(s for s in groups if v in s)
                if a is b:return False
                a.update(b);groups.remove(b);total+=w
            return total==summary[0] and len(groups)==summary[1]
        if key in ('dijkstra','bfs') and var==2:
            n,m,s=tokens[:3];offset=3;edges={}
            if key=='bfs':sources=set(tokens[offset:offset+s]);offset+=s
            else:sources={s}
            for i in range(m):
                if key=='bfs':u,v=tokens[offset:offset+2];w=1;offset+=2
                else:u,v,w=tokens[offset:offset+3];offset+=3
                edges[u,v]=min(edges.get((u,v),10**40),w)
            q=tokens[offset];targets=tokens[offset+1:];expected_lines=expected.splitlines();position=0
            if len(targets)!=q:return False
            for i,t in enumerate(targets):
                if position+2>len(got):return False
                distance,k=got[position:position+2];position+=2
                if k<0 or k>n or distance!=int(expected_lines[i].split()[0]):return False
                path=got[position:position+k];position+=k
                if len(path)!=k or len(set(path))!=k:return False
                if distance==-1:
                    if k:return False
                    continue
                if not path or path[0] not in sources or path[-1]!=t or any((u,v) not in edges for u,v in zip(path,path[1:])):return False
                if sum(edges[u,v] for u,v in zip(path,path[1:]))!=distance:return False
            return position==len(got)
    except (ValueError,IndexError,KeyError,StopIteration,TypeError):return False
    return actual.split()==expected.split()

@lru_cache(maxsize=8)
def bundle(identity):
    item=definitions()[identity];cases=[]
    for seed in range(24):
        text,expected=generate(item['templateKey'],item['variant'],seed)
        cases.append({'name':f'测试 {seed+1}','input':text,'output':expected})
    return {'scope':'template','cases':cases,'limits':{'timeMs':2000,'memoryMb':256},'checker':lambda text,actual,expected:check(identity,text,actual,expected),'nonunique':False,'caseInsensitive':False}
