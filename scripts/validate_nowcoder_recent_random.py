"""Brute partitions, literal range updates, substring sets and digit predicates."""
from collections import Counter
from itertools import combinations, product, permutations
from functools import lru_cache
import math,random,time,subprocess
from validate_nowcoder_optimized_random import check, COUNTS, LEDGER, PERFORMANCE
from nowcoder_editorials import OUT,write
RNG=random.Random(2026110813)


def strings():
    for _ in range(45):
        s=''.join(RNG.choice('abc') for i in range(RNG.randint(1,12)))
        counts=Counter(s[l:r] for l in range(len(s)) for r in range(l+1,len(s)+1))
        check(237304,s,len(counts))
        check(237650,s,max([len(t)*v for t,v in counts.items() if v>1]+[0]))
        check(237661,s,[max(v for t,v in counts.items() if len(t)==length) for length in range(1,len(s)+1)])
        query=[(RNG.randint(1,len(s)),RNG.randint(1,len(s))) for i in range(15)]
        query=[(min(l,r),max(l,r)) for l,r in query]
        check(237662,s+'\n'+str(len(query))+'\n'+'\n'.join(f'{l} {r}' for l,r in query),[counts[s[l-1:r]] for l,r in query])
        t=''.join(RNG.choice('abc') for i in range(RNG.randint(1,12)))
        other={t[l:r] for l in range(len(t)) for r in range(l+1,len(t)+1)}
        check(237308,s+'\n'+t,len(counts.keys()&other))
        check(236737,str(len(s))+'\n'+s,max(len(t)*v for t,v in counts.items() if t==t[::-1]))
        p,q=RNG.randint(1,10),RNG.randint(1,10)
        dp=[0]+[10**9]*len(s)
        for i in range(1,len(s)+1):
            dp[i]=dp[i-1]+p
            for length in range(1,i+1):
                if s[i-length:i] in s[:i-length]: dp[i]=min(dp[i],dp[i-length]+q)
        check(237664,f'{s}\n{p} {q}',dp[-1])
        patterns=[''.join(RNG.choice('abc') for i in range(RNG.randint(1,5))) for j in range(RNG.randint(1,6))]
        check(234273,str(len(patterns))+'\n'+'\n'.join(patterns)+'\n'+s,[sum(s.startswith(t,i) for i in range(len(s))) for t in patterns])
    for _ in range(35):
        patterns=[''.join(RNG.choice('ABC') for i in range(RNG.randint(1,3))) for j in range(RNG.randint(1,5))]
        m=RNG.randint(1,4)
        # Independent ordinary 26-transition AC via longest relevant suffix strings.
        prefixes={''}|{s[:i] for s in patterns for i in range(1,len(s)+1)}
        dp={'':1}
        for i in range(m):
            next_dp=Counter()
            for state,count in dp.items():
                for ch in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                    text=state+ch
                    if any(text.endswith(p) for p in patterns): continue
                    to=max((p for p in prefixes if text.endswith(p)),key=len)
                    next_dp[to]+=count
            dp=next_dp
        expected=(26**m-sum(dp.values()))%10007
        data=f'{len(patterns)} {m}\n'+'\n'.join(patterns)
        check(20155,data,expected);check(234268,data,expected)


def digits():
    for _ in range(30):
        l=RNG.randint(0,500);r=l+RNG.randint(1,700)
        check(233097,f'{l} {r}\n-1 -1',sum(str(x).count('0') for x in range(l,r+1)))
        l=max(1,l)
        check(20491,f'{l} {r}',[sum(str(x).count(str(d)) for x in range(l,r+1)) for d in range(10)])
        check(15035,f'{l} {r}\n0 0',sum('4' in str(x) or '38' in str(x) for x in range(l,r+1)))
        check(20665,f'{l} {r}\n0 0',sum(x%7==0 and sum(map(int,str(x)))%7==0 for x in range(l,r+1)))
        check(232847,f'1\n{l} {r}',sum(all(x%int(d)==0 for d in str(x) if d!='0') for x in range(l,r+1)))
        constraints=[(RNG.randint(1,9),RNG.randint(0,3)) for i in range(5)]
        limits={d:min(k for digit,k in constraints if digit==d) for d,k in constraints}
        def good(x):
            text=str(x)
            for d,limit in limits.items():
                if str(d)*(limit+1) in text:return False
            return True
        check(20669,f'1\n{l} {r} 5\n'+'\n'.join(f'{d} {k}' for d,k in constraints),sum(good(x) for x in range(l,r+1)))
        bound=RNG.randint(1,10000)
        check(17385,f'1\n{bound}',f'Case 1: {sum(x%sum(map(int,str(x)))==0 for x in range(1,bound+1))}')
    query=[(0,20000),(10000,10086),(10007,10007)]
    answer=0
    for l,r in query:
        count=0
        for x in range(l,r+1):
            it=iter(str(x))
            count+=all(any(c==d for c in it) for d in '007')
        answer^=count
    check(19327,str(len(query))+'\n'+'\n'.join(f'{l} {r}' for l,r in query),answer)


