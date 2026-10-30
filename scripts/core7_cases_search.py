"""Independent small-state models for the nineteen search-unit problems."""
from collections import Counter,deque,defaultdict
from functools import lru_cache
from fractions import Fraction
import itertools
import random

IDS={'AT_arc001_2','P1331','P1605','P2802','CF1059B','P1019','P1219','P1825','P2895','SP4580','CF55B','AT_abc184_f','CF700B','CF1401D','P1790','P4289','P10488','UVA11367','B3625'}
DIRECTIONS=[(1,0),(-1,0),(0,1),(0,-1)]


def rectangle_partitions(rows,columns):
    """Colour-cell frontier connectivity DP, independent of cut-line DFS."""
    states={(tuple([0]*columns),0,0):1}
    def normal(front):
        positive={};negative={};result=[]
        for token in front:
            if token>0:result.append(positive.setdefault(token,len(positive)+1))
            elif token<0:result.append(-negative.setdefault(token,len(negative)+1))
            else:result.append(0)
        return tuple(result)
    for at in range(rows*columns):
        row,col=divmod(at,columns);next_states=defaultdict(int)
        for (front,closed,touched),ways in states.items():
            for colour in ([0] if at==0 else [0,1]):
                if closed>>colour&1:continue
                sign=1 if colour==0 else -1;up=front[col];left=front[col-1] if col else 0
                same=lambda x:x*sign>0
                token=left if same(left) else up if same(up) else sign*(max(map(abs,front))+1)
                changed=list(front)
                if same(left) and same(up) and left!=up:changed=[left if x==up else x for x in changed]
                changed[col]=token;new_closed=closed
                if up and not same(up) and up not in changed:
                    previous_colour=0 if up>0 else 1
                    if any(x and (x>0)==(up>0) for x in changed):continue
                    new_closed|=1<<previous_colour
                boundary=row in [0,rows-1] or col in [0,columns-1]
                new_touched=touched|((1<<colour) if boundary else 0)
                next_states[(normal(changed),new_closed,new_touched)]+=ways
        states=next_states
    answer=0
    for (front,closed,touched),ways in states.items():
        if touched!=3:continue
        if len({x for x in front if x>0})>1 or len({x for x in front if x<0})>1:continue
        answer+=ways
    return answer


def rectangle_subset_brute(rows,columns):
    count=rows*columns;full=(1<<count)-1;boundary=0;neighbours=[]
    for i in range(count):
        r,c=divmod(i,columns)
        if r in [0,rows-1] or c in [0,columns-1]:boundary|=1<<i
        neighbours.append([nr*columns+nc for dr,dc in DIRECTIONS if 0<=(nr:=r+dr)<rows and 0<=(nc:=c+dc)<columns])
    def connected(mask):
        if not mask:return False
        seen=mask&-mask;todo=[seen.bit_length()-1]
        for u in todo:
            for v in neighbours[u]:
                if mask>>v&1 and not seen>>v&1:seen|=1<<v;todo.append(v)
        return seen==mask
    return sum(bool((mask<<1)&boundary) and bool((full^(mask<<1))&boundary) and connected(mask<<1) and connected(full^(mask<<1)) for mask in range(1,1<<(count-1)))


@lru_cache(None)
def book_distances(n):
    start=tuple(range(1,n+1));distance={start:0};todo=deque([start])
    while todo:
        a=todo.popleft()
        # The literal cut-out/insert operation, rather than adjacent-block swaps.
        for left in range(n):
            for right in range(left+1,n+1):
                piece=a[left:right];remaining=a[:left]+a[right:]
                for pos in range(len(remaining)+1):
                    changed=remaining[:pos]+piece+remaining[pos:]
                    if changed not in distance:distance[changed]=distance[a]+1;todo.append(changed)
    return distance


def path_edges(graph,start,end):
    previous={start:None};todo=[start]
    for u in todo:
        if u==end:break
        for v,index in graph[u]:
            if v not in previous:previous[v]=(u,index);todo.append(v)
    result=[];at=end
    while at!=start:at,index=previous[at];result.append(index)
    return result


