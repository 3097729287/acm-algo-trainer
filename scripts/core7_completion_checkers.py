def check(kind, inp, actual, expected):
    if kind=='new-year-letter':
        try:
            k,x,n,m=map(int,inp.split());words=actual.split()
            if words==['Happy','new','year!']:return expected.startswith('Happy new year!')
            if len(words)!=2 or len(words[0])!=n or len(words[1])!=m or not all(w.isascii() and w.isalpha() and w.isupper() for w in words):return False
            def describe(s):return s[0],s[-1],sum(s[i:i+2]=='AC' for i in range(len(s)-1))
            a,b=map(describe,words)
            for _ in range(3,k+1):a,b=b,(a[0],b[1],a[2]+b[2]+(a[1]=='A' and b[0]=='C'))
            return b[2]==x
        except (ValueError,IndexError):return False
    if kind=='type-printer':
        try:
            from collections import Counter
            tokens=inp.split();n=int(tokens[0]);words=tokens[1:];out=actual.split();count=int(out[0]);ops=out[1:]
            if len(words)!=n or len(ops)!=count:return False
            prefixes={w[:i] for w in words for i in range(1,len(w)+1)}
            if count!=2*len(prefixes)-max(map(len,words))+n:return False
            current='';printed=[]
            for op in ops:
                if op=='P':printed.append(current)
                elif op=='-':
                    if not current:return False
                    current=current[:-1]
                elif len(op)==1 and 'a'<=op<='z':current+=op
                else:return False
            return Counter(printed)==Counter(words)
        except (ValueError,IndexError):return False
    if kind=='universal-pairs':
        try:
            n=int(inp);out=list(map(int,actual.split()));q=out[0]
            if not 0<=q<=500000 or len(out)!=2*q+1:return False
            a=list(range(n+1));expressions={}
            for i in range(q):
                x,y=out[2*i+1:2*i+3]
                if not 1<=x<=n or not 1<=y<=n:return False
                pair=(a[x],a[y])
                if pair not in expressions:expressions[pair]=n+1+len(expressions)
                a[x]=a[y]=expressions[pair]
            return len(set(a[1:]))<=2
        except (ValueError,IndexError):return False
    if kind=='music':
        try:
            it=iter(map(int,inp.split()));out=iter(actual.split())
            for _ in range(next(it)):
                n,k,a,b=(next(it) for _ in range(4));cost=int(next(out));s=next(out)
                if len(s)!=n:return False
                accents=[int(s[i]==s[i+1]) for i in range(n-1)]
                prefix=[0]
                for x in accents:prefix.append(prefix[-1]+x)
                clean=sum(prefix[l+k-1]==prefix[l] for l in range(max(0,n-k+1)))
                if sum(accents)*a+clean*b!=cost:return False
                if k>n:optimal=0
                else:
                    W=n-k+1;w=k-1
                    optimal=min(c*a+max(0,W-c*w)*b for c in {0,W//w,(W+w-1)//w})
                if cost!=optimal:return False
            return next(out,None) is None
        except (StopIteration,ValueError,IndexError):return False
    if kind=='subtree-centroid':
        try:
            it=iter(map(int,inp.split()));n,q=next(it),next(it);parent=[0]+[next(it)-1 for _ in range(n-1)];g=[[] for _ in range(n)]
            for v in range(1,n):g[parent[v]].append(v)
            order=[0]
            for v in order:order.extend(g[v])
            size=[1]*n
            for v in reversed(order[1:]):size[parent[v]]+=size[v]
            tin=[0]*n;tout=[0]*n;timer=0;stack=[(0,False)]
            while stack:
                v,leave=stack.pop()
                if leave:tout[v]=timer;continue
                tin[v]=timer;timer+=1;stack.append((v,True));stack.extend((u,False) for u in reversed(g[v]))
            out=list(map(int,actual.split()))
            if len(out)!=q:return False
            for value in out:
                root=next(it)-1;c=value-1
                if not 0<=c<n or not tin[root]<=tin[c]<tout[root]:return False
                if max([size[root]-size[c]]+[size[u] for u in g[c]])*2>size[root]:return False
            return True
        except (StopIteration,ValueError,IndexError):return False
    if kind=='provinces':
        try:
            it=iter(map(int,inp.split()));n,B=next(it),next(it);g=[[] for _ in range(n)]
            for _ in range(n-1):
                a,b=next(it)-1,next(it)-1;g[a].append(b);g[b].append(a)
            out=iter(map(int,actual.split()));k=next(out)
            if not 1<=k<=n:return False
            belong=[next(out)-1 for _ in range(n)];capitals=[next(out)-1 for _ in range(k)]
            if next(out,None) is not None or not all(0<=x<k for x in belong) or not all(0<=x<n for x in capitals):return False
            groups=[[v for v in range(n) if belong[v]==i] for i in range(k)]
            for i,group in enumerate(groups):
                if not B<=len(group)<=3*B:return False
                cap=capitals[i];seen={cap};q=[cap]
                for v in q:
                    for u in g[v]:
                        if u not in seen and belong[u]==i:seen.add(u);q.append(u)
                if not set(group)<=seen:return False
            return True
        except (StopIteration,ValueError,IndexError):return False
    if kind=='flower-arrangement':
        try:
            it=iter(map(int,inp.split()));F,V=next(it),next(it);a=[[next(it) for _ in range(V)] for _ in range(F)];out=list(map(int,actual.split()))
            if len(out)!=F+1 or out[0]!=int(expected.split()[0]):return False
            path=out[1:]
            return all(1<=p<=V for p in path) and all(x<y for x,y in zip(path,path[1:])) and sum(a[i][p-1] for i,p in enumerate(path))==out[0]
        except (StopIteration,ValueError,IndexError):return False
    if kind=='lcm-subsequence':
        try:
            import math
            it=iter(map(int,inp.split()));n,m=next(it),next(it);a=[next(it) for _ in range(n)];out=list(map(int,actual.split()));L,k=out[:2];indices=out[2:]
            if not 1<=L<=m or len(indices)!=k or indices!=sorted(set(indices)) or not all(1<=x<=n for x in indices):return False
            if k!=int(expected.split()[1]):return False
            return math.lcm(*(a[i-1] for i in indices))==L
        except (StopIteration,ValueError,IndexError):return False
    if kind=='forbidden-triples':
        try:
            it=iter(map(int,inp.split()));n,m,k=next(it),next(it),next(it);edges=set()
            for _ in range(m):
                a,b=next(it),next(it);edges.add((a,b));edges.add((b,a))
            bad={tuple(next(it) for _ in range(3)) for _ in range(k)}
            out=list(map(int,actual.split()));length=out[0]
            if length!=int(expected.split()[0]):return False
            if length<0:return out==[-1]
            path=out[1:]
            return len(path)==length+1 and path[0]==1 and path[-1]==n and all((a,b) in edges for a,b in zip(path,path[1:])) and all(tuple(path[i:i+3]) not in bad for i in range(len(path)-2))
        except (StopIteration,ValueError,IndexError):return False
    if kind=='police-forest':
        try:
            it=iter(map(int,inp.split()));n,k,d=next(it),next(it),next(it);stations={next(it)-1 for _ in range(k)};edges=[(next(it)-1,next(it)-1) for _ in range(n-1)]
            out=list(map(int,actual.split()));size=out[0];cut=set(out[1:])
            if size!=len(stations)-1 or len(cut)!=size or len(out)!=size+1 or not all(1<=x<n for x in cut):return False
            g=[[] for _ in range(n)]
            for i,(a,b) in enumerate(edges,1):
                if i not in cut:g[a].append(b);g[b].append(a)
            distances=[-1]*n;q=list(stations)
            for v in q:distances[v]=0
            for v in q:
                for u in g[v]:
                    if distances[u]<0:distances[u]=distances[v]+1;q.append(u)
            return all(0<=x<=d for x in distances)
        except (StopIteration,ValueError,IndexError):return False
    if kind=='invariant-tree':
        try:
            it=iter(map(int,inp.split()));n=next(it);p=[next(it)-1 for _ in range(n)];tokens=actual.split()
            seen=set();cycles=[]
            for i in range(n):
                if i in seen:continue
                cycle=[];v=i
                while v not in seen:seen.add(v);cycle.append(v);v=p[v]
                cycles.append(cycle)
            possible=any(len(c)==1 for c in cycles) or (any(len(c)==2 for c in cycles) and all(len(c)%2==0 for c in cycles))
            if tokens[0]=='NO':return len(tokens)==1 and not possible
            if tokens[0]!='YES' or not possible or len(tokens)!=1+2*(n-1):return False
            edges={tuple(sorted((int(tokens[i])-1,int(tokens[i+1])-1))) for i in range(1,len(tokens),2)}
            if len(edges)!=n-1:return False
            g=[[] for _ in range(n)]
            for a,b in edges:
                if not 0<=a<b<n or tuple(sorted((p[a],p[b]))) not in edges:return False
                g[a].append(b);g[b].append(a)
            q=[0];visited={0}
            for v in q:
                for u in g[v]:
                    if u not in visited:visited.add(u);q.append(u)
            return len(visited)==n
        except (StopIteration,ValueError,IndexError):return False
    if kind=='power-grid':
        try:
            it=iter(map(int,inp.split()));n=next(it);points=[(next(it),next(it)) for _ in range(n)];c=[next(it) for _ in range(n)];k=[next(it) for _ in range(n)];out=iter(map(int,actual.split()));total=next(out);optimal=int(expected.split()[0]);count=next(out);stations=[next(out)-1 for _ in range(count)];wires=next(out);edges=[(next(out)-1,next(out)-1) for _ in range(wires)]
            if total!=optimal or next(out,None) is not None or len(set(stations))!=count:return False
            parent=list(range(n+1))
            def find(v):
                while parent[v]!=v:v=parent[v]
                return v
            def join(a,b):parent[find(a)]=find(b)
            cost=0
            for v in stations:
                if not 0<=v<n:return False
                cost+=c[v];join(v,n)
            for a,b in edges:
                if not 0<=a<n or not 0<=b<n:return False
                cost+=(abs(points[a][0]-points[b][0])+abs(points[a][1]-points[b][1]))*(k[a]+k[b]);join(a,b)
            return cost==total and all(find(v)==find(n) for v in range(n))
        except (StopIteration,ValueError,IndexError):return False
    if kind=='binary-flips':
        try:
            tokens=list(map(int,inp.split()));n,limit=tokens[:2];a=tokens[2:];out=list(map(int,actual.split()))
            if not out or out[0]<0:return False
            count=out[0]
            if count>limit or len(out)!=count+1:return False
            for p in out[1:]:
                p-=1
                if not 0<=p<n or 0<p<n-1 and a[p-1]==a[p+1]:return False
                a[p]^=1
            return len(set(a))==1
        except (ValueError,IndexError):return False
    if kind=='mex-merges':
        from collections import Counter
        try:
            tokens=iter(map(int,inp.split()));out=iter(map(int,actual.split()))
            for _ in range(next(tokens)):
                n=next(tokens);a=[next(tokens) for _ in range(n)];zero=a.count(0)
                possible= n>=4 or n==1 and zero==1 or n==2 and zero==0 or n==3 and 0<zero<3
                bag=Counter(a)
                if not possible:
                    if next(out)!=-1:return False
                    continue
                for _ in range(n-1):
                    x,y=next(out),next(out)
                    if bag[x]<=0:return False
                    bag[x]-=1
                    if bag[y]<=0:return False
                    bag[y]-=1
                    value=0
                    while value==x or value==y:value+=1
                    bag[value]+=1
                if {v:c for v,c in bag.items() if c}!={0:1}:return False
            return next(out,None) is None
        except (StopIteration,ValueError):return False
    if kind=='vertex-blocks':
        def blocks(value):
            tokens=iter(value.split());n=int(next(tokens));result=[]
            for _ in range(n):
                size=int(next(tokens));result.append(tuple(sorted(int(next(tokens)) for _ in range(size))))
            if next(tokens,None) is not None:raise ValueError('Extra output')
            return sorted(result)
        try:return blocks(actual)==blocks(expected)
        except (StopIteration,ValueError):return False
    if kind == 'set-construction':
        tokens=iter(inp.split()); output=iter(actual.split())
        try:
            for _ in range(int(next(tokens))):
                n=int(next(tokens)); matrix=[next(tokens) for _ in range(n)]; sets=[]
                for i in range(n):
                    size=int(next(output)); values=[int(next(output)) for _ in range(size)]
                    if not 1<=size<=n or len(set(values))!=size or not all(1<=x<=n for x in values):return False
                    sets.append(set(values))
                for i in range(n):
                    for j in range(n):
                        if i!=j and (sets[i]<sets[j]) != (matrix[i][j]=='1'):return False
            return next(output,None) is None
        except (StopIteration,ValueError):return False
    raise ValueError(kind)
