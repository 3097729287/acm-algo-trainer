"""Enumerate choices and literal trajectories independently of the DP states."""
from collections import deque
from functools import lru_cache
from itertools import product,combinations,permutations
import math
import random

IDS={'P1077','P1203','P2834','P2842','P1095','P1280','P1544','P1874','P2285',
     'P2758','P3842','CF946D','P1005','P1020','P1436','P1541','P4310','P17594'}


def flower_counts(limits,target):
    return sum(sum(row)==target for row in product(*(range(v+1) for v in limits)))


def necklace(text):
    # Enumerate both end colours and all non-overlapping prefix/suffix lengths.
    n=len(text);best=0
    for cut in range(n):
        row=text[cut:]+text[:cut]
        for a,b in product('rb',repeat=2):
            for left in range(n+1):
                if any(c not in (a,'w') for c in row[:left]):continue
                for right in range(n-left+1):
                    if all(c in (b,'w') for c in row[n-right:]):best=max(best,left+right)
    return best


def coin_combinations(coins,target):
    def enumerate_counts(i,remaining):
        if i==len(coins):return int(remaining==0)
        return sum(enumerate_counts(i+1,remaining-count*coins[i]) for count in range(remaining//coins[i]+1))
    return enumerate_counts(0,target)


def partition_number(n):
    # Euler's pentagonal recurrence, not coin-by-coin unbounded-knapsack updates.
    p=[1]+[0]*n
    for value in range(1,n+1):
        j=1
        while j*(3*j-1)//2<=value:
            sign=1 if j%2 else -1;a=j*(3*j-1)//2;b=j*(3*j+1)//2
            p[value]+=sign*p[value-a]
            if b<=value:p[value]+=sign*p[value-b]
            j+=1
    return p[n]


def coin_bfs(coins,target):
    distance={0:0};queue=deque([0])
    while queue:
        value=queue.popleft()
        if value==target:return distance[value]
        for coin in coins:
            nxt=value+coin
            if nxt<=target and nxt not in distance:distance[nxt]=distance[value]+1;queue.append(nxt)
    return None


def escape_states(mana,target,seconds):
    if target==0:return 'Yes\n0\n'
    states={mana:0}
    for t in range(1,seconds+1):
        nxt={}
        for magic,distance in states.items():
            choices=[(magic,distance+17),(magic+4,distance)]
            if magic>=10:choices.append((magic-10,distance+60))
            for key,value in choices:nxt[key]=max(nxt.get(key,-1),value)
        states=nxt
        if max(states.values())>=target:return f'Yes\n{t}\n'
    return f'No\n{max(states.values())}\n'


def escape_counts(mana,seconds):
    best=0
    for flashes in range(seconds+1):
        rest=max(0,(10*flashes-mana+3)//4)
        if flashes+rest<=seconds:best=max(best,60*flashes+17*(seconds-flashes-rest))
    return best


def schedule_enumeration(n,jobs):
    starts={}
    for p,t in jobs:starts.setdefault(p,[]).append(t)
    def enumerate_schedules(now):
        if now>n:return 0
        if now not in starts:return 1+enumerate_schedules(now+1)
        return max(enumerate_schedules(now+length) for length in starts[now])
    return enumerate_schedules(1)


def boosted_paths(triangle,limit):
    n=len(triangle);best=-10**100
    for route in product((0,1),repeat=n-1):
        column=0;values=[triangle[0][0]]
        for row,direction in enumerate(route,1):column+=direction;values.append(triangle[row][column])
        for mask in range(1<<n):
            if mask.bit_count()<=limit:best=max(best,sum(v*(3 if mask>>i&1 else 1) for i,v in enumerate(values)))
    return best


def plus_signs(text,target):
    best=len(text)+1
    for mask in range(1<<(len(text)-1)):
        start=0;total=0
        for j in range(len(text)-1):
            if mask>>j&1:total+=int(text[start:j+1]);start=j+1
        total+=int(text[start:])
        if total==target:best=min(best,mask.bit_count())
    return -1 if best==len(text)+1 else best


def mole_motion(n,events):
    by_time={}
    for t,x,y in events:by_time.setdefault(t,set()).add((x-1,y-1))
    score=[[0]*n for _ in range(n)]
    for t in range(1,max(by_time)+1):
        nxt=[[0]*n for _ in range(n)]
        for x in range(n):
            for y in range(n):
                nxt[x][y]=max(score[a][b] for a,b in [(x,y),(x-1,y),(x+1,y),(x,y-1),(x,y+1)] if 0<=a<n and 0<=b<n)+int((x,y) in by_time.get(t,set()))
        score=nxt
    return max(map(max,score))


def edit_bfs(a,b):
    alphabet=sorted(set(a+b));bound=max(len(a),len(b));distance={a:0};queue=deque([a])
    while queue:
        s=queue.popleft()
        if s==b:return distance[s]
        candidates={s[:i]+s[i+1:] for i in range(len(s))}
        candidates|={s[:i]+c+s[i+1:] for i in range(len(s)) for c in alphabet}
        if len(s)<bound:candidates|={s[:i]+c+s[i:] for i in range(len(s)+1) for c in alphabet}
        for t in candidates:
            if t not in distance:distance[t]=distance[s]+1;queue.append(t)


def line_grid_bfs(lines):
    n=len(lines)
    def bit(row,column):
        l,r=lines[row];return 1<<(column-l) if l<=column<=r else 0
    full=[(1<<(r-l+1))-1 for l,r in lines]
    start=(0,0,bit(0,0));distance={start:0};queue=deque([start])
    while queue:
        row,column,mask=queue.popleft();cost=distance[row,column,mask]
        if row==n-1 and column==n-1 and mask==full[row]:return cost
        candidates=[]
        for col in [column-1,column+1]:
            if 0<=col<n:candidates.append((row,col,mask|bit(row,col)))
        if row+1<n and mask==full[row]:candidates.append((row+1,column,bit(row+1,column)))
        for state in candidates:
            if state not in distance:distance[state]=cost+1;queue.append(state)


def timetable_subsets(rows,limit):
    lessons=[(day,hour) for day,row in enumerate(rows) for hour,c in enumerate(row) if c=='1'];best=10**9
    for removed in range(1<<len(lessons)):
        if removed.bit_count()>limit:continue
        kept=[[] for _ in rows]
        for i,(day,hour) in enumerate(lessons):
            if not(removed>>i&1):kept[day].append(hour)
        best=min(best,sum(max(row)-min(row)+1 for row in kept if row))
    return best


def row_take_enumeration(row):
    def play(l,r,round):
        if l>r:return 0
        return max(row[l]*(1<<round)+play(l+1,r,round+1),row[r]*(1<<round)+play(l,r-1,round+1))
    return play(0,len(row)-1,1)


def missile_enumeration(values):
    n=len(values);longest=0
    for mask in range(1<<n):
        selected=[values[i] for i in range(n) if mask>>i&1]
        if all(a>=b for a,b in zip(selected,selected[1:])):longest=max(longest,len(selected))
    @lru_cache(None)
    def partition(i,tops):
        if i==n:return len(tops)
        x=values[i];best=partition(i+1,tuple(sorted(tops+(x,))))
        for t in set(tops):
            if t>=x:
                nxt=list(tops);nxt.remove(t);nxt.append(x);best=min(best,partition(i+1,tuple(sorted(nxt))))
        return best
    return longest,partition(0,())


def board_peel_plans(board,pieces):
    # Enumerate actual cut sequences; each stopped-off piece is never revisited.
    @lru_cache(None)
    def value(a,b,c,d):return sum(board[x][y] for x in range(a,c) for y in range(b,d))**2
    best=10**100
    def enumerate_plans(a,b,c,d,left,closed):
        nonlocal best
        if (c-a)*(d-b)<left:return
        if left==1:best=min(best,closed+value(a,b,c,d));return
        for cut in range(a+1,c):
            enumerate_plans(cut,b,c,d,left-1,closed+value(a,b,cut,d))
            enumerate_plans(a,b,cut,d,left-1,closed+value(cut,b,c,d))
        for cut in range(b+1,d):
            enumerate_plans(a,cut,c,d,left-1,closed+value(a,b,c,cut))
            enumerate_plans(a,b,c,cut,left-1,closed+value(a,cut,c,d))
    enumerate_plans(0,0,8,8,pieces,0);return best


def turtle_permutations(score,cards):
    best=0
    for row in set(permutations(cards)):
        position=0;total=score[0]
        for step in row:position+=step;total+=score[position]
        best=max(best,total)
    return best


def bit_subsequences(values):
    best=0
    for mask in range(1<<len(values)):
        row=[v for i,v in enumerate(values) if mask>>i&1]
        if all(a&b for a,b in zip(row,row[1:])):best=max(best,len(row))
    return best


def operations_outcomes(x,y):
    possible={y}
    while x:
        p=x&-x;x-=p;possible={value for old in possible for value in (old+p,old|p)}
    return min(possible)


def cases_for(pid):
    rng=random.Random(202610311);result=[]
    def put(inp,out):result.append((f'线性单元独立基准 {len(result)+1}',str(inp),str(out)))
    if pid=='P1077':
        for _ in range(260):
            n=rng.randint(1,7);m=rng.randint(1,24);limits=[rng.randint(0,4) for _ in range(n)];put(f'{n} {m}\n'+' '.join(map(str,limits))+'\n',flower_counts(limits,m)%1000007)
        put('100 100\n'+' '.join(['100']*100)+'\n',math.comb(199,100)%1000007)
        put('100 100\n'+' '.join(['0']*100)+'\n',0)
    elif pid=='P1203':
        for n in range(3,7):
            for row in product('rbw',repeat=n):
                text=''.join(row);put(f'{n}\n{text}\n',necklace(text))
        put('350\n'+'w'*350+'\n',350);put('350\n'+'r'*350+'\n',350)
        for _ in range(100):
            n=rng.randint(7,12);text=''.join(rng.choice('rbw') for _ in range(n));put(f'{n}\n{text}\n',necklace(text))
    elif pid=='P2834':
        for _ in range(250):
            n=rng.randint(1,6);target=rng.randint(1,35);coins=rng.sample(range(1,18),n);put(f'{n} {target}\n'+' '.join(map(str,coins))+'\n',coin_combinations(coins,target)%1000000007)
        put('1000 10000\n'+' '.join(str(10*i) for i in range(1,1001))+'\n',partition_number(1000)%1000000007)
        put('1000 10000\n'+' '.join(map(str,range(9001,10001)))+'\n',1)
    elif pid=='P2842':
        put('3 6\n1 3 4\n',2)
        for _ in range(270):
            n=rng.randint(1,8);target=rng.randint(1,70);coins=rng.sample(range(1,25),n);best=coin_bfs(coins,target)
            if best is not None:put(f'{n} {target}\n'+' '.join(map(str,coins))+'\n',best)
        put('1000 10000\n'+' '.join(map(str,range(1,1001)))+'\n',10)
    elif pid=='P1095':
        for _ in range(600):
            mana=rng.randint(0,40);target=rng.randint(0,600);seconds=rng.randint(0,16);put(f'{mana} {target} {seconds}\n',escape_states(mana,target,seconds))
        put('1000 100000000 300000\n',f'No\n{escape_counts(1000,300000)}\n')
        put('1000 6000 300000\n','Yes\n100\n')
    elif pid=='P1280':
        for _ in range(270):
            n=rng.randint(1,14);jobs=[]
            for i in range(rng.randint(1,11)):
                p=rng.randint(1,n);jobs.append((p,rng.randint(1,n-p+1)))
            rng.shuffle(jobs);put(f'{n} {len(jobs)}\n'+''.join(f'{p} {t}\n' for p,t in jobs),schedule_enumeration(n,jobs))
        n=10000;put(f'{n} {n}\n'+''.join(f'{i} 1\n' for i in range(1,n+1)),0)
        put(f'{n} {n}\n'+''.join(f'1 {i}\n' for i in range(1,n+1)),n-1)
    elif pid=='P1544':
        for _ in range(200):
            n=rng.randint(1,7);limit=rng.randint(0,n*(n+1)//2);board=[[rng.randint(-20,20) for _ in range(i)] for i in range(1,n+1)]
            put(f'{n} {limit}\n'+''.join(' '.join(map(str,row))+'\n' for row in board),boosted_paths(board,limit))
        n=100
        for value,limit,out in [(10**9,5050,3*10**11),(-10**9,5050,-10**11),(-1,0,-100)]:
            put(f'{n} {limit}\n'+''.join(' '.join([str(value)]*i)+'\n' for i in range(1,n+1)),out)
    elif pid=='P1874':
        for _ in range(260):
            length=rng.randint(1,12);text=''.join(str(rng.randrange(10)) for _ in range(length));target=rng.randint(1,200)
            if rng.randrange(2):target=max(1,sum(map(int,text)))
            put(text+'\n'+str(target)+'\n',plus_signs(text,target))
        put('303\n6\n',1);put('0'*39+'1\n1\n',0);put('9'*40+'\n360\n',39)
        put('1'*40+'\n100000\n',-1);put('0'*40+'\n100000\n',-1)
    elif pid=='P2285':
        for _ in range(240):
            n=rng.randint(1,4);choices=[(t,x,y) for t in range(1,16) for x in range(1,n+1) for y in range(1,n+1)];events=sorted(rng.sample(choices,rng.randint(1,min(30,len(choices)))))
            put(f'{n} {len(events)}\n'+''.join(f'{t} {x} {y}\n' for t,x,y in events),mole_motion(n,events))
        put('1000 10000\n'+''.join(f'{t} 1 1\n' for t in range(1,10001)),10000)
        put('1000 10000\n'+''.join(f'{t} '+('1 1' if t%2 else '1000 1000')+'\n' for t in range(1,10001)),5000)
    elif pid=='P2758':
        words=[''.join(row) for size in range(1,4) for row in product('ab',repeat=size)]
        for a,b in product(words,repeat=2):put(a+'\n'+b+'\n',edit_bfs(a,b))
        for _ in range(140):
            a=''.join(rng.choice('abc') for _ in range(rng.randint(1,5)));b=''.join(rng.choice('abc') for _ in range(rng.randint(1,5)));put(a+'\n'+b+'\n',edit_bfs(a,b))
        put('a'*2000+'\n'+'b'*2000+'\n',2000);put('a'*2000+'\n'+'a'*2000+'\n',0)
    elif pid=='P3842':
        for _ in range(320):
            n=rng.randint(1,5);lines=[]
            for i in range(n):l=rng.randrange(n);r=rng.randint(l,n-1);lines.append((l,r))
            put(str(n)+'\n'+''.join(f'{l+1} {r+1}\n' for l,r in lines),line_grid_bfs(lines))
        n=20000;put(f'{n}\n'+f'1 {n}\n'*n,(n+2)*(n-1));put(f'{n}\n'+f'{n} {n}\n'*n,2*n-2)
    elif pid=='CF946D':
        for _ in range(220):
            n=rng.randint(1,3);m=rng.randint(1,5);rows=[''.join(rng.choice('01') for _ in range(m)) for i in range(n)];count=sum(row.count('1') for row in rows);limit=rng.randint(0,min(10,count+2))
            put(f'{n} {m} {limit}\n'+'\n'.join(rows)+'\n',timetable_subsets(rows,limit))
        put('500 500 500\n'+('1'*500+'\n')*500,249500)
        put('500 500 500\n'+('1'+'0'*498+'1\n')*500,500)
        put('1 3 500\n000\n',0)
    elif pid=='P1005':
        for _ in range(220):
            n=rng.randint(1,5);m=rng.randint(1,9);matrix=[[rng.randint(0,1000) for _ in range(m)] for i in range(n)]
            put(f'{n} {m}\n'+''.join(' '.join(map(str,row))+'\n' for row in matrix),sum(row_take_enumeration(row) for row in matrix))
        put('80 80\n'+(' '.join(['1000']*80)+'\n')*80,80*1000*((1<<81)-2))
        put('80 80\n'+(' '.join(['0']*80)+'\n')*80,0)
    elif pid=='P1020':
        for _ in range(250):
            n=rng.randint(1,12);values=[rng.randint(1,20) for _ in range(n)];a,b=missile_enumeration(values);put(' '.join(map(str,values))+'\n',f'{a}\n{b}\n')
        put(' '.join(['50000']*100000)+'\n','100000\n1\n')
        put(' '.join(map(str,list(range(1,50001))*2))+'\n','2\n50000\n')
        put(' '.join(map(str,list(range(50000,0,-1))*2))+'\n','50001\n2\n')
    elif pid=='P1436':
        for _ in range(210):
            pieces=rng.randint(2,4);board=[[rng.randrange(100) for _ in range(8)] for i in range(8)]
            put(str(pieces)+'\n'+''.join(' '.join(map(str,row))+'\n' for row in board),board_peel_plans(board,pieces))
        board=[[0]*8 for i in range(8)]
        for x,y in [(0,0),(0,7),(7,0),(7,7)]:board[x][y]=1
        put('4\n'+''.join(' '.join(map(str,row))+'\n' for row in board),6)
        put('15\n'+('0 '*7+'0\n')*8,0)
        board=[[0]*8 for i in range(8)];board[7][7]=99;put('15\n'+''.join(' '.join(map(str,row))+'\n' for row in board),9801)
    elif pid=='P1541':
        for _ in range(230):
            cards=[rng.randint(1,4) for i in range(rng.randint(1,8))];n=sum(cards)+1;score=[rng.randint(0,100) for i in range(n)]
            put(f'{n} {len(cards)}\n'+' '.join(map(str,score))+'\n'+' '.join(map(str,cards))+'\n',turtle_permutations(score,cards))
        cards=[value for value in range(1,5) for _ in range(30)];put('301 120\n'+' '.join(['100']*301)+'\n'+' '.join(map(str,cards))+'\n',12100)
        put('3 2\n50 0 0\n1 1\n',50)
    elif pid=='P4310':
        for _ in range(270):
            n=rng.randint(1,13);values=[rng.randrange(32) for i in range(n)];put(f'{n}\n'+' '.join(map(str,values))+'\n',bit_subsequences(values))
        put('3\n1 3 2\n',3);put('100000\n'+' '.join(['0']*100000)+'\n',1)
        put('100000\n'+' '.join(['1000000000']*100000)+'\n',100000)
        put('100000\n'+' '.join(str(1<<(i%30)) for i in range(100000))+'\n',3334)
    elif pid=='P17594':
        small=[(x,y) for x in range(64) for y in range(64)]
        small += [(rng.randrange(1024),rng.randrange(1<<30)) for _ in range(2000)]
        put(str(len(small))+'\n'+''.join(f'{x} {y}\n' for x,y in small),'\n'.join(str(operations_outcomes(x,y)) for x,y in small))
        tests=[];answer=[]
        for _ in range(10000):
            mode=rng.randrange(4)
            if mode==0:x=0;y=rng.randrange(1<<30);best=y
            elif mode==1:x=1<<rng.randrange(30);y=rng.randrange(1<<30);best=x|y
            elif mode==2:x=(1<<30)-1;y=0;best=x
            else:x=y=(1<<30)-1;best=y
            tests.append((x,y));answer.append(best)
        put('10000\n'+''.join(f'{x} {y}\n' for x,y in tests),'\n'.join(map(str,answer)))
    else:raise KeyError(pid)
    return result
