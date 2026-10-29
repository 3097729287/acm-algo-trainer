"""Independent exhaustive oracles for the greedy/construction unit."""
from collections import deque
from functools import lru_cache
import itertools
import math
import random

IDS=set('P1031 P1208 P1478 P2695 P4995 P5639 B3753 P1056 P2431 P2949 P12041 AT_arc161_c B4225 P1650 P6155 P11036 P12676'.split())

@lru_cache(None)
def blackboard_finals(state):
    if len(state)==1:return frozenset(state)
    result=set()
    for i,j in itertools.combinations(range(len(state)),2):
        if (state[i]-state[j])%2:continue
        nxt=tuple(sorted([x for at,x in enumerate(state) if at not in [i,j]]+[(state[i]+state[j])//2]))
        result.update(blackboard_finals(nxt))
    return frozenset(result)

@lru_cache(None)
def tree_targets(n,edges):
    graph=[[] for _ in range(n)]
    for u,v in edges:graph[u].append(v);graph[v].append(u)
    outputs=set()
    for mask in range(1<<n):
        outputs.add(''.join('B' if sum((mask>>v)&1 for v in graph[u])*2>len(graph[u]) else 'W' for u in range(n)))
    return outputs

def graph_feasible(n,edges):
    # Exhaust every binary weighting. For a fixed weighting enumerate positive
    # reachability from each vertex, independently of the constructor's DSU.
    for mask in range(1<<len(edges)):
        graph=[[] for _ in range(n)]
        for i,(u,v,f) in enumerate(edges):
            if mask>>i&1:graph[u].append(v);graph[v].append(u)
        reach=[]
        for start in range(n):
            seen={start};queue=deque([start])
            while queue:
                for v in graph[queue.popleft()]:
                    if v not in seen:seen.add(v);queue.append(v)
            reach.append(seen)
        if all((0 if v in reach[u] else 1)==f for u,v,f in edges):return True
    return False

def small_equal_possible(n,m):
    if n*(m+1)%2:return False
    goal=n*(m+1)//2;states={(0,)*m};rows=list(itertools.permutations(range(1,m+1)))
    for at in range(n):
        remaining=n-at-1;following=set()
        for state in states:
            for row in rows:
                sums=tuple(x+y for x,y in zip(state,row))
                if all(s+remaining<=goal<=s+remaining*m for s in sums):following.add(sums)
        states=following
    return (goal,)*m in states

def exact_modification(a,b):
    # Exhaust the assignment of costs to original elements, then solve the
    # resulting fixed-cost scheduling problem by subsets. No LIFO construction
    # or rearrangement sorting is used by this oracle.
    n=len(a);slots=[];last=-1
    for value in sorted(a):last=max(last+1,value);slots.append(last)
    answer=10**30
    for weights in set(itertools.permutations(b)):
        dp=[10**30]*(1<<n);dp[0]=0
        for mask in range((1<<n)-1):
            if dp[mask]==10**30:continue
            time=slots[mask.bit_count()]
            for i in range(n):
                if not mask>>i&1 and a[i]<=time:
                    nxt=mask|1<<i;dp[nxt]=min(dp[nxt],dp[mask]+weights[i]*(time-a[i]))
        answer=min(answer,dp[-1])
    return answer

def cases_for(pid):
    assert pid in IDS,pid
    rng=random.Random(20261031);values=[]
    def put(inp,expected):values.append((f'独立校验 {len(values)+1}',str(inp),str(expected)))
    if pid=='P1031':
        inputs={(1,(1,)),(4,(9,8,17,6)),(4,(1,1,1,9))}
        while len(inputs)<90:
            n=rng.randint(2,4);a=tuple(rng.randint(1,4) for _ in range(n))
            if sum(a)%n==0:inputs.add((n,a))
        for n,a in sorted(inputs):
            goal=(sum(a)//n,)*n;queue=deque([(a,0)]);seen={a}
            while queue:
                state,distance=queue.popleft()
                if state==goal:break
                for source in range(n):
                    for destination in [source-1,source+1]:
                        if not 0<=destination<n:continue
                        for amount in range(1,state[source]+1):
                            nxt=list(state);nxt[source]-=amount;nxt[destination]+=amount;nxt=tuple(nxt)
                            if nxt not in seen:seen.add(nxt);queue.append((nxt,distance+1))
            put(str(n)+'\n'+' '.join(map(str,a)),distance)
    elif pid=='P1208':
        for _ in range(170):
            m=rng.randint(1,7);farm=[(rng.randint(0,1000),rng.randint(0,5)) for _ in range(m)];need=rng.randint(0,sum(a for p,a in farm))
            dp={0:0}
            for price,amount in farm:
                following=dict(dp)
                for purchased,cost in dp.items():
                    for take in range(1,min(amount,need-purchased)+1):
                        q=purchased+take;following[q]=min(following.get(q,10**30),cost+price*take)
                dp=following
            put(f'{need} {m}\n'+'\n'.join(f'{p} {a}' for p,a in farm),dp[need])
        put('0 0',0);put('2000000 1\n1000 2000000',2000000000)
    elif pid=='P1478':
        for _ in range(170):
            n=rng.randint(1,12);s=rng.randint(0,40);a,b=rng.randint(1,50),rng.randint(1,200);apples=[(rng.randint(1,280),rng.randint(0,20)) for _ in range(n)]
            best=0
            for mask in range(1<<n):
                chosen=[apples[i] for i in range(n) if mask>>i&1]
                if all(h<=a+b for h,e in chosen) and sum(e for h,e in chosen)<=s:best=max(best,len(chosen))
            put(f'{n} {s}\n{a} {b}\n'+'\n'.join(f'{h} {e}' for h,e in apples),best)
    elif pid=='P2695':
        for _ in range(160):
            n,m=rng.randint(1,7),rng.randint(1,9);heads=[rng.randint(1,20) for _ in range(n)];knights=[rng.randint(1,25) for _ in range(m)]
            @lru_cache(None)
            def search(i,used):
                if i==n:return 0
                return min((knights[j]+search(i+1,used|1<<j) for j in range(m) if not used>>j&1 and knights[j]>=heads[i]),default=10**30)
            best=search(0,0);put(f'{n} {m}\n'+'\n'.join(map(str,heads+knights)),best if best<10**30 else 'you died!')
        put('20000 20000\n'+'100000\n'*40000,2000000000)
    elif pid=='P4995':
        for _ in range(100):
            n=rng.randint(1,8);h=rng.sample(range(1,70),n)
            answer=max(sum((x-y)**2 for x,y in zip((0,)+row,row)) for row in itertools.permutations(h))
            put(str(n)+'\n'+' '.join(map(str,h)),answer)
    elif pid=='P5639':
        sequences=[(0,)+tail for n in range(1,9) for tail in itertools.product(range(2),repeat=n-1)]
        sequences += [(0,)+tuple(rng.randrange(2) for _ in range(rng.randint(1,30))) for _ in range(100)]
        for a in sequences:
            n=len(a);queue=deque([(0,0,0)]);seen={(0,0)}
            while queue:
                passed,parity,time=queue.popleft()
                if passed==n:break
                ends=[passed];at=passed
                while at<n and a[at]==parity:at+=1;ends.append(at)
                for end in ends:
                    state=end,parity^1
                    if state not in seen:seen.add(state);queue.append((end,parity^1,time+1))
            put(str(n)+'\n'+' '.join(map(str,a)),time)
        put('1000000\n'+'0 1 '*500000,1000000);put('1000000\n'+'0 '*1000000,1)
    elif pid=='B3753':
        for n in [*range(1,301),1000000000]+[rng.randint(1,10**9) for _ in range(100)]:put(n,'VALID')
    elif pid=='P1056':
        while len(values)<140:
            m,n=rng.randint(2,7),rng.randint(2,7);k,l=rng.randrange(m),rng.randrange(n)
            pairs=[(r,c,r+1,c) for r in range(1,m) for c in range(1,n+1)]+[(r,c,r,c+1) for r in range(1,m+1) for c in range(1,n)]
            rng.shuffle(pairs);pairs=pairs[:rng.randrange(len(pairs)+1)];best=-1;winners=[]
            for rows in itertools.combinations(range(1,m),k):
                for columns in itertools.combinations(range(1,n),l):
                    score=sum((x!=p and min(x,p) in rows) or (y!=q and min(y,q) in columns) for x,y,p,q in pairs)
                    if score>best:best=score;winners=[(rows,columns)]
                    elif score==best:winners.append((rows,columns))
            if len(winners)!=1:continue
            rows,columns=winners[0];put(f'{m} {n} {k} {l} {len(pairs)}\n'+'\n'.join(' '.join(map(str,p)) for p in pairs),' '.join(map(str,rows))+'\n'+' '.join(map(str,columns))+'\n')
    elif pid=='P2431':
        for _ in range(300):
            a,b=sorted([rng.randint(1,3000),rng.randint(1,3000)]);put(f'{a} {b}',max(x.bit_count() for x in range(a,b+1)))
        def digit_best(a,b):
            low=f'{a:063b}';high=f'{b:063b}'
            @lru_cache(None)
            def dp(at,tight_low,tight_high):
                if at==63:return 0
                minimum=int(low[at]) if tight_low else 0;maximum=int(high[at]) if tight_high else 1
                return max(bit+dp(at+1,tight_low and bit==int(low[at]),tight_high and bit==int(high[at])) for bit in range(minimum,maximum+1))
            return dp(0,True,True)
        queries=[(1,2**63-1),(2**62,2**63-1)]
        for k in range(63):queries.extend([(2**k,2**k),(max(1,2**k-1),min(2**63-1,2**k+1))])
        queries += [tuple(sorted([rng.randint(1,2**63-1),rng.randint(1,2**63-1)])) for _ in range(100)]
        for a,b in queries:put(f'{a} {b}',digit_best(a,b))
    elif pid=='P2949':
        for _ in range(170):
            n=rng.randint(1,13);jobs=[(rng.randint(1,15),rng.randint(1,1000)) for _ in range(n)];best=0
            for mask in range(1<<n):
                selected=[jobs[i] for i in range(n) if mask>>i&1]
                if all(d>=i+1 for i,(d,p) in enumerate(sorted(selected))):best=max(best,sum(p for d,p in selected))
            put(str(n)+'\n'+'\n'.join(f'{d} {p}' for d,p in jobs),best)
        put('100000\n'+'1000000000 1000000000\n'*100000,10**14)
    elif pid=='P12041':
        for _ in range(180):
            n,m=rng.randint(1,7),rng.randint(1,9);edges=[(rng.randrange(n),rng.randrange(n),rng.choice([0,0,1,1,2])) for _ in range(m)]
            possible=graph_feasible(n,edges)
            put(f'{n} {m}\n'+'\n'.join(f'{u+1} {v+1} {f}' for u,v,f in edges),'Yes' if possible else 'No')
        put('100000 99999\n'+'\n'.join(f'{i} {i+1} {i%2}' for i in range(1,100000)),'Yes')
    elif pid=='AT_arc161_c':
        def odd_tree(n):
            edges=[(0,1)]
            for v in range(2,n,2):
                parent=rng.randrange(v);edges.extend([(parent,v),(parent,v+1)])
            return tuple(edges)
        def tree_input(n,edges,target):return str(n)+'\n'+'\n'.join(f'{u+1} {v+1}' for u,v in edges)+'\n'+target
        examples=[];flags=[]
        for n in [2,4,6]:
            edges=odd_tree(n);reachable=tree_targets(n,edges)
            for colors in itertools.product('BW',repeat=n):
                target=''.join(colors);examples.append(tree_input(n,edges,target));flags.append('YES' if target in reachable else '-1')
        put(str(len(examples))+'\n'+'\n'.join(examples),'\n'.join(flags))
        for _ in range(55):
            examples=[];flags=[]
            for _ in range(rng.randint(1,8)):
                n=rng.randrange(1,6)*2;edges=odd_tree(n);target=''.join(rng.choice('BW') for _ in range(n))
                examples.append(tree_input(n,edges,target));flags.append('YES' if target in tree_targets(n,edges) else '-1')
            put(str(len(examples))+'\n'+'\n'.join(examples),'\n'.join(flags))
        spine=100001;n=2*spine-2;edges=[(i-1,i) for i in range(1,spine)]+[(i,spine+i-1) for i in range(1,spine-1)]
        degrees=[0]*n;black=[0]*n
        for u,v in edges:degrees[u]+=1;degrees[v]+=1;black[u]+=v%2;black[v]+=u%2
        target=''.join('B' if black[u]*2>degrees[u] else 'W' for u in range(n))
        put('1\n'+tree_input(n,edges,target),'YES')
    elif pid=='B4225':
        for length in range(2,9):
            finals=blackboard_finals(tuple(range(length)))
            for a in [1,5,99990]:
                b=a+length-1
                for x in range(a,b+1):put(f'{a} {b} {x}','YES' if x-a in finals else '-1')
        for x in [2,50000,99999]:put(f'1 100000 {x}','YES')
    elif pid=='P1650':
        for _ in range(150):
            n=rng.randint(1,8);a=[rng.randint(0,15) for _ in range(n)];b=[rng.randint(0,15) for _ in range(n)]
            answer=200*max(sum((x>y)-(x<y) for x,y in zip(a,row)) for row in set(itertools.permutations(b)))
            put(str(n)+'\n'+' '.join(map(str,a))+'\n'+' '.join(map(str,b)),answer)
        put('2000\n'+'100 '*2000+'\n'+'100 '*2000,0)
    elif pid=='P6155':
        for _ in range(100):
            n=rng.randint(1,6);a=[rng.randint(1,7) for _ in range(n)];b=[rng.randint(1,7) for _ in range(n)]
            put(str(n)+'\n'+' '.join(map(str,a))+'\n'+' '.join(map(str,b)),exact_modification(a,b))
        put('3\n3 3 4\n3 2 1',2)
        n=1000000;put(str(n)+'\n'+'1 '*n+'\n'+'1000000000 '*n,n*(n-1)//2*10**9%2**64)
    elif pid=='P11036':
        numbers=[*range(1,10001),10**9,2**29,3*2**28]
        numbers += [rng.randint(1,10**9) for _ in range(20000)]
        put(str(len(numbers))+'\n'+'\n'.join(map(str,numbers)),'VALID')
    elif pid=='P12676':
        pairs=[(n,m) for n in range(1,6) for m in range(1,5)]
        flags=['YES' if small_equal_possible(n,m) else 'NO' for n,m in pairs]
        put(str(len(pairs))+'\n'+'\n'.join(f'{n} {m}' for n,m in pairs),'\n'.join(flags))
        for _ in range(100):
            pairs=[(rng.randint(1,20),rng.randint(1,40)) for _ in range(rng.randint(1,12))]
            flags=['YES' if m==1 or (n>1 and (n%2==0 or m%2==1)) else 'NO' for n,m in pairs]
            put(str(len(pairs))+'\n'+'\n'.join(f'{n} {m}' for n,m in pairs),'\n'.join(flags))
        put('1\n3 333333','YES');put('1\n2 500000','YES');put('1\n1000000 1','YES')
    assert values,pid
    return values
