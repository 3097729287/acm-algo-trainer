"""Literal deletions, partitions, game trees and complete operation graphs."""
from collections import deque
from fractions import Fraction
from itertools import combinations,permutations,product
from math import comb,factorial
import random
import string

IDS={'P12593','P2622','AT_abc359_d','P1441','P2210','P5911','P10865','P1450','P2167','P2473','P2831','P3694','P3786','P3947','P4928','P7296','P9017','CF11D'}


def deletion_permutations(n,edges):
    best=10**30
    for order in permutations(range(n)):
        remaining=set(range(n));value=0
        for u in order:
            weights=[w for a,b,w in edges if (a==u and b in remaining) or (b==u and a in remaining)]
            value+=len(weights)*sum(weights);remaining.remove(u)
        best=min(best,value)
    return best


def light_states(effects):
    n=len(effects[0]);start=(1,)*n;distance={start:0};todo=deque([start])
    while todo:
        state=todo.popleft()
        if not any(state):return distance[state]
        for effect in effects:
            nxt=tuple(0 if x==1 else 1 if x==-1 else state[i] for i,x in enumerate(effect))
            if nxt not in distance:distance[nxt]=distance[state]+1;todo.append(nxt)
    return -1


def palindrome_replacements(s,k):
    holes=[i for i,c in enumerate(s) if c=='?'];count=0
    for chosen in product('AB',repeat=len(holes)):
        word=list(s)
        for i,c in zip(holes,chosen):word[i]=c
        count+=all(word[i:i+k]!=list(reversed(word[i:i+k])) for i in range(len(word)-k+1))
    return count


def retained_weight_subsets(weights,removed_count):
    best=0;n=len(weights)
    for removed in combinations(range(n),removed_count):
        rest=[i for i in range(n) if i not in removed];sums=set()
        for size in range(1,len(rest)+1):
            for chosen in combinations(rest,size):sums.add(sum(weights[i] for i in chosen))
        best=max(best,len(sums))
    return best


def cow_arrangements(n,edges):
    best=10**9
    for order in permutations(range(n)):
        position=[0]*n
        for i,u in enumerate(order):position[u]=i
        best=min(best,sum(abs(position[u]-position[v]) for u,v in edges))
    return best


def bridge_partitions(times,weights,capacity):
    best=sum(times);groups=[]
    def place(i):
        nonlocal best
        if i==len(times):best=min(best,sum(t for w,t in groups));return
        for at in range(len(groups)):
            w,t=groups[at]
            if w+weights[i]<=capacity:
                groups[at]=(w+weights[i],max(t,times[i]));place(i+1);groups[at]=(w,t)
        groups.append((weights[i],times[i]));place(i+1);groups.pop()
    place(0);return best


def bomb_literal(height,width,points,counts):
    # All grid cells are possible centers; no production candidate reduction.
    actions=[tuple(i for i,(x,y) in enumerate(points) if abs(x-a)+abs(y-b)<=1) for a in range(height) for b in range(width)]
    actions=[a for a in actions if a];todo=deque([tuple(counts)]);distance={tuple(counts):0}
    while todo:
        state=todo.popleft()
        if not any(state):return distance[state]
        for action in actions:
            nxt=list(state)
            for i in action:nxt[i]=max(0,nxt[i]-1)
            nxt=tuple(nxt)
            if nxt not in distance:distance[nxt]=distance[state]+1;todo.append(nxt)
    raise AssertionError('Each fish cell itself can be bombed')


def coin_vectors(coins,limits,target):
    return sum(sum(c*x for c,x in zip(coins,counts))==target for counts in product(*(range(d+1) for d in limits)))


