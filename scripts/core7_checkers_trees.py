"""Check the full geometric or interval relation, allowing all valid answers."""


def tree_embedding(inp,got,expected=None):
    try:
        tokens=iter(map(int,inp.split()));n=next(tokens)
        edges=[(next(tokens)-1,next(tokens)-1) for _ in range(n-1)]
        points=[(next(tokens),next(tokens)) for _ in range(n)]
        placed=list(map(int,got.split()))
        assert sorted(placed)==list(range(1,n+1)),'Expected tree vertex at each point, exactly once'
        position=[None]*n
        for p,v in zip(points,placed):position[v-1]=p
        def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
        for i,(u,v) in enumerate(edges):
            a,b=position[u],position[v]
            for x,y in edges[i+1:]:
                if u in (x,y) or v in (x,y):continue
                c,d=position[x],position[y]
                if max(a[0],b[0])<min(c[0],d[0]) or max(c[0],d[0])<min(a[0],b[0]):continue
                if max(a[1],b[1])<min(c[1],d[1]) or max(c[1],d[1])<min(a[1],b[1]):continue
                assert not(cross(a,b,c)*cross(a,b,d)<0 and cross(c,d,a)*cross(c,d,b)<0),'Two non-adjacent edges cross'
        return True
    except (AssertionError,ValueError,StopIteration,IndexError,TypeError) as error:return False,str(error)


def tree_overlap_intervals(inp,got,expected=None):
    try:
        data=iter(map(int,inp.split()));n=next(data)
        edges=[(next(data)-1,next(data)-1) for _ in range(n-1)]
        values=list(map(int,got.split()));assert len(values)==2*n,'Expected n pairs'
        assert sorted(values)==list(range(1,2*n+1)),'Endpoints must be a permutation of 1..2n'
        pairs=list(zip(values[::2],values[1::2]));assert all(l<r for l,r in pairs),'Invalid interval order'
        for u,v in edges:
            a,b=pairs[u];c,d=pairs[v]
            assert a<c<b<d or c<a<d<b,'An original edge is not a strict interval crossing'
        # Count every crossing, rather than only checking the n-1 required ones.
        events=[None]*(2*n+1)
        for l,r in pairs:events[l]=r;events[r]=-r
        bit=[0]*(2*n+1);crossings=0
        for x in range(1,2*n+1):
            value=events[x]
            if value>0:
                j=value-1
                while j:crossings+=bit[j];j-=j&-j
                j=value;delta=1
            else:j=-value;delta=-1
            while j<=2*n:bit[j]+=delta;j+=j&-j
        assert crossings==n-1,'Additional non-edge crossings'
        return True
    except (AssertionError,ValueError,StopIteration,IndexError,TypeError) as error:return False,str(error)


def selftest():
    graph='4\n1 2\n2 3\n3 4\n0 0\n1 0\n1 1\n0 1\n'
    assert tree_embedding(graph,'1 2 3 4') is True
    assert tree_embedding(graph,'4 3 2 1') is True
    assert tree_embedding(graph,'1 3 2 4')[0] is False
    assert tree_embedding(graph,'1 1 3 4')[0] is False
    graph='3\n1 2\n1 3\n'
    assert tree_overlap_intervals(graph,'1 4\n2 6\n3 5') is True
    assert tree_overlap_intervals(graph,'1 6\n2 3\n4 5')[0] is False
    assert tree_overlap_intervals(graph,'1 4\n2 5\n3 6')[0] is False
    assert tree_overlap_intervals('1\n','1 2') is True


if __name__=='__main__':selftest();print('Both construction checkers accept alternatives and reject false relations.')
