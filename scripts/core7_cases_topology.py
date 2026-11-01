"""Literal schedules, permutations, simple cycles, paths and visited-set walks."""
from collections import deque
from fractions import Fraction
from functools import lru_cache
import itertools
import json
import random

IDS={'B3644','P1113','P1137','P1960','P2419','P2712','P3183','P4017','P7113','P10166',
     'UVA10305','CF1361A','P1038','P3243','P3627','P8269','P11022','CF1385E'}


def all_orders(n,edges):
    from core7_checkers_topology import valid_order
    return [p for p in itertools.permutations(range(1,n+1)) if valid_order(n,edges,p)]


def random_dag(rng,n):
    order=list(range(1,n+1));rng.shuffle(order)
    edges=[(order[i],order[j]) for i in range(n) for j in range(i+1,n) if rng.randrange(3)==0]
    return order,edges


def graph_text(n,edges):return f'{n} {len(edges)}\n'+''.join(f'{u} {v}\n' for u,v in edges)


def water_answers(n,graph,m):
    water=[Fraction(0) for _ in range(n+1)]
    def walk(u,amount):
        if not graph[u]:water[u]+=amount;return
        for v in graph[u]:walk(v,amount/len(graph[u]))
    for u in range(1,m+1):walk(u,Fraction(1))
    return ''.join(f'{water[u].numerator} {water[u].denominator}\n' for u in range(1,n+1) if not graph[u])


