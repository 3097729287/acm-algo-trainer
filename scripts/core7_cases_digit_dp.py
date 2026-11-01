"""Independent integer enumeration, partitions, block graphs and stream models."""
from collections import Counter,defaultdict
from functools import lru_cache
from itertools import permutations,product
from math import comb,factorial
import random

IDS={'P2657','P14074','P1836','P4798','P4999','SP17247','UVA1640','CF401D','P2518','P4124','P4127','P5128','P6218','P14084','SP10606','UVA1652','CF628D','CF1073E'}

def digit_sum(n):return sum(map(int,str(n)))
def windy(n):return all(abs(int(a)-int(b))>=2 for a,b in zip(str(n),str(n)[1:]))
def balanced(n):return all(count%2==1-digit%2 for digit,count in Counter(map(int,str(n))).items())
def telephone(n):
    s=str(n);return not ('4' in s and '8' in s) and any(s[i]==s[i+1]==s[i+2] for i in range(len(s)-2))

def odd_bit_numeric_prefix(n):
    if n<0:return 0
    answer=0;head=0;parity=0
    for remaining in range(n.bit_length()-1,-1,-1):
        if n>>remaining&1:
            wanted=1^parity
            if remaining==0:count,total=int(wanted==0),0
            elif remaining==1:count,total=1,wanted
            else:count,total=2**(remaining-1),2**(remaining-2)*(2**remaining-1)
            answer+=head*2**(remaining+1)*count+total
            head=head*2+1;parity^=1
        else:head*=2
    return answer+(n if parity else 0)

def restricted_growth(n):
    result=[]
    def visit(word,maximum):
        if len(word)==n:result.append(tuple(word));return
        for x in range(1,maximum+2):word.append(x);visit(word,max(maximum,x));word.pop()
    visit([],0);return result

@lru_cache(None)
def bell_mod(n):
    row=[1]
    for i in range(1,n+1):
        next_row=[row[-1]]
        for value in row:next_row.append((next_row[-1]+value)%1000007)
        row=next_row
    return row[0]

def zero_deleted_permutations(text):
    values=set();zeros=text.count('0')
    for removed in range(zeros+1):
        chars=list(text)
        for _ in range(removed):chars.remove('0')
        for word in set(permutations(chars)):
            if word and word[0]!='0':values.add(int(''.join(word)))
    return sum(x<int(text) for x in values)

def progression_value(n,base):
    digits=[]
    while n:digits.append(n%base);n//=base
    best=run=min(2,len(digits))
    for i in range(2,len(digits)):
        run=run+1 if digits[i]-digits[i-1]==digits[i-1]-digits[i-2] else 2;best=max(best,run)
    return best

@lru_cache(None)
def progression_complete_lengths(base,length):
    # Keep the actual maximum in the state; the production program instead
    # counts numbers avoiding each separately chosen threshold.
    mod=19260821;answer=base-1
    if length==1:return answer
    dp={(a,b,2,2):1 for a in range(1,base) for b in range(base)}
    answer+=2*(base-1)*base
    for size in range(3,length+1):
        totals=defaultdict(int);next_dp=defaultdict(int)
        for (a,b,run,best),count in dp.items():totals[b,best]=(totals[b,best]+count)%mod
        for (b,best),count in totals.items():
            for c in range(base):next_dp[b,c,2,best]=count
        for (a,b,run,best),count in dp.items():
            c=2*b-a
            if 0<=c<base:
                key=b,c,2,best;next_dp[key]=(next_dp[key]-count)%mod
                key=b,c,run+1,max(best,run+1);next_dp[key]=(next_dp[key]+count)%mod
        dp={key:value for key,value in next_dp.items() if value}
        answer=(answer+sum(key[3]*value for key,value in dp.items()))%mod
    return answer%mod

def block_graph(l,k,m):
    # Every possible literal block, with a separate comparison bit.
    mod=998244353;n=len(l);states=1<<n;bound=int(l,2);size=2*states
    matrix=[[0]*size for _ in range(size)];vector=[0]*size
    for v in range(bound+1):vector[v+states*int(v<bound)]=1
    for old in range(size):
        previous,loose=old%states,old//states
        for v in range(states):
            if previous.bit_count()+v.bit_count()>m or (not loose and v>bound):continue
            new=v+states*int(loose or v<bound);matrix[old][new]+=1
    def square(a):
        out=[[0]*size for _ in range(size)]
        for i in range(size):
            for j in range(size):
                if a[i][j]:
                    for h in range(size):out[i][h]=(out[i][h]+a[i][j]*a[j][h])%mod
        return out
    exponent=k-1
    while exponent:
        if exponent&1:vector=[sum(vector[i]*matrix[i][j] for i in range(size))%mod for j in range(size)]
        matrix=square(matrix);exponent//=2
    return sum(vector)%mod

