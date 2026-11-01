"""Small explicit graphs, enumerated assignments/trees and literal operations."""
from collections import deque
import itertools
import math
import random

IDS={'P1536','CF1263D','P1656','P2256','P3420','P10378','UVA10369','CF1365D','P1196','P1621','P2294','P2916','P7073','P7991','P13308','P16495','UVA1395','CF1624G'}

def labels(n,edges):
    graph=[[] for _ in range(n)]
    for u,v in edges:graph[u].append(v);graph[v].append(u)
    result=[-1]*n;count=0
    for start in range(n):
        if result[start]>=0:continue
        result[start]=count;todo=[start]
        for u in todo:
            for v in graph[u]:
                if result[v]<0:result[v]=count;todo.append(v)
        count+=1
    return result,count

def road_input(n,edges):
    return f'{n} {len(edges)}\n'+''.join(f'{u+1} {v+1}\n' for u,v in edges)

def tree_choices(n,edges):
    for chosen in itertools.combinations(range(len(edges)),n-1):
        if labels(n,[(edges[i][0],edges[i][1]) for i in chosen])[1]==1:yield chosen

def cases_for(pid):
    rng=random.Random(2026103018);cases=[]
    def put(inp,out):
        cases.append((f'独立图/操作校验 {len(cases)+1}',str(inp),str(out)))
    def batched(rows,size=100):
        for start in range(0,len(rows),size):
            part=rows[start:start+size];put(str(len(part))+'\n'+''.join(x for x,y in part),'\n'.join(str(y) for x,y in part)+'\n')

    if pid=='P1536':
        for _ in range(220):
            blocks=[];answers=[]
            for _ in range(rng.randint(1,8)):
                n=rng.randint(1,15);edges=[(rng.randrange(n),rng.randrange(n)) for _ in range(rng.randrange(50))]
                blocks.append(road_input(n,edges));answers.append(str(labels(n,edges)[1]-1))
            put(''.join(blocks)+'0\n','\n'.join(answers))
        put('999 0\n0\n',998)
    elif pid=='CF1263D':
        for _ in range(300):
            words=[''.join(rng.choice('abcdef') for _ in range(rng.randint(1,12))) for _ in range(rng.randint(1,25))]
            edges=[(i,j) for i in range(len(words)) for j in range(i) if set(words[i])&set(words[j])]
            put(str(len(words))+'\n'+'\n'.join(words),labels(len(words),edges)[1])
        put('200000\n'+''.join(chr(97+i%26)+'\n' for i in range(200000)),26)
    elif pid=='P1656':
        graphs=[]
        for n in range(2,5):
            possible=list(itertools.combinations(range(n),2))
            for mask in range(1<<len(possible)):
                edges=[e for i,e in enumerate(possible) if mask>>i&1]
                if labels(n,edges)[1]==1:graphs.append((n,edges))
        for _ in range(220):
            n=rng.randint(2,12);edges=[(v,rng.randrange(v)) for v in range(1,n)]
            for e in itertools.combinations(range(n),2):
                if e not in edges and e[::-1] not in edges and rng.random()<.15:edges.append(e)
            graphs.append((n,edges))
        graphs.extend([(150,[(i,i+1) for i in range(149)]),(150,[(i,(i+1)%150) for i in range(150)])])
        for n,edges in graphs:
            answer=sorted(tuple(sorted((u+1,v+1))) for i,(u,v) in enumerate(edges) if labels(n,edges[:i]+edges[i+1:])[1]>1)
            put(road_input(n,edges),''.join(f'{u} {v}\n' for u,v in answer))
    elif pid=='P2256':
        for _ in range(220):
            n=rng.randint(2,25);names=[f'Person{i:014d}' for i in range(n)]
            edges=[tuple(rng.sample(range(n),2)) for _ in range(rng.randint(1,70))]
            group,_=labels(n,edges);queries=[(rng.randrange(n),rng.randrange(n)) for _ in range(60)]
            inp=f'{n} {len(edges)}\n'+'\n'.join(names)+'\n'+''.join(f'{names[u]} {names[v]}\n' for u,v in edges)+str(len(queries))+'\n'+''.join(f'{names[u]} {names[v]}\n' for u,v in queries)
            put(inp,'\n'.join('Yes.' if group[u]==group[v] else 'No.' for u,v in queries))
    elif pid=='P3420':
        mappings=[]
        for n in range(1,5):mappings.extend(itertools.product(range(n),repeat=n))
        for _ in range(140):
            n=rng.randint(5,8);mappings.append(tuple(rng.randrange(n) for _ in range(n)))
        for where in mappings:
            n=len(where);answer=n
            for mask in range(1<<n):
                if mask.bit_count()>=answer:continue
                opened=mask
                while True:
                    changed=opened
                    for i,container in enumerate(where):
                        if opened>>container&1:changed|=1<<i
                    if changed==opened:break
                    opened=changed
                if opened==(1<<n)-1:answer=mask.bit_count()
            put(str(n)+'\n'+'\n'.join(str(x+1) for x in where),answer)
        n=10**6;put(str(n)+'\n'+'\n'.join(str((i+1)%n+1) for i in range(n)),1)
    elif pid=='P10378':
        for _ in range(260):
            n=rng.randint(2,10);school=[rng.randrange(2) for i in range(n)];school[0]=0;school[1]=1
            possible=[(u,v) for u in range(n) for v in range(u) if school[u]!=school[v]]
            edges=rng.choices(possible,k=rng.randint(1,max(1,len(possible)*2)))
            counts=[mask.bit_count() for mask in range(1<<n) if all(((mask>>u)^(mask>>v))&1 for u,v in edges)]
            put(road_input(n,edges),f'{min(counts)} {max(counts)}')
    elif pid=='UVA10369':
        rows=[]
        for _ in range(240):
            n=rng.randint(2,9);s=rng.randint(1,n-1);points=[(rng.randrange(20),rng.randrange(20)) for _ in range(n)]
            pairs=[((x-u)**2+(y-v)**2,i,j) for i,(x,y) in enumerate(points) for j,(u,v) in enumerate(points[:i])]
            for threshold in sorted(set(w for w,u,v in pairs)):
                if labels(n,[(u,v) for w,u,v in pairs if w<=threshold])[1]<=s:break
            inp=f'{s} {n}\n'+''.join(f'{x} {y}\n' for x,y in points)
            rows.append((inp,f'{math.sqrt(threshold):.2f}'))
        batched(rows)
        put('1\n1 2\n0 0\n10000 10000\n',f'{math.sqrt(2*10**8):.2f}')
    elif pid=='CF1365D':
        def possible(rows):
            h=len(rows);w=len(rows[0]);empty=[(r,c) for r in range(h) for c in range(w) if rows[r][c]=='.']
            for mask in range(1<<len(empty)):
                blocked={p for i,p in enumerate(empty) if mask>>i&1}
                seen=set();todo=[]
                if (h-1,w-1) not in blocked:seen.add((h-1,w-1));todo=[(h-1,w-1)]
                for r,c in todo:
                    for nr,nc in [(r+1,c),(r-1,c),(r,c+1),(r,c-1)]:
                        if 0<=nr<h and 0<=nc<w and rows[nr][nc]!='#' and (nr,nc) not in blocked and (nr,nc) not in seen:seen.add((nr,nc));todo.append((nr,nc))
                if all((rows[r][c]!='G' or (r,c) in seen) and (rows[r][c]!='B' or (r,c) not in seen) for r in range(h) for c in range(w)):return True
            return False
        grids=[]
        for chars in itertools.product('.#GB',repeat=3):grids.append([''.join(chars[:2]),chars[2]+'.'])
        for _ in range(360):
            h=rng.randint(1,3);w=rng.randint(1,3);grid=[[rng.choice('.#GB') for c in range(w)] for r in range(h)];grid[-1][-1]='.';grids.append([''.join(row) for row in grid])
        batched([(f'{len(g)} {len(g[0])}\n'+'\n'.join(g)+'\n','Yes' if possible(g) else 'No') for g in grids])
    elif pid=='P1196':
        for _ in range(220):
            n=24;queues=[[i] for i in range(1,n+1)];commands=[];answers=[]
            for _ in range(120):
                if len(queues)>1 and rng.random()<.42:
                    a,b=rng.sample(range(len(queues)),2);i=rng.choice(queues[a]);j=rng.choice(queues[b]);commands.append(f'M {i} {j}')
                    merged=queues[b]+queues[a];queues=[q for k,q in enumerate(queues) if k not in (a,b)]+[merged]
                else:
                    i,j=rng.sample(range(1,n+1),2);commands.append(f'C {i} {j}')
                    row=next(q for q in queues if i in q);answers.append(str(abs(row.index(i)-row.index(j))-1) if j in row else '-1')
            put(str(len(commands))+'\n'+'\n'.join(commands),'\n'.join(answers))
        commands=['C 1 2']+[f'M {i} {i+1}' for i in range(1,30000)]+['C 1 30000','C 1 2','C 29999 30000']
        put(str(len(commands))+'\n'+'\n'.join(commands),'-1\n29998\n0\n0')
    elif pid=='P1621':
        def legal(x,y,p):
            g=math.gcd(x,y);factor=2;largest=1
            while factor*factor<=g:
                if g%factor==0:
                    largest=max(largest,factor)
                    while g%factor==0:g//=factor
                factor+=1
            return max(largest,g)>=p
        for _ in range(300):
            a=rng.randint(1,40);b=rng.randint(max(a,2),a+15);p=rng.randint(2,b);numbers=list(range(a,b+1))
            edges=[(i,j) for i,x in enumerate(numbers) for j,y in enumerate(numbers[:i]) if legal(x,y,p)]
            put(f'{a} {b} {p}',labels(len(numbers),edges)[1])
        primes=sum(all(x%d for d in range(2,math.isqrt(x)+1)) for x in range(50001,100001))
        put('1 100000 2',primes+2)
    elif pid=='P2294':
        def consistent(n,equations):
            graph=[[] for i in range(n+1)]
            for a,b,v in equations:graph[a-1].append((b,v));graph[b].append((a-1,-v))
            values={}
            for start in range(n+1):
                if start in values:continue
                values[start]=0;todo=[start]
                for u in todo:
                    for v,difference in graph[u]:
                        expected=values[u]+difference
                        if v in values:
                            if values[v]!=expected:return False
                        else:values[v]=expected;todo.append(v)
            return True
        rows=[]
        for _ in range(1200):
            n=rng.randint(1,8);prefix=[rng.randint(-10**9,10**9) for i in range(n+1)];equations=[]
            for j in range(rng.randint(1,25)):
                a=rng.randint(1,n);b=rng.randint(a,n);v=prefix[b]-prefix[a-1]
                if rng.random()<.08:v+=rng.choice([-1,1])
                equations.append((a,b,v))
            rows.append((f'{n} {len(equations)}\n'+''.join(f'{a} {b} {v}\n' for a,b,v in equations),'true' if consistent(n,equations) else 'false'))
        batched(rows,50)
    elif pid=='P2916':
        for _ in range(180):
            n=rng.randint(5,6);points=list(itertools.combinations(range(n),2));rng.shuffle(points)
            edges=[(u,v,rng.randrange(9)) for u,v in points[:rng.randint(n-1,min(9,len(points)))]]
            if labels(n,[(u,v) for u,v,w in edges])[1]!=1:continue
            cost=[rng.randint(1,20) for _ in range(n)];answer=10**30
            for chosen in tree_choices(n,edges):
                graph=[[] for i in range(n)]
                for i in chosen:
                    u,v,w=edges[i];graph[u].append((v,w));graph[v].append((u,w))
                def walk(u,parent):
                    total=cost[u]
                    for v,w in graph[u]:
                        if v!=parent:total+=w+walk(v,u)+w+cost[u]
                    return total
                answer=min(answer,min(walk(start,-1) for start in range(n)))
            put(f'{n} {len(edges)}\n'+'\n'.join(map(str,cost))+'\n'+''.join(f'{u+1} {v+1} {w}\n' for u,v,w in edges),answer)
    elif pid=='P7073':
        def tokens(tree):
            if tree[0]=='v':return ['x'+str(tree[1])]
            if tree[0]=='!':return tokens(tree[1])+['!']
            return tokens(tree[1])+tokens(tree[2])+[tree[0]]
        def evaluate(tree,values):
            if tree[0]=='v':return values[tree[1]-1]
            if tree[0]=='!':return 1-evaluate(tree[1],values)
            a=evaluate(tree[1],values);b=evaluate(tree[2],values)
            return a&b if tree[0]=='&' else a|b
        for _ in range(300):
            n=rng.randint(2,12);parts=[('v',i) for i in range(1,n+1)];rng.shuffle(parts)
            while len(parts)>1:
                a=parts.pop(rng.randrange(len(parts)));b=parts.pop(rng.randrange(len(parts)));node=(rng.choice('&|'),a,b)
                if rng.randrange(3)==0:node=('!',node)
                parts.append(node)
            tree=parts[0];values=[rng.randrange(2) for i in range(n)];queries=list(range(1,n+1))+[rng.randint(1,n) for i in range(8)];answers=[]
            for x in queries:
                changed=values[:];changed[x-1]^=1;answers.append(str(evaluate(tree,changed)))
            put(' '.join(tokens(tree))+f'\n{n}\n'+' '.join(map(str,values))+f'\n{len(queries)}\n'+'\n'.join(map(str,queries)),'\n'.join(answers))
        n=100000;expression='x1 '+ ' '.join(f'x{i} &' for i in range(2,n+1));assert len(expression)<=10**6
        put(expression+f'\n{n}\n'+'1 '*n+f'\n{n}\n'+'\n'.join(map(str,range(1,n+1))),'0\n'*n)
        put('x1 x2 &'+' !'*399999+'\n2\n1 1\n2\n1\n2\n','1\n1')
    elif pid=='P7991':
        rows=[]
        for _ in range(260):
            n=rng.randint(2,7);possible=list(itertools.combinations(range(n),2));edges=[e for e in possible if rng.random()<.2]
            answer=0 if labels(n,edges)[0][0]==labels(n,edges)[0][-1] else 10**30
            for count in [1,2]:
                for additions in itertools.combinations(possible,count):
                    cost=sum((u-v)**2 for u,v in additions)
                    if cost>=answer:continue
                    group,_=labels(n,edges+list(additions))
                    if group[0]==group[-1]:answer=cost
            rows.append((road_input(n,edges),answer))
        batched(rows,20)
        n=100000;d=n-1;put(f'1\n{n} 0\n',(d//2)**2+(d-d//2)**2)
    elif pid=='P13308':
        for _ in range(280):
            n=rng.randint(2,6);last=(1<<n)-1;deleted=set();ops=[];answer=0
            for _ in range(rng.randint(1,80)):
                kind=rng.choice([1,2,2]);u=rng.randint(1,last);ops.append((kind,u))
                if kind==1:
                    if u!=1:deleted.add(u)
                else:
                    seen={u};todo=[u]
                    for x in todo:
                        neighbors=([x//2] if x!=1 and x not in deleted else [])+[v for v in [2*x,2*x+1] if v<=last and v not in deleted]
                        for v in neighbors:
                            if v not in seen:seen.add(v);todo.append(v)
                    answer^=len(seen)
            put(f'{n} {len(ops)}\n'+''.join(f'{k} {u}\n' for k,u in ops),answer)
        n=60;total=(1<<n)-1;ops=[(2,1)];answer=total
        for i in range(100000):
            leaf=(1<<59)+i;ops.append((1,leaf))
            if i%3==0:ops.append((1,leaf))
            ops.append((2,1));answer^=total-i-1
        put(f'{n} {len(ops)}\n'+''.join(f'{k} {u}\n' for k,u in ops),answer)
        put('4 8\n2 1\n1 5\n2 10\n1 10\n2 5\n1 5\n1 1\n2 1\n',15^3^2^12)
    elif pid=='P16495':
        sequences=[(2,seq) for seq in itertools.product(range(4),repeat=4)]
        sequences.extend((1,seq) for seq in itertools.product(range(2),repeat=6))
        for _ in range(220):
            n=rng.randint(1,6);sequences.append((n,[rng.randrange(1<<n) for _ in range(rng.randint(1,20))]))
        for n,seq in sequences:
            answer=[]
            for end in range(1,len(seq)+1):
                edges=[(i,j) for i in range(end) for j in range(i) if seq[i]|seq[j]!=(1<<n)-1]
                answer.append(str(labels(end,edges)[1]))
            put(f'{n} {len(seq)}\n'+'\n'.join(map(str,seq)),'\n'.join(answer))
        q=500000;put(f'60 {q}\n'+'0\n'*q,'1\n'*q)
        q=2000;put(f'60 {q}\n'+str((1<<60)-1)+'\n'+(str((1<<60)-1)+'\n')*(q-1),'\n'.join(map(str,range(1,q+1))))
    elif pid in ['UVA1395','CF1624G']:
        rows=[]
        for _ in range(300):
            n=rng.randint(3 if pid=='CF1624G' else 2,6);possible=list(itertools.combinations(range(n),2));rng.shuffle(possible)
            pairs=possible[:rng.randint(0,min(9,len(possible)))];edges=[(u,v,rng.randint(1,31)) for u,v in pairs];best=None
            for chosen in tree_choices(n,edges):
                weights=[edges[i][2] for i in chosen]
                if pid=='UVA1395':value=max(weights)-min(weights)
                else:
                    value=0
                    for w in weights:value|=w
                best=value if best is None else min(best,value)
            if pid=='CF1624G' and best is None:continue
            inp=f'{n} {len(edges)}\n'+''.join(f'{u+1} {v+1} {w}\n' for u,v,w in edges)
            if pid=='UVA1395':put(inp+'0 0\n',-1 if best is None else best)
            else:rows.append((inp,best))
        if pid=='CF1624G':
            rows.append(('3 3\n1 2 3\n2 3 4\n1 3 4\n',4));rows.append(('3 2\n1 2 1000000000\n2 3 536870912\n',1000000000|536870912));batched(rows)
    else:raise ValueError(pid)
    return cases
