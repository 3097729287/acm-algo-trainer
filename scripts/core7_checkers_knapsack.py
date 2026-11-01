"""Replay every reported FIFO operation, including sacrificial prefix cells."""
from collections import deque


def fifo_selection(inp,got,expected=None):
    try:
        data=list(map(int,inp.split()));n=data[0];a=data[1:n+1];b=data[n+1:]
        lines=got.strip('\r\n').splitlines()
        assert len(lines)==3,'Expected count, complete index sequence, and score on three lines'
        count=int(lines[0]);chosen=list(map(int,lines[1].split()));score=int(lines[2])
        assert 0<=count<=n and len(chosen)==count,'Incorrect number of selected cells'
        assert all(1<=x<=n for x in chosen),'Index out of bounds'
        assert all(x<y for x,y in zip(chosen,chosen[1:])),'Indices must be strictly increasing'
        queue=deque()
        for x in chosen:
            i=x-1
            for _ in range(min(b[i],len(queue))):queue.popleft()
            queue.append(i)
        assert sum(a[i] for i in queue)==score,'Reported score differs from literal FIFO replay'
        optimum=int(str(expected).split()[-1])
        assert score==optimum,'The reported score is not optimal'
        return True
    except (AssertionError,ValueError,IndexError,TypeError) as error:return False,str(error)


def selftest():
    inp='3\n-9 5 6\n0 0 1\n'
    assert fifo_selection(inp,'3\n1 2 3\n11\n','11') is True
    for bad in ['2\n2 3\n11\n','3\n1 3 2\n11\n','3\n1 1 3\n11\n','3\n1 2 3\n6\n','1\n4\n11\n']:
        assert fifo_selection(inp,bad,'11')[0] is False
    assert fifo_selection('1\n-1\n0\n','0\n\n0\n','0') is True


if __name__=='__main__':selftest();print('FIFO checker validates full operations and rejects final-survivor-only output.')
