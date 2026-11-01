"""Literal subsets, FIFO replay, count products and independent small oracles."""
from collections import Counter,deque
from functools import lru_cache
from itertools import product
from math import isqrt
import random

IDS={'P1048','P2392','P1679','P1855','P2639','P11246','B3873','P1466','P2170',
     'P2725','P5365','P14920','P1156','P1776','P4912','P13018','P11274'}


def subsets(values):
    sums=[0]
    for v in values:sums += [s+v for s in sums]
    return sums


def zero_one(items,capacity):
    pairs=[(0,0)]
    for weight,value in items:pairs += [(w+weight,v+value) for w,v in pairs]
    return max(v for w,v in pairs if w<=capacity)


def two_resources(items,money,time):
    states=[(0,0,0)]
    for m,t in items:states += [(x+m,y+t,z+1) for x,y,z in states]
    return max(z for x,y,z in states if x<=money and y<=time)


def drinks(items,required):
    states=[(0,0)]
    for price,volume in items:states += [(p+price,v+volume) for p,v in states]
    candidates=[p for p,v in states if v>=required]
    return min(candidates) if candidates else 'no solution'


@lru_cache(None)
def fourth_bfs(bound=100000):
    coins=[i**4 for i in range(1,19) if i**4<=bound];distance=[-1]*(bound+1);distance[0]=0;queue=deque([0])
    while queue:
        x=queue.popleft()
        for c in coins:
            if x+c>bound:break
            if distance[x+c]<0:distance[x+c]=distance[x]+1;queue.append(x+c)
    return distance


def squares_enumeration(n):
    square=[i*i for i in range(1,isqrt(n)+1)];single=set(square)
    if n in single:return 1
    pair={a+b for i,a in enumerate(square) for b in square[i:] if a+b<=n}
    if n in pair:return 2
    if any(n-a in pair for a in square):return 3
    assert any(n-a in pair for a in pair),'Four-square witness not found'
    return 4


