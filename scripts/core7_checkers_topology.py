"""Check actual order, mex and simple-path constraints, not sample spelling."""
import itertools
import json


def valid_order(n,edges,order):
    if sorted(order)!=list(range(1,n+1)):return False
    position={u:i for i,u in enumerate(order)}
    return all(position[u]<position[v] for u,v in edges)


def family_order(inp,got,other=None):
    try:
        data=iter(map(int,inp.split()));n=next(data);edges=[]
        for u in range(1,n+1):
            for v in data:
                if not v:break
                edges.append((u,v))
        return valid_order(n,edges,list(map(int,got.split())))
    except (ValueError,StopIteration):return False,'Malformed family order'


def task_order(inp,got,other=None):
    try:
        data=iter(map(int,inp.split()));output=iter(map(int,got.split()))
        while True:
            n,m=next(data),next(data)
            if not n and not m:break
            edges=[(next(data),next(data)) for _ in range(m)]
            if not valid_order(n,edges,[next(output) for _ in range(n)]):return False,'Invalid dependency order'
        return next(output,None) is None
    except (ValueError,StopIteration):return False,'Missing or malformed task order'


def ranking_order(inp,got,other=None):
    try:
        data=iter(map(int,inp.split()));n,m=next(data),next(data);edges=[(next(data),next(data)) for _ in range(m)]
        output=list(map(int,got.split()))
        if len(output)!=n+1 or not valid_order(n,edges,output[:-1]):return False,'Invalid ranks'
        expected_flag=int(other.split()[-1])
        return output[-1]==expected_flag,'Wrong uniqueness flag'
    except (ValueError,StopIteration,IndexError):return False,'Malformed ranking'


def blogs_match(n,edges,topic,order):
    if sorted(order)!=list(range(1,n+1)):return False
    graph=[[] for _ in range(n+1)]
    for u,v in edges:graph[u].append(v);graph[v].append(u)
    written=[False]*(n+1)
    for u in order:
        used={topic[v-1] for v in graph[u] if written[v]};mex=1
        while mex in used:mex+=1
        if mex!=topic[u-1]:return False
        written[u]=True
    return True


def blog_order(inp,got,other=None):
    try:
        data=iter(map(int,inp.split()));n,m=next(data),next(data);edges=[(next(data),next(data)) for _ in range(m)];topic=[next(data) for _ in range(n)]
        if got.strip()=='-1':return other.strip()=='-1','Incorrect impossibility claim'
        return blogs_match(n,edges,topic,list(map(int,got.split())))
    except (ValueError,StopIteration):return False,'Malformed blog order'


def acyclic(n,edges):
    graph=[[] for _ in range(n+1)]
    for u,v in edges:graph[u].append(v)
    color=[0]*(n+1);at=[0]*(n+1)
    for root in range(1,n+1):
        if color[root]:continue
        color[root]=1;stack=[root]
        while stack:
            u=stack[-1]
            if at[u]==len(graph[u]):color[u]=2;stack.pop();continue
            v=graph[u][at[u]];at[u]+=1
            if color[v]==1:return False
            if not color[v]:color[v]=1;stack.append(v)
    return True


def directed_edges(inp,got,other=None):
    try:
        data=iter(map(int,inp.split()));output=iter(got.split());tests=next(data)
        for _ in range(tests):
            n,m=next(data),next(data);original=[(next(data),next(data),next(data)) for _ in range(m)]
            verdict=next(output).upper();possible=acyclic(n,[(u,v) for t,u,v in original if t])
            if verdict=='NO':
                if possible:return False,'Claimed impossible although original directions are acyclic'
                continue
            if verdict!='YES' or not possible:return False,'Wrong verdict'
            fixed={(min(u,v),max(u,v)):(u,v) if t else None for t,u,v in original};oriented=[];seen=set()
            for _ in range(m):
                u,v=int(next(output)),int(next(output));key=min(u,v),max(u,v)
                if key not in fixed or key in seen:return False,'Missing, duplicate or invented edge'
                if fixed[key] is not None and fixed[key]!=(u,v):return False,'Reversed an existing directed edge'
                seen.add(key);oriented.append((u,v))
            if not acyclic(n,oriented):return False,'Constructed directions have a cycle'
        return next(output,None) is None
    except (ValueError,StopIteration):return False,'Malformed edge construction'


def simple_path_constraints(n,edges):
    """Enumerate simple paths, stopping at two, independently of bridge theory."""
    graph=[[] for _ in range(n)]
    for u,v in edges:graph[u-1].append(v-1);graph[v-1].append(u-1)
    constrained=[]
    for source in range(n):
        for target in range(source+1,n):
            count=0
            def walk(u,mask):
                nonlocal count
                if count>=2:return
                if u==target:count+=1;return
                for v in graph[u]:
                    if not mask>>v&1:walk(v,mask|1<<v)
            walk(source,1<<source)
            if count<2:constrained.append((source,target))
    # Each pair with fewer than two paths must share a color. Components of
    # these enumerated equalities determine whether two colors are possible.
    parent=list(range(n))
    def find(x):
        while parent[x]!=x:x=parent[x]
        return x
    for u,v in constrained:parent[find(u)]=find(v)
    return len({find(u) for u in range(n)})>1,constrained


def two_paths_color(inp,got,other=None):
    try:
        data=iter(map(int,inp.split()));output=iter(got.split());tests=next(data)
        large=json.loads(other) if other and other.startswith('{') else {}
        for test in range(tests):
            n,m=next(data),next(data);edges=[(next(data),next(data)) for _ in range(m)]
            if n<=10:possible,pairs=simple_path_constraints(n,edges);groups=None
            else:
                # Large model graphs have explicitly known unique-path groups
                # (cycle, tree, or a triangle with one attached chain).
                model=large[str(test)];possible=model['possible'];groups=model.get('groups',[]);pairs=[]
            answer=next(output)
            if answer=='-1':
                if possible:return False,'A coloring exists'
                continue
            if not possible or len(answer)!=n or set(answer)!={'B','W'}:return False,'Invalid verdict or colors'
            if any(answer[u]!=answer[v] for u,v in pairs):return False,'An opposite-color pair has fewer than two simple paths'
            if groups is not None and any(len({answer[u-1] for u in group})>1 for group in groups):return False,'Unique-path group has mixed colors'
        return next(output,None) is None
    except (ValueError,StopIteration,KeyError):return False,'Malformed coloring'
