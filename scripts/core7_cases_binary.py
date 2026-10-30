"""Small exhaustive models, event simulations and explicit extreme answers."""
from collections import deque
from functools import lru_cache
from fractions import Fraction
import itertools
import json
import math
import random
import sys

IDS={'B3691','P1678','P7713','P11962','CF1967A','P1570','P2005','P2920','P8873','P14115','P14635','UVA10125','P3611','P6465','P10445','P13824','UVA11134','P12342','CF1237B','CF1304C','CF1148B','CF644B'}


def allocations(total,n):
    if n==1:yield (total,);return
    for x in range(total+1):
        for rest in allocations(total-x,n-1):yield (x,)+rest


def tree_path(graph,start,end):
    todo=[start];before={start:None}
    for u in todo:
        if u==end:break
        for v in graph[u]:
            if v not in before:before[v]=u;todo.append(v)
    path=[end]
    while path[-1]!=start:path.append(before[path[-1]])
    return path[::-1]


def cases_for(pid):
    rng=random.Random(7579644);values=[]
    def put(inp,answer):values.append((f'独立校验 {len(values)+1}',str(inp)+'\n',str(answer)+'\n'))
    def ints(a):return ' '.join(map(str,a))
    if pid=='B3691':
        for _ in range(140):
            a=[rng.randrange(1,10) for i in range(rng.randrange(1,40))];b=[rng.randrange(1,10) for i in range(rng.randrange(1,15))]
            erased=''.join('|' if x in set(b) else 'x' for x in a)
            put(f'{len(a)} {len(b)}\n{ints(a)}\n{ints(b)}',sum(bool(s) for s in erased.split('|')))
        put('500000 1\n'+'1 '*500000+'\n2',1)
    elif pid=='P1678':
        for _ in range(150):
            a=[rng.randrange(0,100) for i in range(rng.randrange(1,20))];b=[rng.randrange(0,100) for i in range(rng.randrange(1,30))]
            put(f'{len(a)} {len(b)}\n{ints(a)}\n{ints(b)}',sum(min(abs(x-y) for y in a) for x in b))
        put('1 100000\n0\n'+'1000000 '*100000,10**11)
    elif pid=='P7713':
        for _ in range(160):
            n=rng.randrange(3,7);m=rng.randrange(6);a=[rng.randrange(6) for i in range(n)]
            answer=max(sum(sorted(x+y for x,y in zip(a,extra))[1:-1]) for extra in allocations(m,n))
            put(f'{n} {m}\n{ints(a)}',answer)
        put('100000 1000000000\n'+'1000000000 '*100000,99998*10**9+999989999)
    elif pid=='P11962':
        for _ in range(100):
            n=rng.randrange(1,31);edges=[(i,rng.randrange(i)) for i in range(1,n)];graph=[[] for i in range(n)]
            for a,b in edges:graph[a].append(b);graph[b].append(a)
            answer=[]
            for start in range(n):
                seen={(start,0)};todo=[(start,0)]
                for u,parity in todo:
                    for v in graph[u]:
                        state=(v,1-parity)
                        if state not in seen:seen.add(state);todo.append(state)
                answer.append(sum(p==0 for u,p in seen))
            put(str(n)+'\n'+'\n'.join(f'{u+1} {v+1}' for u,v in edges),ints(answer))
        n=200000;put(str(n)+'\n'+'\n'.join(f'{i} {i+1}' for i in range(1,n)),('100000 ')*n)
    elif pid=='CF1967A':
        def best_order(counts):
            n=len(counts)
            @lru_cache(None)
            def go(remaining,tail):
                if not any(remaining):return 0
                answer=0
                for c in range(n):
                    if not remaining[c]:continue
                    changed=list(remaining);changed[c]-=1;window=tail+(c,)
                    score=int(len(window)>=n and len(set(window[-n:]))==n)
                    answer=max(answer,score+go(tuple(changed),window[-(n-1):] if n>1 else ()))
                return answer
            return go(tuple(counts),())
        tests=[]
        for _ in range(90):
            n=rng.randrange(1,5);k=rng.randrange(4);a=[rng.randrange(1,3) for i in range(n)]
            answer=max(best_order([x+y for x,y in zip(a,extra)]) for extra in allocations(k,n))
            tests.append((n,k,a,answer))
        put(str(len(tests))+'\n'+'\n'.join(f'{n} {k}\n{ints(a)}' for n,k,a,s in tests),'\n'.join(str(s) for n,k,a,s in tests))
        n=200000;h=10**12+5000000;put(f'1\n{n} {10**12}\n'+('1000000000000 ')*n,n*h-n+1)
    elif pid=='P1570':
        cases=[([1],[16],1),([1],[2000],1),([9999],[10],1),([10000],[10],1)]
        for _ in range(140):
            n=rng.randrange(1,10);cases.append(([rng.randrange(1,40) for i in range(n)],[rng.randrange(1,40) for i in range(n)],rng.randrange(1,n+1)))
        for v,c,m in cases:
            ratio=max(Fraction(sum(v[i] for i in selected),sum(c[i] for i in selected)) for selected in itertools.combinations(range(len(v)),m))
            rounded=(ratio.numerator*2000+ratio.denominator)//(2*ratio.denominator)
            put(f'{len(v)} {m}\n{ints(v)}\n{ints(c)}',f'{rounded//1000}.{rounded%1000:03d}')
    elif pid=='P2005':
        sys.set_int_max_str_digits(100000)
        for _ in range(150):
            m=rng.randrange(1,10**rng.randrange(1,101));q=rng.randrange(6227020801);r=rng.randrange(m);n=m*q+r
            put(f'{n}\n{m}',n//m)
        maximum=math.factorial(6250);q=math.factorial(13);m=maximum//q
        put(f'{maximum}\n{m}',maximum//m)
        put('0000001\n0000002',0)
    elif pid=='P2920':
        for _ in range(110):
            n=rng.randrange(1,8);jobs=[(rng.randrange(1,8),rng.randrange(1,45)) for i in range(n)]
            best=-1
            for order in itertools.permutations(jobs):
                elapsed=0;latest=10**9
                for duration,deadline in order:elapsed+=duration;latest=min(latest,deadline-elapsed)
                if latest>=0:best=max(best,latest)
            put(str(n)+'\n'+'\n'.join(f'{t} {s}' for t,s in jobs),best)
        put('1000\n'+'1000 1000000\n'*1000,0)
    elif pid=='P8873':
        sequence=[]
        for peak in range(50):sequence.extend(list(range(peak+1))+list(range(peak-1,-peak-1,-1))+list(range(-peak+1,1)))
        # For peak zero, the final range is empty and the initial zero occurs once.
        put(str(len(sequence))+'\n'+'\n'.join(str(i+1) for i in range(len(sequence))),'\n'.join(map(str,sequence)))
        queries=[];answers=[]
        for i in [1000,10**6,10**9,1414213561]:
            for offset,value in [(0,0),(i,i),(3*i,-i),(4*i,0)]:
                k=i*(2*i-1)+1+offset
                if k<=4*10**18:queries.append(k);answers.append(value)
        put(str(len(queries))+'\n'+'\n'.join(map(str,queries)),'\n'.join(map(str,answers)))
    elif pid=='P14115':
        for _ in range(130):
            n=rng.randrange(1,5);m=rng.randrange(6);k=rng.randrange(5);h=rng.randrange(2,7);a=[rng.randrange(1,9) for i in range(n)]
            best=max(min(a[i]+short[i]+h*long[i] for i in range(n)) for short in allocations(m,n) for long in allocations(k,n))
            put(f'{n} {m} {k} {h}\n{ints(a)}',best)
        put('1 1000000000 1000000000 1000000000\n1000000000',10**18+2*10**9)
        put('100000 0 1000000000 1000000000\n'+'1 '*100000,10**13+1)
    elif pid=='P14635':
        for _ in range(130):
            n=rng.randrange(1,6);money=rng.randrange(1,61);prices=[(rng.randrange(1,15),rng.randrange(1,15)) for i in range(n)]
            dp={0:0}
            for x,y in prices:
                changed={}
                for paid,count in dp.items():
                    for take in range(money+1):
                        cost=(take//2)*(x+y)+(take%2)*x
                        if paid+cost<=money:changed[paid+cost]=max(changed.get(paid+cost,-1),count+take)
                dp=changed
            put(f'{n} {money}\n'+'\n'.join(f'{x} {y}' for x,y in prices),max(dp.values()))
        put('1 1000000000000000000\n1 1',10**18)
    elif pid=='UVA10125':
        tests=[];answers=[]
        for _ in range(200):
            n=rng.randrange(1,11);a=rng.sample(range(-25,26),n);possible=[]
            for d in range(n):
                if any(sum(a[i] for i in triple)==a[d] for triple in itertools.combinations([i for i in range(n) if i!=d],3)):possible.append(a[d])
            tests.append(str(n)+'\n'+'\n'.join(map(str,a)));answers.append(str(max(possible)) if possible else 'no solution')
        put('\n'.join(tests)+'\n0','\n'.join(answers))
        # Values one to 1000 include 1+2+997=1000 with distinct elements.
        put('1000\n'+'\n'.join(map(str,range(1,1001)))+'\n0',1000)
    elif pid=='P3611':
        for _ in range(150):
            n=rng.randrange(1,30);a=[rng.randrange(1,30) for i in range(n)];limit=rng.randrange(max(a),sum(a)+1)
            def event_simulation(capacity):
                events=[(a[i],i) for i in range(capacity)];next_cow=capacity;last=0
                while events:
                    time,cow=min(events);events.remove((time,cow));last=max(last,time)
                    if next_cow<n:events.append((time+a[next_cow],next_cow));next_cow+=1
                return last
            answer=next(k for k in range(1,n+1) if event_simulation(k)<=limit)
            put(f'{n} {limit}\n'+'\n'.join(map(str,a)),answer)
        put('10000 100000\n'+'100000\n'*10000,10000)
    elif pid=='P6465':
        for _ in range(150):
            n=rng.randrange(1,31);l=rng.randrange(1,n+1);a=[rng.randrange(1,min(n,5)+1) for i in range(n)];answer=0
            for left in range(n):
                for right in range(left+1,n):
                    if right-left+1>=l and a[left]!=a[right] and all(a[i]!=a[i+1] for i in range(left,right)):answer+=1
            put(f'1\n{n} {l}\n{ints(a)}',answer)
        n=500000;put(f'1\n{n} 1\n'+ints(range(1,n+1)),n*(n-1)//2)
    elif pid=='P12342':
        for _ in range(130):
            n=rng.randrange(1,8);a=[rng.randrange(1,16) for i in range(n)];b=[rng.randrange(1,16) for i in range(n)]
            kept=max(sum(x>y for x,y in zip(a,order)) for order in itertools.permutations(b))
            put(f'{n}\n{ints(a)}\n{ints(b)}',n-kept)
        n=100000;put(f'{n}\n'+'1 '*n+'\n'+'1 '*n,n)
    elif pid=='CF1237B':
        for _ in range(150):
            n=rng.randrange(1,50);a=rng.sample(range(1,n+1),n);b=rng.sample(a,n);pos={x:i for i,x in enumerate(a)}
            answer=sum(any(pos[y]<pos[x] for y in b[j+1:]) for j,x in enumerate(b))
            put(f'{n}\n{ints(a)}\n{ints(b)}',answer)
        n=100000;put(f'{n}\n'+ints(range(1,n+1))+'\n'+ints(range(n,0,-1)),n-1)
    elif pid=='CF1304C':
        tests=[];answers=[]
        for _ in range(180):
            n=rng.randrange(1,8);initial=rng.randrange(-5,6);time=0;appointments=[];possible={initial};previous=0
            for i in range(n):
                time+=rng.randrange(4);l=rng.randrange(-12,12);h=l+rng.randrange(6);appointments.append((time,l,h))
                for minute in range(time-previous):possible={x+delta for x in possible for delta in [-1,0,1]}
                possible={x for x in possible if l<=x<=h};previous=time
            tests.append(f'{n} {initial}\n'+'\n'.join(ints(row) for row in appointments));answers.append('YES' if possible else 'NO')
        put(str(len(tests))+'\n'+'\n'.join(tests),'\n'.join(answers))
    elif pid=='CF1148B':
        for _ in range(140):
            n=rng.randrange(1,7);m=rng.randrange(1,7);k=rng.randrange(1,n+m+1);ta=rng.randrange(1,8);tb=rng.randrange(1,8)
            a=sorted(rng.sample(range(1,25),n));b=sorted(rng.sample(range(1,35),m));worst=0
            for removed in itertools.combinations(range(n+m),k):
                banned=set(removed);routes=[y+tb for i,x in enumerate(a) if i not in banned for j,y in enumerate(b) if n+j not in banned and x+ta<=y]
                if not routes:worst=-1;break
                worst=max(worst,min(routes))
            put(f'{n} {m} {ta} {tb} {k}\n{ints(a)}\n{ints(b)}',worst)
        put('1 2 1000000000 1000000000 1\n1000000000\n1 2',-1)
    elif pid=='CF644B':
        for _ in range(160):
            n=rng.randrange(1,60);b=rng.randrange(1,8);time=0;events=[];answer=[];running=None;waiting=deque()
            for i in range(n):
                time+=rng.randrange(1,7);duration=rng.randrange(1,20);events.append((time,duration))
                while running is not None and running<=time:
                    done=running
                    if waiting:running=done+waiting.popleft()
                    else:running=None
                if running is None:running=time+duration;answer.append(running)
                elif len(waiting)<b:answer.append(running+sum(waiting)+duration);waiting.append(duration)
                else:answer.append(-1)
            put(f'{n} {b}\n'+'\n'.join(ints(row) for row in events),ints(answer))
        n=200000;put(f'{n} {n}\n'+'\n'.join(f'{i+1} 1000000000' for i in range(n)),ints(1+(i+1)*10**9 for i in range(n)))
    elif pid=='UVA11134':
        from core7_checkers_binary import axis_feasible
        for _ in range(120):
            n=rng.randrange(1,9);rectangles=[]
            for i in range(n):
                l,r=sorted([rng.randrange(1,n+1),rng.randrange(1,n+1)]);b,t=sorted([rng.randrange(1,n+1),rng.randrange(1,n+1)]);rectangles.append((l,b,r,t))
            # Checker independently validates the full construction or matching impossibility.
            put(str(n)+'\n'+'\n'.join(ints(row) for row in rectangles)+'\n0','')
        n=5000;put(str(n)+'\n'+'\n'.join(f'{i} {i} {i} {i}' for i in range(1,n+1))+'\n0','')
    elif pid=='P10445':
        from core7_checkers_binary import sign_optimum
        for _ in range(160):
            n=rng.randrange(1,11);a=[rng.randrange(-12,13) for i in range(n)];budget=rng.randrange(1,35);gift=rng.randrange(1,n+1)
            # Brute all subsets as a cross-check of the separate extremes oracle.
            best=[]
            for mask in range(1<<n):
                selected=[i+1 for i in range(n) if mask>>i&1];positions=[0]+[a[i-1] for i in selected]
                if 2*(max(positions)-min(positions))>budget+5*(gift in selected):continue
                if len(selected)>len(best) or len(selected)==len(best) and selected<best:best=selected
            assert best==sign_optimum(a,budget,gift)
            put(f'{n} {budget} {gift}\n{ints(a)}',json.dumps({'best':best}))
        put('3 1 2\n1000000000000000000 -1000000000000000000 0',json.dumps({'best':[3]}))
        n=1000000;put(f'{n} 1 1\n'+'0 '*n,json.dumps({'best':list(range(1,n+1))}))
    elif pid=='P13824':
        for case in range(55):
            n=3 if case==0 else rng.randrange(3,9)
            points=[(0,0),(10,0),(10,1)] if case==0 else [(rng.randrange(0,21),rng.randrange(0,21)) for i in range(n)]
            edges=[(1,0),(2,0)] if case==0 else [(i,rng.randrange(i)) for i in range(1,n)]
            graph=[[] for i in range(n)]
            for u,v in edges:graph[u].append(v);graph[v].append(u)
            def squared(u,v):return sum((a-b)**2 for a,b in zip(points[u],points[v]))
            root_dist=[len(tree_path(graph,0,i))-1 for i in range(n)];options=[]
            for u in range(n):
                for v in range(u,n):
                    path=tree_path(graph,u,v);peak=min(range(len(path)),key=lambda i:root_dist[path[i]])
                    thresholds=sorted({squared(a,b) for a in path for b in path})
                    def possible(cap):
                        if squared(u,v)>cap:return False
                        seen={(0,len(path)-1)};todo=[(0,len(path)-1)]
                        for left,right in todo:
                            if left==right:return True
                            for dl,dr in [(1,0),(0,-1),(1,-1)]:
                                if dl and left>=peak or dr and right<=peak:continue
                                state=(left+dl,right+dr)
                                if state not in seen and squared(path[state[0]],path[state[1]])<=cap:seen.add(state);todo.append(state)
                        return False
                    needed=next(cap for cap in thresholds if possible(cap));length=sum(squared(a,b) for a,b in zip(path,path[1:]));options.append((needed,length,u+1,v+1))
            queries=sorted({0,1,10000}|{cap for cap,length,u,v in options}|{max(0,cap-1) for cap,length,u,v in options})
            answers=[]
            for cap in queries:
                chosen=min(((-length,u,v) for need,length,u,v in options if need<=cap));answers.append(f'{chosen[1]} {chosen[2]}')
            put(f'{n} {len(queries)}\n'+'\n'.join(ints(p) for p in points)+'\n'+'\n'.join(f'{u+1} {v+1}' for u,v in edges)+'\n'+'\n'.join(map(str,queries)),'\n'.join(answers))
        # A thousand coincident points: every path is length zero, tie chooses (1,1).
        n=1000;put(f'{n} 1\n'+'0 0\n'*n+'\n'.join(f'1 {i}' for i in range(2,n+1))+'\n0','1 1')
    return values
