"""Small-domain enumeration and independent arithmetic/output oracles."""
from collections import deque
from decimal import Decimal,localcontext,ROUND_HALF_UP
from functools import lru_cache
import itertools
import math
import random

IDS=set('P2345 P1002 P1010 P1044 P1226 P1257 P1464 P2437 CF873B P1228 P1498 P1908 P1928 AT_agc005_b AT_joisc2014_h P2717 P7167 SP32079'.split())

def cases_for(pid):
    assert pid in IDS,pid
    rng=random.Random(20261101);values=[]
    def put(inp,answer):values.append((f'独立校验 {len(values)+1}',str(inp),str(answer)))
    def array(a):return str(len(a))+'\n'+' '.join(map(str,a))+'\n'
    if pid=='P2345':
        for _ in range(180):
            n=rng.randint(1,55);coordinates=rng.sample(range(1,20001),n)
            cows=[(rng.choice([1,20000,rng.randint(1,50)]),x) for x in coordinates]
            expected=sum(max(v,w)*abs(x-y) for (v,x),(w,y) in itertools.combinations(cows,2))
            put(str(n)+'\n'+'\n'.join(f'{v} {x}' for v,x in cows),expected)
        n=20000;put(str(n)+'\n'+'\n'.join(f'20000 {i}' for i in range(1,n+1)),20000*n*(n*n-1)//6)
    elif pid=='P1002':
        # Count unrestricted monotone paths with binomial coefficients, then
        # subtract paths by their first controlled point (not a grid DP).
        def paths(x,y):return math.comb(x+y,x) if x>=0 and y>=0 else 0
        tests=[]
        for n in range(1,8):
            for m in range(1,8):
                for _ in range(8):tests.append((n,m,rng.randint(0,9),rng.randint(0,9)))
        tests += [(20,20,20,20),(20,20,0,20),(20,20,20,0),(20,20,10,10),(1,1,20,20)]
        for n,m,hx,hy in tests:
            forbidden=sorted((x,y) for x in range(n+1) for y in range(m+1)
                             if (x==hx and y==hy) or abs(x-hx)*abs(y-hy)==2)
            if (0,0) in forbidden:continue # excluded by the official guarantee
            first=[]
            for x,y in forbidden:
                first.append(paths(x,y)-sum(count*paths(x-u,y-v) for (u,v),count in zip(forbidden,first)))
            expected=paths(n,m)-sum(count*paths(n-x,m-y) for (x,y),count in zip(forbidden,first))
            put(f'{n} {m} {hx} {hy}',expected)
    elif pid=='P1010':
        # Bottom-up table of expressions, independently of recursive printing.
        expression={0:'0',1:'2(0)'}
        for number in range(2,20001):
            pieces=[]
            for exponent in range(number.bit_length()-1,-1,-1):
                if number&(1<<exponent):pieces.append('2' if exponent==1 else '2('+expression[exponent]+')')
            expression[number]='+'.join(pieces)
        tests=list(range(1,65))+[137,1315,16383,16384,19999,20000]+rng.sample(range(65,20000),150)
        for n in tests:put(n,expression[n])
    elif pid=='P1044':
        for n in range(1,10):
            outputs=set()
            def visit(next_value,stack,output):
                if len(output)==n:outputs.add(output);return
                if next_value<=n:visit(next_value+1,stack+(next_value,),output)
                if stack:visit(next_value,stack[:-1],output+(stack[-1],))
            visit(1,(),());put(n,len(outputs))
        for n in range(10,19):put(n,math.comb(2*n,n)//(n+1))
    elif pid=='P1226':
        tests=[(0,1,2),(1,0,2),(2,10,9),(2147483647,2147483647,2147483647),(2147483647,2147483646,2147483646)]
        tests += [(rng.randrange(2**31),rng.randrange(2**31),rng.randrange(2,2**31)) for _ in range(200)]
        for a,b,p in tests:put(f'{a} {b} {p}',f'{a}^{b} mod {p}={pow(a,b,p)}')
    elif pid=='P1257':
        def show(square):
            with localcontext() as context:
                context.prec=80
                return str(Decimal(square).sqrt().quantize(Decimal('.0001'),rounding=ROUND_HALF_UP))
        inputs=[[(0,0),(10**9,10**9)],[(5,5),(5,5)],[(0,0),(1,1)],[(0,0),(10000,1)],[(0,0),(1,10000)]]
        for _ in range(180):
            n=rng.randint(2,40)
            inputs.append([(rng.randrange(10**9+1),rng.randrange(10**9+1)) for _ in range(n)])
        inputs += [[(0,i*57) for i in range(30)],[(i//3,i%3) for i in range(30)]]
        for points in inputs:
            square=min((x-u)**2+(y-v)**2 for (x,y),(u,v) in itertools.combinations(points,2))
            put(str(len(points))+'\n'+'\n'.join(f'{x} {y}' for x,y in points),show(square))
        put('10000\n'+'\n'.join(f'{i*100000} 0' for i in range(10000)),'100000.0000')
        put('10000\n'+'\n'.join(f'0 {i}' for i in range(10000)),'1.0000')
    elif pid=='P1464':
        table=[[[1]*21 for _ in range(21)] for _ in range(21)]
        for a in range(1,21):
            for b in range(1,21):
                for c in range(1,21):
                    if a<b<c:table[a][b][c]=table[a][b][c-1]+table[a][b-1][c-1]-table[a][b-1][c]
                    else:table[a][b][c]=table[a-1][b][c]+table[a-1][b-1][c]+table[a-1][b][c-1]-table[a-1][b-1][c-1]
        triples=list(itertools.product([-2**63,-1,0,1,2,19,20,21,2**63-1],repeat=3))
        triples += [(rng.randint(-2,25),rng.randint(-2,25),rng.randint(-2,25)) for _ in range(700)]
        triples=[q for q in triples if q!=(-1,-1,-1)]
        def answer(a,b,c):
            if min(a,b,c)<=0:return 1
            if max(a,b,c)>20:return table[20][20][20]
            return table[a][b][c]
        put('\n'.join(f'{a} {b} {c}' for a,b,c in triples)+'\n-1 -1 -1',
            '\n'.join(f'w({a}, {b}, {c}) = {answer(a,b,c)}' for a,b,c in triples))
    elif pid=='P2437':
        tests=[(1,2),(1,3),(1,14),(1,1000),(999,1000)]
        tests += [tuple(sorted(rng.sample(range(1,1001),2))) for _ in range(90)]
        for m,n in tests:
            d=n-m
            # Choose positions of all two-step moves among the total moves.
            put(f'{m} {n}',sum(math.comb(d-twos,twos) for twos in range(d//2+1)))
    elif pid=='CF873B':
        strings=[''.join(bits) for n in range(1,8) for bits in itertools.product('01',repeat=n)]
        strings += [''.join(rng.choices('01',k=rng.randint(8,75))) for _ in range(100)]
        for s in strings:
            answer=0
            for l in range(len(s)):
                zeros=ones=0
                for r in range(l,len(s)):
                    if s[r]=='0':zeros+=1
                    else:ones+=1
                    if zeros==ones:answer=max(answer,r-l+1)
            put(f'{len(s)}\n{s}',answer)
        put('100000\n'+'01'*50000,100000);put('100000\n'+'1'*100000,0)
    elif pid=='P1228':
        # Output is checked by independently painting all three cells per tile.
        for k in range(1,5):
            for x in range(1,2**k+1):
                for y in range(1,2**k+1):put(f'{k}\n{x} {y}','SPJ')
        for k,x,y in [(10,1,1),(10,512,513),(10,1024,1024),(9,219,312)]:put(f'{k}\n{x} {y}','SPJ')
    elif pid=='P1498':
        # Lucas' parity rule generates the triangular pattern directly; this
        # oracle never recursively places three copies of a smaller picture.
        for n in range(1,11):
            height=2**n;canvas=[[' ']*(2*height) for _ in range(height)]
            for level in range(height//2):
                for j in range(level+1):
                    if j&level!=j:continue
                    column=height-2-2*level+4*j
                    for offset,c in enumerate(' /\\'):canvas[2*level][column+offset]=c
                    for offset,c in enumerate('/__\\'):canvas[2*level+1][column+offset]=c
            put(n,'\n'.join(''.join(row).rstrip() for row in canvas))
    elif pid=='P1908':
        inputs=[list(a) for n in range(1,6) for a in itertools.product(range(1,4),repeat=n)]
        inputs += [[rng.randint(1,10**9) for _ in range(rng.randint(1,70))] for _ in range(180)]
        for a in inputs:put(array(a),sum(a[i]>a[j] for i in range(len(a)) for j in range(i+1,len(a))))
        n=500000;put(array(list(range(n,0,-1))),n*(n-1)//2);put(array([10**9]*n),0)
    elif pid=='P1928':
        # Use a token stack with explicit repetition markers for nested groups.
        def iterative(s):
            stack=[];i=0
            while i<len(s):
                c=s[i]
                if c=='[':
                    i+=1;j=i
                    while s[i].isdigit():i+=1
                    stack.append(int(s[j:i]));continue
                if c==']':
                    parts=[]
                    while isinstance(stack[-1],str):parts.append(stack.pop())
                    count=stack.pop();stack.append(''.join(reversed(parts))*count)
                else:stack.append(c)
                i+=1
            return ''.join(stack)
        inputs=['A','AC[3FUN]','[12A]','[2[2CB]]','[99AB][3CD]','[1'*10+'Z'+']'*10,'[99[99A]]','[99AB][99CD]']
        def expression(depth):
            if depth==0 or rng.randrange(3)==0:return ''.join(rng.choices('ABCXYZ',k=rng.randint(1,5)))
            return '['+str(rng.randint(1,4))+expression(depth-1)+']'+expression(0)
        inputs += [expression(4) for _ in range(180)]
        for s in inputs:put(s,iterative(s))
    elif pid=='AT_agc005_b':
        inputs=[list(a) for n in range(1,6) for a in itertools.permutations(range(1,n+1))]
        for _ in range(180):
            a=list(range(1,rng.randint(6,55)));rng.shuffle(a);inputs.append(a)
        for a in inputs:
            answer=0
            for l in range(len(a)):
                smallest=10**9
                for r in range(l,len(a)):smallest=min(smallest,a[r]);answer+=smallest
            put(array(a),answer)
        n=200000;put(array(list(range(1,n+1))),n*(n+1)*(n+2)//6)
        put(array(list(range(n,0,-1))),n*(n+1)*(n+2)//6)
    elif pid=='AT_joisc2014_h':
        strings=[''.join(s) for n in range(1,7) for s in itertools.product('JOI',repeat=n)]
        strings += [''.join(rng.choices('JOI',k=rng.randint(7,75))) for _ in range(100)]
        for s in strings:
            best=0
            for l in range(len(s)):
                counts={'J':0,'O':0,'I':0}
                for r in range(l,len(s)):
                    counts[s[r]]+=1
                    if len(set(counts.values()))==1:best=max(best,r-l+1)
            put(f'{len(s)}\n{s}',best)
        put('200000\n'+'JOI'*66666+'JO',199998);put('200000\n'+'J'*200000,0)
    elif pid=='P2717':
        for n in range(1,6):
            for a in itertools.product(range(1,4),repeat=n):
                for k in range(1,4):
                    answer=0
                    for l in range(n):
                        total=0
                        for r in range(l,n):total+=a[r];answer+=total>=k*(r-l+1)
                    put(f'{n} {k}\n'+' '.join(map(str,a)),answer)
        for _ in range(130):
            n=rng.randint(1,60);k=rng.randint(1,10000);a=[rng.randint(1,10000) for _ in range(n)]
            put(f'{n} {k}\n'+' '.join(map(str,a)),sum(sum(a[l:r])>=k*(r-l) for l in range(n) for r in range(l+1,n+1)))
        n=100000;put(f'{n} 10000\n'+'10000 '*n,n*(n+1)//2);put(f'{n} 10000\n'+'1 '*n,0)
    elif pid=='P7167':
        for _ in range(150):
            n=rng.randint(2,50);diameter=[rng.randint(1,10) for _ in range(n)];capacity=[rng.randint(1,10) for _ in range(n)]
            queries=[(rng.randrange(n),rng.randint(1,200)) for _ in range(65)]+[(i,capacity[i]) for i in range(n)]
            answers=[]
            for start,water in queries:
                u=start
                while True:
                    if water<=capacity[u]:answers.append(u+1);break
                    water-=capacity[u];candidates=[v for v in range(u+1,n) if diameter[v]>diameter[u]]
                    if not candidates:answers.append(0);break
                    u=candidates[0]
            put(f'{n} {len(queries)}\n'+'\n'.join(f'{d} {c}' for d,c in zip(diameter,capacity))+'\n'+
                '\n'.join(f'{u+1} {v}' for u,v in queries),'\n'.join(map(str,answers)))
        n=100000;queries=[(1,1),(1,n),(1,n+1),(n,1),(n,2),(50000,50001),(50000,50002),(1,10**9)]
        put(f'{n} {len(queries)}\n'+'\n'.join(f'{i} 1' for i in range(1,n+1))+'\n'+
            '\n'.join(f'{u} {v}' for u,v in queries),'\n'.join(str(u+v-1 if v<=n-u+1 else 0) for u,v in queries))
    elif pid=='SP32079':
        inputs=[list(a) for n in range(1,5) for a in itertools.product(range(4),repeat=n)]
        inputs += [[rng.randint(0,10**6) for _ in range(rng.randint(1,65))] for _ in range(160)]
        inputs += [[0,0,12,0,6,3,0],[2**k for k in range(19,-1,-1)]]
        for a in inputs:
            total=0
            for l in range(len(a)):
                g=0
                for r in range(l,len(a)):g=math.gcd(g,a[r]);total+=g
            put(array(a),total)
        n=300000;put(array([10**6]*n),10**6*n*(n+1)//2);put(array([0]*n),0)
    else:raise AssertionError(pid)
    return values
