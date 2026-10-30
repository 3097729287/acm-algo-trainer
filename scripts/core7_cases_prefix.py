"""Literal operation, subset, rectangle, partition and finite-game oracles."""
from collections import deque
from functools import lru_cache
import bisect
import itertools
import math
import random

IDS=set('P8649 B3799 P1496 P3131 P7714 P9749 P14028 UVA11059 P1719 P2879 P3948 P5542 P9533 P10719 P12674 P13787 P14520 UVA1210'.split())

@lru_cache(None)
def sorting_cost(a):
    if tuple(sorted(a))==a:return 0
    best=len(a)
    for l in range(len(a)):
        for r in range(l+2,len(a)+1):
            nxt=a[:l]+tuple(sorted(a[l:r]))+a[r:]
            if nxt!=a:best=min(best,r-l+sorting_cost(nxt))
    return best

@lru_cache(None)
def reachable_xor_max(a):
    def count(state):
        result=0
        for l in range(len(state)):
            x=0
            for r in range(l,len(state)):x^=state[r];result+=x==0
        return result
    seen={a};queue=deque([a]);answer=0
    while queue:
        state=queue.popleft();answer=max(answer,count(state))
        for l in range(len(state)):
            x=0
            for r in range(l,len(state)):
                x^=state[r]
                if x==0:
                    nxt=state[:l]+state[l:r+1][::-1]+state[r+1:]
                    if nxt not in seen:seen.add(nxt);queue.append(nxt)
    return answer

