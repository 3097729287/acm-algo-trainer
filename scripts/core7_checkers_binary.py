"""Validate independent axis matchings and complete optimal sign-in routes."""
import itertools
import json


def axis_feasible(intervals,n):
    """Augmenting paths, rather than the editorial's deadline greedy."""
    occupant={}
    def augment(item,seen):
        l,r=intervals[item]
        for p in range(l,r+1):
            if p in seen:continue
            seen.add(p)
            if p not in occupant or augment(occupant[p],seen):occupant[p]=item;return True
        return False
    return all(augment(i,set()) for i in range(n))


def rooks(inp,got,other=None):
    try:
        data=iter(map(int,inp.split()));out=iter(got.split())
        while True:
            n=next(data)
            if not n:break
            rectangles=[tuple(next(data) for _ in range(4)) for _ in range(n)]
            first=next(out)
            if first=='IMPOSSIBLE':
                assert not (axis_feasible([(l,r) for l,b,r,t in rectangles],n) and axis_feasible([(b,t) for l,b,r,t in rectangles],n)),'Feasible placement rejected'
                continue
            placement=[(int(first),int(next(out)))]+[(int(next(out)),int(next(out))) for _ in range(n-1)]
            assert len({x for x,y in placement})==n and len({y for x,y in placement})==n,'Rooks attack'
            for (x,y),(l,b,r,t) in zip(placement,rectangles):assert 1<=x<=n and 1<=y<=n and l<=x<=r and b<=y<=t,'Rook outside rectangle'
        assert next(out,None) is None,'Extra output'
        return True
    except (AssertionError,ValueError,StopIteration,RecursionError) as error:return False,str(error)


def sign_optimum(coordinates,budget,gift):
    """Enumerate actual left/right travel extremes, no sliding window or RMQ."""
    best=[]
    values=set(coordinates+[0])
    for left in values:
        if left>0:continue
        for right in values:
            if right<0:continue
            selected=[i+1 for i,x in enumerate(coordinates) if left<=x<=right]
            if 2*(right-left)>budget+5*(gift in selected):continue
            if len(selected)>len(best) or len(selected)==len(best) and selected<best:best=selected
    return best


def sign_route(inp,got,other=None):
    try:
        data=list(map(int,inp.split()));n,budget,gift=data[:3];coordinates=data[3:];assert len(coordinates)==n
        out=list(map(int,got.split()));assert out and out[0]==len(out)-1,'Wrong reported count'
        route=out[1:];assert len(set(route))==len(route) and all(1<=x<=n for x in route),'Repeated or invalid id'
        positions=[0]+[coordinates[i-1] for i in route]+[0]
        assert sum(abs(a-b) for a,b in zip(positions,positions[1:]))<=budget+5*(gift in route),'Route exceeds time budget'
        if other and other.startswith('{'):best=json.loads(other)['best']
        else:
            assert n<=50,'Large oracle must be independently supplied'
            best=sign_optimum(coordinates,budget,gift)
        assert sorted(route)==best,'Wrong maximum count or lexicographic set'
        return True
    except (AssertionError,ValueError,KeyError,TypeError) as error:return False,str(error)