def matching_words(patterns,k):
    # Letters absent from every fixed position have identical behavior. Use one
    # literal representative with its exact multiplicity, still enumerate words.
    letters=sorted(set(''.join(patterns))-{'?'});other=next(c for c in string.ascii_lowercase if c not in letters);alphabet=letters+[other];multiplier=26-len(letters);answer=0
    for word in product(alphabet,repeat=len(patterns[0])):
        matches=sum(all(p=='?' or p==c for p,c in zip(pattern,word)) for pattern in patterns)
        if matches==k:answer+=multiplier**word.count(other)
    return answer%1000003


def reward_tree(throws,scores,prerequisites,eaten=frozenset()):
    if not throws:return Fraction(0)
    total=Fraction(0)
    for item in range(len(scores)):
        skip=reward_tree(throws-1,scores,prerequisites,eaten)
        if prerequisites[item]<=eaten:
            take=scores[item]+reward_tree(throws-1,scores,prerequisites,eaten|{item});total+=max(skip,take)
        else:total+=skip
    return total/len(scores)


def bird_fraction_cover(points):
    n=len(points);covers={frozenset([i]) for i in range(n)}
    for i,j in combinations(range(n),2):
        x,y=points[i];xx,yy=points[j]
        if x==xx:continue
        a=(Fraction(y,x)-Fraction(yy,xx))/(x-xx);b=Fraction(y,x)-a*x
        if a<0:covers.add(frozenset(k for k,(u,v) in enumerate(points) if a*u*u+b*u==v))
    start=frozenset();todo=deque([start]);distance={start:0};full=frozenset(range(n))
    while todo:
        state=todo.popleft()
        if state==full:return distance[state]
        for cover in covers:
            nxt=state|cover
            if nxt not in distance:distance[nxt]=distance[state]+1;todo.append(nxt)
    raise AssertionError(points)


def band_target_arrays(a,m):
    count=[a.count(j) for j in range(m)];best=len(a)
    for order in permutations(range(m)):
        target=[j for j in order for _ in range(count[j])];best=min(best,sum(x!=y for x,y in zip(a,target)))
    return best


