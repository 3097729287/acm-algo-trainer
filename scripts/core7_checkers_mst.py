"""Validate an actual shortest-path tree, allowing every optimal edge set."""
from decimal import Decimal,InvalidOperation
import heapq
import re


def mst_decimal(inp,got,expected=None):
    expected=str(expected).strip();got=got.strip()
    if expected=='Impossible':return got=='Impossible'
    if not re.fullmatch(r'-?\d+\.\d{2}',got):return False,'Expected two decimal places'
    try:
        return Decimal(got)==Decimal(expected),'Incorrect rounded Euclidean total'
    except InvalidOperation:return False,'Malformed decimal'


def shortest_tree(inp,got,expected=None):
    try:
        data=iter(map(int,inp.split()));n,m=next(data),next(data);edges=[];graph=[[] for _ in range(n)]
        for i in range(m):
            u,v,w=next(data)-1,next(data)-1,next(data);edges.append((u,v,w));graph[u].append((v,w));graph[v].append((u,w))
        source=next(data)-1;tokens=list(map(int,got.split()))
        assert len(tokens)==n,'Expected total plus n-1 edge IDs'
        total,ids=tokens[0],[v-1 for v in tokens[1:]]
        assert len(set(ids))==n-1 and all(0<=v<m for v in ids),'Invalid or repeated edge ID'
        assert total==int(str(expected).split()[0]),'Tree weight is not optimal'
        chosen=[[] for _ in range(n)];actual=0
        for i in ids:
            u,v,w=edges[i];chosen[u].append((v,w));chosen[v].append((u,w));actual+=w
        assert actual==total,'Reported total differs from selected edges'
        route=[None]*n;route[source]=0;order=[source]
        for u in order:
            for v,w in chosen[u]:
                if route[v] is None:route[v]=route[u]+w;order.append(v)
        assert len(order)==n,'Selected edges do not connect the graph'
        distance=[10**80]*n;distance[source]=0;queue=[(0,source)]
        while queue:
            du,u=heapq.heappop(queue)
            if du!=distance[u]:continue
            for v,w in graph[u]:
                if du+w<distance[v]:distance[v]=du+w;heapq.heappush(queue,(du+w,v))
        assert route==distance,'Selected tree changes a source distance'
        return True
    except (AssertionError,ValueError,StopIteration,TypeError,IndexError) as error:return False,str(error)


def selftest():
    data='4 4\n1 2 1\n1 3 1\n2 4 1\n3 4 1\n1\n'
    assert shortest_tree(data,'3\n1 2 3\n','3') is True
    assert shortest_tree(data,'3\n1 2 4\n','3') is True
    for wrong in ['3\n1 3 4\n','3\n1 1 3\n','2\n1 2 3\n']:
        assert shortest_tree(data,wrong,'3')[0] is False


if __name__=='__main__':selftest();print('Shortest-tree checker accepts both optima and rejects same-weight wrong-distance trees.')
