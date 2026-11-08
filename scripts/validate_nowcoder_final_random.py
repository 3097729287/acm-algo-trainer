"""Independent small games, mutable arrays, tree paths and exact geometric definitions."""
from collections import Counter
from functools import lru_cache
from itertools import combinations
import bisect,math,random,subprocess,time
from validate_nowcoder_optimized_random import check,COUNTS,LEDGER
from nowcoder_editorials import OUT,write
RNG=random.Random(2026110815)


def near(number,data,expected,tolerance=1e-7):
    run=subprocess.run([str(OUT/'compiled'/str(number)/'main.exe')],input=data,text=True,capture_output=True,timeout=15)
    assert run.returncode==0,(number,run.stderr)
    assert math.isclose(float(run.stdout),expected,rel_tol=tolerance,abs_tol=tolerance),(number,data,expected,run.stdout)
    COUNTS[str(number)]=COUNTS.get(str(number),0)+1


def games():
    for s in range(1,80):
        sg=[0]*(s+1)
        for c in range(s-1,0,-1):
            possible={sg[x] for x in range(c+1,min(s,c+c*c)+1)}
            while sg[c] in possible:sg[c]+=1
        for c in RNG.sample(range(s+1),min(4,s+1)):
            check(236919,f'1\n{s} {c}','Yes' if sg[c] else 'No')
    @lru_cache(None)
    def palindrome(a,b,c,reverse_used):
        if not a and not b and not c:return 0
        choices=[]
        if a:choices.append(1-palindrome(a-1,b+1,c,False))
        if b:choices.append(1-palindrome(a,b-1,c,False))
        if c:choices.append(1-palindrome(a,b,0,False))
        if b and not reverse_used:choices.append(-palindrome(a,b,c,True))
        return min(choices)
    for _ in range(50):
        n=RNG.randint(1,12);s=''.join(RNG.choice('01') for i in range(n))
        a=sum(s[i]==s[-1-i]=='0' for i in range(n//2));b=sum(s[i]!=s[-1-i] for i in range(n//2));c=int(n%2 and s[n//2]=='0')
        value=palindrome(a,b,c,False)
        check(236137,f'1\n{n}\n{s}','ALICE' if value<0 else 'BOB' if value>0 else 'DRAW')
    for _ in range(50):
        a=[RNG.randrange(256) for i in range(RNG.randint(1,15))];initial=a.copy();ops=[];answer=[]
        for j in range(30):
            if RNG.randrange(3)==0:
                x=RNG.randrange(256);a.append(x);ops.append(f'1 {x}')
            else:
                k=RNG.randint(1,len(a));ops.append(f'2 {k}')
                winning=[False]*len(a)
                for i in range(len(a)-1,-1,-1):
                    winning[i]=any((a[i]^a[j]).bit_count()<=1 and not winning[j] for j in range(i+1,len(a)))
                answer.append('Bob' if winning[k-1] else 'Alice')
        check(236260,f'{len(initial)} {len(ops)}\n'+' '.join(map(str,initial))+'\n'+'\n'.join(ops),answer)
    for _ in range(30):
        stack=[];ops=[];answer=[]
        for j in range(15):
            if stack and (len(stack)>=8 or RNG.randrange(3)==0):
                stack.pop();ops.append('DEL')
            else:
                a,b=RNG.randint(1,31),RNG.randint(1,20);stack.append((a,b));ops.append(f'ADD {a} {b}')
            total=0
            for a,b in stack:total^=a
            best=10**9
            for mask in range(1<<len(stack)):
                value=cost=0
                for i,(a,b) in enumerate(stack):
                    if mask>>i&1:value^=a;cost+=b
                if value==total:best=min(best,cost)
            answer.append(best)
        check(236249,str(len(ops))+'\n'+'\n'.join(ops),answer)


def mutable_structures():
    for _ in range(35):
        a=[RNG.randint(1,20) for i in range(RNG.randint(1,16))]
        query=[sorted([RNG.randint(1,len(a)),RNG.randint(1,len(a))]) for i in range(30)]
        answer=[]
        for l,r in query:
            order={v:i+1 for i,v in enumerate(sorted(set(a[l-1:r])))}
            answer.append(sum(order[v]!=v for v in a[l-1:r]))
        check(21758,str(len(a))+'\n'+' '.join(map(str,a))+'\n'+str(len(query))+'\n'+'\n'.join(f'{l} {r}' for l,r in query),answer)
        a=[];ops=[];answer=[]
        for j in range(80):
            if not a or RNG.randrange(3)==0:
                x=RNG.randint(-20,20);bisect.insort(a,x);ops.append(f'1 {x}')
            else:
                op=RNG.randint(2,6)
                if op==2:
                    x=RNG.choice(a);a.remove(x);ops.append(f'2 {x}')
                elif op==3:
                    x=RNG.randint(-25,25);ops.append(f'3 {x}');answer.append(bisect.bisect_left(a,x)+1)
                elif op==4:
                    k=RNG.randint(1,len(a));ops.append(f'4 {k}');answer.append(a[k-1])
                elif op==5:
                    x=RNG.randint(a[0]+1,30);ops.append(f'5 {x}');answer.append(a[bisect.bisect_left(a,x)-1])
                else:
                    x=RNG.randint(-30,a[-1]-1);ops.append(f'6 {x}');answer.append(a[bisect.bisect_right(a,x)])
        check(51117,str(len(ops))+'\n'+'\n'.join(ops),answer)
    for _ in range(35):
        n=RNG.randint(1,12);parents=[-1]+[RNG.randrange(i) for i in range(1,n)]
        a=[RNG.randint(0,15) for i in range(n)];initial=a.copy();ops=[];answer=[]
        def path(u,v):
            left=[];x=u
            while x>=0:left.append(x);x=parents[x]
            right=[];x=v
            while x not in left:right.append(x);x=parents[x]
            return left[:left.index(x)+1]+right[::-1]
        def is_child(v,u):
            while v>=0:
                if v==u:return True
                v=parents[v]
            return False
        for j in range(30):
            op=RNG.randint(1,3);u=RNG.randrange(n)
            if op==1:
                x=RNG.randint(0,9);ops.append(f'1 {u+1} {x}')
                for v in range(n):
                    if is_child(v,u):a[v]+=x
            elif op==2:
                v=RNG.randrange(n);x=RNG.randint(0,9);ops.append(f'2 {u+1} {v+1} {x}')
                for k in path(u,v):a[k]+=x
            else:
                v=RNG.randrange(n);ops.append(f'3 {u+1} {v+1}');points=path(u,v)
                answer.append(sum(a[x]*a[y] for x,y in combinations(points,2))%1000000007)
        data=f'{n} {len(ops)}\n'+' '.join(map(str,initial))+'\n'+'\n'.join(f'{parents[i]+1} {i+1}' for i in range(1,n))+'\n'+'\n'.join(ops)
        check(18939,data,answer)


def geometry():
    def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    def hull(points):
        points=sorted(set(points));lower=[];upper=[]
        for p in points:
            while len(lower)>1 and cross(lower[-2],lower[-1],p)<=0:lower.pop()
            lower.append(p)
        for p in points[::-1]:
            while len(upper)>1 and cross(upper[-2],upper[-1],p)<=0:upper.pop()
            upper.append(p)
        return lower[:-1]+upper[:-1]
    for _ in range(50):
        n=RNG.randint(3,9);p=RNG.sample([(x,y) for x in range(11) for y in range(11)],n)
        doubled=sum(abs(cross(a,b,c)) for a,b,c in combinations(p,3))
        data=str(n)+'\n'+'\n'.join(f'{x} {y}' for x,y in p)
        near(232543,data,doubled/2)
        acute=0
        for tri in combinations(p,3):
            if not cross(*tri):continue
            length=sorted((a[0]-b[0])**2+(a[1]-b[1])**2 for a,b in combinations(tri,2))
            acute+=length[0]+length[1]>length[2]
        check(232804,data,acute)
        best=max(min(math.dist(a,b),math.dist(a,c),math.dist(b,c))/2 for a,b,c in combinations(p,3))
        near(285230,data,best)
    for _ in range(30):
        n=RNG.randint(6,9);p=[]
        while len(p)<n:
            candidate=(RNG.randint(-15,15),RNG.randint(-15,15))
            if candidate not in p and all(cross(a,b,candidate)!=0 for a,b in combinations(p,2)):p.append(candidate)
        color=[i%3 for i in range(n)];RNG.shuffle(color)
        triangles=[tri for tri in combinations(range(n),3) if len({color[i] for i in tri})==3]
        def contained(point,tri):
            signs=[cross(p[tri[i]],p[tri[(i+1)%3]],point) for i in range(3)]
            return min(signs)>0 or max(signs)<0
        def separate(a,b):
            if set(a)&set(b):return False
            if any(contained(p[v],b) for v in a) or any(contained(p[v],a) for v in b):return False
            for i in range(3):
                for j in range(3):
                    x,y=p[a[i]],p[a[(i+1)%3]];u,v=p[b[j]],p[b[(j+1)%3]]
                    if cross(x,y,u)*cross(x,y,v)<0 and cross(u,v,x)*cross(u,v,y)<0:return False
            return True
        answer=sum(separate(a,b) for a,b in combinations(triangles,2))
        check(53264,str(n)+'\n'+'\n'.join(f'{x} {y} {c}' for (x,y),c in zip(p,color)),answer)


if __name__=='__main__':
    games();mutable_structures();geometry()
    report={'passed':True,'fixtures':sum(COUNTS.values()),'seed':2026110815,
            'problems':{k:{'fixtures':v,'programSha256':LEDGER['nowcoder-global::'+k]['programSha256']} for k,v in COUNTS.items()}}
    write(OUT/'final-independent-validation.json',report);print(report)
