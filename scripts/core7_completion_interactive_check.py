"""Local protocol judges. These are not original-site acceptance claims."""
import queue,random,subprocess,threading

def graph_cases(kind):
    rng=random.Random(20261108);cases=[]
    for n in [2,3,4,7,20,100] if kind=='dungeon' else [3,4,5,9,25,100,1000]:
        for shape in ['chain','star','binary','random']:
            edges=[(i,(i-1 if shape=='chain' else 0 if shape=='star' else (i-1)//2 if shape=='binary' else rng.randrange(i))) for i in range(1,n)]
            labels=list(range(n));rng.shuffle(labels);edges=[(labels[a],labels[b]) for a,b in edges];rng.shuffle(edges)
            if kind=='dungeon':
                present={tuple(sorted(e)) for e in edges}
                for _ in range(3*n):
                    a,b=rng.randrange(n),rng.randrange(n)
                    if a!=b:present.add(tuple(sorted((a,b))))
                edges=list(present)
            cases.append((f'{shape}-{n}',n,edges))
    return cases

def adjacency(n,edges):
    g=[[] for _ in range(n)]
    for i,(a,b) in enumerate(edges):g[a].append((b,i));g[b].append((a,i))
    return g

def canonical(n,edges):
    g=adjacency(n,edges);degree=[len(x) for x in g];leaves=[v for v in range(n) if degree[v]<=1];remaining=n
    while remaining>2:
        remaining-=len(leaves);new=[]
        for v in leaves:
            for u,_ in g[v]:
                degree[u]-=1
                if degree[u]==1:new.append(u)
        leaves=new
    values=[]
    for root in leaves:
        order=[root];parent=[-1]*n;parent[root]=root
        for v in order:
            for u,_ in g[v]:
                if parent[u]<0:parent[u]=v;order.append(u)
        if len(order)!=n:raise AssertionError('Disconnected answer')
        code=['']*n
        for v in reversed(order):code[v]='('+''.join(sorted(code[u] for u,_ in g[v] if parent[u]==v))+')'
        values.append(code[root])
    return min(values)

def run_case(kind,exe,name,n,edges):
    proc=subprocess.Popen([str(exe)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf8',bufsize=1)
    lines=queue.Queue()
    def reader():
        for line in proc.stdout:lines.put(line.rstrip('\n'))
        lines.put(None)
    threading.Thread(target=reader,daemon=True).start()
    def send(value):proc.stdin.write(value+'\n');proc.stdin.flush()
    def read():
        result=lines.get(timeout=5)
        if result is None:raise AssertionError('Premature exit')
        return result
    g=adjacency(n,edges);queries=[0,0];moves=0
    try:
        if kind=='dungeon':
            send(f'{n} {len(edges)}');current=0
            while current!=n-1:
                neighbors=sorted(u for u,_ in g[current]);send(str(len(neighbors))+' '+' '.join(str(u+1) for u in neighbors))
                tokens=read().split();assert len(tokens)==1
                target=int(tokens[0])-1;assert target in neighbors
                current=target;moves+=1;assert moves<=2*n
            send('OK')
        else:
            send(str(n));answer=[]
            def distances(start,weights):
                d=[-1]*n;d[start]=0;order=[start]
                for v in order:
                    for u,e in g[v]:
                        if d[u]<0:d[u]=d[v]+weights[e];order.append(u)
                return d
            while True:
                tokens=read().split()
                if tokens==['!']:
                    for _ in range(n-1):
                        a,b=map(int,read().split());assert 1<=a<=n and 1<=b<=n and a!=b;answer.append((a-1,b-1))
                    assert len({tuple(sorted(e)) for e in answer})==n-1
                    assert canonical(n,answer)==canonical(n,edges)
                    break
                assert len(tokens)>=2 and tokens[0]=='?';type_=int(tokens[1]);assert type_ in (1,2);queries[type_-1]+=1;assert queries[type_-1]<=n
                if type_==1:
                    weights=list(map(int,tokens[2:]));assert len(weights)==n-1 and all(1<=x<=10**9 for x in weights)
                    d=distances(0,weights);a=max(range(n),key=d.__getitem__);send(str(max(distances(a,weights))))
                else:
                    assert len(tokens)==4;a,b=(int(x)-1 for x in tokens[2:]);assert 0<=a<n-1 and 0<=b<n-1
                    d=[-1]*n;order=list(edges[a])
                    for v in order:d[v]=0
                    for v in order:
                        for u,_ in g[v]:
                            if d[u]<0:d[u]=d[v]+1;order.append(u)
                    send(str(min(d[v] for v in edges[b])))
        proc.stdin.close();proc.wait(timeout=5)
        assert proc.returncode==0
        assert lines.get(timeout=5) is None, 'Output after completion'
        return {'case':name,'passed':True,'n':n,'moves':moves,'type1':queries[0],'type2':queries[1]}
    except Exception as exc:
        proc.kill();proc.wait();return {'case':name,'passed':False,'n':n,'error':str(exc),'type1':queries[0],'type2':queries[1]}

def validate(kind,exe):
    return [run_case(kind,exe,*case) for case in graph_cases(kind)]