def subset_partitions(n):
    target=n*(n+1)//2
    if target%2:return 0
    half=n//2;a=Counter(subsets(range(1,half+1)));b=Counter(subsets(range(half+1,n+1)))
    return sum(count*b[target//2-x] for x,count in a.items())//2


def components(n,edges):
    graph=[[] for _ in range(n)]
    for u,v in edges:graph[u].append(v);graph[v].append(u)
    seen=set();sizes=[]
    for i in range(n):
        if i in seen:continue
        seen.add(i);todo=[i]
        for u in todo:
            for v in graph[u]:
                if v not in seen:seen.add(v);todo.append(v)
        sizes.append(len(todo))
    return sizes


def selected_count(n,target,edges):
    return min(subsets(components(n,edges)),key=lambda s:(abs(s-target),s))


def stamp_layers(coins,limit):
    all_sums={0};layer={0}
    for _ in range(limit):layer={s+c for s in layer for c in coins};all_sums |= layer
    answer=0
    while answer+1 in all_sums:answer+=1
    return answer


def skin_choices(k,cost,target):
    best=None
    for chosen in product(*(range(x+1) for x in k)):
        ways=1
        for x in chosen:ways*=max(1,x)
        if ways>=target:
            price=sum(x*c for x,c in zip(chosen,cost));best=price if best is None else min(best,price)
    assert best is not None
    return best


def skin_uniform(target):
    # Integer factorizations by additive cost; 121 identical heroes exceed any
    # needed factor count at the first successful cost, so counts cannot bind.
    best=[1]
    for price in range(1,201):
        best.append(max([1]+[best[price-x]*x for x in range(2,11) if x<=price]))
        if best[-1]>=target:return price
    raise AssertionError('Uniform upper bound too small')


def garbage_actions(depth,events):
    states={(0,10)}
    for t,food,height in sorted(events):
        nxt=set(states)
        for h,death in states:
            if death<t:continue
            if h+height>=depth:return t
            nxt.add((h,death+food));nxt.add((h+height,death))
        states=nxt
    return max(death for h,death in states)


def bounded_enumeration(items,capacity):
    return max(sum(c*v for c,(v,w,m) in zip(chosen,items))
               for chosen in product(*(range(m+1) for v,w,m in items))
               if sum(c*w for c,(v,w,m) in zip(chosen,items))<=capacity)


def spells_subsets(a,b,w,target):
    n=len(a);best=None
    for mask in range(1,1<<n):
        chosen=[i for i in range(n) if mask>>i&1]
        if sum(a[i] for i in chosen)!=target:continue
        value=sum(b[i] for i in chosen)+sum(w[j][i] for j,i in zip(chosen,chosen[1:]))
        best=value if best is None else max(best,value)
    return -1 if best is None else best


def flavour_subsets(items):
    states=[(0,0)]
    for a,b in items:states += [(x+a,y+b) for x,y in states]
    return max(x+y for x,y in states if x==y)


def fifo_score(a,b,chosen):
    queue=deque()
    for i in chosen:
        for _ in range(min(b[i],len(queue))):queue.popleft()
        queue.append(i)
    return sum(a[i] for i in queue)


def fifo_subsets(a,b):
    return max(fifo_score(a,b,[i for i in range(len(a)) if mask>>i&1]) for mask in range(1<<len(a)))


def cases_for(pid):
    rng=random.Random(20261031+sum(map(ord,pid)));result=[]
    def put(inp,out):result.append((f'{pid}-independent-{len(result)+1}',inp,str(out).rstrip()+'\n'))
    def rows(items):return ''.join(' '.join(map(str,row))+'\n' for row in items)
    if pid=='P1048':
        for _ in range(190):
            n=rng.randint(1,12);cap=rng.randint(1,50);items=[(rng.randint(1,40),rng.randint(1,100)) for _ in range(n)]
            put(f'{cap} {n}\n'+rows(items),zero_one(items,cap))
        put('4 1\n2 3\n',3);put('1000 100\n'+'10 100\n'*100,10000)
    elif pid=='P2392':
        for _ in range(170):
            groups=[[rng.randint(1,60) for j in range(rng.randint(1,8))] for i in range(4)]
            put(' '.join(map(str,map(len,groups)))+'\n'+rows(groups),sum(min(max(s,sum(g)-s) for s in subsets(g)) for g in groups))
        put('3 1 1 1\n3 3 3\n1\n1\n1\n',9)
        put('20 20 20 20\n'+('60 '*19+'60\n')*4,2400)
    elif pid=='P1679':
        oracle=fourth_bfs()
        for target in list(range(1,181))+[rng.randint(1,100000) for _ in range(70)]+[706,65536,100000]:put(f'{target}\n',oracle[target])
    elif pid=='P1855':
        for _ in range(210):
            n=rng.randint(1,11);money=rng.randint(0,35);time=rng.randint(0,35);items=[(rng.randint(0,25),rng.randint(0,25)) for i in range(n)]
            put(f'{n} {money} {time}\n'+rows(items),two_resources(items,money,time))
        put('100 0 0\n'+'0 0\n'*100,100);put('100 200 200\n'+'2 2\n'*100,100)
    elif pid=='P2639':
        for _ in range(180):
            h=rng.randint(5,70);weights=[rng.randint(1,h) for i in range(rng.randint(1,13))]
            put(f'{h} {len(weights)}\n'+'\n'.join(map(str,weights))+'\n',max(s for s in subsets(weights) if s<=h))
        put('45000 500\n'+'90\n'*500,45000);put('45000 500\n'+'91\n'*500,44954)
    elif pid=='P11246':
        for target in list(range(1,201))+[99999,100000,65536]:put(f'{target}\n',squares_enumeration(target))
    elif pid=='B3873':
        for _ in range(200):
            n=rng.randint(1,12);required=rng.randint(1,70);items=[(rng.randint(1,50),rng.randint(1,80)) for i in range(n)]
            put(f'{n} {required}\n'+rows(items),drinks(items,required))
        put('500 2000\n'+'1000000 1\n'*500,'no solution')
        put('500 2000\n'+'1000000 1000000\n'*500,1000000)
        put('500 2000\n'+'1000000 4\n'*500,500000000)
    elif pid=='P1466':
        for n in list(range(1,20))+[23,27,31,35,39]:put(f'{n}\n',subset_partitions(n))
    elif pid=='P2170':
        for _ in range(240):
            n=rng.randint(1,11);target=rng.randint(0,n);edges=[(rng.randrange(n),rng.randrange(n)) for i in range(rng.randrange(18))]
            put(f'{n} {target} {len(edges)}\n'+rows([(u+1,v+1) for u,v in edges]),selected_count(n,target,edges))
        put('20000 10000 0\n',10000);put('20000 10000 19999\n'+rows([(i,i+1) for i in range(1,20000)]),0)
        edges=[];offset=0;sizes=[]
        for s in range(1,200):
            sizes.append(s);edges += [(offset+i,offset+i+1) for i in range(1,s)];offset+=s
        reachable=1
        for s in sizes:reachable |= reachable<<s
        target=12345;expected=min((i for i in range(offset+1) if reachable>>i&1),key=lambda x:(abs(x-target),x))
        put(f'{offset} {target} {len(edges)}\n'+rows(edges),expected)
    elif pid=='P2725':
        for _ in range(210):
            k=rng.randint(1,7);coins=[rng.randint(1,15) for i in range(rng.randint(1,8))]
            put(f'{k} {len(coins)}\n'+' '.join(map(str,coins))+'\n',stamp_layers(coins,k))
        put('2 2\n1 3\n',4);put('200 50\n'+' '.join(map(str,range(1,51)))+'\n',10000)
        put('200 50\n'+' '.join(map(str,range(9951,10001)))+'\n',0)
    elif pid=='P5365':
        for _ in range(210):
            n=rng.randint(1,5);k=[rng.randint(1,5) for i in range(n)];cost=[rng.randint(1,199) for i in range(n)];maximum=1
            for x in k:maximum*=x
            target=rng.randint(1,maximum)
            put(f'{n} {target}\n'+' '.join(map(str,k))+'\n'+' '.join(map(str,cost))+'\n',skin_choices(k,cost,target))
        put('2 4\n4 4\n199 1\n',4)
        put('121 100000000000000000\n'+' '.join(['10']*121)+'\n'+' '.join(['199']*121)+'\n',199*skin_uniform(10**17))
        put('121 1\n'+' '.join(['1']*121)+'\n'+' '.join(['199']*121)+'\n',0)
    elif pid=='P14920':
        for _ in range(200):
            n=rng.randint(1,12);budget=rng.randint(1,200);items=[(rng.randint(1,500),rng.randint(1,200)) for i in range(n)]
            put(f'{n} {budget}\n'+rows(items),zero_one([(c,a) for a,c in items],budget))
        put('500 1000000000\n'+'500 2000000\n'*500,250000)
        put('500 1000000000\n'+'500 1000000000\n'*500,500)
    elif pid=='P1156':
        for _ in range(230):
            depth=rng.randint(2,25);events=[(rng.randint(1,50),rng.randint(1,15),rng.randint(1,10)) for i in range(rng.randint(1,8))];rng.shuffle(events)
            put(f'{depth} {len(events)}\n'+rows(events),garbage_actions(depth,events))
        put('10 1\n10 1 10\n',10);put('100 1\n10 30 1\n',40)
        put('100 100\n'+'10 30 1\n'*100,10)
        put('100 100\n'+rows([(i*31,30,1) for i in range(1,101)]),10)
    elif pid=='P1776':
        for _ in range(190):
            capacity=rng.randint(0,80);items=[(rng.randint(1,1000),rng.randint(1,40),rng.randint(1,5)) for i in range(rng.randint(1,5))]
            put(f'{len(items)} {capacity}\n'+rows(items),bounded_enumeration(items,capacity))
        put('100 40000\n'+'1000 1 1000\n'*100,40000000)
        put('100 0\n'+'1000 1 1000\n'*100,0)
        put('1 40000\n1000 1000000000 100000\n',0)
    elif pid=='P4912':
        for _ in range(270):
            n=rng.randint(1,11);a=[rng.randint(-8,8) for i in range(n)];b=[rng.randint(-15,15) for i in range(n)];w=[[rng.randint(-20,20) for j in range(n)] for i in range(n)];target=rng.randint(1,25)
            put(f'{n} {target}\n'+rows(list(zip(a,b)))+rows(w),spells_subsets(a,b,w,target))
        put('2 1\n-3 10\n4 20\n0 7\n0 0\n',37)
        put('50 2500\n'+'50 50\n'*50+(' '.join(['50']*50)+'\n')*50,4950)
        put('50 2500\n'+'-50 50\n'*50+(' '.join(['50']*50)+'\n')*50,-1)
    elif pid=='P13018':
        for _ in range(230):
            items=[(rng.randint(1,30),rng.randint(1,30)) for i in range(rng.randint(1,12))];put(f'{len(items)}\n'+rows(items),flavour_subsets(items))
        put('100\n'+'500 1\n'*50+'1 500\n'*50,50100)
        put('100\n'+'500 1\n'*100,0);put('100\n'+'500 500\n'*100,100000)
    elif pid=='P11274':
        put('3\n-9 5 6\n0 0 1\n',11)
        for _ in range(1000):
            n=rng.randint(1,12);a=[rng.randint(-20,20) for i in range(n)];b=[rng.randrange(n+1) for i in range(n)]
            put(f'{n}\n'+' '.join(map(str,a))+'\n'+' '.join(map(str,b))+'\n',fifo_subsets(a,b))
        for n,a,b,expected in [(3000,[10**8]*3000,[0]*3000,3*10**11),(3000,[-10**8]*3000,[0]*3000,0),(3000,list(range(1,3001)),[3000]*3000,3000)]:
            put(f'{n}\n'+' '.join(map(str,a))+'\n'+' '.join(map(str,b))+'\n',expected)
    else:raise KeyError(pid)
    return result