def partitions():
    for _ in range(40):
        n=RNG.randint(1,9);a=[RNG.randint(1,5) for i in range(n)]
        best=10**9;c=RNG.randint(1,5);discount=10**9
        for mask in range(1<<(n-1)):
            parts=[];start=0
            for i in range(n):
                if i==n-1 or mask>>i&1:parts.append(a[start:i+1]);start=i+1
            best=min(best,sum(len(set(p))**2 for p in parts))
            discount=min(discount,sum(sum(p)-sum(sorted(p)[:len(p)//c]) for p in parts))
        check(210805,str(n)+'\n'+' '.join(map(str,a)),best)
        check(232855,f'{n} {c}\n'+' '.join(map(str,a)),discount)
        k=RNG.randint(2,min(4,n+1))
        check(54585,f'{n} {k}\n'+' '.join(map(str,a)),sum(all(a[c[i]]<a[c[i+1]] for i in range(k-1)) for c in combinations(range(n),k)))
        inversions=sum(sum(p[i]>p[j] for i in range(len(p)) for j in range(i+1,len(p))) for l in range(n) for r in range(l+1,n+1) for p in [a[l:r]])
        check(14522,str(n)+'\n'+' '.join(map(str,a)),inversions)
        check(210689,str(n)+'\n'+' '.join(map(str,a))+'\n'+str(n)+'\n'+'\n'.join(map(str,range(1,n+1))),
              [sum(len(set(a[i:i+length])) for i in range(n-length+1)) for length in range(1,n+1)])
        m=RNG.randint(0,n-1);optimal=10**9;ways=0
        for mask in range(1<<(n-1)):
            if mask.bit_count()>m:continue
            sums=[];value=0
            for i,x in enumerate(a):
                value+=x
                if i==n-1 or mask>>i&1:sums.append(value);value=0
            cost=max(sums)
            if cost<optimal:optimal=cost;ways=1
            elif cost==optimal:ways+=1
        check(19972,f'{n} {m}\n'+' '.join(map(str,a)),f'{optimal} {ways}')
    for n in range(1,8):
        full=[x for p in permutations(range(1,n+1)) for x in p]
        query=[];answer=[]
        for m in range(1,n+1):
            query.append(f'{n} {m}')
            target=set(range(1,m+1))
            answer.append(sum(set(full[i:i+m])==target for i in range(len(full)-m+1)))
        check(229299,str(n)+'\n'+'\n'.join(query),answer)


def ranges_and_trees():
    for _ in range(35):
        n=RNG.randint(1,12);a=[RNG.randint(-10,15) for i in range(n)];current=a.copy()
        ops=[];answer=[]
        for j in range(30):
            l=RNG.randint(1,n);r=RNG.randint(l,n)
            if RNG.randrange(2):
                x=RNG.randint(-5,5);ops.append(f'1 {l} {r} {x}')
                for k in range(l-1,r):current[k]+=x
            else:
                ops.append(f'2 {l} {r}');answer.append(sum(current[i]*current[j] for i in range(l-1,r) for j in range(i+1,r)))
        check(25879,f'{n} {len(ops)}\n'+' '.join(map(str,a))+'\n'+'\n'.join(ops),answer)
        current=a.copy();ops=[];answer=[]
        for j in range(30):
            if RNG.randrange(2):
                p=RNG.randrange(n);v=RNG.randint(-10,15);ops.append(f'1 {p+1} {v}');current[p]=v
            else:
                l=RNG.randint(1,n);r=RNG.randint(l,n);ops.append(f'0 {l} {r}')
                answer.append(max(sum(current[i:j]) for i in range(l-1,r) for j in range(i+1,r+1)
                                  if all(current[t]%2!=current[t+1]%2 for t in range(i,j-1))))
        check(15162,f'{n} {len(ops)}\n'+' '.join(map(str,a))+'\n'+'\n'.join(ops),answer)
        n=RNG.randint(1,10);parent=[0,0]+[RNG.randint(1,i-1) for i in range(2,n+1)];k=[0]+[RNG.randint(1,n) for i in range(n)]
        masks=[]
        for i in range(1,n+1):
            covered=0;u=i
            for j in range(k[i]):
                if not u:break
                covered|=1<<(u-1);u=parent[u]
            masks.append(covered)
        best=n
        for mask in range(1<<n):
            covered=0
            for i in range(n):
                if mask>>i&1:covered|=masks[i]
            if covered==(1<<n)-1:best=min(best,mask.bit_count())
        check(13249,str(n)+'\n'+'\n'.join(map(str,parent[2:]))+'\n'+' '.join(map(str,k[1:])),best)


if __name__=='__main__':
    strings();digits();partitions();ranges_and_trees()
    report={'passed':True,'fixtures':sum(COUNTS.values()),'seed':2026110813,
            'problems':{k:{'fixtures':v,'programSha256':LEDGER['nowcoder-global::'+k]['programSha256']} for k,v in COUNTS.items()}}
    write(OUT/'recent-independent-validation.json',report);print(report)
