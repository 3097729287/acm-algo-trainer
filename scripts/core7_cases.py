"""Independent oracles for the explicitly authored route entries."""
import math
import random
import itertools
from functools import lru_cache
from fractions import Fraction
from decimal import Decimal, ROUND_HALF_UP


def cases_for(pid):
    from core7_cases_recurrence import IDS as recurrence_ids,cases_for as recurrence_cases
    if pid in recurrence_ids:return recurrence_cases(pid)
    from core7_cases_greedy import IDS as greedy_ids,cases_for as greedy_cases
    if pid in greedy_ids:return greedy_cases(pid)
    from core7_cases_simulation import IDS,cases_for as simulation_cases
    if pid in IDS:return simulation_cases(pid)
    rng = random.Random(20261030)
    values = []
    def put(inp, expected):
        values.append((f'独立校验 {len(values)+1}', str(inp), str(expected)))
    if pid == 'B2002':
        put('', 'Hello,World!\n')
    elif pid == 'B2005':
        for c in 'A09*#@xz!':
            put(c, '  '+c+'\n '+c*3+'\n'+c*5+'\n')
    elif pid == 'B2025':
        put('', '  *\n ***\n*****\n ***\n  *\n')
    elif pid == 'B2029':
        for h, r in [(1,1),(500,100),(100,10),(1,100)]+[(rng.randint(1,500),rng.randint(1,100)) for _ in range(200)]:
            volume = 314*r*r*h
            # Independent definition: find the first bucket count meeting target.
            count=1
            while count*volume < 2000000:
                count+=1
            put(f'{h} {r}\n', count)
    elif pid == 'P1001':
        for a,b in [(-10**9,-10**9),(10**9,10**9),(0,0),(-1,1)]+[(rng.randint(-10**9,10**9),rng.randint(-10**9,10**9)) for _ in range(200)]:
            put(f'{a} {b}\n', a+b)
    elif pid == 'P1421':
        for total in list(range(400))+[100009]:
            count=0
            while (count+1)*19<=total:
                count+=1
            put(f'{total//10} {total%10}\n',count)
    elif pid == 'P1425':
        for a,b,c,d in [(12,50,19,10),(0,0,0,60),(0,60,2,0),(0,0,24,0)]+[(x//60,x%60,y//60,y%60) for x,y in [sorted(rng.sample(range(1441),2)) for _ in range(200)]]:
            duration = (c-a)*60+d-b
            put(f'{a} {b} {c} {d}\n',f'{duration//60} {duration%60}')
    elif pid == 'P3954':
        for _ in range(220):
            a,b,c=[rng.randrange(0,101,10) for _ in range(3)]
            put(f'{a} {b} {c}\n',a//10*2+b//10*3+c//10*5)
    elif pid == 'P5703':
        for a,b in [(1,1),(1,10**9),(10**9,1),(46340,46340)]+[(rng.randint(1,30000),rng.randint(1,30000)) for _ in range(200)]:
            put(f'{a} {b}\n',a*b)
    elif pid == 'P5704':
        for c in 'abcdefghijklmnopqrstuvwxyz':
            put(c,c.upper())
    elif pid == 'P5705':
        for n,d in [(100,0),(120,0),(101,9),(999,9)]+[(rng.randrange(100,1000),rng.randrange(10)) for _ in range(200)]:
            value=f'{n}.{d}'
            put(value, value[::-1])
    elif pid == 'P5706':
        for t,n in [(0,1),(10000,1000),(1,1000),(1,3)]+[(rng.randrange(10000001)/1000,rng.randrange(1,1001)) for _ in range(200)]:
            put(f'{t:.3f} {n}\n', f'{t/n:.3f}\n{2*n}')
    elif pid == 'P5707':
        for s,v in [(1,1),(100,99),(470,1),(471,1),(10000,1)]+[(rng.randrange(1,10001),rng.randrange(1,10001)) for _ in range(200)]:
            minutes=0
            while minutes*v < s:
                minutes+=1
            t=(480-minutes-10)%1440
            put(f'{s} {v}\n', f'{t//60:02d}:{t%60:02d}')
    elif pid == 'P5708':
        # Exact-area right triangles, scaled by an integer; no floating oracle.
        for a,b,c,area in [(3,4,5,6),(5,12,13,30),(8,15,17,60)]:
            for k in range(1,51):
                put(f'{a*k} {b*k} {c*k}\n',f'{area*k*k}.0')
    elif pid == 'P1035':
        for k in range(1,7):
            total=Fraction();n=0
            while total<=k:n+=1;total+=Fraction(1,n)
            put(f'{k}\n',n)
    elif pid == 'P1085':
        for _ in range(220):
            pairs=[(rng.randrange(10),rng.randrange(10)) for _ in range(7)]
            choices=[(a+b,-i) for i,(a,b) in enumerate(pairs,1) if a+b>8]
            put('\n'.join(f'{a} {b}' for a,b in pairs),-max(choices)[1] if choices else 0)
    elif pid == 'P1307':
        for n in [0,10,-380,1000,-1000,-1000000000,1000000000]+[rng.randrange(-10**9,10**9+1) for _ in range(200)]:
            put(n,(-1 if n<0 else 1)*int(str(abs(n))[::-1]))
    elif pid == 'P1422':
        for n in [1,149,150,151,399,400,401,10000]+list(range(500,10000,1000))+[rng.randrange(1,10001) for _ in range(200)]:
            units=[Decimal('0.4463') if i<=150 else Decimal('0.4663') if i<=400 else Decimal('0.5663') for i in range(1,n+1)]
            expected=sum(units,Decimal()).quantize(Decimal('.1'),rounding=ROUND_HALF_UP)
            put(n,str(expected))
    elif pid == 'P1424':
        for x in range(1,8):
            for n in list(range(1,32))+[1000000]:
                workdays=sum(((x-1+d)%7)<5 for d in range(n))
                put(f'{x} {n}\n',250*workdays)
    elif pid == 'P1888':
        for a,b,c in itertools.permutations([6,8,10]):
            put(f'{a} {b} {c}\n','3/5')
        for _ in range(200):
            scale=rng.randrange(1,10**7)
            sides=[3*scale,4*scale,5*scale];rng.shuffle(sides)
            put(' '.join(map(str,sides)),'3/5')
    elif pid == 'P2669':
        sequence=[]
        for x in range(1,150):sequence += [x]*x
        for k in list(range(1,100))+[rng.randrange(1,10001) for _ in range(200)]:
            put(k,sum(sequence[:k]))
    elif pid == 'P4956':
        for s in range(4,401):
            choices=[(x,k) for x in range(101) for k in range(1,134) if x+3*k==s]
            x,k=max(choices,key=lambda pair:(pair[0],-pair[1]));put(364*s,f'{x}\n{k}')
    elif pid == 'P5710':
        for x in range(1001):
            properties=[x%2==0,4<x<=12];n=sum(properties)
            put(x,f'{int(n==2)} {int(n>=1)} {int(n==1)} {int(n==0)}')
    elif pid == 'P5712':
        for n in range(101):put(n,f'Today, I ate {n} apple'+('s' if n>1 else '')+'.')
    elif pid == 'P5714':
        pairs=[(40000,2000),(41625,1500),(54000,1500),(120000,1400)]
        for h in range(1400,2001):
            for threshold in [Fraction(37,2),Fraction(24)]:
                exact=threshold*h*h/1000
                if exact.denominator==1 and 40000<=exact<=120000:
                    pairs += [(int(exact)+delta,h) for delta in [-1,0,1] if 40000<=int(exact)+delta<=120000]
        pairs += [(rng.randrange(40000,120001),rng.randrange(1400,2001)) for _ in range(200)]
        for M,H in pairs:
            b=Fraction(1000*M,H*H)
            put(f'{M/1000:.3f} {H/1000:.3f}', 'Underweight' if b<Fraction(37,2) else 'Normal' if b<24 else format(float(b),'.6g')+'\nOverweight')
    elif pid in ['P5716','P5737']:
        def leap(y):
            # Gregorian 400-year cycle: divisible by four except 100,200,300.
            return y%400%4==0 and y%400 not in [100,200,300]
        if pid=='P5716':
            for y,m in [(1900,2),(2000,2),(2100,2),(2024,2)]+[(rng.randrange(1582,3001),rng.randrange(1,13)) for _ in range(200)]:
                days=[31,28+leap(y),31,30,31,30,31,31,30,31,30,31][m-1]
                put(f'{y} {m}',days)
        else:
            for _ in range(200):
                x,y=sorted(rng.sample(range(1582,3001),2));years=[z for z in range(x,y+1) if leap(z)]
                put(f'{x} {y}',str(len(years))+'\n'+' '.join(map(str,years))+'\n')
    elif pid == 'P5720':
        for a in list(range(1,401))+[10**9,2**29-1,2**29,2**29+1]:put(a,a.bit_length())
    elif pid == 'P5722':
        for n in list(range(1,201))+[10000]:put(n,sum(range(1,n+1)))
    elif pid == 'P5725':
        for n in range(1,10):
            square=[''.join(f'{i*n+j+1:02d}' for j in range(n)) for i in range(n)]
            value=1;triangle=[]
            for row in range(1,n+1):
                triangle.append(' '*(2*(n-row))+''.join(f'{x:02d}' for x in range(value,value+row)));value+=row
            put(n,'\n'.join(square)+'\n\n'+'\n'.join(triangle)+'\n')
    elif pid == 'P1055':
        for _ in range(220):
            digits=[rng.randrange(10) for _ in range(9)];checksum=sum((i+1)*x for i,x in enumerate(digits))%11
            correct=str(checksum) if checksum<10 else 'X';given=rng.choice('0123456789X')
            prefix=f'{digits[0]}-'+''.join(map(str,digits[1:4]))+'-'+''.join(map(str,digits[4:]))+'-'
            put(prefix+given,'Right' if given==correct else prefix+correct)
    elif pid in ['P5726','P5738']:
        for _ in range(220):
            n=rng.randrange(1,12) if pid=='P5738' else 1;m=rng.randrange(3,21)
            rows=[[rng.randrange(11) for _ in range(m)] for _ in range(n)]
            means=[sum(sorted(row)[1:-1])/(m-2) for row in rows]
            header=f'{n} {m}' if pid=='P5738' else str(m)
            put(header+'\n'+'\n'.join(' '.join(map(str,row)) for row in rows),f'{max(means):.2f}')
    elif pid == 'P2433':
        answers=['I love Luogu!','6 4','3\n12\n2','166.667','15','10.8167','110\n90\n0','31.4159\n78.5398\n523.599','22','9','33.3333','13\nR','16','50']
        for i,answer in enumerate(answers,1):put(i,answer)
    elif pid == 'P1047':
        for _ in range(220):
            length=rng.randrange(1,61);m=rng.randrange(1,15)
            segments=[sorted(rng.choices(range(length+1),k=2)) for _ in range(m)]
            remaining=sum(not any(a<=x<=b for a,b in segments) for x in range(length+1))
            put(f'{length} {m}\n'+'\n'.join(f'{a} {b}' for a,b in segments),remaining)
    elif pid == 'P1161':
        for _ in range(200):
            # Two identical operations cancel, leaving the one-element operation.
            scale=rng.randrange(1000000,3000000);t=rng.randrange(1,80);target=rng.randrange(1,51)
            a=f'{scale//1000000}.{scale%1000000:06d}'
            put(f'3\n{a} {t}\n{a} {t}\n{target}.000000 1\n',target)
    elif pid == 'P1319':
        for _ in range(200):
            n=rng.randrange(1,15);bits=[rng.randrange(2) for _ in range(n*n)]
            lengths=[];bit=0;run=0
            for x in bits:
                if x==bit:run+=1
                else:lengths.append(run);run=1;bit=x
            lengths.append(run)
            expected='\n'.join(''.join(map(str,bits[i*n:(i+1)*n])) for i in range(n))
            put(str(n)+' '+' '.join(map(str,lengths)),expected)
    elif pid == 'P1321':
        for _ in range(200):
            length=rng.randrange(10,80);board=['.']*length;owners=[-1]*length;words=[]
            for step in range(25):
                word=rng.choice(['boy','girl']);start=rng.randrange(length-len(word)+1)
                candidate=owners[:]
                candidate[start:start+len(word)]=[len(words)]*len(word)
                if any(i not in candidate for i in range(len(words))):continue
                owners=candidate;board[start:start+len(word)]=word;words.append(word)
            put(''.join(board),f'{words.count("boy")}\n{words.count("girl")}')
    elif pid == 'P1428':
        for _ in range(220):
            n=rng.randrange(1,50);a=[rng.randrange(30) for _ in range(n)]
            answer=[sum(x<a[i] for x in a[:i]) for i in range(n)]
            put(str(n)+'\n'+' '.join(map(str,a)),' '.join(map(str,answer)))
    elif pid == 'P1597':
        for _ in range(220):
            state={'a':0,'b':0,'c':0};ops=[]
            for __ in range(rng.randrange(1,50)):
                left=rng.choice('abc');right=rng.choice('abc0123456789');ops.append(left+':='+right+';')
                state[left]=int(right) if right.isdigit() else state[right]
            put(''.join(ops),' '.join(str(state[x]) for x in 'abc'))
    elif pid == 'P1765':
        keyboard=['abc','def','ghi','jkl','mno','pqrs','tuv','wxyz',' ']
        for _ in range(220):
            s=''.join(rng.choices('abcdefghijklmnopqrstuvwxyz ',k=rng.randrange(1,150)))
            put(s,sum(next(group.index(c)+1 for group in keyboard if c in group) for c in s))
    elif pid == 'P2550':
        for _ in range(220):
            winning=set(rng.sample(range(1,34),7));tickets=[set(rng.sample(range(1,34),7)) for _ in range(rng.randrange(1,25))]
            counts=[len(ticket&winning) for ticket in tickets]
            inp=str(len(tickets))+'\n'+' '.join(map(str,winning))+'\n'+'\n'.join(' '.join(map(str,t)) for t in tickets)
            put(inp,' '.join(str(counts.count(h)) for h in range(7,0,-1)))
    elif pid == 'P5015':
        for _ in range(220):
            s=''.join(rng.choices('abXZ019 ',k=rng.randrange(1,51)));put(s,len(s.replace(' ','')))
    elif pid == 'P5727':
        for n in range(1,201):
            path=[];x=n
            while x!=1:path.append(x);x=x//2 if x%2==0 else 3*x+1
            put(n,' '.join(map(str,[1]+path[::-1])))
    elif pid == 'P5729':
        for _ in range(220):
            w,x,h=[rng.randrange(1,7) for _ in range(3)];q=rng.randrange(1,10);blocks=[]
            present={(i,j,k) for i in range(1,w+1) for j in range(1,x+1) for k in range(1,h+1)}
            for __ in range(q):
                a,d=sorted(rng.choices(range(1,w+1),k=2));b,e=sorted(rng.choices(range(1,x+1),k=2));c,f=sorted(rng.choices(range(1,h+1),k=2));blocks.append((a,b,c,d,e,f))
                present-={(i,j,k) for i in range(a,d+1) for j in range(b,e+1) for k in range(c,f+1)}
            put(f'{w} {x} {h} {q}\n'+'\n'.join(' '.join(map(str,b)) for b in blocks),len(present))
    elif pid == 'P5732':
        for n in range(1,21):
            put(n,'\n'.join(' '.join(str(math.comb(i,j)) for j in range(i+1)) for i in range(n)))
    elif pid == 'P1125':
        for _ in range(220):
            s=''.join(rng.choices('abcdefgh',k=rng.randrange(1,101)));counts=[s.count(c) for c in set(s)];d=max(counts)-min(counts)
            prime=d>=2 and sum(d%i==0 for i in range(1,d+1))==2
            put(s,'Lucky Word\n'+str(d) if prime else 'No Answer\n0')
    elif pid == 'P1553':
        for _ in range(220):
            left=str(rng.randrange(1000000000));right=str(rng.randrange(1,1000000000));kind=rng.choice(['','.','/','%'])
            inp=left+kind+(right if kind in './' and kind else '')
            l=str(int(left[::-1]));r=right[::-1].rstrip('0') or '0' if kind=='.' else str(int(right[::-1]))
            put(inp,l+kind+(r if kind in './' and kind else ''))
    elif pid == 'P1603':
        names=['zero','one','two','three','four','five','six','seven','eight','nine','ten','eleven','twelve','thirteen','fourteen','fifteen','sixteen','seventeen','eighteen','nineteen','twenty']
        mapping={s:i for i,s in enumerate(names)};mapping.update(a=1,both=2,another=1,first=1,second=2,third=3)
        for _ in range(220):
            words=rng.choices(list(mapping)+['hello','bye','unknown'],k=6);parts=[f'{mapping[w]**2%100:02d}' for w in words if w in mapping]
            answer=min(int(''.join(order)) for order in itertools.permutations(parts)) if parts else 0
            put(' '.join(words)+' .',answer)
    elif pid == 'P1957':
        for _ in range(220):
            n=rng.randrange(1,15);lines=[];output=[];op='a'
            for i in range(n):
                a,b=rng.randrange(10001),rng.randrange(10001)
                explicit=i==0 or rng.choice([True,False])
                if explicit:op=rng.choice('abc')
                lines.append((op+' ' if explicit else '')+f'{a} {b}')
                val={'a':a+b,'b':a-b,'c':a*b}[op];symbol={'a':'+','b':'-','c':'*'}[op]
                expr=f'{a}{symbol}{b}={val}';output += [expr,str(len(expr))]
            put(str(n)+'\n'+'\n'.join(lines),'\n'.join(output))
    elif pid == 'P2615':
        for n in range(1,40,2):
            # Closed-form odd-order Siamese square, independent of movement.
            square=[[n*((r+c+1+n//2)%n)+(r+2*c+1)%n+1 for c in range(n)] for r in range(n)]
            put(n,'\n'.join(' '.join(map(str,row)) for row in square))
    elif pid == 'P5734':
        for _ in range(220):
            original='abcdef';s=original;ops=[];output=[]
            for __ in range(30):
                t=rng.randrange(1,5);word=''.join(rng.choices('abcxyz',k=rng.randrange(1,6)))
                if t==1:ops.append('1 '+word);s+=word;output.append(s)
                elif t==2:
                    start=rng.randrange(len(s));length=rng.randrange(1,len(s)-start+1);ops.append(f'2 {start} {length}');s=s[start:start+length];output.append(s)
                elif t==3:
                    pos=rng.randrange(len(s)+1);ops.append(f'3 {pos} {word}');s=s[:pos]+word+s[pos:];output.append(s)
                else:ops.append('4 '+word);output.append(str(s.find(word)))
            put(str(len(ops))+'\n'+original+'\n'+'\n'.join(ops),'\n'.join(output))
    elif pid == 'CF2136A':
        @lru_cache(None)
        def possible(a,b,last=-1,run=0):
            if not a and not b:return True
            return any(possible(a-(team==0),b-(team==1),team,run+1 if team==last else 1)
                       for team,amount in [(0,a),(1,b)] if amount and (team!=last or run<2))
        data=[];answers=[]
        for _ in range(500):
            a,b,x,y=[rng.randrange(9) for __ in range(4)];data.append(f'{a} {b} {a+x} {b+y}');answers.append('YES' if possible(a,b) and possible(x,y) else 'NO')
        put(str(len(data))+'\n'+'\n'.join(data),'\n'.join(answers))
    elif pid == 'CF2136B':
        # Exhaustive strings and k values; output checker examines all intervals.
        data=[]
        for n in range(1,8):
            for bits in itertools.product('01',repeat=n):
                for k in range(1,n+1):data.append(f'{n} {k}\n'+''.join(bits))
        put(str(len(data))+'\n'+'\n'.join(data),'')
    elif pid == 'P3156':
        for _ in range(220):
            n=rng.randrange(1,61);m=rng.randrange(1,61);a=[rng.randrange(1,10**9) for _ in range(n)];qs=[rng.randrange(n) for _ in range(m)]
            put(f'{n} {m}\n'+' '.join(map(str,a))+'\n'+' '.join(str(x+1) for x in qs),'\n'.join(str(a[x]) for x in qs))
    elif pid == 'P5743':
        for n in range(1,21):put(n,3*2**(n-1)-2)
    elif pid == 'P9496':
        data=[];answers=[]
        for n in range(1,32):
            reachable={n}
            for step in range(3):
                for m in range(1,32):
                    if m in reachable and (n,m) not in data:data.append((n,m));answers.append(step)
                reachable |= {x|y for x in reachable for y in range(1,32)} | {x&y for x in reachable for y in range(1,32)}
        put(str(len(data))+'\n'+'\n'.join(f'{n} {m}' for n,m in data),'\n'.join(map(str,answers)))
    elif pid == 'P11033':
        boards=[]
        for _ in range(200):boards.append([[rng.randrange(2) for _ in range(5)] for __ in range(5)])
        for kind in range(12):
            a=[[0]*5 for _ in range(5)]
            cells=[(kind,i) for i in range(5)] if kind<5 else [(i,kind-5) for i in range(5)] if kind<10 else [(i,i if kind==10 else 4-i) for i in range(5)]
            for r,c in cells:a[r][c]=1
            boards.append(a)
        for a in boards:
            lines=list(a)+list(zip(*a))+[[a[i][i] for i in range(5)],[a[i][4-i] for i in range(5)]]
            put('\n'.join(' '.join(map(str,row)) for row in a),'Yes' if any(sum(line)==5 for line in lines) else 'No')
    elif pid == 'CF2135A':
        def neat(b):
            i=0
            while i<len(b):
                x=b[i]
                if i+x>len(b) or any(y!=x for y in b[i:i+x]):return False
                i+=x
            return True
        data=[];answers=[]
        for _ in range(250):
            n=rng.randrange(1,12);a=[rng.randrange(1,n+1) for _ in range(n)]
            best=max(sum(mask>>i&1 for i in range(n)) for mask in range(1<<n) if neat([a[i] for i in range(n) if mask>>i&1]))
            data.append(str(n)+'\n'+' '.join(map(str,a)));answers.append(str(best))
        put(str(len(data))+'\n'+'\n'.join(data),'\n'.join(answers))
    elif pid == 'P1449':
        def expression(depth):
            if depth==0 or rng.randrange(3)==0:
                x=rng.randrange(1,51);return f'{x}.',x
            l,a=expression(depth-1);r,b=expression(depth-1);op=rng.choice('+-*')
            return l+r+op,{'+' : a+b,'-':a-b,'*':a*b}[op]
        for _ in range(220):
            s,value=expression(3);put(s+'@',value)
        put('10.28.30./*7.-@',-7)
    elif pid == 'P1918':
        for _ in range(220):
            n=rng.randrange(1,60);a=rng.sample(range(1,1000),n);qs=rng.choices(a+list(range(1001,1050)),k=30)
            put(str(n)+'\n'+' '.join(map(str,a))+'\n'+str(len(qs))+'\n'+'\n'.join(map(str,qs)),'\n'.join(str(a.index(x)+1 if x in a else 0) for x in qs))
    elif pid == 'P2415':
        for _ in range(200):
            a=rng.sample(range(1,1001),rng.randrange(1,12));total=0
            for mask in range(1<<len(a)):total+=sum(a[i] for i in range(len(a)) if mask>>i&1)
            put(' '.join(map(str,a)),total)
    elif pid == 'P3405':
        for _ in range(220):
            n=rng.randrange(1,60);codes=['AA','AB','BA','BB','CC'];entries=[];used=set()
            for i in range(n):
                prefix=rng.choice(codes);state=rng.choice(codes);city=prefix+''.join(rng.choices('ABCDEFGHIJKLMNOP',k=4))
                entries.append((city,state))
            answer=sum(a[:2]==d and c[:2]==b and b!=d for i,(a,b) in enumerate(entries) for c,d in entries[i+1:])
            put(str(n)+'\n'+'\n'.join(a+' '+b for a,b in entries),answer)
    elif pid == 'P3613':
        for _ in range(220):
            boxes={};ops=[];answers=[]
            for __ in range(60):
                i,j=rng.randrange(1,21),rng.randrange(1,31)
                if not boxes or rng.randrange(3):
                    k=rng.randrange(6);boxes[i,j]=k;ops.append(f'1 {i} {j} {k}')
                else:
                    i,j=rng.choice(list(boxes));ops.append(f'2 {i} {j}');answers.append(str(boxes[i,j]))
            put(f'20 {len(ops)}\n'+'\n'.join(ops),'\n'.join(answers))
    elif pid == 'P4305':
        for _ in range(220):
            arrays=[[rng.randrange(-20,21) for i in range(rng.randrange(1,61))] for __ in range(3)]
            put(str(len(arrays))+'\n'+'\n'.join(str(len(a))+'\n'+' '.join(map(str,a)) for a in arrays),'\n'.join(' '.join(map(str,dict.fromkeys(a))) for a in arrays))
    elif pid == 'P5741':
        for _ in range(220):
            n=rng.randrange(1,30);names=[f'A{chr(65+i)}' for i in range(n)];scores=[[rng.randrange(51) for i in range(3)] for __ in range(n)]
            pairs=[]
            for i in range(n):
                for j in range(i+1,n):
                    if max(abs(x-y) for x,y in zip(scores[i],scores[j]))<=5 and abs(sum(scores[i])-sum(scores[j]))<=10:pairs.append(names[i]+' '+names[j])
            put(str(n)+'\n'+'\n'.join(name+' '+' '.join(map(str,s)) for name,s in zip(names,scores)),'\n'.join(pairs))
    elif pid == 'P9497':
        for _ in range(200):
            n=rng.randrange(1,4);a=[[rng.randrange(1,7) for i in range(n)] for __ in range(n)];qs=list(range(1,8));answers=[]
            for v in qs:
                arrangements=itertools.product(*(list(itertools.permutations(row)) for row in a))
                best=max(sum(any(matrix[r][c]>=v for r in range(n)) for c in range(n)) for matrix in arrangements)
                answers.append(str(best))
            put(f'{n} {len(qs)}\n'+'\n'.join(' '.join(map(str,row)) for row in a)+'\n'+'\n'.join(map(str,qs)),'\n'.join(answers))
    elif pid == 'P15320':
        @lru_cache(None)
        def alice_wins(a,turn):
            if len(a)==1:return a[0]==0
            outcomes=[]
            for mask in range(1<<len(a)):
                if mask.bit_count()<2:continue
                selected={a[i] for i in range(len(a)) if mask>>i&1};mex=0
                while mex in selected:mex+=1
                remaining=tuple(sorted([a[i] for i in range(len(a)) if not(mask>>i&1)]+[mex]))
                outcomes.append(alice_wins(remaining,1-turn))
                if outcomes[-1]==(turn==0):return turn==0
            return turn==1
        arrays=[list(a) for n in range(1,7) for a in itertools.combinations_with_replacement(range(4),n)]
        put(str(len(arrays))+'\n'+'\n'.join(str(len(a))+'\n'+' '.join(map(str,a)) for a in arrays),'\n'.join('Alice' if alice_wins(tuple(a),0) else 'Bob' for a in arrays))
    elif pid == 'P1152':
        for _ in range(220):
            n=rng.randrange(1,40);a=[rng.randrange(-200,201) for i in range(n)]
            if rng.randrange(3)==0:
                differences=list(range(1,n));rng.shuffle(differences);a=[0]
                for d in differences:a.append(a[-1]+rng.choice([-1,1])*d)
            ok=sorted(abs(a[i]-a[i-1]) for i in range(1,n))==list(range(1,n))
            put(str(n)+' '+' '.join(map(str,a)),'Jolly' if ok else 'Not jolly')
    elif pid == 'P1059':
        for _ in range(220):
            a=[rng.randrange(1,1001) for i in range(rng.randrange(1,101))];expected=sorted(set(a))
            put(str(len(a))+'\n'+' '.join(map(str,a)),str(len(expected))+'\n'+' '.join(map(str,expected)))
    elif pid == 'P1068':
        for _ in range(220):
            n=rng.randrange(5,50);m=rng.randrange(3,2*n//3+1)
            ids=rng.sample(range(1000,10000),n);rows=[(id,rng.randrange(1,101)) for id in ids]
            if rng.randrange(5)==0:rows=[(id,88) for id in ids]
            ordered=sorted(rows,key=lambda row:(-row[1],row[0]));cutoff=ordered[3*m//2-1][1];accepted=[x for x in ordered if x[1]>=cutoff]
            put(f'{n} {m}\n'+'\n'.join(f'{id} {s}' for id,s in rows),f'{cutoff} {len(accepted)}\n'+'\n'.join(f'{id} {s}' for id,s in accepted))
    elif pid == 'P1093':
        for _ in range(220):
            n=rng.randrange(5,40);scores=[[rng.randrange(101) for j in range(3)] for i in range(n)]
            if rng.randrange(4)==0:scores=[rng.choice([[80,90,90],[90,80,90],[90,90,80]]) for i in range(n)]
            order=sorted(range(n),key=lambda i:(-sum(scores[i]),-scores[i][0],i))[:5]
            put(str(n)+'\n'+'\n'.join(' '.join(map(str,row)) for row in scores),'\n'.join(f'{i+1} {sum(scores[i])}' for i in order))
    elif pid == 'P1104':
        for _ in range(220):
            n=rng.randrange(2,50);dates=[(rng.randrange(1960,2021),rng.randrange(1,13),rng.randrange(1,29)) for i in range(n)]
            if rng.randrange(3)==0:dates=[(2000,1,1)]*n
            order=sorted(range(n),key=lambda i:(*dates[i],-i))
            put(str(n)+'\n'+'\n'.join('Name'+str(i)+' '+' '.join(map(str,d)) for i,d in enumerate(dates)),'\n'.join('Name'+str(i) for i in order))
    elif pid == 'P1116':
        for _ in range(220):
            n=rng.randrange(1,50);a=rng.sample(range(1,1001),n);b=a[:];swaps=0
            for i in range(n):
                for j in range(n-1):
                    if b[j]>b[j+1]:b[j],b[j+1]=b[j+1],b[j];swaps+=1
            put(str(n)+'\n'+' '.join(map(str,a)),swaps)
        put('1000\n'+' '.join(map(str,range(1000,0,-1))),1000*999//2)
    elif pid == 'P1177':
        for _ in range(220):
            a=[rng.randrange(1,10**9+1) for i in range(rng.randrange(1,101))]
            if rng.randrange(4)==0:a=[7]*len(a)
            put(str(len(a))+'\n'+' '.join(map(str,a)),' '.join(map(str,sorted(a))))
        put('100000\n'+' '.join(map(str,range(100000,0,-1))),' '.join(map(str,range(1,100001))))
    elif pid == 'P1271':
        for _ in range(220):
            n=rng.randrange(1,1000);a=[rng.randrange(1,n+1) for i in range(rng.randrange(1,1001))]
            put(f'{n} {len(a)}\n'+' '.join(map(str,a)),' '.join(map(str,sorted(a))))
    elif pid == 'P1781':
        for _ in range(220):
            n=rng.randrange(1,21);votes=set()
            while len(votes)<n:votes.add(rng.randrange(10**rng.randrange(1,101)))
            a=list(votes);rng.shuffle(a);winner=max(range(n),key=a.__getitem__)
            put(str(n)+'\n'+'\n'.join(str(x) for x in a),f'{winner+1}\n{a[winner]}')
        put('2\n000999\n001000\n','2\n1000')
    elif pid == 'P1923':
        for _ in range(220):
            n=rng.randrange(1,51)*2-1;k=rng.randrange(n);a=[rng.randrange(1,30) for i in range(n)]
            put(f'{n} {k}\n'+' '.join(map(str,a)),sorted(a)[k])
        put('4999999 2499999\n'+'7 '*4999999,7)
    elif pid == 'P2676':
        for _ in range(220):
            n=rng.randrange(1,14);a=[rng.randrange(1,30) for i in range(n)];b=rng.randrange(1,sum(a)+1)
            best=min(mask.bit_count() for mask in range(1<<n) if sum(a[i] for i in range(n) if mask>>i&1)>=b)
            put(f'{n} {b}\n'+'\n'.join(map(str,a)),best)
    elif pid == 'P5143':
        for _ in range(220):
            n=rng.randrange(1,30);heights=rng.sample(range(-100,101),n);points=[(rng.randrange(-100,101),rng.randrange(-100,101),z) for z in heights]
            sequence=sorted(points,key=lambda p:p[2]);answer=math.fsum(math.dist(a,b) for a,b in zip(sequence,sequence[1:]))
            put(str(n)+'\n'+'\n'.join(' '.join(map(str,p)) for p in points),f'{answer:.3f}')
    return values
