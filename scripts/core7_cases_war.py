"""Full finite game graph, including arbitrary transfers and passing."""
from collections import deque
from functools import lru_cache
import itertools

def compositions(total,n):
    if n==1:
        yield (total,);return
    for first in range(total+1):
        for tail in compositions(total-first,n-1):yield (first,)+tail

@lru_cache(None)
def solve(n,total):
    armies=list(compositions(total,n));index={a:i for i,a in enumerate(armies)}
    size=len(armies)*(n+1)*2;parents=[[] for _ in range(size)];degree=[0]*size;winner=[-1]*size;queue=deque()
    def node(a,b,turn):return (index[a]*(n+1)+b)*2+turn
    for a in armies:
        for b in range(n+1):
            for turn in range(2):
                u=node(a,b,turn)
                if b in [0,n]:winner[u]=0 if b==n else 1;queue.append(u);continue
                following={node(a,b,turn^1)}
                owned=range(b) if turn==0 else range(b,n)
                for source in owned:
                    if a[source]==0:continue
                    for target in [source-1,source+1]:
                        if target in owned:
                            nxt=list(a);nxt[target]+=nxt[source];nxt[source]=0
                            following.add(node(tuple(nxt),b,turn^1))
                source,target=(b-1,b) if turn==0 else (b,b-1)
                if (a[source]>a[target] if turn==0 else a[source]>=a[target]):
                    nxt=list(a);nxt[target]+=nxt[source];nxt[source]=0
                    following.add(node(tuple(nxt),b+(1 if turn==0 else -1),turn^1))
                degree[u]=len(following)
                for v in following:parents[v].append(u)
    while queue:
        v=queue.popleft();w=winner[v]
        for u in parents[v]:
            if winner[u]!=-1:continue
            if (u%2)==w:winner[u]=w;queue.append(u)
            else:
                degree[u]-=1
                if degree[u]==0:winner[u]=w;queue.append(u)
    return {a:tuple(winner[node(a,b,0)] for b in range(1,n)) for a in armies}

