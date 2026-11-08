"""Small definitions and complete game trees, independent of editorial formulas."""
import math
from functools import lru_cache
from itertools import combinations, product, permutations
from validate_nowcoder_optimized_random import check, COUNTS, LEDGER
from nowcoder_editorials import OUT, write
import random

RNG = random.Random(2026110812)


def arithmetic():
    n = 180
    check(23048,str(n),[sum(i//math.gcd(i,j) for i in range(1,j+1)) for j in range(1,n+1)])
    check(53079,'200',[sum(next(d for d in range(2,x+1) if x%d==0) for x in range(2,201))])
    queries = [(1,x) for x in range(1,180)] + [(63,64),(64,127),(127,129)]
    def omega(x):
        total,d = 0,2
        while d*d <= x:
            while x%d==0: x//=d; total+=1
            d+=1
        return total+(x>1)
    check(224933,str(len(queries))+'\n'+'\n'.join(f'{l} {r}' for l,r in queries),
          [sum(omega(x)==2 for x in range(l,r+1)) for l,r in queries])
    history,ops,answers = [],[],[]
    for _ in range(100):
        x = RNG.choice([RNG.randint(1,100),99991,83160])
        k,p = RNG.randint(1,20),RNG.randint(1,100000)
        history.append(x); ops.append(f'{x} {k} {p}')
        answers.append(sum(pow(math.gcd(x,y),k,p) for y in history)%p)
    check(20812,str(len(ops))+'\n'+'\n'.join(ops),answers)
    values = list(range(1,100)) + [99991,100003*100019,9999999967]
    expected = []
    for x in values:
        if x < 100: expected.append(sum(i for i in range(1,x+1) if math.gcd(i,x)!=1)%1000000007)
        else:
            phi,rem,d = x,x,2
            while d*d <= rem:
                if rem%d==0:
                    phi=phi//d*(d-1)
                    while rem%d==0: rem//=d
                d+=1
            if rem>1: phi=phi//rem*(rem-1)
            expected.append(x*(x+1-phi)//2%1000000007)
    check(20667,'\n'.join(map(str,values)),expected)
    for _ in range(25):
        n=RNG.randint(1,100)
        check(23047,str(n),math.prod([1]) and __import__('functools').reduce(int.__xor__,[pow(x,n,1000000007) for x in range(1,n+1)],0))
        check(17247,str(n),sum(omega(i//math.gcd(i,j))==1 and omega(j//math.gcd(i,j))==1 for i in range(1,n+1) for j in range(1,n+1)))
        a=[RNG.randint(1,30) for i in range(RNG.randint(1,5))]
        m=RNG.randint(1,30)
        seen={0}; pending=[0]
        for x in pending:
            for d in a:
                y=(x+d)%m
                if y not in seen: seen.add(y);pending.append(y)
        check(17873,f'{len(a)} {m}\n'+' '.join(map(str,a)),len(seen))
    for n in range(2,8):
        # Exhaustive circular seats; anchor person 0 to quotient rotations.
        answer=0
        for p in permutations(range(1,2*n)):
            if n>4: break
            order=(0,)+p
            answer+=all(order[i]//2 != order[(i+1)%(2*n)]//2 for i in range(2*n))
        if n<=4: check(19857,str(n),answer)
    for _ in range(35):
        n=RNG.randint(2,18)//2*2; times=RNG.randint(0,15); p=list(range(1,n+1))
        for i in range(times): p=[x for pair in zip(p[n//2:],p[:n//2]) for x in pair]
        where=RNG.randint(1,n)
        check(19872,f'{n} {times} {where}',p[where-1])
        n=RNG.randint(1,4);m=RNG.randint(1,6)
        orbits=set()
        for s in product(range(n),repeat=m):
            orbits.add(min(t[i:]+t[:i] for t in (s,s[::-1]) for i in range(m)))
        check(15069,f'1\n{n} {m}',len(orbits))
    for _ in range(20):
        n=RNG.randint(1,5);m=RNG.randint(1,5)
        forbidden=[(RNG.randrange(m),RNG.randint(1,n)) for i in range(RNG.randint(0,10))]
        answer=sum(math.prod(s) for s in product(range(1,n+1),repeat=m) if all(s[x]!=y for x,y in forbidden))%1000000007
        check(19989,f'{n} {m} {len(forbidden)}\n'+'\n'.join(f'{x+1} {y}' for x,y in forbidden),answer)


def game_trees():
    for n in range(1,16):
        @lru_cache(None)
        def win(mask):
            if not mask: return True  # taking the final number loses
            for x in range(1,n+1):
                if mask>>(x-1)&1:
                    y=x;next_mask=mask
                    while y and next_mask>>(y-1)&1:
                        next_mask^=1<<(y-1);y//=2
                    if not win(next_mask): return True
            return False
        check(26212,str(n),'Shi' if win((1<<n)-1) else 'Yang')
    for _ in range(60):
        n=RNG.randint(1,4);a=''.join(RNG.choice('UD') for i in range(2*n));b=''.join(RNG.choice('UD') for i in range(2*n))
        @lru_cache(None)
        def game(mask,first,second):
            if not mask: return (first>second)-(first<second)
            turn=(2*n-mask.bit_count())%2
            results=[]
            for i in range(2*n):
                if mask>>i&1:
                    results.append(game(mask^(1<<i),first*2+(a[i]=='U') if not turn else first,
                                        second*2+(b[i]=='U') if turn else second))
            return min(results) if turn else max(results)
        value=game((1<<(2*n))-1,0,0)
        check(18993,f'{n}\n{a}\n{b}',{1:'clccle trl!',0:'orz sarlendy!',-1:'sarlendy tql!'}[value])
    @lru_cache(None)
    def split_win(state):
        for i,x in enumerate(state):
            if x%2:
                for y in range(1,x):
                    child=tuple(sorted(state[:i]+state[i+1:]+(y,x-y)))
                    if not split_win(child): return True
            else:
                for j in range(i+1,len(state)):
                    if state[j]%2==0:
                        child=tuple(sorted(tuple(v for k,v in enumerate(state) if k not in (i,j))+(x+state[j],)))
                        if not split_win(child): return True
        return False
    for _ in range(40):
        state=tuple(sorted(RNG.randint(1,7) for i in range(RNG.randint(1,4))))
        check(19156,str(len(state))+'\n'+' '.join(map(str,state)),'Alice' if split_win(state) else 'Bob')
    for _ in range(40):
        n=RNG.randint(1,5);order=list(product('WB',range(1,n+1)));RNG.shuffle(order)
        rank={item:i for i,item in enumerate(order)}
        best=10**9
        for whites in combinations(range(2*n),n):
            target=[];w=b=1;positions=set(whites)
            for i in range(2*n):
                if i in positions:target.append(rank['W',w]);w+=1
                else:target.append(rank['B',b]);b+=1
            best=min(best,sum(target[i]>target[j] for i in range(2*n) for j in range(i+1,2*n)))
        check(19832,str(n)+'\n'+'\n'.join(f'{c} {x}' for c,x in order),best)


if __name__ == '__main__':
    arithmetic()
    game_trees()
    report={'passed':True,'fixtures':sum(COUNTS.values()),'seed':2026110812,
            'problems':{k:{'fixtures':v,'programSha256':LEDGER['nowcoder-global::'+k]['programSha256']} for k,v in COUNTS.items()}}
    write(OUT/'number-games-independent-validation.json',report)
    print(report)
