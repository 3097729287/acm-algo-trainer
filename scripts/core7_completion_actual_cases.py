"""Exhaustive and direct small-instance oracles, independent of reference code."""
from collections import Counter,deque
from itertools import product,permutations,combinations,combinations_with_replacement
from math import factorial,gcd,lcm,comb
import heapq,random

def attach(entries):
    rng=random.Random(31415926)
    def case(pid,inp,expected):
        if pid in entries:entries[pid].cases.append((inp,str(expected)+'\n'))
    def batch(pid,rows,size=20):
        for i in range(0,len(rows),size):
            part=rows[i:i+size];case(pid,str(len(part))+'\n'+'\n'.join(r[0] for r in part),'\n'.join(str(r[1]) for r in part))
    def tree(n):return [(v,rng.randrange(v)) for v in range(1,n)]
    def graph(n,edges):
        g=[[] for _ in range(n)]
        for a,b in edges:g[a].append(b);g[b].append(a)
        return g
    def all_distances(g):
        out=[]
        for start in range(len(g)):
            d=[-1]*len(g);d[start]=0;q=[start]
            for v in q:
                for u in g[v]:
                    if d[u]<0:d[u]=d[v]+1;q.append(u)
            out.append(d)
        return out

    for n in range(21):case('P1754',str(n),comb(2*n,n)//(n+1))

    original_rng_state=rng.getstate()
    rows=[]
    for _ in range(12):
        n=rng.choice([1,2]);X=rng.randrange(1,4);rectangles=[];targets=[]
        for i in range(n):
            lo=rng.randrange(1,7);hi=rng.randrange(lo+1,10);right=rng.randrange(X+1,8)
            rectangles.append((lo,hi,right));targets.extend([(X,lo,0),(X,hi,0),(right,lo,1),(right,hi,-1)])
        slopes=[rng.choice([-4,-3,-2,-1,1,2,3,4]) for _ in range(4*n)];best=None
        for order in permutations(slopes):
            if any(required and slope*required<0 for (_,_,required),slope in zip(targets,order)):continue
            intercepts=[y-slope*x for (x,y,_),slope in zip(targets,order)];value=max(intercepts)-min(intercepts)
            best=value if best is None else min(best,value)
        inp=f'{n} {X}\n'+'\n'.join(f'{a} {b} {x}' for a,b,x in rectangles)+'\n'+' '.join(map(str,slopes));rows.append((inp,best if best is not None else -1))
    batch('P10190',rows,10)
    rng.setstate(original_rng_state)

    for length in range(1,8):
        for chars in product('ab',repeat=length):
            s=''.join(chars);best=0
            for i in range(length):
                for c in 'abc':
                    changed=s[:i]+c+s[i+1:]
                    best=max(best,max((k for k in range(1,length) if changed[:k]==changed[-k:]),default=0))
            case('P13790',s,best)

    rows=[]
    for _ in range(400):
        n=rng.randrange(2,8);C=rng.randrange(1,4);q=rng.randrange(1,n)
        known=[rng.randrange(C+1) for _ in range(n)]
        constraints=[(a,rng.randrange(a+1,n+1)) for a in rng.sample(range(1,n),q)]
        unknown=[i for i,x in enumerate(known) if not x];answer=None
        for fill in product(range(1,C+1),repeat=len(unknown)):
            a=known[:]
            for i,x in zip(unknown,fill):a[i]=x
            if all(max(a[:l])==max(a[:h-1])<a[h-1] for l,h in constraints):answer=a;break
        inp=f'{n} {q} {C}\n'+' '.join(map(str,known))+'\n'+'\n'.join(f'{a} {b}' for a,b in constraints)
        rows.append((inp,' '.join(map(str,answer)) if answer else '-1'))
    batch('P10134',rows)

    for _ in range(120):
        n=rng.randrange(2,45);parents=[rng.randrange(v) for v in range(1,n)];degree=[0]*n;best=[]
        for v,p in enumerate(parents,1):
            degree[v]+=1;degree[p]+=1
            best.append(max(degree[a]+degree[b]-1-int((b>0 and parents[b-1]==a) or (a>0 and parents[a-1]==b)) for a in range(v+1) for b in range(a)))
        case('P16943',str(n)+'\n'+' '.join(str(p+1) for p in parents),' '.join(map(str,best)))

    for n in range(1,5):
        def inversions(bits):return sum(bits[i] and not bits[j] for i in range(n) for j in range(i+1,n))
        distance={};q=deque()
        for bits in product((0,1),repeat=2*n):
            if inversions(bits[:n])==inversions(bits[n:]):distance[bits]=0;q.append(bits)
        while q:
            bits=q.popleft()
            for i in range(2*n-1):
                if bits[i]==bits[i+1]:continue
                next_=list(bits);next_[i],next_[i+1]=next_[i+1],next_[i];next_=tuple(next_)
                if next_ not in distance:distance[next_]=distance[bits]+1;q.append(next_)
        for bits in product((0,1),repeat=2*n):case('P5426',str(n)+'\n'+' '.join(map(str,bits)),distance[bits])

    for _ in range(24):
        n=rng.randrange(2,8);m=rng.randrange(1,5);a=[rng.randrange(1,m+1) for _ in range(n)];edges=tree(n);g=graph(n,edges);best=0
        for w in product(range(1,m+1),repeat=n-1):
            incident=[[] for _ in range(n)]
            for (u,v),weight in zip(edges,w):incident[u].append(weight);incident[v].append(weight)
            if all(sorted(incident[v])[len(incident[v])//2]<=a[v] for v in range(n)):best=max(best,sum(w))
        case('P6748',f'{n} {m}\n'+' '.join(map(str,a))+'\n'+'\n'.join(f'{a+1} {b+1}' for a,b in edges),best)

    case('P7480','2 0 100\n100 0\n1 -1',201)
    for _ in range(35):
        n=rng.randrange(1,10);positions=[0]+rng.sample([x for x in range(-12,13) if x],n-1);prices=[rng.randrange(1,21) for _ in range(n)];target=rng.randrange(1,16)
        x=positions+[target];c=prices+[0];d=[10**30]*(n+1);d[0]=0;heap=[(0,0)]
        while heap:
            value,v=heapq.heappop(heap)
            if d[v]!=value:continue
            for u in range(n+1):
                candidate=value+c[v]*abs(x[v]-x[u])
                if candidate<d[u]:d[u]=candidate;heapq.heappush(heap,(candidate,u))
        case('P7480',f'{n} 0 {target}\n'+'\n'.join(f'{p} {x}' for p,x in zip(prices,positions)),d[-1])

    rows=[]
    for n in range(1,7):
        for k in range(1,9):
            answer=sum(n==1 or values[-1]+values[-2]<=k+1 for values in combinations_with_replacement(range(1,k+1),n))
            rows.append((f'{n} {k}',answer))
    batch('P9035',rows)

    rows=[]
    for n in range(2,10):
        for _ in range(4):
            k=rng.randrange(2,12);a,b=rng.randrange(1,10),rng.randrange(1,10);best=10**20;word=''
            for chars in product('ab',repeat=n):
                s=''.join(chars);value=a*sum(s[i]==s[i+1] for i in range(n-1))+b*sum(all(s[i+j]!=s[i+j+1] for j in range(k-1)) for i in range(max(0,n-k+1)))
                if value<best:best=value;word=s
            rows.append((f'{n} {k} {a} {b}',str(best)+'\n'+word))
    batch('P9087',rows)

    rows=[]
    for n in range(1,6):
        for chars in product('ab',repeat=n):
            for k in range(1,6):
                s=''.join(chars);t=s*k;answer=sum(t[l:r]==t[l:r][::-1] for l in range(len(t)) for r in range(l+1,len(t)+1))
                rows.append((f'{n} {k}\n{s}',answer))
    batch('P11749',rows,10000)

    rows=[]
    for n in range(2,9):
        for _ in range(4):
            m=rng.randrange(2,5);strings=[]
            for i in range(n):
                s='a'*m
                while len(set(s))<2:s=''.join(rng.choice('ab') for _ in range(m))
                strings.append(s)
            if n>6:continue
            k=rng.randrange(2,n*m+1);answer=0
            for order in permutations(range(n)):
                s=''.join(strings[i] for i in order);answer+=sum(len(set(s[l:l+k]))==1 for l in range(len(s)-k+1))
            case('P7942',f'{n} {m} {k}\n'+'\n'.join(strings),answer%998244353)

    for _ in range(18):
        n=rng.randrange(2,7);a=rng.sample(range(1,n+1),n);totals=[0]*n
        for order in permutations(range(n-1)):
            parent=list(range(n));winner=list(range(n));survive=[n-1]*n
            def find(v):
                while parent[v]!=v:v=parent[v]
                return v
            for step,boundary in enumerate(order,1):
                x,y=find(boundary),find(boundary+1);u,v=winner[x],winner[y]
                if a[u]<a[v]:u,v=v,u
                survive[v]=step-1;parent[y]=x;winner[x]=u
            for i,value in enumerate(survive):totals[i]+=value
        inverse=pow(factorial(n-1),-1,998244353)
        case('P6046',str(n)+'\n'+' '.join(map(str,a)),' '.join(str(x*inverse%998244353) for x in totals))

    for n in range(2,8):
        counts=[[0]*n for _ in range(n+2)]
        for p in permutations(range(1,n+1)):
            for m in range(3,n+2):counts[m][sum(p[i]+p[i+1]>=m for i in range(n-1))]+=1
        for x in [1,2,1234567]:
            answer=sum(counts[m][k]*pow(x,m*n+k,1000000007) for m in range(3,n+2) for k in range(n))%1000000007
            case('CF1909I',f'{n} {x}',answer)

    rows=[];reachable={1}
    for k in range(13):
        for n in range(min(2**k+3,5000)):rows.append((f'{k} {n}','Yes' if n in reachable else 'No'))
        reachable={y for x in reachable for y in (x-1,2*x)}
    batch('P10026',rows,100000)

    for _ in range(24):
        n=rng.randrange(5,10);points=[]
        def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
        while len(points)<n:
            p=(rng.randrange(1,101),rng.randrange(1,101))
            if p not in points and all(cross(a,b,p) for a,b in combinations(points,2)):points.append(p)
        def hull(values):
            values=sorted(values);half=[]
            for p in values:
                while len(half)>=2 and cross(half[-2],half[-1],p)<=0:half.pop()
                half.append(p)
            other=[]
            for p in reversed(values):
                while len(other)>=2 and cross(other[-2],other[-1],p)<=0:other.pop()
                other.append(p)
            return len(half)+len(other)-2
        answer=3
        for size in range(n,2,-1):
            if any(hull(group)==size for group in combinations(points,size)):answer=size;break
        case('P2924',str(n)+'\n'+'\n'.join(f'{x} {y}' for x,y in points),answer)

    for _ in range(20):
        h,w=rng.randrange(2,5),rng.randrange(2,5);N=h*w;start,goal=rng.sample(range(N),2);a=[rng.choices([0,1,2],[4,3,2])[0] for _ in range(N)];a[start]=3;a[goal]=4;water=[i for i,x in enumerate(a) if x==0]
        def connected(added):
            allowed={i for i,x in enumerate(a) if x in (1,3,4)}|set(added);seen={start};q=[start]
            for v in q:
                for dx,dy in [(1,2),(1,-2),(-1,2),(-1,-2),(2,1),(2,-1),(-2,1),(-2,-1)]:
                    x,y=v//w+dx,v%w+dy;u=x*w+y
                    if 0<=x<h and 0<=y<w and u in allowed and u not in seen:seen.add(u);q.append(u)
            return goal in seen
        answer='-1'
        for size in range(len(water)+1):
            count=sum(connected(group) for group in combinations(water,size))
            if count:answer=f'{size}\n{count}';break
        case('P1606',f'{h} {w}\n'+'\n'.join(' '.join(map(str,a[i*w:(i+1)*w])) for i in range(h)),answer)

    for _ in range(20):
        n=rng.randrange(2,25);edges=tree(n);g=graph(n,edges);parent=[-1]*n;depth=[0]*n;parent[0]=0;order=[0]
        for v in order:
            for u in g[v]:
                if parent[u]<0:parent[u]=v;depth[u]=depth[v]+1;order.append(u)
        distance=all_distances(g);versions=[[0]*n];ops=[];answers=[]
        for event in range(1,51):
            type_=rng.choice([1,1,2,2,3]);state=versions[-1][:]
            if type_==1:
                v=rng.randrange(n);state[v]^=1;ops.append(f'1 {v+1}')
            elif type_==2:
                v=rng.randrange(n);y=rng.randrange(0,2*n);answers.append(sum(state[u] for u in range(n) if depth[u]==depth[v] and distance[u][v]==y));ops.append(f'2 {v+1} {y}')
            else:
                version=rng.randrange(event);state=versions[version][:];ops.append(f'3 {version}')
            versions.append(state)
        case('P7394',str(n)+'\n'+'\n'.join(f'{a+1} {b+1}' for a,b in edges)+'\n'+str(len(ops))+'\n'+'\n'.join(ops),'\n'.join(map(str,answers)))

    for _ in range(20):
        n=rng.randrange(2,30);edges=tree(n);parent=[0]*n
        for v,p in edges:parent[v]=p
        original=[rng.randrange(1,200) for _ in range(n)];a=original[:];ops=[];answer=[]
        updates=0
        for i in range(40):
            v=rng.randrange(n)
            if updates<8 and rng.random()<.2:
                x=rng.choice([1,2147483647,99991,rng.randrange(1,500)]);a[v]=x;ops.append(f'2 {v+1} {x}');updates+=1
            else:
                u=parent[v] if v else -1
                while u>=0 and gcd(a[v],a[u])==1:u=parent[u] if u else -1
                answer.append(u+1 if u>=0 else -1);ops.append(f'1 {v+1}')
        case('P2441',f'{n} {len(ops)}\n'+' '.join(map(str,original))+'\n'+'\n'.join(f'{p+1} {v+1}' for v,p in edges)+'\n'+'\n'.join(ops),'\n'.join(map(str,answer)))

    for _ in range(20):
        n=rng.randrange(1,22);s=[''.join(rng.choice('...X') for _ in range(n)) for _ in range(2)];free=[i for i in range(2*n) if s[i//n][i%n]=='.']
        if not free:continue
        queries=[(rng.choice(free),rng.choice(free)) for _ in range(20)];answers=[]
        for start,goal in queries:
            d={start:0};q=[start]
            for v in q:
                r,c=v//n,v%n
                for nr,nc in [(r^1,c),(r,c-1),(r,c+1)]:
                    u=nr*n+nc
                    if 0<=nc<n and s[nr][nc]=='.' and u not in d:d[u]=d[v]+1;q.append(u)
            answers.append(d.get(goal,-1))
        case('CF413E',f'{n} {len(queries)}\n'+'\n'.join(s)+'\n'+'\n'.join(f'{a+1} {b+1}' for a,b in queries),'\n'.join(map(str,answers)))

    for _ in range(20):
        S=set();ops=[]
        for i in range(40):
            a,b=sorted([rng.randrange(0,7),rng.randrange(0,7)]);left=rng.choice('[(');right=rng.choice('])');L=2*a+(left=='(');R=2*b-(right==')');T=set(range(L,R+1));op=rng.choice('UIDCS');ops.append(f'{op} {left}{a},{b}{right}')
            S= S|T if op=='U' else S&T if op=='I' else S-T if op=='D' else T-S if op=='C' else S^T
        result=[]
        while S:
            l=min(S);r=l
            while r+1 in S:r+=1
            result.append(('(' if l%2 else '[')+str(l//2)+','+str((r+1)//2)+(')' if r%2 else ']'));S-=set(range(l,r+1))
        case('P5568','\n'.join(ops),' '.join(result) if result else 'empty set')

    for _ in range(20):
        n=rng.randrange(1,16);a=[rng.randrange(1,200001) for _ in range(n)];queries=[];answers=[]
        for i in range(20):
            l=rng.randrange(n);r=rng.randrange(l,n);x=rng.randrange(1,200001);answer=1
            for v in a[l:r+1]:answer=answer*lcm(v,x)%1000000007
            queries.append(f'{l+1} {r+1} {x}');answers.append(answer)
        case('P6217',f'{n} {len(queries)}\n'+' '.join(map(str,a))+'\n'+'\n'.join(queries),'\n'.join(map(str,answers)))

    for _ in range(20):
        n=rng.randrange(2,15);active=[1]*n;edges=[];present=set();ops=[];answer=[0]*n
        for event in range(1,31):
            candidates=['D'] if any(active) else []
            if sum(active)>=2:candidates+=['A']*2
            if present:candidates+=['R']
            if not candidates:break
            op=rng.choice(candidates)
            if op=='D':
                v=rng.choice([i for i,x in enumerate(active) if x]);active[v]=0;ops.append(f'D {v+1}')
            elif op=='A':
                a,b=rng.sample([i for i,x in enumerate(active) if x],2);edges.append((a,b));present.add(len(edges)-1);ops.append(f'A {a+1} {b+1}')
            else:
                e=rng.choice(sorted(present));present.remove(e);ops.append(f'R {e+1}')
            g=graph(n,[edges[e] for e in present]);seen={i for i,x in enumerate(active) if x};q=list(seen)
            for v in q:
                for u in g[v]:
                    if u not in seen:seen.add(u);q.append(u)
            for v in seen:answer[v]=event
        case('P8097',f'{n} {len(ops)}\n'+'\n'.join(ops),'\n'.join(map(str,answer)))

    for n in range(1,7):
        ps=list(permutations(range(1,n+1)));answer=0
        for y in ps:
            for z in ps:
                w=[i-y[i-1]+z[i-1] for i in range(1,n+1)]
                answer+=sorted(w)==list(range(1,n+1))
        case('P16940',str(n),answer*factorial(n))

    for _ in range(20):
        n=rng.randrange(1,11);s=''.join(rng.choice('abc') for _ in range(n));t=''.join(rng.choice('abc') for _ in range(n));subseq={''.join(s[i] for i in range(n) if mask>>i&1) for mask in range(1,1<<n)};substrings={t[l:r] for l in range(n) for r in range(l+1,n+1)}
        case('P7469',f'{n}\n{s}\n{t}',len(subseq&substrings))

    for _ in range(20):
        words=[''.join(rng.choice('aA0') for _ in range(rng.randrange(1,8))) for i in range(rng.randrange(1,20))];ans=0
        for a,b in combinations(words,2):
            i=0
            while i<len(a) and i<len(b) and a[i]==b[i]:ans+=2;i+=1
            ans+=2 if a==b else 1
        case('UVA11732',str(len(words))+'\n'+'\n'.join(words)+'\n0','Case 1: '+str(ans))