def cases_for(pid):
    rng=random.Random(20261031);values=[]
    def put(inp,answer):values.append((f'独立校验 {len(values)+1}',str(inp)+'\n',str(answer)+'\n'))
    def ints(a):return ' '.join(map(str,a))
    if pid=='AT_arc001_2':
        todo=deque([0]);distance={0:0}
        while todo:
            u=todo.popleft()
            for delta in [-10,-5,-1,1,5,10]:
                v=u+delta
                if -400<=v<=400 and v not in distance:distance[v]=distance[u]+1;todo.append(v)
        independent={d:min(abs(t)+abs(f)+abs(d-10*t-5*f) for t in range(-40,41) for f in range(-40,41)) for d in range(-40,41)}
        assert all(distance[d]==independent[d] for d in independent)
        for a in range(41):
            for b in range(41):put(f'{a} {b}',independent[b-a])
    elif pid=='P1331':
        boards=[]
        for mask in range(512):boards.append([''.join('#' if mask>>(r*3+c)&1 else '.' for c in range(3)) for r in range(3)])
        for _ in range(120):boards.append([''.join(rng.choice('#.') for c in range(5)) for r in range(4)])
        for grid in boards:
            n,m=len(grid),len(grid[0]);bad=any(sum(grid[r+dr][c+dc]=='#' for dr in range(2) for dc in range(2))==3 for r in range(n-1) for c in range(m-1))
            corners=sum(grid[r][c]=='#' and (r==0 or grid[r-1][c]=='.') and (c==0 or grid[r][c-1]=='.') for r in range(n) for c in range(m))
            put(f'{n} {m}\n'+'\n'.join(grid),'Bad placement.' if bad else f'There are {corners} ships.')
        put('1000 1000\n'+('#'*1000+'\n')*1000,'There are 1 ships.')
    elif pid=='P1605':
        for _ in range(140):
            n=rng.randrange(1,5);m=rng.randrange(2,5)
            if n*m>12:continue
            size=n*m;start=rng.randrange(size);end=rng.randrange(size);blocked=set(rng.sample([i for i in range(size) if i!=start],rng.randrange(1,min(10,size-1)+1)))
            states={(1<<start,start):1};answer=0
            while states:
                following=defaultdict(int)
                for (mask,last),ways in states.items():
                    if last==end:answer+=ways;continue
                    r,c=divmod(last,m)
                    for dr,dc in DIRECTIONS:
                        nr,nc=r+dr,c+dc;v=nr*m+nc
                        if 0<=nr<n and 0<=nc<m and v not in blocked and not mask>>v&1:following[(mask|(1<<v),v)]+=ways
                states=following
            sx,sy=divmod(start,m);fx,fy=divmod(end,m)
            put(f'{n} {m} {len(blocked)}\n{sx+1} {sy+1} {fx+1} {fy+1}\n'+'\n'.join(f'{i//m+1} {i%m+1}' for i in sorted(blocked)),answer)
        put('5 5 5\n1 1 5 5\n'+'\n'.join(f'3 {c}' for c in range(1,6)),0)
    elif pid=='P2802':
        boards=[[[2,1,1,1,1,3]],[[2,1,1,1,1,1,3]],[[2,1,1,1,1,4,1,1,3]],[[2,1,1,1,1,1,4,1,3]]]
        for _ in range(130):
            n=rng.randrange(1,5);m=rng.randrange(2,6);grid=[[rng.choice([0,1,1,1,4]) for c in range(m)] for r in range(n)];start,end=rng.sample(range(n*m),2);grid[start//m][start%m]=2;grid[end//m][end%m]=3;boards.append(grid)
        for grid in boards:
            n,m=len(grid),len(grid[0]);start=next((r,c) for r in range(n) for c in range(m) if grid[r][c]==2);end=next((r,c) for r in range(n) for c in range(m) if grid[r][c]==3)
            edges=[]
            for r in range(n):
                for c in range(m):
                    if not grid[r][c]:continue
                    for hp in range(2,7):
                        for dr,dc in DIRECTIONS:
                            nr,nc=r+dr,c+dc
                            if 0<=nr<n and 0<=nc<m and grid[nr][nc]:edges.append(((r,c,hp),(nr,nc,6 if grid[nr][nc]==4 else hp-1)))
            distance={(start[0],start[1],6):0}
            for _ in range(n*m*6):
                changed=False
                for u,v in edges:
                    if u in distance and distance[u]+1<distance.get(v,10**9):distance[v]=distance[u]+1;changed=True
                if not changed:break
            answer=min((d for (r,c,hp),d in distance.items() if (r,c)==end),default=-1)
            put(f'{n} {m}\n'+'\n'.join(ints(row) for row in grid),answer)
    elif pid=='CF1059B':
        def stamp_masks(n,m):
            return [sum(1<<((r+dr)*m+c+dc) for dr in [-1,0,1] for dc in [-1,0,1] if dr or dc) for r in range(1,n-1) for c in range(1,m-1)]
        for n,m in [(3,3),(3,4),(4,4)]:
            reachable={0}
            for stamp in stamp_masks(n,m):reachable|={mask|stamp for mask in list(reachable)}
            tests=set(range(512)) if n==m==3 else set(rng.randrange(1<<(n*m)) for _ in range(120))|reachable
            for mask in sorted(tests):put(f'{n} {m}\n'+'\n'.join(''.join('#' if mask>>(r*m+c)&1 else '.' for c in range(m)) for r in range(n)),'YES' if mask in reachable else 'NO')
        put('1000 1000\n'+('#'*1000+'\n')*1000,'YES')
    elif pid=='P1019':
        for _ in range(65):
            n=rng.randrange(1,5);words=[''.join(rng.choice('ab') for _ in range(rng.randrange(1,5))) for i in range(n)];first=rng.choice(words)[0]
            states={(word,i,tuple(1 if j==i else 0 for j in range(n))) for i,word in enumerate(words) if word[0]==first};answer=0
            while states:
                following=set()
                for text,last,used in states:
                    answer=max(answer,len(text))
                    for j,word in enumerate(words):
                        if used[j]>=2:continue
                        for k in range(1,min(len(words[last]),len(word))):
                            if text[-k:]==word[:k]:
                                changed=list(used);changed[j]+=1;following.add((text+word[k:],j,tuple(changed)))
                states=following
            put(str(n)+'\n'+'\n'.join(words)+'\n'+first,answer)
        put('20\n'+'aaa\n'*20+'a',81)
        put('20\n'+'\n'.join('a'*i for i in range(2,22))+'\na',421)
    elif pid=='P1219':
        for n in range(6,14):
            full=(1<<n)-1;todo=[(0,0,0,())];count=0;first=[]
            while todo:
                columns,left,right,path=todo.pop()
                if columns==full:
                    count+=1
                    if len(first)<3:first.append(path)
                    continue
                options=full&~(columns|left|right);choices=[]
                while options:bit=options&-options;options-=bit;choices.append(bit)
                for bit in reversed(choices):todo.append((columns|bit,((left|bit)<<1)&full,(right|bit)>>1,path+(bit.bit_length(),)))
            if n<=8:
                exact=[p for p in itertools.permutations(range(1,n+1)) if len({i+x for i,x in enumerate(p)})==n and len({i-x for i,x in enumerate(p)})==n]
                assert count==len(exact) and first==exact[:3]
            put(n,'\n'.join(ints(p) for p in first)+'\n'+str(count))
    elif pid=='P1825':
        for _ in range(130):
            n=rng.randrange(4,8);m=rng.randrange(4,8);grid=[['#']*m for r in range(n)]
            for r in range(1,n-1):
                for c in range(1,m-1):grid[r][c]=rng.choice(['.','.','.','#'])
            start=(rng.randrange(1,n-1),rng.randrange(1,m-1));end=(0,rng.randrange(1,m-1));grid[start[0]][start[1]]='@';grid[end[0]][end[1]]='='
            available=[(r,c) for r in range(1,n-1) for c in range(1,m-1) if (r,c)!=start];rng.shuffle(available);portals={}
            for letter in range(min(rng.randrange(3),len(available)//2)):
                a,b=available.pop(),available.pop();grid[a[0]][a[1]]=grid[b[0]][b[1]]=chr(65+letter);portals[a]=b;portals[b]=a
            edges=[]
            for r in range(n):
                for c in range(m):
                    if grid[r][c]=='#':continue
                    for dr,dc in DIRECTIONS:
                        nr,nc=r+dr,c+dc
                        if 0<=nr<n and 0<=nc<m and grid[nr][nc]!='#':edges.append(((r,c),portals.get((nr,nc),(nr,nc))))
            distance={start:0}
            for _ in range(n*m):
                changed=False
                for u,v in edges:
                    if u in distance and distance[u]+1<distance.get(v,10**9):distance[v]=distance[u]+1;changed=True
                if not changed:break
            put(f'{n} {m}\n'+'\n'.join(''.join(row) for row in grid),distance.get(end,-1))
        n=300;grid=['#'*n]+['#'+'.'*(n-2)+'#' for _ in range(n-2)]+['#'*n];grid[1]='#@'+'.'*(n-3)+'#';grid[-1]='#'*(n-2)+'=#';put(f'{n} {n}\n'+'\n'.join(grid),595)
    elif pid=='P2895':
        for _ in range(170):
            events=[(rng.randrange(7),rng.randrange(7),rng.randrange(21)) for i in range(rng.randrange(1,25))];at=defaultdict(set);ever=set()
            for x,y,time in events:
                for dr,dc in [(0,0)]+DIRECTIONS:
                    nx,ny=x+dr,y+dc
                    if nx>=0 and ny>=0:at[time].add((nx,ny));ever.add((nx,ny))
            destroyed=set(at[0]);front={(0,0)}-destroyed;answer=-1
            for time in range(max(t for x,y,t in events)+1):
                if not front:break
                if front-ever:answer=time;break
                destroyed|=at[time+1]
                front={(x+dr,y+dc) for x,y in front for dr,dc in DIRECTIONS if x+dr>=0 and y+dc>=0} - destroyed
            put(str(len(events))+'\n'+'\n'.join(ints(e) for e in events),answer)
        put('50000\n'+'300 300 1000\n'*50000,0)
    elif pid=='SP4580':
        for _ in range(100):
            n=rng.randrange(1,6);a=rng.sample(range(-6,7),n);answer=0
            for x,b,c,d,e,f in itertools.product(a,repeat=6):
                if d and Fraction(x*b+c,d)-e==f:answer+=1
            put(str(n)+'\n'+'\n'.join(map(str,a)),answer)
        a=list(range(-50,50));frequency=Counter(x*y+z for x in a for y in a for z in a)
        answer=sum(frequency[d*(e+f)] for d in a if d for e in a for f in a);put('100\n'+'\n'.join(map(str,a)),answer)
    elif pid=='CF55B':
        for _ in range(170):
            a=[rng.randrange(0,1001) for i in range(4)];operations=[rng.choice('+*') for i in range(3)];states={tuple(sorted(a))}
            for operation in operations:
                following=set()
                for state in states:
                    for i in range(len(state)):
                        for j in range(i+1,len(state)):
                            value=state[i]+state[j] if operation=='+' else state[i]*state[j]
                            following.add(tuple(sorted([state[k] for k in range(len(state)) if k not in [i,j]]+[value])))
                states=following
            put(ints(a)+'\n'+' '.join(operations),min(s[0] for s in states))
        put('1000 1000 1000 1000\n* * *',10**12)
    elif pid=='AT_abc184_f':
        for _ in range(120):
            n=rng.randrange(1,15);limit=rng.randrange(1,101);a=[rng.randrange(1,90) for i in range(n)]
            answer=max((sum(x for x,take in zip(a,selected) if take) for selected in itertools.product([0,1],repeat=n) if sum(x for x,take in zip(a,selected) if take)<=limit),default=0)
            put(f'{n} {limit}\n{ints(a)}',answer)
        put('40 17\n'+'1 '*40,17)
        put('40 1000000000\n'+'1000000000 '*40,10**9)
    elif pid in ['CF700B','CF1401D']:
        tests=[];answers=[]
        for _ in range(95 if pid=='CF700B' else 75):
            n=rng.randrange(2,10 if pid=='CF700B' else 7);edges=[(i,rng.randrange(i)) for i in range(1,n)];graph=[[] for i in range(n)]
            for index,(u,v) in enumerate(edges):graph[u].append((v,index));graph[v].append((u,index))
            if pid=='CF700B':
                k=rng.randrange(1,n//2+1);universities=rng.sample(range(n),2*k);distance={(u,v):len(path_edges(graph,u,v)) for u in range(n) for v in range(n)}
                def matching(remaining):
                    if not remaining:return 0
                    first=remaining[0];return max(distance[first,remaining[i]]+matching(remaining[1:i]+remaining[i+1:]) for i in range(1,len(remaining)))
                answer=matching(universities)
                put(f'{n} {k}\n'+ints(u+1 for u in universities)+'\n'+'\n'.join(f'{u+1} {v+1}' for u,v in edges),answer)
            else:
                count=[0]*(n-1)
                for u in range(n):
                    for v in range(u+1,n):
                        for index in path_edges(graph,u,v):count[index]+=1
                m=rng.randrange(1,7);primes=[rng.choice([2,3,5,7]) for i in range(m)];best=(-1,-1)
                for assignment in itertools.product(range(n-1),repeat=m):
                    weights=[1]*(n-1)
                    for factor,index in zip(primes,assignment):weights[index]*=factor
                    value=(sum(w!=1 for w in weights),sum(c*w for c,w in zip(count,weights)));best=max(best,value)
                tests.append(str(n)+'\n'+'\n'.join(f'{u+1} {v+1}' for u,v in edges)+f'\n{m}\n{ints(primes)}');answers.append(best[1]%1000000007)
        if pid=='CF700B':
            n=200000;put(f'{n} {n//2}\n'+ints(range(1,n+1))+'\n'+'\n'.join(f'{i} {i+1}' for i in range(1,n)),n*n//4)
        else:
            put(str(len(tests))+'\n'+'\n'.join(tests),'\n'.join(map(str,answers)))
            put('1\n2\n1 2\n60000\n'+'2 '*60000,pow(2,60000,1000000007))
            n=100000;put(f'1\n{n}\n'+'\n'.join(f'{i} {i+1}' for i in range(1,n))+'\n1\n2',(n*(n*n-1)//6+n*n//4)%1000000007)
    elif pid=='P1790':
        for n in range(1,7):
            for m in range(2,7):
                answer=rectangle_partitions(n,m)
                if n*m<=16:assert answer==rectangle_subset_brute(n,m),(n,m,answer)
                put(f'{n} {m}',answer)
    elif pid=='P4289':
        def distance_sets(start,target):
            if len(start)!=len(target):return -1
            distance={start:0};todo=deque([start])
            while todo:
                state=todo.popleft()
                if state==target:return distance[state]
                for p in state:
                    r,c=divmod(p,4)
                    for dr,dc in DIRECTIONS:
                        nr,nc=r+dr,c+dc;q=nr*4+nc
                        if 0<=nr<4 and 0<=nc<4 and q not in state:
                            changed=(state-{p})|{q}
                            if changed not in distance:distance[changed]=distance[state]+1;todo.append(changed)
        examples=[]
        for _ in range(65):
            k=rng.randrange(4);examples.append((frozenset(rng.sample(range(16),k)),frozenset(rng.sample(range(16),k))))
        for k in [8,8,15,16,0]:examples.append((frozenset(range(k)),frozenset(range(16-k,16))))
        examples.append((frozenset({0}),frozenset({0,1})))
        for start,target in examples:
            board=lambda state:'\n'.join(''.join('1' if 4*r+c in state else '0' for c in range(4)) for r in range(4))
            put(board(start)+'\n\n'+board(target),distance_sets(start,target))
    elif pid=='P10488':
        for _ in range(95):
            n=rng.randrange(1,8);a=tuple(rng.sample(range(1,n+1),n));answer=book_distances(n)[a]
            put(f'1\n{n}\n{ints(a)}',answer if answer<5 else '5 or more')
        distance=book_distances(7);hard=[p for p,d in distance.items() if d==4]
        for prefix in rng.sample(hard,min(3,len(hard))):
            # Projecting out the sorted suffix cannot increase a block-move distance.
            a=prefix+tuple(range(8,16));put('1\n15\n'+ints(a),4)
        put('3\n15\n'+ints(range(15,0,-1))+'\n15\n'+ints(range(1,16))+'\n15\n'+ints(list(range(6,16))+list(range(1,6))),'5 or more\n0\n1')
    elif pid=='UVA11367':
        for _ in range(110):
            n=rng.randrange(1,8);prices=[rng.randrange(1,101) for i in range(n)];roads=[(u,v,rng.randrange(1,10)) for u in range(n) for v in range(u+1,n) if rng.randrange(3)]
            queries=[];answers=[]
            for _ in range(4):
                capacity=rng.randrange(1,10);start=rng.randrange(n);end=rng.randrange(n);queries.append((capacity,start,end));edges=[];width=capacity+1
                for u in range(n):
                    for fuel in range(capacity):edges.append((u*width+fuel,u*width+fuel+1,prices[u]))
                for u,v,length in roads:
                    for fuel in range(length,capacity+1):edges.append((u*width+fuel,v*width+fuel-length,0));edges.append((v*width+fuel,u*width+fuel-length,0))
                distance=[10**15]*(n*width);distance[start*width]=0
                for _ in range(n*width):
                    changed=False
                    for u,v,cost in edges:
                        if distance[u]+cost<distance[v]:distance[v]=distance[u]+cost;changed=True
                    if not changed:break
                answer=min(distance[end*width:(end+1)*width]);answers.append(str(answer) if answer<10**15 else 'impossible')
            put(f'{n} {len(roads)}\n{ints(prices)}\n'+'\n'.join(ints(road) for road in roads)+f'\n{len(queries)}\n'+'\n'.join(ints(q) for q in queries),'\n'.join(answers))
        n=1000;prices=[i%100+1 for i in range(n)];put(f'{n} {n-1}\n{ints(prices)}\n'+'\n'.join(f'{i} {i+1} 100' for i in range(n-1))+'\n3\n100 0 999\n99 0 999\n1 0 0',str(100*sum(prices[:-1]))+'\nimpossible\n0')
    elif pid=='B3625':
        for _ in range(160):
            n=rng.randrange(1,20);m=rng.randrange(1,20);grid=[[rng.choice(['.','.','#']) for c in range(m)] for r in range(n)];grid[0][0]=grid[-1][-1]='.';parent=list(range(n*m))
            def find(x):
                while parent[x]!=x:x=parent[x]
                return x
            for r in range(n):
                for c in range(m):
                    if grid[r][c]!='.':continue
                    for dr,dc in [(1,0),(0,1)]:
                        nr,nc=r+dr,c+dc
                        if nr<n and nc<m and grid[nr][nc]=='.':parent[find(r*m+c)]=find(nr*m+nc)
            put(f'{n} {m}\n'+'\n'.join(''.join(row) for row in grid),'Yes' if find(0)==find(n*m-1) else 'No')
        put('100 100\n'+('.'*100+'\n')*100,'Yes')
    return values
