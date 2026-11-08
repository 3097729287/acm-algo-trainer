"""Definition-based checks for valid constructive output, independent of formatting."""
import itertools
import math


def check_extra(checker,case,actual):
    if checker=='apollonius-two-circles':
        try:
            data=list(map(float,case['input'].split()));values=list(map(float,actual.split()))
            expected=list(map(float,case['output'].split()));at=expect=0
            for t in range(int(data[0])):
                x1,y1,r1,x2,y2,r2,xp,yp=data[1+8*t:9+8*t]
                count=int(values[at]);at+=1;target=int(expected[expect]);expect+=1+3*target
                if count!=target:return False
                circles=[]
                for i in range(count):
                    x,y,r=values[at:at+3];at+=3
                    if not all(math.isfinite(v) for v in (x,y,r)) or r<=0:return False
                    if not all(abs(a-b)<=2e-4 for a,b in [
                        (math.hypot(x-xp,y-yp),r),(math.hypot(x-x1,y-y1),r+r1),
                        (math.hypot(x-x2,y-y2),r+r2)]):return False
                    if any(math.hypot(x-a,y-b)<1e-5 and abs(r-c)<1e-5 for a,b,c in circles):return False
                    circles.append((x,y,r))
            return at==len(values) and expect==len(expected)
        except (ValueError,IndexError):return False
    if checker=='argument-order':
        from collections import Counter
        data=list(map(int,case['input'].split()));original=list(zip(data[1::2],data[2::2]))
        try:out=list(map(int,actual.split()))
        except ValueError:return False
        if len(out)!=2*len(original):return False
        points=list(zip(out[::2],out[1::2]))
        angles=[math.atan2(y,x) for x,y in points]
        return Counter(original)==Counter(points) and all(a<=b+1e-14 for a,b in zip(angles,angles[1:]))
    if checker=='nan-quotient-hack':
        try:a,b=map(int,actual.split())
        except ValueError:return False
        return a==0 and b==0
    if checker=='pairwise-gcd-groups':
        n,k=map(int,case['input'].split())
        try: values=list(map(int,actual.split()))
        except ValueError:return False
        if len(values)!=4*n+1 or values[0]!=(6*n-1)*k:return False
        points=values[1:]
        return (len(set(points))==4*n and min(points)>=1 and max(points)==values[0]
                and all(math.gcd(a,b)==k for i in range(n) for a,b in itertools.combinations(points[4*i:4*i+4],2)))
    if checker=='color-or-odd-cycle':
        data=list(map(int,case['input'].split()));n,m=data[:2];edges=set()
        for u,v in zip(data[2::2],data[3::2]):edges.add((u,v));edges.add((v,u))
        try:values=list(map(int,actual.split()))
        except ValueError:return False
        if not values:return False
        length=values[0]
        if length==0:return len(values)==n+1 and all(c in (0,1) for c in values[1:]) and all(values[u]!=values[v] for u,v in edges)
        cycle=values[1:]
        return length>=3 and length%2==1 and len(cycle)==length and len(set(cycle))==length and all(1<=u<=n for u in cycle) and all((cycle[i],cycle[(i+1)%length]) in edges for i in range(length))
    if checker=='minimum-path-cover':
        data=list(map(int,case['input'].split()));n,m=data[:2];edge=set(zip(data[2::2],data[3::2]))
        try:rows=[list(map(int,line.split())) for line in actual.splitlines() if line.strip()]
        except ValueError:return False
        if not rows or len(rows[-1])!=1:return False
        paths=rows[:-1]
        if rows[-1][0]!=len(paths) or sorted(x for row in paths for x in row)!=list(range(1,n+1)):return False
        if any((a,b) not in edge for row in paths for a,b in zip(row,row[1:])):return False
        adjacency=[[] for i in range(n)]
        for u,v in edge:adjacency[u-1].append(v-1)
        mate=[-1]*n
        def augment(u,seen):
            if u in seen:return False
            seen.add(u)
            for v in adjacency[u]:
                if mate[v]<0 or augment(mate[v],seen):mate[v]=u;return True
            return False
        maximum=sum(augment(u,set()) for u in range(n))
        return len(paths)==n-maximum
    if checker=='magic-ball-paths':
        columns=int(case['input']);expected=int(case['output'].split()[0])
        try:rows=[list(map(int,line.split())) for line in actual.splitlines()]
        except ValueError:return False
        if not rows or rows[0]!=[expected] or len(rows)!=columns+1:return False
        return sorted(v for row in rows[1:] for v in row)==list(range(1,expected+1)) and all(math.isqrt(a+b)**2==a+b for row in rows[1:] for a,b in zip(row,row[1:]))
    if checker=='round-table-assignment':
        data=list(map(int,case['input'].split()));groups,tables=data[:2];amount=data[2:groups+2];capacity=data[groups+2:]
        feasible=all(sum(sorted(amount,reverse=True)[:k])<=sum(min(k,c) for c in capacity) for k in range(1,groups+1))
        try:rows=[list(map(int,line.split())) for line in actual.splitlines() if line.strip()]
        except ValueError:return False
        if not rows:return False
        if not feasible:return rows==[[0]]
        if rows[0]!=[1] or len(rows)!=groups+1:return False
        used=[0]*tables
        for need,row in zip(amount,rows[1:]):
            if len(row)!=need or len(set(row))!=need or any(not 1<=t<=tables for t in row):return False
            for t in row:used[t-1]+=1
        return all(a<=b for a,b in zip(used,capacity))
    return None