def fruit_walks(height,width,total,start,melons,small_count):
    cells=height*width;positions=[{} for _ in range(total+1)];small_index=0
    for begin,end,small,track in melons:
        flag=1<<small_index if small else None
        if small:small_index+=1
        for t,p in zip(range(begin,end),track):positions[t][p]=flag
    assert small_index==small_count
    neighbors=[[v for v in range(cells) if abs(u//width-v//width)+abs(u%width-v%width)<=1] for u in range(cells)];best=10**9
    def walk(t,p,collected,moves):
        nonlocal best
        if p in positions[t]:
            flag=positions[t][p]
            if flag is None:return
            collected=collected|{flag}
        if t==total:
            if len(collected)==small_count:best=min(best,moves)
            return
        for q in neighbors[p]:walk(t+1,q,collected,moves+(p!=q))
    walk(1,start,frozenset(),0);return -1 if best==10**9 else best


def song_permutations(names,durations,open_time,target,deadline):
    if sum(durations)>deadline:return 'No Answer'
    best=-1;lex=None
    for order in permutations(range(len(names))):
        elapsed=score=0
        for j in order:elapsed+=durations[j];score+=max(0,open_time[j]-elapsed)
        words=tuple(names[j] for j in order)
        if score>best or score==best and (lex is None or words<lex):best=score;lex=words
    return 'No Answer' if best<target else str(best)+'\n'+'\n'.join(lex)


def clothes_sequences(colors,wash,weather):
    available=[1]*len(colors);best=None
    def choose(day,value):
        nonlocal best
        if day>len(weather):best=value if best is None else max(best,value);return
        for i in range(len(colors)):
            if available[i]<=day:
                old=available[i];available[i]=day+wash[i]+1;choose(day+1,value+colors[i]*weather[day-1]);available[i]=old
    choose(1,0);return 'gcd loves her clothes!' if best is None else best


def alphabet_orders(text):
    letters=sorted(set(text));best=len(text)
    for order in permutations(letters):
        where={c:i for i,c in enumerate(order)};songs=1;cursor=-1
        for c in text:
            at=where[c]
            if at<=cursor:songs+=1
            cursor=at
        best=min(best,songs)
    return best


def switch_distances(n):
    # Reverse BFS of the literal (lights,switches) graph, not an effect-mask DP.
    states=1<<n;dist=[-1]*(states*states);todo=deque()
    for switches in range(states):dist[switches]=0;todo.append(switches)
    while todo:
        code=todo.popleft();lights,switches=divmod(code,states)
        after_toggle=(switches>>1)|((switches&1)<<(n-1));old_lights=lights^after_toggle
        for bit in range(n):
            old_code=old_lights*states+(after_toggle^(1<<bit))
            if dist[old_code]<0:dist[old_code]=dist[code]+1;todo.append(old_code)
    assert min(dist)>=0
    return dist


def cycle_edge_sets(n,edges):
    answer=0
    for count in range(3,len(edges)+1):
        for chosen in combinations(edges,count):
            degree=[0]*n;graph=[[] for _ in range(n)]
            for u,v in chosen:degree[u]+=1;degree[v]+=1;graph[u].append(v);graph[v].append(u)
            active={u for u in range(n) if degree[u]}
            if any(degree[u]!=2 for u in active):continue
            todo=[next(iter(active))];seen=set(todo)
            for u in todo:
                for v in graph[u]:
                    if v not in seen:seen.add(v);todo.append(v)
            answer+=seen==active
    return answer


def cases_for(pid):
    rng=random.Random(20261103+sum(map(ord,pid)));result=[]
    def put(inp,out):result.append((f'{pid}-literal-{len(result)+1}',inp,str(out).rstrip()+'\n'))
    def row(values):return ' '.join(map(str,values))+'\n'
    def graph_lines(edges):return ''.join(f'{u+1} {v+1}'+(f' {rest[0]}' if rest else '')+'\n' for u,v,*rest in edges)
    if pid=='P12593':
        for _ in range(180):
            n=rng.randint(1,7);edges=[(rng.randrange(v),v,rng.randint(1,1000000000)) for v in range(1,n)];used={tuple(sorted(e[:2])) for e in edges}
            for e in combinations(range(n),2):
                if e not in used and rng.randrange(3)==0:edges.append((*e,rng.randint(1,1000000000)))
            rng.shuffle(edges);put(f'{n} {len(edges)}\n'+graph_lines(edges),deletion_permutations(n,edges))
        n=8;w=1000000000
        edges=[(u,v,w) for u,v in combinations(range(n),2)];put(f'{n} {len(edges)}\n'+graph_lines(edges),w*n*(n-1)*(2*n-1)//6)
        edges=[(u,u+1,w) for u in range(n-1)];put(f'{n} {len(edges)}\n'+graph_lines(edges),w*(n-1))
        edges=[(u,(u+1)%n,w) for u in range(n)];put(f'{n} {len(edges)}\n'+graph_lines(edges),w*(n+2))
    elif pid=='P2622':
        for _ in range(280):
            n=rng.randint(1,7);m=rng.randint(1,9);effects=[[rng.choice([-1,0,1]) for j in range(n)] for i in range(m)]
            put(f'{n}\n{m}\n'+''.join(row(e) for e in effects),light_states(effects))
        n=10;effects=[[int(i==j) for j in range(n)] for i in range(n)]
        put('10\n10\n'+''.join(row(e) for e in effects),10)
        put('10\n100\n'+''.join(row([0]*n) for _ in range(100)),-1)
        put('10\n1\n'+row([1]*n),1)
    elif pid=='AT_abc359_d':
        for n in range(2,6):
            for chars in product('AB?',repeat=n):
                s=''.join(chars)
                for k in range(2,n+1):put(f'{n} {k}\n{s}\n',palindrome_replacements(s,k))
        for _ in range(160):
            n=rng.randint(6,12);k=rng.randint(2,min(10,n));s=''.join(rng.choice('AB?') for _ in range(n))
            put(f'{n} {k}\n{s}\n',palindrome_replacements(s,k))
        put('1000 2\n'+'?'*1000+'\n',2)
        put('1000 3\n'+'?'*1000+'\n',4)
        put('1000 10\n'+'AB'*500+'\n',1)
        put('1000 10\n'+'A'*1000+'\n',0)
        put('10 10\n'+'?'*10+'\n',2**10-2**5)
    elif pid=='P1441':
        for _ in range(160):
            n=rng.randint(1,11);m=rng.randint(0,min(4,n-1));weights=[rng.randint(1,100) for i in range(n)]
            put(f'{n} {m}\n'+row(weights),retained_weight_subsets(weights,m))
        for m in range(5):put(f'20 {m}\n'+row([100]*20),20-m)
        put('20 0\n'+row(range(1,21)),210)
    elif pid=='P2210':
        def encode(n,edges):
            friends=[[] for _ in range(n)]
            for u,v in edges:friends[u].append(v+1);friends[v].append(u+1)
            assert all(len(v)==3 for v in friends)
            for v in friends:rng.shuffle(v)
            return f'{n}\n'+''.join(row(v) for v in friends)
        for n in [4,6]:
            all_edges=list(combinations(range(n),2))
            for edges in combinations(all_edges,3*n//2):
                degree=[0]*n
                for u,v in edges:degree[u]+=1;degree[v]+=1
                if degree!=[3]*n:continue
                put(encode(n,edges),cow_arrangements(n,edges))
        n=8
        for _ in range(24):
            cycle={tuple(sorted((i,(i+1)%n))) for i in range(n)}
            while True:
                p=list(range(n));rng.shuffle(p);extra=[tuple(sorted(p[i:i+2])) for i in range(0,n,2)]
                if not(set(extra)&cycle):break
            edges=list(cycle|set(extra));put(encode(n,edges),cow_arrangements(n,edges))
        edges=[(u,v) for base in [0,4,8] for u,v in combinations(range(base,base+4),2)];put(encode(12,edges),30)
        edges=[(u,v) for base in [0,6] for u in range(base,base+3) for v in range(base+3,base+6)]
        small=[(u,v) for u in range(3) for v in range(3,6)];put(encode(12,edges),2*cow_arrangements(6,small))
    elif pid=='P5911':
        for _ in range(220):
            n=rng.randint(1,8);capacity=rng.randint(100,400);times=[rng.randint(1,50) for i in range(n)];weights=[rng.randint(10,100) for i in range(n)]
            put(f'{capacity} {n}\n'+''.join(f'{t} {w}\n' for t,w in zip(times,weights)),bridge_partitions(times,weights,capacity))
        put('100 16\n'+''.join(f'{i+1} 100\n' for i in range(16)),sum(range(1,17)))
        put('400 16\n'+''.join(f'{i+1} 10\n' for i in range(16)),16)
        put('400 16\n'+'50 100\n'*16,200)
    elif pid=='P10865':
        for _ in range(250):
            n,m=rng.randint(1,4),rng.randint(1,4);points=rng.sample(list(product(range(n),range(m))),rng.randint(1,min(5,n*m)));fish=[rng.randint(1,3) for p in points]
            put(f'{n} {m} {len(points)}\n'+''.join(f'{x+1} {y+1} {c}\n' for (x,y),c in zip(points,fish)),bomb_literal(n,m,points,fish))
        put('1000 1000 10\n'+''.join(f'{10+30*i} {10+30*i} 3\n' for i in range(10)),30)
        put('1 1000 10\n'+''.join(f'1 {i+1} 3\n' for i in range(10)),12)
        points=[(x+dx,y+dy) for x,y in [(10,10),(900,900)] for dx,dy in [(0,0),(-1,0),(1,0),(0,-1),(0,1)]]
        put('1000 1000 10\n'+''.join(f'{x} {y} 3\n' for x,y in points),6)
    elif pid=='P1450':
        for _ in range(180):
            coins=[rng.randint(1,12) for i in range(4)];queries=[];answers=[]
            for q in range(5):
                limits=[rng.randint(1,5) for i in range(4)];target=rng.randint(1,80);queries.append(row(limits+[target]));answers.append(coin_vectors(coins,limits,target))
            put(row(coins+[5])+''.join(queries),'\n'.join(map(str,answers)))
        put('1 1 1 1 1000\n'+''.join(row([100000]*4+[100000]) for _ in range(1000)),'\n'.join([str(comb(100003,3))]*1000))
        targets=list(range(1,1000))+[100000]
        put(row([100000]*4+[1000])+''.join(row([100000]*4+[s]) for s in targets),'\n'.join('4' if s==100000 else '0' for s in targets))
    elif pid=='P2167':
        for _ in range(40):
            cases=[];answers=[]
            for case in range(5):
                n=rng.randint(1,10);length=rng.randint(1,5);k=rng.randint(0,n+2);patterns=[''.join(rng.choice('abc?') for i in range(length)) for j in range(n)]
                cases.append(f'{n} {k}\n'+'\n'.join(patterns)+'\n');answers.append(matching_words(patterns,k))
            put('5\n'+''.join(cases),'\n'.join(map(str,answers)))
        mod=1000003;cases=[];answers=[]
        for k,patterns,answer in [(15,['?'*50]*15,pow(26,50,mod)),(14,['?'*50]*15,0),(1,['a'+'?'*49]*14+['?'*50],25*pow(26,49,mod)%mod),(15,['a'+'?'*49]*14+['?'*50],pow(26,49,mod)),(16,['?'*50]*15,0)]:
            cases.append(f'15 {k}\n'+'\n'.join(patterns)+'\n');answers.append(answer)
        put('5\n'+''.join(cases),'\n'.join(map(str,answers)))
    elif pid=='P2473':
        for _ in range(200):
            n=rng.randint(1,5);throws=rng.randint(1,4);scores=[rng.randint(-9,15) for i in range(n)];prerequisites=[]
            for i in range(n):prerequisites.append(set(rng.sample([j for j in range(n) if j!=i],rng.randint(0,n-1))))
            text=f'{throws} {n}\n'+''.join(row([scores[i]]+[j+1 for j in sorted(prerequisites[i])]+[0]) for i in range(n))
            put(text,reward_tree(throws,scores,prerequisites))
        put('2 2\n-1 0\n100 1 0\n',Fraction(49,2))
        put('100 1\n1000000 0\n',100000000)
        put('100 15\n'+'1000000 0\n'*15,100000000)
        put('100 15\n'+'-1000000 0\n'*15,0)
        put('100 15\n'+''.join(f'1000000 {(i+1)%15+1} 0\n' for i in range(15)),0)
    elif pid=='P2831':
        def scaled(v):return f'{v//100}.{v%100:02d}'
        def encode(points):return f'{len(points)} 0\n'+''.join(f'{scaled(x)} {scaled(y)}\n' for x,y in points)
        for _ in range(25):
            cases=[];answers=[]
            for case in range(10):
                n=rng.randint(1,8);points=set()
                if rng.randrange(4)==0:
                    x=rng.randint(1,999);points={(x,y) for y in rng.sample(range(1,1000),n)}
                else:
                    while len(points)<n:points.add((rng.randint(1,999),rng.randint(1,999)))
                points=list(points);rng.shuffle(points);cases.append(encode(points));answers.append(bird_fraction_cover(points))
            put('10\n'+''.join(cases),'\n'.join(map(str,answers)))
        curves=[[(x,-x*x+36*x) for x in range(1,19)],[(x,600) for x in range(1,19)],[(500,y) for y in range(1,19)]]
        put('3\n'+''.join(encode(points) for points in curves),'1\n9\n18')
    elif pid=='P3694':
        def encode(a,m):return f'{len(a)} {m}\n'+''.join(f'{j+1}\n' for j in a)
        for _ in range(220):
            n=rng.randint(1,14);m=rng.randint(1,min(7,n));a=list(range(m))+[rng.randrange(m) for i in range(n-m)];rng.shuffle(a)
            put(encode(a,m),band_target_arrays(a,m))
        put(encode(list(range(20))*5000,20),95000)
        put(encode([j for j in range(20) for i in range(5000)],20),0)
        put(encode([0,1]*50000,2),50000)
        put(encode([0]*100000,1),0)
    elif pid=='P3786':
        def encode(h,w,total,start,melons,small):
            text=f'{h} {w} {total} {start%w+1} {start//w+1}\n{len(melons)} {small}\n'
            for begin,end,flag,track in melons:text+=f'{begin} {end}\n{flag}\n'+''.join(f'{p%w+1} {p//w+1}\n' for p in track)
            return text
        for _ in range(240):
            h,w=rng.randint(1,3),rng.randint(1,3);cells=h*w;total=rng.randint(1,6);n=rng.randint(1,min(6,cells));m=rng.randint(0,min(n,4));flags=[1]*m+[0]*(n-m);rng.shuffle(flags)
            used=[set() for _ in range(total+1)];melons=[]
            for flag in flags:
                begin=rng.randint(1,total);end=rng.randint(begin+1,total+1);track=[]
                for t in range(begin,end):p=rng.choice([q for q in range(cells) if q not in used[t]]);used[t].add(p);track.append(p)
                melons.append((begin,end,flag,track))
            start=rng.randrange(cells);put(encode(h,w,total,start,melons,m),fruit_walks(h,w,total,start,melons,m))
        melons=[(1,101,int(p<10),[p]*100) for p in range(20)];put(encode(5,5,100,0,melons,10),9)
        melons=[(1,101,0,[p]*100) for p in range(5,25)];put(encode(5,5,100,0,melons,0),0)
        put('1 1 2 1 1\n2 1\n1 2\n1\n1 1\n2 3\n0\n1 1\n',-1)
        put('1 2 2 1 1\n1 0\n1 3\n0\n2 1\n1 1\n',1)
    elif pid=='P3947':
        def encode(names,durations,open_time,target,deadline):return f'{len(names)} {target} {deadline}\n'+''.join(f'{name} {t} {last}\n' for name,t,last in zip(names,durations,open_time))
        for index in range(180):
            n=rng.randint(1,8);names=sorted(rng.choice(['A','B','C','D']) for i in range(n));durations=[rng.randint(1,6) for i in range(n)];open_time=[rng.randint(t,16) for t in durations]
            deadline=sum(durations)+rng.randrange(4) if index%4 else rng.randint(1,sum(durations));target=1 if index%3==0 else rng.randint(1,sum(open_time)+1)
            put(encode(names,durations,open_time,target,deadline),song_permutations(names,durations,open_time,target,deadline))
        names=[f'A{i:02d}' for i in range(22)]
        put(encode(names,[1]*22,[22]*22,231,22),'231\n'+'\n'.join(names))
        put(encode(names,[1]*22,[22]*22,232,22),'No Answer')
        put(encode(names,[1]*22,[22]*22,1,21),'No Answer')
        put(encode(['A']*22,[1]*22,[22]*22,231,22),'231\n'+'\n'.join(['A']*22))
        durations=[i%4+1 for i in range(22)];open_time=[1000+i for i in range(22)];order=sorted(range(22),key=lambda i:(durations[i],names[i]));time=0;score=0
        for i in order:time+=durations[i];score+=open_time[i]-time
        put(encode(names,durations,open_time,1,sum(durations)),str(score)+'\n'+'\n'.join(names[i] for i in order))
    elif pid=='P4928':
        def encode(colors,wash,weather):return f'{len(colors)} {len(weather)}\n'+row(colors)+row(wash)+row(weather)
        for index in range(220):
            n=rng.randint(2,4);days=rng.randint(2,8);colors=[rng.randint(1,100) for i in range(n)]
            if index%7==0:colors=[10**80+rng.randint(1,100) for i in range(n)]
            wash=[rng.randint(1,min(6,days-1)) for i in range(n)];weather=[rng.randint(-100000000,100000000) for i in range(days)]
            put(encode(colors,wash,weather),clothes_sequences(colors,wash,weather))
        put(encode([1]*4,[1]*4,[-1]*2000),-2000)
        put(encode([1]*4,[1,2,3,6],[1,-1]*1000),0)
        put(encode([1,2,3,4],[6]*4,[100000000]*2000),'gcd loves her clothes!')
        put(encode([10**100,10**100+1],[1,1],[1,-1]*1000),1000)
    elif pid=='P7296':
        pool=''.join(c for c in string.ascii_lowercase if c not in 'mildred')
        for length in range(1,9):
            for chars in product('ab',repeat=length):
                text=''.join(chars);put(text+'\n',alphabet_orders(text))
        for index in range(120):
            source='mildrebs' if index%4==0 else pool;letters=rng.sample(source,rng.randint(1,7));text=''.join(rng.choice(letters) for i in range(rng.randint(1,18)))
            put(text+'\n',alphabet_orders(text))
        put(pool*5000+'\n',5000)
        put('a'*100000+'\n',100000)
    elif pid=='P9017':
        def word(mask,n):return ''.join('1' if mask>>i&1 else '0' for i in range(n))
        for n in range(2,9):
            states=1<<n;distance=switch_distances(n)
            put(f'{states*states} {n}\n'+''.join(word(lights,n)+' '+word(switches,n)+'\n' for lights in range(states) for switches in range(states)),'\n'.join(map(str,distance)))
        n=20;tests=200000;queries=[];answers=[]
        for i in range(tests):
            if i%3==0:lights=0;switches=rng.randrange(1<<n);answer=0
            elif i%3==1:
                switches=rng.randrange(1<<n);lights=switches^(1<<rng.randrange(n));answer=int(lights!=0)
            else:switches=0;lights=3|(1<<(2+i%18));answer=2
            queries.append(word(lights,n)+' '+word(switches,n)+'\n');answers.append(answer)
        put(f'{tests} {n}\n'+''.join(queries),'\n'.join(map(str,answers)))
    elif pid=='CF11D':
        for n in range(1,5):
            all_edges=list(combinations(range(n),2))
            for mask in range(1<<len(all_edges)):
                edges=[edge for i,edge in enumerate(all_edges) if mask>>i&1];put(f'{n} {len(edges)}\n'+graph_lines(edges),cycle_edge_sets(n,edges))
        for _ in range(200):
            n=rng.randint(5,7);all_edges=list(combinations(range(n),2));edges=rng.sample(all_edges,rng.randint(0,min(11,len(all_edges))))
            put(f'{n} {len(edges)}\n'+graph_lines(edges),cycle_edge_sets(n,edges))
        def clique_cycles(n):return sum(comb(n,k)*factorial(k-1)//2 for k in range(3,n+1))
        edges=list(combinations(range(19),2));put(f'19 {len(edges)}\n'+graph_lines(edges),clique_cycles(19))
        edges=[(u,v) for u in range(9) for v in range(9,19)];put(f'19 {len(edges)}\n'+graph_lines(edges),sum(comb(9,k)*comb(10,k)*factorial(k)*factorial(k-1)//2 for k in range(2,10)))
        edges=list(combinations(range(9),2))+list(combinations(range(9,19),2))+[(0,9)];put(f'19 {len(edges)}\n'+graph_lines(edges),clique_cycles(9)+clique_cycles(10))
        edges=[(i,(i+1)%19) for i in range(19)];put('19 19\n'+graph_lines(edges),1)
        put('19 0\n',0)
    else:raise KeyError(pid)
    return result
