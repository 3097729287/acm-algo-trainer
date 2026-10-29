"""Small-domain, exact arithmetic and independent schedule oracles."""
from collections import defaultdict
from decimal import Decimal,localcontext,ROUND_FLOOR
from functools import lru_cache
import itertools
import math
import random

IDS=set('P2670 P1036 P1067 P1088 P1149 P1157 P1303 P1563 P1591 P1618 P1706 P2089 P3392 P3654 P1045 P1065 P1518 P3799'.split())

@lru_cache(None)
def matchstick_histogram():
    segments=['abcedf','bc','abged','abgcd','fgbc','afgcd','afgecd','abc','abcdefg','abfgcd']
    # Actual seven-segment sets: cardinality, independently of reference table.
    sizes=[len(set(s)) for s in segments]
    assert sizes==[6,2,5,5,4,5,6,3,7,6]
    costs=[sum(sizes[int(ch)] for ch in str(x)) for x in range(19999)]
    candidates=[x for x in range(10000) if costs[x]<=16]
    totals=defaultdict(int)
    for a,b in itertools.combinations_with_replacement(candidates,2):
        total=costs[a]+costs[b]+costs[a+b]+4
        if total<=24:totals[total]+=1 if a==b else 2
    return totals

@lru_cache(None)
def ratio_catalog():
    result=defaultdict(list)
    for digits in itertools.permutations(range(1,10)):
        x,y,z=[100*digits[k]+10*digits[k+1]+digits[k+2] for k in [0,3,6]]
        if not x<y<z:continue
        g=math.gcd(x,math.gcd(y,z));result[x//g,y//g,z//g].append((x,y,z))
    return result

@lru_cache(None)
def chicken_catalog():
    result=defaultdict(list)
    for row in itertools.product(range(1,4),repeat=10):result[sum(row)].append(row)
    return result

def cases_for(pid):
    assert pid in IDS,pid
    rng=random.Random(20261031);values=[]
    def put(inp,expected):values.append((f'独立校验 {len(values)+1}',str(inp),str(expected)))
    if pid=='P2670':
        for _ in range(180):
            n,m=rng.randint(1,9),rng.randint(1,9);g=[''.join(rng.choice('*???') for j in range(m)) for i in range(n)]
            mines=[(r,c) for r in range(n) for c in range(m) if g[r][c]=='*']
            answer=[''.join('*' if g[r][c]=='*' else str(sum(max(abs(r-x),abs(c-y))==1 for x,y in mines)) for c in range(m)) for r in range(n)]
            put(f'{n} {m}\n'+'\n'.join(g),'\n'.join(answer))
        put('1 1\n?','0');put('1 1\n*','*')
    elif pid=='P1036':
        for _ in range(150):
            n=rng.randint(2,13);k=rng.randint(1,n-1);a=[rng.randint(1,90) for i in range(n)]
            maximum=sum(a);prime=[True]*(maximum+1);prime[0]=prime[1]=False
            for p in range(2,math.isqrt(maximum)+1):
                if prime[p]:
                    for x in range(p*p,maximum+1,p):prime[x]=False
            answer=sum(prime[sum(row)] for row in itertools.combinations(a,k))
            put(f'{n} {k}\n'+' '.join(map(str,a)),answer)
        put('20 10\n'+'5000000 '*20,0)
        put('3 2\n1 1 1',3)
    elif pid=='P1067':
        for _ in range(220):
            n=rng.randint(0,100);a=[rng.choice([0,0,-1,1,rng.randint(-100,100)]) for i in range(n+1)]
            if a[0]==0:a[0]=rng.choice([-1,1,100,-100])
            terms=[]
            for p,c in zip(range(n,-1,-1),a):
                if not c:continue
                magnitude=('' if abs(c)==1 and p else str(abs(c)))+('x' if p else '')+('^'+str(p) if p>1 else '')
                terms.append(('-' if c<0 else '+')+magnitude)
            answer=''.join(terms).lstrip('+')
            put(str(n)+'\n'+' '.join(map(str,a)),answer)
        put('0\n0','0')
    elif pid=='P1088':
        for _ in range(180):
            n=rng.randint(3,7);perms=list(itertools.permutations(range(1,n+1)));start=rng.randrange(len(perms)-1);m=rng.randint(1,min(100,len(perms)-start-1))
            put(f'{n}\n{m}\n'+' '.join(map(str,perms[start])),' '.join(map(str,perms[start+m])))
        suffix=list(itertools.permutations(range(9995,10001)))[100]
        put('10000\n100\n'+' '.join(map(str,range(1,10001))),' '.join(map(str,[*range(1,9995),*suffix])))
    elif pid=='P1149':
        hist=matchstick_histogram()
        for n in range(1,25):put(n,hist[n])
    elif pid=='P1157':
        for n in range(2,11):
            for r in range(n+1):
                answer='\n'.join(''.join(f'{x:3d}' for x in row) for row in itertools.combinations(range(1,n+1),r))+'\n'
                put(f'{n} {r}',answer)
        for r in [1,2,19,20]:put(f'20 {r}','\n'.join(''.join(f'{x:3d}' for x in row) for row in itertools.combinations(range(1,21),r))+'\n')
    elif pid=='P1303':
        pairs=[('0','0'),('000','002'),('9'*2000,'9'*2000),('1'+'0'*2000,'1'+'0'*2000)]
        for _ in range(180):
            a=''.join(str(rng.randrange(10)) for i in range(rng.randint(1,450)))
            b=''.join(str(rng.randrange(10)) for i in range(rng.randint(1,450)));pairs.append((a,b))
        for a,b in pairs:put(a+'\n'+b,str(int(a)*int(b)))
    elif pid=='P1563':
        for _ in range(180):
            n,m=rng.randint(2,15),rng.randint(1,50);faces=[rng.randrange(2) for i in range(n)];commands=[(rng.randrange(2),rng.randint(1,n-1)) for i in range(m)];pos=0
            for direction,s in commands:
                delta=[[-1,1],[1,-1]][faces[pos]][direction]
                for i in range(s):pos=(pos+delta)%n
            inp=f'{n} {m}\n'+'\n'.join(f'{f} Person{i}' for i,f in enumerate(faces))+'\n'+'\n'.join(f'{d} {s}' for d,s in commands)
            put(inp,'Person'+str(pos))
    elif pid=='P1591':
        for n in [1,2,5,10,100,500,999,1000]:
            text=str(math.factorial(n));put('10\n'+'\n'.join(f'{n} {d}' for d in range(10)),'\n'.join(str(text.count(str(d))) for d in range(10)))
        for _ in range(70):
            pairs=[(rng.randint(1,1000),rng.randrange(10)) for i in range(rng.randint(1,10))]
            put(str(len(pairs))+'\n'+'\n'.join(f'{n} {d}' for n,d in pairs),'\n'.join(str(str(math.factorial(n)).count(str(d))) for n,d in pairs))
    elif pid=='P1618':
        catalog=ratio_catalog();queries=[(0,1,2),(1,2,3),(2,4,6),(7,8,9),(111,222,333),(997,998,999)]
        keys=[key for key in catalog if max(key)<=499]
        for _ in range(140):
            if rng.randrange(2):
                a,b,c=rng.choice(keys);scale=rng.randint(1,min(999//c,3));queries.append((a*scale,b*scale,c*scale))
            else:queries.append(tuple(sorted(rng.sample(range(1000),3))))
        for a,b,c in queries:
            g=math.gcd(a,math.gcd(b,c));answer=catalog.get((a//g,b//g,c//g),[])
            put(f'{a} {b} {c}','\n'.join(' '.join(map(str,row)) for row in sorted(answer)) if answer else 'No!!!')
    elif pid=='P1706':
        for n in range(1,8):put(n,'\n'.join(''.join(f'{x:5d}' for x in row) for row in itertools.permutations(range(1,n+1)))+'\n')
    elif pid=='P2089':
        catalog=chicken_catalog()
        for n in [*range(1,34),10000]:
            rows=catalog.get(n,[]);put(n,str(len(rows))+'\n'+'\n'.join(' '.join(map(str,row)) for row in rows))
    elif pid=='P3392':
        for _ in range(160):
            n,m=rng.randint(3,9),rng.randint(3,9);g=[''.join(rng.choice('WBR') for j in range(m)) for i in range(n)]
            answer=min(sum(g[i][j]!=('W' if i<a else 'B' if i<b else 'R') for i in range(n) for j in range(m)) for a,b in itertools.combinations(range(1,n),2))
            put(f'{n} {m}\n'+'\n'.join(g),answer)
        put('3 3\nWWW\nBBB\nRRR',0)
    elif pid=='P3654':
        for _ in range(200):
            r,c=rng.randint(1,9),rng.randint(1,9);k=rng.randint(1,min(r,c));g=[''.join(rng.choice('...#') for j in range(c)) for i in range(r)];placements=set()
            for x in range(r):
                for y in range(c):
                    for dx,dy in [(0,1),(1,0)]:
                        points=frozenset((x+i*dx,y+i*dy) for i in range(k))
                        if all(a<r and b<c and g[a][b]=='.' for a,b in points):placements.add(points)
            put(f'{r} {c} {k}\n'+'\n'.join(g),len(placements))
        for k in [1,2,100]:put(f'100 100 {k}\n'+('\n'.join(['.'*100]*100)),10000 if k==1 else 200*(101-k))
    elif pid=='P1045':
        with localcontext() as ctx:
            ctx.prec=80;logarithm=Decimal(2).log10()
            exponents=[1001,1279,1661,2136,10000,100000,1000000,3099999]+[rng.randint(1001,3099999) for _ in range(65)]
            for p in exponents:
                digits=int((p*logarithm).to_integral_value(rounding=ROUND_FLOOR))+1
                tail=f'{(pow(2,p,10**500)-1)%(10**500):0500d}'
                put(p,str(digits)+'\n'+'\n'.join(tail[i:i+50] for i in range(0,500,50)))
    elif pid=='P1065':
        for _ in range(180):
            m,n=rng.randint(1,8),rng.randint(1,8);order=list(range(n))*m;rng.shuffle(order)
            machines=[rng.sample(range(m),m) for i in range(n)];durations=[[rng.randint(1,20) for j in range(m)] for i in range(n)]
            occupied=[set() for i in range(m)];next_op=[0]*n;finish=[0]*n
            for j in order:
                op=next_op[j];next_op[j]+=1;which=machines[j][op];d=durations[j][op];start=finish[j]
                while any(t in occupied[which] for t in range(start,start+d)):start+=1
                occupied[which].update(range(start,start+d));finish[j]=start+d
            inp=f'{m} {n}\n'+' '.join(str(j+1) for j in order)+'\n'+'\n'.join(' '.join(str(j+1) for j in row) for row in machines)+'\n'+'\n'.join(' '.join(map(str,row)) for row in durations)
            put(inp,max(finish))
    elif pid=='P1518':
        for _ in range(110):
            density=rng.choice([0,.1,.3,.6,.9]);g=[['*' if rng.random()<density else '.' for j in range(10)] for i in range(10)]
            f,c=rng.sample(range(100),2);g[f//10][f%10]='F';g[c//10][c%10]='C';inp='\n'.join(map(''.join,g))
            transitions={}
            directions=[(-1,0),(0,1),(1,0),(0,-1)]
            for r in range(10):
                for col in range(10):
                    if g[r][col]=='*':continue
                    for d,(dr,dc) in enumerate(directions):
                        nr,nc=r+dr,col+dc
                        transitions[(r,col,d)]=(nr,nc,d) if 0<=nr<10 and 0<=nc<10 and g[nr][nc]!='*' else (r,col,(d+1)%4)
            state=((f//10,f%10,0),(c//10,c%10,0));seen=set();time=0
            while state not in seen and state[0][:2]!=state[1][:2]:
                seen.add(state);state=transitions[state[0]],transitions[state[1]];time+=1
            put(inp,time if state[0][:2]==state[1][:2] else 0)
    elif pid=='P3799':
        for _ in range(200):
            n=rng.randint(1,14);a=[rng.randint(1,10) for i in range(n)]
            answer=0
            for row in itertools.combinations(a,4):
                x,y,s,t=sorted(row);answer+=s==t and x+y==s
            put(str(n)+'\n'+'\n'.join(map(str,a)),answer)
        put('100000\n'+'1\n'*50000+'2\n'*50000,math.comb(50000,2)**2%1000000007)
        put('10000\n'+'\n'.join(str(x) for x in range(1,5001) for repeat in range(2)),sum((s-1)//2*4+(1 if s%2==0 else 0) for s in range(2,5001))%1000000007)
    assert values,pid
    return values
