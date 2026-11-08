"""Deterministic small-domain oracles; these do not reuse production algorithms."""
from functools import lru_cache
from itertools import product,combinations,permutations
from math import gcd
import random


def attach(entries):
    rng=random.Random(20261108)
    def case(pid,inp,out):
        if pid in entries:entries[pid].cases.append((inp,str(out)+'\n'))

    for _ in range(24):
        n=rng.randrange(1,9);a=[rng.randrange(-3,4) for _ in range(n)]
        answer=n*n
        for signs in product((-1,1),repeat=n):
            b=[abs(x)*s for x,s in zip(a,signs)];count=0
            for l in range(n):
                for r in range(l+1,n):
                    count+=b[l]==b[r] and all(abs(x)<=abs(b[l]) for x in b[l:r+1])
            answer=min(answer,count)
        case('P10798',f'{n}\n'+ ' '.join(map(str,a)),answer)

    samples=[]
    for length in range(1,9):
        for chars in product('ab',repeat=length):
            s=''.join(chars);answer=1
            for end in range(1,length+1):
                count=sum(s[:b]==s[end-b:end] for b in range(1,end//2+1))
                answer=answer*(count+1)%1000000007
            samples.append((s,answer))
    case('P2375',str(len(samples))+'\n'+'\n'.join(s for s,_ in samples),
         '\n'.join(str(a) for _,a in samples))

    for _ in range(30):
        n=rng.randrange(2,13);s=''.join(rng.choice('AB') for _ in range(n));states=set()
        for pos in range(n):
            order=s[1:pos+1]+s[0]+s[pos+1:];balance=0;result=''
            for c in order:
                balance+=1 if c=='A' else -1;result+='A' if balance>0 else 'B' if balance<0 else 'C'
            states.add(result)
        case('AT_arc172_c',str(n)+'\n'+s,len(states))

    f=[0]
    for n in range(1,101):
        total=0
        for target in range(1,n+1):
            l,r,count=1,n,0
            while True:
                mid=(l+r)//2;count+=1
                if mid==target:break
                if mid<target:l=mid+1
                else:r=mid-1
            total+=count
        f.append(total)
    ranges=[(rng.randint(1,100),rng.randint(1,100)) for _ in range(60)]
    ranges=[tuple(sorted(v)) for v in ranges]
    case('P13831',str(len(ranges))+'\n'+'\n'.join(f'{a} {b}' for a,b in ranges),
         '\n'.join(str(sum(f[a:b+1])) for a,b in ranges))

    for _ in range(18):
        n=rng.randrange(1,8);a=[rng.randrange(1,5) for _ in range(n)]
        @lru_cache(None)
        def solve(alive,used):
            answer=alive.bit_count()
            for i in range(n):
                if alive>>i&1 and not used>>i&1:
                    for j in range(n):
                        if alive>>j&1 and a[i]>a[j]:
                            answer=min(answer,solve(alive^(1<<j),used|(1<<i)))
            return answer
        case('P11231',str(n)+'\n'+' '.join(map(str,a)),solve((1<<n)-1,0))

    for _ in range(18):
        n=rng.randrange(1,12);q=25;a=[0]*n;commands=[];answers=[]
        for j in range(q):
            l,r=sorted([rng.randrange(n),rng.randrange(n)]);op=rng.randrange(2)
            commands.append(f'{op} {l+1} {r+1}')
            if op==0:
                for i in range(l,r+1):a[i]^=1
            else:answers.append(sum(a[l:r+1]))
        case('P2846',f'{n} {q}\n'+'\n'.join(commands),'\n'.join(map(str,answers)))

    for _ in range(18):
        n=rng.randrange(1,12);q=25;a=[0]*n;commands=[];answers=[]
        for j in range(q):
            p=rng.randrange(n);commands.append(p+1);a[p]^=1
            best=run=1
            for i in range(1,n):
                run=run+1 if a[i]!=a[i-1] else 1;best=max(best,run)
            answers.append(best)
        case('P6492',f'{n} {q}\n'+'\n'.join(map(str,commands)),'\n'.join(map(str,answers)))

    for _ in range(18):
        n=rng.randrange(1,12);q=25;s=[rng.choice('IO') for _ in range(n)];initial=''.join(s);commands=[];answers=[]
        for j in range(q):
            if rng.randrange(2):
                p=rng.randrange(n);c=rng.choice('IO');commands.append(f'1 {p+1} {c}');s[p]=c
            else:
                l,r=sorted([rng.randrange(n),rng.randrange(n)]);commands.append(f'2 {l+1} {r+1}')
                answers.append(sum(s[a]+s[b]+s[c]=='IOI' for a,b,c in combinations(range(l,r+1),3)))
        case('P6373',f'{n} {q}\n{initial}\n'+'\n'.join(commands),'\n'.join(map(str,answers)))

    for _ in range(24):
        n=rng.randrange(1,12);k=rng.randrange(-3,4);a=[rng.randrange(-3,4) for _ in range(n)];queries=[];answers=[]
        for j in range(20):
            l,r=sorted([rng.randrange(n),rng.randrange(n)]);queries.append(f'{l+1} {r+1}')
            answers.append(sum(sum(a[x:y+1])==k for x in range(l,r+1) for y in range(x,r+1)))
        inp=f'{n} {k}\n'+' '.join('1' if x>=0 else '2' for x in a)+'\n'+' '.join(str(abs(x)) for x in a)+f'\n{len(queries)}\n'+'\n'.join(queries)
        case('CF877F',inp,'\n'.join(map(str,answers)))

    for _ in range(18):
        n=rng.randrange(1,10);m=rng.randrange(1,5);a=[rng.randrange(1,8) for _ in range(n)]
        answer=sum(sum(a[l:r+1])>m*(r-l+1) for l in range(n) for r in range(l,n))
        case('P2804',f'{n} {m}\n'+' '.join(map(str,a)),answer)

    for _ in range(18):
        n=rng.randrange(1,9);a=[rng.randrange(0,25) for _ in range(n)];parent=[rng.randrange(v) for v in range(1,n)];edges=[(p,v) for v,p in enumerate(parent,1)];g=[[] for _ in range(n)]
        for u,v in edges:g[u].append(v);g[v].append(u)
        distances=[];concatenation=0
        for start in range(n):
            d=[None]*n;strings=[None]*n;d[start]=0;strings[start]=str(a[start]);queue=[start]
            for v in queue:
                for u in g[v]:
                    if d[u] is None:d[u]=d[v]+(a[u]^a[v]);strings[u]=strings[v]+str(a[u]);queue.append(u)
            distances.append(d);concatenation+=sum(int(s) for s in strings)
        edge_text='\n'.join(f'{u+1} {v+1}' for u,v in edges)
        case('CF1882D',f'1\n{n}\n'+' '.join(map(str,a))+'\n'+edge_text,
             ' '.join(str(sum(d)) for d in distances))
        case('P9437',str(n)+'\n'+' '.join(map(str,a))+'\n'+' '.join(str(p+1) for p in parent),concatenation%998244353)

    for _ in range(14):
        n=rng.randrange(2,9);k=rng.randrange(n+1);edges=[(rng.randrange(v),v,rng.randrange(1,8)) for v in range(1,n)];g=[[] for _ in range(n)]
        for u,v,w in edges:g[u].append((v,w));g[v].append((u,w))
        distances=[]
        for start in range(n):
            d=[None]*n;d[start]=0;queue=[start]
            for v in queue:
                for u,w in g[v]:
                    if d[u] is None:d[u]=d[v]+w;queue.append(u)
            distances.append(d)
        answer=0
        for black in combinations(range(n),k):
            black=set(black);score=sum(distances[u][v] for u in range(n) for v in range(u+1,n) if (u in black)==(v in black));answer=max(answer,score)
        case('P3177',f'{n} {k}\n'+'\n'.join(f'{u+1} {v+1} {w}' for u,v,w in edges),answer)

    for n in range(1,51):
        case('P10031',f'1\n{n}',__import__('functools').reduce(int.__xor__,(gcd(i,n) for i in range(1,n+1)),0))
    for _ in range(12):
        n=rng.randrange(1,8);a=[rng.randrange(1,15) for _ in range(n)];best=0
        for p in permutations(a):
            g=0;total=0
            for x in p:g=gcd(g,x);total+=g
            best=max(best,total)
        case('CF1614D1',str(n)+'\n'+' '.join(map(str,a)),best)