def cases_for(pid):
    assert pid in IDS,pid
    rng=random.Random(20261102);values=[]
    def put(inp,answer):values.append((f'独立校验 {len(values)+1}',str(inp),str(answer)))
    def array(a):return str(len(a))+'\n'+' '.join(map(str,a))+'\n'
    if pid=='P8649':
        for _ in range(250):
            n,k=rng.randint(1,45),rng.randint(1,25);a=[rng.randint(1,100000) for _ in range(n)]
            put(f'{n} {k}\n'+' '.join(map(str,a)),sum(sum(a[l:r])%k==0 for l in range(n) for r in range(l+1,n+1)))
        n=100000;put(f'{n} 1\n'+'1 '*n,n*(n+1)//2);put(f'{n} {n}\n'+'1 '*n,1)
    elif pid=='B3799':
        for _ in range(180):
            n,m=rng.randint(1,10),rng.randint(1,40);a=[rng.randint(-30,30) for _ in range(n)];state=a[:];operations=[];answers=[]
            for turn in range(m):
                if rng.randrange(3)==0 or turn==m-1:
                    operations.append('2');answers.append(max(sum(state[i] for i in range(n) if mask>>i&1) for mask in range(1<<n)))
                else:
                    delta=rng.randint(-20,20);operations.append(f'1 {delta}');state=[x+delta for x in state]
            put(f'{n} {m}\n'+' '.join(map(str,a))+'\n'+'\n'.join(operations),'\n'.join(map(str,answers)))
        n,m=500000,500000
        put(f'{n} {m}\n'+'500000 '*n+'\n'+('1 500000\n'*(m-1))+'2',n*(500000+(m-1)*500000))
    elif pid=='P1496':
        for _ in range(200):
            segments=[sorted(rng.sample(range(-25,26),2)) for _ in range(rng.randint(1,16))];burning=set()
            for l,r in segments:burning.update(range(l,r))
            put(str(len(segments))+'\n'+'\n'.join(f'{l} {r}' for l,r in segments),len(burning))
        put('2\n-2147483648 -2147483640\n2147483640 2147483647',15)
        put('3\n0 1\n1 2\n2 3',3);put('3\n0 10\n2 3\n0 10',10)
    elif pid=='P3131':
        for _ in range(250):
            n=rng.randint(1,65);a=rng.sample(range(1000001),n)
            answer=max([0]+[r-l for l in range(n) for r in range(l+1,n+1) if sum(a[l:r])%7==0]);put(array(a),answer)
        n=50000;put(array([7*i for i in range(n)]),n);put('1\n1',0);put('1\n0',1)
    elif pid=='P7714':
        for n in range(1,7):
            for a in itertools.permutations(range(1,n+1)):put('1\n'+array(a),sorting_cost(a))
        n=1000000;put('1\n'+array(list(range(n,0,-1))),n);put('1\n'+array(list(range(1,n+1))),0)
    elif pid=='P9749':
        for _ in range(180):
            n,d=rng.randint(1,6),rng.randint(1,6);road=[rng.randint(1,9) for _ in range(n-1)];price=[rng.randint(1,15) for _ in range(n)]
            limit=(sum(road)+d-1)//d;dp={0:0}
            for distance,cost in zip(road,price):
                following={}
                for fuel,money in dp.items():
                    for purchase in range(limit+1):
                        left=fuel+purchase*d-distance
                        if 0<=left<=limit*d:following[left]=min(following.get(left,10**30),money+purchase*cost)
                dp=following
            put(f'{n} {d}\n'+' '.join(map(str,road))+'\n'+' '.join(map(str,price)),min(dp.values()))
        n=100000;put(f'{n} 1\n'+'100000 '*(n-1)+'\n'+'100000 '*n,(n-1)*100000*100000)
        put('3 4\n10 10\n9 8 1',43)
    elif pid=='P14028':
        for _ in range(130):
            n,m=rng.randint(1,3),rng.randint(1,3);a=tuple(rng.randint(1,8) for _ in range(n));ranges=[sorted(rng.choices(range(n),k=2)) for _ in range(m)]
            reachable={a}
            for l,r in ranges:
                following=set()
                for state in reachable:
                    for changes in itertools.product([-1,0,1],repeat=r-l+1):
                        nxt=list(state)
                        for i,change in enumerate(changes,l):nxt[i]+=change
                        following.add(tuple(nxt))
                reachable=following
            answer=min(max(state)-min(state) for state in reachable)
            put(f'1\n{n} {m}\n'+' '.join(map(str,a))+'\n'+'\n'.join(f'{l+1} {r+1}' for l,r in ranges),answer)
        n,m=200000,200000
        put(f'1\n{n} {m}\n1 '+'1000000000 '*(n-1)+'\n'+f'1 {n}\n'*m,999599999)
    elif pid=='UVA11059':
        groups=[[-10],[0],[10],[-10,-10],[10]*18,[-10]*17,[0,2,0,-3,0]]
        groups += [[rng.randint(-10,10) for _ in range(rng.randint(1,18))] for _ in range(190)]
        for a in groups:
            answer=max([0]+[math.prod(a[l:r]) for l in range(len(a)) for r in range(l+1,len(a)+1)])
            put(array(a),f'Case #1: The maximum product is {answer}.\n\n')
        chosen=groups[:10];answers=[max([0]+[math.prod(a[l:r]) for l in range(len(a)) for r in range(l+1,len(a)+1)]) for a in chosen]
        put('\n'.join(map(array,chosen)),'\n\n'.join(f'Case #{i+1}: The maximum product is {answer}.' for i,answer in enumerate(answers))+'\n\n')
    elif pid=='P1719':
        for _ in range(150):
            n=rng.randint(1,5);grid=[[rng.randint(-127,127) for _ in range(n)] for _ in range(n)]
            answer=max(sum(grid[x][y] for x in range(top,bottom+1) for y in range(left,right+1))
                       for top in range(n) for bottom in range(top,n) for left in range(n) for right in range(left,n))
            put(str(n)+'\n'+'\n'.join(' '.join(map(str,row)) for row in grid),answer)
        n=120
        for x in [-127,0,127]:put(str(n)+'\n'+'\n'.join(' '.join([str(x)]*n) for _ in range(n)),x*n*n if x>=0 else x)
    elif pid=='P2879':
        for _ in range(160):
            n,H=rng.randint(1,5),rng.randint(1,4);heights=[rng.randint(1,H) for _ in range(n)];highest=rng.randrange(n);heights[highest]=H
            possible=[(a,b) for a in range(n) for b in range(n) if a!=b and heights[b]>=heights[a]
                      and all(heights[i]<heights[a] for i in range(min(a,b)+1,max(a,b)))]
            relations=rng.choices(possible,k=rng.randint(0,9)) if possible else []
            maximum=[0]*n
            for state in itertools.product(range(1,H+1),repeat=n):
                if state[highest]!=H:continue
                if all(state[b]>=state[a] and all(state[i]<state[a] for i in range(min(a,b)+1,max(a,b))) for a,b in relations):
                    maximum=[max(x,y) for x,y in zip(maximum,state)]
            assert all(maximum)
            put(f'{n} {highest+1} {H} {len(relations)}\n'+'\n'.join(f'{a+1} {b+1}' for a,b in relations),'\n'.join(map(str,maximum)))
        n=10000;relations=[(i,n+1-i) for i in range(1,n//2+1)]*2
        put(f'{n} 1 1000000 {len(relations)}\n'+'\n'.join(f'{a} {b}' for a,b in relations),
            '\n'.join(str(1000000-min(i-1,n-i)) for i in range(1,n+1)))
    else:
        return remaining(pid,rng,values,put,array)
    return values

def remaining(pid,rng,values,put,array):
    if pid=='P3948':
        def remainder(x,m):return x%m if x>=0 else -((-x)%m)
        for _ in range(160):
            n,op=rng.randint(1,35),rng.randint(1,80);mod=rng.randint(1,2**31-1);low,high=sorted([rng.randint(-mod,mod),rng.randint(-mod,mod)])
            state=[0]*n;operations=[];answers=[]
            def query(l,r):return sum(low<=remainder(state[i]*(i+1),mod)<=high for i in range(l,r+1))
            for _ in range(op):
                l,r=sorted(rng.choices(range(n),k=2))
                if rng.randrange(4):
                    x=rng.randint(-2**31,2**31-1);operations.append(f'A {l+1} {r+1} {x}')
                    for i in range(l,r+1):state[i]+=x
                else:operations.append(f'Q {l+1} {r+1}');answers.append(query(l,r))
            final=[sorted(rng.choices(range(n),k=2)) for _ in range(rng.randint(1,45))]
            answers += [query(l,r) for l,r in final]
            put(f'{n} {op} {mod} {low} {high}\n'+'\n'.join(operations)+f'\n{len(final)}\n'+
                '\n'.join(f'{l+1} {r+1}' for l,r in final),'\n'.join(map(str,answers)))
        n=80000;updates=100000;mod=2147483647;low,high=-1000000000,0;value=-2147483648*updates
        answer=sum(low<=remainder(value*i,mod)<=high for i in range(1,n+1))
        put(f'{n} {updates+1} {mod} {low} {high}\n'+f'A 1 {n} -2147483648\n'*updates+f'Q 1 {n}\n1\n1 {n}',f'{answer}\n{answer}')
    elif pid=='P5542':
        for _ in range(150):
            n=rng.randint(1,15);k=rng.randint(1,n);rectangles=[];grid=[[0]*8 for _ in range(8)]
            for _ in range(n):
                x1,x2=sorted(rng.sample(range(8),2));y1,y2=sorted(rng.sample(range(8),2));rectangles.append((x1,y1,x2,y2))
                for x in range(x1,x2):
                    for y in range(y1,y2):grid[x][y]+=1
            put(f'{n} {k}\n'+'\n'.join(' '.join(map(str,r)) for r in rectangles),sum(v==k for row in grid for v in row))
        n=100000;put(f'{n} {n}\n'+'0 0 1000 1000\n'*n,1000000)
    elif pid=='P9533':
        inputs=[a for n in range(1,6) for a in itertools.product(range(3),repeat=n)]
        inputs += [tuple(rng.randint(0,7) for _ in range(rng.randint(1,7))) for _ in range(100)]
        for a in inputs:put(array(a),reachable_xor_max(a))
        n=100000;put(array([0]*n),n*(n+1)//2);put(array([2**19]*n),n*n//4)
    elif pid=='P10719':
        for _ in range(160):
            n,m=rng.randint(1,5),rng.randint(1,5);k=rng.randint(1,n*m);grid=[[rng.randrange(2) for _ in range(m)] for _ in range(n)];best=n*m+1
            for top in range(n):
                for bottom in range(top,n):
                    for left in range(m):
                        for right in range(left,m):
                            black=sum(grid[x][y] for x in range(top,bottom+1) for y in range(left,right+1))
                            if black>=k:best=min(best,(bottom-top+1)*(right-left+1))
            put(f'{n} {m} {k}\n'+'\n'.join(''.join(map(str,row)) for row in grid),best if best<=n*m else 0)
        for c,k,answer in [('0',1,0),('1',10000,10000),('1',1,1)]:put(f'100 100 {k}\n'+('\n'.join([c*100]*100)),answer)
    elif pid=='P12674':
        MOD=998244353
        for _ in range(220):
            n=rng.randint(1,10);a=[rng.randint(1,4) for _ in range(n)];total=0
            for mask in range(1<<(n-1)):
                left=0;contribution=0;ok=True
                for right in range(n):
                    if right==n-1 or mask>>right&1:
                        if a[left]!=a[right]:ok=False;break
                        contribution+=math.prod(a[left:right+1]);left=right+1
                if ok:total+=contribution
            put(array(a),total%MOD)
        n=250000;put(array([1]*n),(n+1)*pow(2,n-2,MOD)%MOD)
        for x in [1,2,40]:put(array([x]),x)
    elif pid=='P13787':
        for _ in range(150):
            n,m=rng.randint(1,9),rng.randint(1,16);rectangles=[];grid=[[0]*n for _ in range(n)]
            for _ in range(m):
                x1,x2=sorted(rng.choices(range(n),k=2));y1,y2=sorted(rng.choices(range(n),k=2));rectangles.append((x1+1,y1+1,x2+1,y2+1))
                for x in range(x1,x2+1):
                    for y in range(y1,y2+1):grid[x][y]+=1
            put(f'{n} {m}\n'+'\n'.join(' '.join(map(str,r)) for r in rectangles),sum((x+y+2)^grid[x][y] for x in range(n) for y in range(n)))
        n,m=5000,200000;answer=sum(min(s-1,2*n+1-s)*(s^m) for s in range(2,2*n+1))
        put(f'{n} {m}\n'+f'1 1 {n} {n}\n'*m,answer)
    elif pid=='P14520':
        from core7_cases_war import solve
        inputs=[a for n in range(2,5) for a in itertools.product(range(1,4),repeat=n)]
        inputs += list(itertools.product(range(1,3),repeat=5))
        inputs += [(4,3,2,5),(3,3,2,4),(7,2,8),(4,1,4,3),(8,1,2,7),(2,5,1,6)]
        inputs += [tuple(rng.randint(1,8) for _ in range(4)) for _ in range(45)]
        for a in inputs:
            exact=solve(len(a),sum(a))[a];assert all(w!=-1 for w in exact)
            put('1\n'+array(a),''.join('1' if w==0 else '0' for w in exact))
        n=100000;put('1\n'+array([1]*n),'0'*(n//2)+'1'*(n//2-1))
        a=list(range(1,n+1));total=n*(n+1)//2
        put('1\n'+array(a),''.join('1' if m*(m+1)>total else '0' for m in range(1,n)))
    elif pid=='UVA1210':
        # Trial division and a binary search of strictly increasing prefix sums;
        # no Eratosthenes marking or nested running-sum precomputation here.
        primes=[v for v in range(2,10001) if all(v%d for d in range(2,math.isqrt(v)+1))];prefix=[0]
        for p in primes:prefix.append(prefix[-1]+p)
        answers=[]
        for target in range(2,10001):
            answer=0
            for left,p in enumerate(primes):
                if p>target:break
                right=bisect.bisect_left(prefix,prefix[left]+target,left+1)
                answer+=right<len(prefix) and prefix[right]==prefix[left]+target
            answers.append(answer)
        put('\n'.join(map(str,range(2,10001)))+'\n0','\n'.join(map(str,answers)))
    else:raise AssertionError(pid)
    return values