def cases_for(pid):
    rng=random.Random(20261030+sum(map(ord,pid)));cases=[]
    def put(inp,expected,label='独立校验'):
        cases.append((f'{label} {len(cases)+1}',str(inp),str(expected)))
    if pid in {'B3644','UVA10305','P1960','P2419'}:
        for _ in range(130):
            n=rng.randrange(2,8);order,edges=random_dag(rng,n)
            if pid=='P2419' and not edges:edges=[tuple(order[:2])]
            if pid=='B3644':
                adjacency={u:[] for u in range(1,n+1)}
                for u,v in edges:adjacency[u].append(v)
                put(str(n)+'\n'+''.join(' '.join(map(str,adjacency[u]+[0]))+'\n' for u in range(1,n+1)),' '.join(map(str,order)))
            elif pid=='UVA10305':
                # Include a second, dependency-free group before the terminator.
                put(graph_text(n,edges)+'3 0\n0 0\n',' '.join(map(str,order))+'\n1 2 3\n')
            else:
                orders=all_orders(n,edges)
                if pid=='P1960':put(str(n)+'\n'+str(len(edges))+'\n'+''.join(f'{u} {v}\n' for u,v in edges),'\n'.join(map(str,orders[0]))+'\n'+str(int(len(orders)>1)))
                else:put(graph_text(n,edges),sum(len({p.index(u) for p in orders})==1 for u in range(1,n+1)))
        n=100 if pid in {'B3644','UVA10305','P2419'} else 5000;edges=[(u,u+1) for u in range(1,n)]
        if pid=='P2419':put(graph_text(n,edges),n,'完整强弱链')
        elif pid=='P1960':put(f'{n}\n{n-1}\n'+''.join(f'{u} {v}\n' for u,v in edges),'\n'.join(map(str,range(1,n+1)))+'\n0','唯一长链')
        elif pid=='UVA10305':put(graph_text(n,edges)+'0 0\n',' '.join(map(str,range(1,n+1))),'完整依赖链')
        else:put(str(n)+'\n'+''.join(f'{u+1} 0\n' for u in range(1,n))+'0\n',' '.join(map(str,range(1,n+1))),'完整家谱链')
    elif pid=='P1113':
        for _ in range(160):
            n=rng.randrange(3,12);duration=[0]+[rng.randrange(1,8) for _ in range(n)]
            deps={u:{v for v in range(1,u) if rng.randrange(3)==0} for u in range(1,n+1)}
            waiting=set(range(1,n+1));done=set();running={};clock=0
            while len(done)<n:
                for u in sorted(waiting):
                    if deps[u]<=done:running[u]=clock+duration[u];waiting.remove(u)
                clock=min(running.values())
                finished=[u for u,t in running.items() if t==clock]
                for u in finished:done.add(u);del running[u]
            inp=str(n)+'\n'+''.join(f'{u} {duration[u]} '+' '.join(map(str,sorted(deps[u])+[0]))+'\n' for u in range(1,n+1))
            put(inp,clock)
        put('3\n1 100 0\n2 1 0\n3 1 0\n',100,'最晚结束不是最后编号')
        n=10000;put(str(n)+'\n1 100 0\n'+''.join(f'{u} 100 {u-1} 0\n' for u in range(2,n+1)),n*100,'最大长度依赖链')
    elif pid in {'P1137','P3183','P4017'}:
        for _ in range(160):
            n=rng.randrange(2,10);_,edges=random_dag(rng,n);graph=[[] for _ in range(n+1)];indegree=[0]*(n+1)
            for u,v in edges:graph[u].append(v);indegree[v]+=1
            best=[1]*(n+1);paths=0
            def walk(u,length):
                nonlocal paths
                best[u]=max(best[u],length)
                if not graph[u]:paths+=int(pid!='P3183' or length>1)
                for v in graph[u]:walk(v,length+1)
            if pid=='P1137':
                for u in range(1,n+1):walk(u,1)
                expected='\n'.join(map(str,best[1:]))
            else:
                for u in range(1,n+1):
                    if not indegree[u]:walk(u,1)
                expected=paths if pid=='P3183' else paths%80112002
            # P4017 has m>=1 in its stated input range.
            if pid=='P4017' and not edges:continue
            put(graph_text(n,edges),expected)
        if pid=='P4017':
            width,layers=10,40;n=width*layers+1;edges=[]
            for level in range(layers-1):
                edges.extend((level*width+i+1,(level+1)*width+j+1) for i in range(width) for j in range(width))
            edges.extend(((layers-1)*width+i+1,n) for i in range(width))
            put(graph_text(n,edges),pow(width,layers,80112002),'大量合流路径与取模')
            put('3 1\n1 2\n',2,'单独物种按两端定义计数')
        else:
            n=100000;put(graph_text(n,[(u,u+1) for u in range(1,n)]),'\n'.join(map(str,range(1,n+1))) if pid=='P1137' else 1,'最大结点数长链')
            if pid=='P3183':put('5 0\n',0,'全孤立物种排除')
    elif pid=='P2712':
        for _ in range(150):
            n=rng.randrange(1,9);positions=rng.sample(range(501),n);watch=[]
            for i in range(n):watch.append([x for x in positions+[500-positions[i]] if rng.randrange(4)==0])
            # Deduplicate the location list without changing the model.
            watch=[list(dict.fromkeys(row)) for row in watch]
            @lru_cache(None)
            def remaining(mask):
                answer=mask.bit_count()
                for i,x in enumerate(positions):
                    if mask>>i&1 and not any(j!=i and mask>>j&1 and x in watch[j] for j in range(n)):
                        answer=min(answer,remaining(mask^(1<<i)))
                return answer
            result=remaining((1<<n)-1)
            inp=str(n)+'\n'+''.join(f'{x} {len(watch[i])} '+' '.join(map(str,watch[i]))+'\n' for i,x in enumerate(positions))
            put(inp,'YES' if not result else result)
        put('4\n0 0\n1 1 2\n2 2 1 3\n3 0\n',3,'环与受阻后继都留下')
        put('1\n0 2 0 500\n','YES','自我监视和普通位置不阻碍')
    elif pid=='P7113':
        for _ in range(130):
            n=rng.randrange(2,11);m=rng.randrange(1,min(4,n)+1);order=list(range(m+1,n+1));rng.shuffle(order);order=list(range(1,m+1))+order
            graph=[[] for _ in range(n+1)]
            for at,u in enumerate(order):
                if at+1>=len(order):continue
                candidates=[v for v in order[at+1:] if v>m];rng.shuffle(candidates);graph[u]=candidates[:rng.randrange(min(5,len(candidates))+1)]
            inp=f'{n} {m}\n'+''.join(str(len(graph[u]))+' '+' '.join(map(str,graph[u]))+'\n' for u in range(1,n+1))
            put(inp,water_answers(n,graph,m))
        # Three sources, eleven divisions each: the joint denominator can exceed
        # signed 64 bits. Spare outlets stop immediately, so literal paths stay small.
        graph=[[] for _ in range(39)];common=34;spare=[35,36,37,38]
        for source,d in zip([1,2,3],[4,3,5]):
            chain=[source]+list(range(4+(source-1)*10,4+source*10))+[common]
            for u,v in zip(chain,chain[1:]):graph[u]=[v]+spare[:d-1]
        inp='38 3\n'+''.join(str(len(graph[u]))+' '+' '.join(map(str,graph[u]))+'\n' for u in range(1,39))
        expected=water_answers(38,graph,3)
        assert any(int(line.split()[1])>2**63-1 for line in expected.splitlines())
        put(inp,expected,'十一层均分与超过六十四位公分母')
        put('3 1\n0\n1 3\n0\n','1 1\n0 1\n','无水源仍要解锁其下游')
    elif pid=='P10166':
        for _ in range(140):
            n=rng.randrange(2,7);_,edges=random_dag(rng,n)
            if rng.randrange(3)==0:edges=[(u,v) for u in range(1,n+1) for v in range(1,n+1) if u!=v and rng.randrange(4)==0]
            candidates=[(u,v) for u in range(1,n+1) for v in range(1,n+1) if u!=v and (u,v) not in edges]
            rng.shuffle(candidates)
            while len(edges)<n-1:edges.append(candidates.pop())
            weight=[0]+[rng.randrange(1,30) for _ in range(n)];existing=set(edges);best=10**9
            # Enumerate every simple cycle itself; charge exactly its absent edges.
            for length in range(2,n+1):
                for group in itertools.combinations(range(1,n+1),length):
                    for tail in itertools.permutations(group[1:]):
                        cycle=(group[0],)+tail;cost=sum(weight[u]+weight[v] for u,v in zip(cycle,cycle[1:]+cycle[:1]) if (u,v) not in existing)
                        best=min(best,cost)
            put(f'{n} {len(edges)}\n'+' '.join(map(str,weight[1:]))+'\n'+''.join(f'{u} {v}\n' for u,v in edges),best)
        put('6 5\n1 2 100 100 100 100\n3 4\n3 5\n3 6\n4 5\n4 6\n',6,'两个孤立便宜点优于补一边')
        put('3 2\n3 100 4\n1 2\n2 3\n',7,'最便宜端点隔多条原边')
        n=500000;put(f'{n} {n-1}\n'+'1000000000 '*n+'\n'+''.join(f'{u} {u+1}\n' for u in range(1,n)),2000000000,'最大深度无递归与宽费用')
    elif pid=='CF1361A':
        from core7_checkers_topology import blogs_match
        for _ in range(140):
            n=rng.randrange(1,8);edges=[(u,v) for u in range(1,n+1) for v in range(u+1,n+1) if rng.randrange(3)==0]
            if rng.randrange(2):
                order=list(range(1,n+1));rng.shuffle(order);topic=[0]*n;written=set()
                for u in order:
                    used={topic[v-1] for a,b in edges for v in [b if a==u else a] if u in (a,b) and v in written};mex=1
                    while mex in used:mex+=1
                    topic[u-1]=mex;written.add(u)
            else:topic=[rng.randrange(1,n+1) for _ in range(n)]
            solution=next((p for p in itertools.permutations(range(1,n+1)) if blogs_match(n,edges,topic,p)),None)
            put(graph_text(n,edges)+' '.join(map(str,topic))+'\n',' '.join(map(str,solution)) if solution else '-1')
        n=500000;edges=''.join(f'1 {u}\n' for u in range(2,n+1))
        put(f'{n} {n-1}\n'+edges+'2 '+'1 '*(n-1)+'\n','possible','最大星形主题去重')
        put('4 3\n1 2\n1 3\n1 4\n3 1 1 1\n','-1','邻居数量够但缺主题二')
    elif pid=='P1038':
        for _ in range(150):
            n=rng.randrange(2,11);_,edges=random_dag(rng,n);weighted=[(u,v,rng.randrange(-10,11)) for u,v in edges]
            incoming=[[] for _ in range(n+1)];outdegree=[0]*(n+1)
            for u,v,w in weighted:incoming[v].append((u,w));outdegree[u]+=1
            initial=[0]+[rng.randrange(6) if not incoming[u] else 0 for u in range(1,n+1)];threshold=[0]+[rng.randrange(11) for _ in range(n)]
            @lru_cache(None)
            def state(u):return initial[u] if not incoming[u] else sum(max(0,state(v))*w for v,w in incoming[u])-threshold[u]
            answer=''.join(f'{u} {state(u)}\n' for u in range(1,n+1) if not outdegree[u] and state(u)>0) or 'NULL\n'
            inp=f'{n} {len(weighted)}\n'+''.join(f'{initial[u]} {threshold[u]}\n' for u in range(1,n+1))+''.join(f'{u} {v} {w}\n' for u,v,w in weighted)
            put(inp,answer)
        n=100;put(f'{n} {n-1}\n1 0\n'+'0 0\n'*(n-1)+''.join(f'{u} {u+1} 1000000000\n' for u in range(1,n)),f'{n} '+str(10**(9*(n-1)))+'\n','连续乘积超出固定宽度')
        put('4 3\n5 100\n6 100\n0 0\n0 0\n1 3 1\n2 3 -1\n3 4 2\n','NULL\n','负贡献抵消后不可提前传播')
        put('2 1\n0 123\n0 0\n1 2 1\n','NULL\n','零状态输入仍是输入层')
    elif pid=='P3243':
        rows=[]
        for _ in range(150):
            n=rng.randrange(2,8);_,edges=random_dag(rng,n)
            if rng.randrange(5)==0:edges+=[(1,2),(2,1)]
            if edges and rng.randrange(3)==0:edges.append(rng.choice(edges))
            orders=all_orders(n,edges)
            best=min(orders,key=lambda p:tuple(p.index(u) for u in range(1,n+1))) if orders else None
            rows.append((graph_text(n,edges),' '.join(map(str,best)) if best else 'Impossible!'))
        rows.extend([('3 1\n3 1\n','3 1 2'),('4 2\n3 1\n4 1\n','3 4 1 2')])
        for at in range(0,len(rows),3):
            group=rows[at:at+3];put(str(len(group))+'\n'+''.join(x for x,_ in group),'\n'.join(y for _,y in group))
        n=100000;put('1\n'+graph_text(n,[(u,u+1) for u in range(1,n)]),' '.join(map(str,range(1,n+1))),'最大深度反向堆')
    elif pid=='P3627':
        for _ in range(130):
            n=rng.randrange(2,9);edges=[(u,v) for u in range(1,n+1) for v in range(1,n+1) if u!=v and rng.randrange(5)==0]
            graph=[[] for _ in range(n)]
            for u,v in edges:graph[u-1].append(v-1)
            money=[rng.randrange(11) for _ in range(n)];start=rng.randrange(n);bars=set(rng.sample(range(n),rng.randrange(1,n+1)));bars.add(start)
            seen={(start,1<<start)};queue=deque(seen);answer=0
            while queue:
                u,mask=queue.popleft()
                if u in bars:answer=max(answer,sum(money[v] for v in range(n) if mask>>v&1))
                for v in graph[u]:
                    state=v,mask|1<<v
                    if state not in seen:seen.add(state);queue.append(state)
            inp=graph_text(n,edges)+'\n'.join(map(str,money))+f'\n{start+1} {len(bars)}\n'+' '.join(str(u+1) for u in sorted(bars))+'\n'
            put(inp,answer)
        put('4 3\n1 2\n2 1\n3 4\n5\n6\n4000\n4000\n1 2\n1 4\n',11,'可重复回酒吧但不可取不可达现金')
        n=500000;put(graph_text(n,[(u,u+1) for u in range(1,n)])+'4000\n'*n+f'1 1\n{n}\n',n*4000,'五十万层显式栈')
    elif pid=='P8269':
        for _ in range(140):
            n=rng.randrange(2,8);to=[rng.choice([v for v in range(n) if v!=u]) for u in range(n)];value=[rng.randrange(21) for _ in range(n)];answer=0
            for order in itertools.permutations(range(n)):
                left=[False]*n;total=0
                for u in order:
                    if not left[to[u]]:left[u]=True;total+=value[u]
                answer=max(answer,total)
            put(str(n)+'\n'+''.join(f'{to[u]+1} {value[u]}\n' for u in range(n)),answer)
        n=100000;put(str(n)+'\n'+''.join(f'{u%n+1} 1000000000\n' for u in range(1,n+1)),(n-1)*10**9,'十万环与六十四位总收益')
        put('6\n2 0\n1 5\n4 1\n3 8\n6 2\n5 9\n',22,'多个独立环与零收益')
    elif pid=='P11022':
        for _ in range(140):
            n=rng.randrange(2,9);edges=[(u,v) for u in range(1,n+1) for v in range(u+1,n+1) if rng.randrange(4)==0]
            put('1\n'+graph_text(n,edges),'Enumerate every simple path up to two')
        put('1\n4 4\n1 2\n2 3\n3 1\n3 4\n','Enumerate every simple path up to two','桥边可以被两条路径共用')
        n=200000
        models=[([(u,u+1) for u in range(1,n)]+[(n,1)],{'possible':True,'groups':[]},'大环任意非单色合法'),
                ([(1,2),(2,3),(3,1)]+[(u,u+1) for u in range(3,n)],{'possible':True,'groups':[list(range(3,n+1))]},'三角形挂最长桥链'),
                ([(u,u+1) for u in range(1,n)],{'possible':False},'长树必须无解')]
        for edges,model,label in models:put('1\n'+graph_text(n,edges),json.dumps({'0':model}),label)
    elif pid=='CF1385E':
        from core7_checkers_topology import acyclic
        rows=[]
        for _ in range(160):
            n=rng.randrange(2,7);pairs=list(itertools.combinations(range(1,n+1),2));rng.shuffle(pairs);pairs=pairs[:rng.randrange(1,min(8,len(pairs))+1)];edges=[]
            for u,v in pairs:
                if rng.randrange(2):u,v=v,u
                edges.append((rng.randrange(2),u,v))
            fixed=[(u,v) for t,u,v in edges if t];free=[(u,v) for t,u,v in edges if not t]
            possible=any(acyclic(n,fixed+[(v,u) if mask>>i&1 else (u,v) for i,(u,v) in enumerate(free)]) for mask in range(1<<len(free)))
            inp=f'{n} {len(edges)}\n'+''.join(f'{t} {u} {v}\n' for t,u,v in edges);rows.append((inp,'YES' if possible else 'NO'))
        for at in range(0,len(rows),8):
            group=rows[at:at+8];put(str(len(group))+'\n'+''.join(x for x,_ in group),'\n'.join(y for _,y in group))
        n=200000;put(f'1\n{n} {n-1}\n'+''.join(f'{u%2} {u} {u+1}\n' for u in range(1,n)),'YES','最大深度定向')
    else:raise ValueError(pid)
    return cases