def balanced_complete_lengths(maximum):
    # Fix the first actual digit, then insert equal digits into labelled slots.
    def for_first(first):
        dp=[1]+[0]*(maximum-1)
        for digit in range(10):
            if digit==first:
                allowed=range(0,maximum,2) if digit%2==0 else range(1,maximum,2)
            else:allowed=[0]+list(range(1 if digit%2==0 else 2,maximum,2))
            next_dp=[0]*maximum
            for used,count in enumerate(dp):
                if count:
                    for c in allowed:
                        if used+c<maximum:next_dp[used+c]+=count*comb(used+c,c)
            dp=next_dp
        return sum(dp)
    return 4*for_first(2)+5*for_first(1)

def zeckendorf(n):
    fibonacci=[1,2]
    while fibonacci[-1]<=n:fibonacci.append(sum(fibonacci[-2:]))
    bits=[]
    for weight in reversed(fibonacci[:-1]):
        bit=int(weight<=n);bits.append(bit);n-=bit*weight
    return bits

def numeric_fibonacci_stream_totals(n):
    if n==0:return 0,0
    bits=zeckendorf(n);dp={(False,False,True):(1,0,0)}
    for limit_bit in bits:
        next_dp={}
        for (started,previous,tight),(count,ones,length) in dp.items():
            for bit in range((limit_bit if tight else 1)+1):
                if previous and bit:continue
                ns=started or bit;key=(ns,bool(bit),tight and bit==limit_bit)
                old=next_dp.get(key,(0,0,0));next_dp[key]=(old[0]+count,old[1]+ones+bit*count,old[2]+length+ns*count)
        dp=next_dp
    return sum(x[2] for x in dp.values()),sum(x[1] for x in dp.values())

def fibonacci_stream_prefix(n):
    lo,hi=0,n
    while lo<hi:
        mid=(lo+hi+1)//2
        if numeric_fibonacci_stream_totals(mid)[0]<=n:lo=mid
        else:hi=mid-1
    length,ones=numeric_fibonacci_stream_totals(lo)
    return ones+sum(zeckendorf(lo+1)[:n-length])

def cases_for(pid):
    rng=random.Random(20261031);result=[]
    def put(inp,out):result.append((f'独立校验 {len(result)+1}',str(inp),str(out)))
    def row(xs):return ' '.join(map(str,xs))+'\n'
    if pid=='P2657':
        for a,b in [(1,1),(1,10),(25,50),(98,102),(10**9,10**9+3000),(2*10**9-3000,2*10**9)]+[(rng.randint(1,2000000),0) for _ in range(220)]:
            if b==0:b=a+rng.randrange(2000)
            put(f'{a} {b}\n',sum(windy(x) for x in range(a,b+1)))
    elif pid=='P14074':
        for a,b in [(1,1),(3,8),(1,10**9),(1,2**29-1),(999990000,10**9)]+[(rng.randint(1,10**9-3000),0) for _ in range(220)]:
            if b==0:b=a+rng.randrange(3000)
            expected=odd_bit_numeric_prefix(b)-odd_bit_numeric_prefix(a-1)
            if b-a<5000:assert expected==sum(x for x in range(a,b+1) if x.bit_count()%2)
            put(f'{a} {b}\n',expected)
    elif pid in {'P1836','P4999','SP17247'}:
        ranges=[(1,1),(1,9),(1,10),(9,10),(99,100)]+[(rng.randint(1,100000),0) for _ in range(220)]
        ranges=[(a,b or a+rng.randrange(1000)) for a,b in ranges]
        if pid=='P1836':
            prefix=[0]
            for x in range(1,100001):prefix.append(prefix[-1]+digit_sum(x))
            for n in [1,9,10,99,100,999,1000,99999,100000]+[rng.randint(1,100000) for _ in range(220)]:put(f'{n}\n',prefix[n])
            for exponent in range(1,10):put(str(10**exponent)+'\n',exponent*45*10**(exponent-1)+1)
        else:
            answers=[sum(digit_sum(x) for x in range(a,b+1)) for a,b in ranges]
            if pid=='SP17247':ranges.insert(0,(0,0));answers.insert(0,0);limit=15
            else:limit=18
            for exponent in range(1,limit+1):ranges.append((1,10**exponent));answers.append(exponent*45*10**(exponent-1)+1)
            for a in [10**limit-1000,10**limit-1]:ranges.append((a,10**limit));answers.append(sum(digit_sum(x) for x in range(a,10**limit+1)))
            batch=20 if pid=='P4999' else 100
            for start in range(0,len(ranges),batch):
                chosen=ranges[start:start+batch];expected=answers[start:start+batch]
                if pid=='P4999':expected=[x%1000000007 for x in expected]
                put(str(len(chosen))+'\n'+''.join(f'{a} {b}\n' for a,b in chosen),'\n'.join(map(str,expected)))
    elif pid=='P4798':
        for n in range(1,8):
            words=restricted_growth(n)
            choices=list(enumerate(words,1)) if n<=5 else rng.sample(list(enumerate(words,1)),min(90,len(words)))
            for rank,word in choices:put(str(n)+'\n'+row(word),rank)
        for n in [100,1000,10000]:
            put(str(n)+'\n'+row([1]*n),1);put(str(n)+'\n'+row(range(1,n+1)),bell_mod(n))
    elif pid=='UVA1640':
        ranges=[(1,1),(1,10),(100,1),(99999999,99999000)]+[(rng.randint(1,100000),rng.randint(1,100000)) for _ in range(80)]
        answers=[]
        for a,b in ranges:
            count=Counter(''.join(map(str,range(min(a,b),max(a,b)+1))));answers.append(' '.join(str(count[str(d)]) for d in range(10)))
        ranges.append((1,99999999));answers.append(' '.join(map(str,[68888889]+[80000000]*9)))
        put(''.join(f'{a} {b}\n' for a,b in ranges)+'0 0\n','\n'.join(answers))
    elif pid=='CF401D':
        for _ in range(180):
            length=rng.randint(1,8);text=str(rng.randint(1,9))+''.join(str(rng.randrange(10)) for _ in range(length-1));m=rng.randint(1,30)
            answer=sum(word[0]!='0' and int(''.join(word))%m==0 for word in set(permutations(text)));put(f'{text} {m}\n',answer)
        put('112233445566778899 1\n',factorial(18)//2**9)
        put('123456789012345678 1\n',(factorial(18)-factorial(17))//2**8)
        put('123456789012345678 100\n',0);put('1000000000000000000 100\n',1)
    elif pid=='P2518':
        for _ in range(180):
            length=rng.randint(1,8);text=str(rng.randint(1,9))+''.join(str(rng.randrange(5)) for _ in range(length-1));put(text+'\n',zero_deleted_permutations(text))
        for text,answer in [('1'+'0'*49,49),('1'*50,0),('1'*25+'2'*25,0),('9'+'1'*49,49)]:put(text+'\n',answer)
    elif pid=='P4124':
        for _ in range(200):
            a=rng.randrange(10**10,10**11-3000);b=a+rng.randrange(3000);put(f'{a} {b}\n',sum(telephone(x) for x in range(a,b+1)))
        for a,b in [(10**10,10**10+10000),(10**11-10000,10**11-1),(14444444444,14444444444),(14444444448,14444444448)]:put(f'{a} {b}\n',sum(telephone(x) for x in range(a,b+1)))
        def triples(q,leading):
            one,two=leading,0
            for _ in range(10):one,two=(one+two)*(q-1),one
            return leading*q**10-one-two
        put(f'{10**10} {10**11-1}\n',2*triples(9,8)-triples(8,7))
    elif pid=='P4127':
        for _ in range(180):
            a=rng.randrange(1,1000000);b=a+rng.randrange(1500);put(f'{a} {b}\n',sum(x%digit_sum(x)==0 for x in range(a,b+1)))
        for a,b in [(1,9),(10,19),(10**18-2000,10**18),(10**18,10**18)]:put(f'{a} {b}\n',sum(x%digit_sum(x)==0 for x in range(a,b+1)))
    elif pid=='P5128':
        for base in range(2,13):
            prefix=[0]
            for x in range(1,10001):prefix.append(prefix[-1]+progression_value(x,base))
            for n in [1,base-1,base,base*base-1,base*base,10000]+[rng.randint(1,10000) for _ in range(18)]:put(f'{n} {base}\n',prefix[n]%19260821)
        for base in [2,3,10,60]:
            full=progression_complete_lengths(base,18);put(f'{base**18-1} {base}\n',full);put(f'{base**18} {base}\n',(full+18)%19260821)
    elif pid=='P6218':
        for _ in range(220):
            a=rng.randint(1,2000000000-2000);b=a+rng.randrange(2000);put(f'{a} {b}\n',sum(bin(x)[2:].count('0')>=bin(x)[2:].count('1') for x in range(a,b+1)))
        for length in [1,2,10,20,30]:put(f'1 {2**length-1}\n',sum(comb(size-1,zeros) for size in range(1,length+1) for zeros in range((size+1)//2,size)))
    elif pid=='P14084':
        for _ in range(120):
            n=rng.randint(1,5);k=rng.randint(2,min(6,18//n));l=format(rng.randrange(1<<n),f'0{n}b');m=rng.randint(0,2*n);answer=0
            for value in range(int(l*k,2)+1):
                blocks=[(value>>(n*j))&((1<<n)-1) for j in range(k)];answer+=all(blocks[j].bit_count()+blocks[j+1].bit_count()<=m for j in range(k-1))
            put(f'{l}\n{k} {m}\n',answer)
        for _ in range(12):
            n=rng.randint(1,3);l=format(rng.randrange(1<<n),f'0{n}b');k=rng.randrange(10**17,10**18+1);m=rng.randrange(2*n+1);put(f'{l}\n{k} {m}\n',block_graph(l,k,m))
        for n in [1,2,60,200]:
            k=10**18;put('1'*n+f'\n{k} {2*n}\n',pow(2,n*k,998244353));put('1'*n+f'\n{k} 0\n',1);put('0'*n+f'\n{k} {n}\n',1)
    elif pid=='SP10606':
        ranges=[(1,9),(1,1000),(1,9999)]+[(rng.randint(1,100000),0) for _ in range(220)]
        ranges=[(a,b or a+rng.randrange(2000)) for a,b in ranges];answers=[sum(balanced(x) for x in range(a,b+1)) for a,b in ranges]
        ranges.append((1,10**19));answers.append(balanced_complete_lengths(19))
        for value in [10**19,10**19-1,777777777777777777,7777777777777777777,2*10**17,2*10**18]:ranges.append((value,value));answers.append(int(balanced(value)))
        put(str(len(ranges))+'\n'+''.join(f'{a} {b}\n' for a,b in ranges),'\n'.join(map(str,answers)))
    elif pid=='UVA1652':
        stream=''
        for length in range(1,17):
            for word in product('01',repeat=length-1):
                text='1'+''.join(word)
                if '11' not in text:stream+=text
        prefix=[0]
        for c in stream:prefix.append(prefix[-1]+(c=='1'))
        positions=[0,1,2,3,4,5,6,20,21,len(stream)]+[rng.randrange(len(stream)+1) for _ in range(900)]
        assert all(prefix[n]==fibonacci_stream_prefix(n) for n in positions[:20])
        put('\n'.join(map(str,positions))+'\n','\n'.join(str(prefix[n]) for n in positions))
        positions=[10**15,10**15-1,10**12,10**9,10**6,0];put('\n'.join(map(str,positions))+'\n','\n'.join(str(fibonacci_stream_prefix(n)) for n in positions))
    elif pid=='CF628D':
        def magic(x,d,m):return x%m==0 and all((int(c)==d)==(i%2==1) for i,c in enumerate(str(x)))
        for _ in range(180):
            length=rng.randint(1,5);a=rng.randint(10**(length-1),10**length-1);b=min(10**length-1,a+rng.randrange(2000));d=rng.randrange(10);m=rng.randint(1,100);put(f'{m} {d}\n{a}\n{b}\n',sum(magic(x,d,m) for x in range(a,b+1)))
        length=2000;a='1'+'0'*(length-1);b='9'*length
        put(f'1 0\n{a}\n{b}\n',pow(9,1000,1000000007));put(f'1 7\n{a}\n{b}\n',8*pow(9,999,1000000007)%1000000007)
        put(f'2000 0\n{a}\n{b}\n',0)
        text='17'*1000;put(f'1999 7\n{text}\n{text}\n',int(int(text)%1999==0))
    elif pid=='CF1073E':
        for _ in range(220):
            a=rng.randint(1,10**8);b=a+rng.randrange(2000);k=rng.randint(1,10);put(f'{a} {b} {k}\n',sum(x for x in range(a,b+1) if len(set(str(x)))<=k)%998244353)
        bound=10**18-1;put(f'1 {bound} 10\n',bound*(bound+1)//2%998244353)
        put(f'1 {bound} 1\n',sum(int(str(d)*length) for length in range(1,19) for d in range(1,10))%998244353)
    else:raise KeyError(pid)
    return result
