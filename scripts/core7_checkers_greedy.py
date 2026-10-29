"""Check constructed outputs by their semantics, not by a chosen sample string."""
from collections import deque
import math

def stack_computer(inp,got,other=None):
    try:
        target=int(inp);lines=got.splitlines();stack=[]
        if not 1<=len(lines)<=200:return False,'Instruction count outside 1..200'
        for line in lines:
            if line=='1':stack.append(1)
            elif line=='dup' and stack:stack.append(stack[-1])
            elif line=='add' and len(stack)>=2:stack.append(stack.pop()+stack.pop())
            else:return False,'Invalid instruction or stack underflow'
        return (True if stack==[target] else (False,'Final stack is not the target singleton'))
    except (ValueError,IndexError):return False,'Malformed stack program'

def mex_graph(inp,got,other=None):
    try:
        data=iter(map(int,inp.split()));n,m=next(data),next(data);edges=[tuple(next(data) for _ in range(3)) for i in range(m)]
        tokens=iter(got.split());verdict=next(tokens).lower();expected=(other or '').split()[0].lower()
        if verdict=='no':return True if expected=='no' and next(tokens,None) is None else (False,'Unexpected NO or extra output')
        if verdict!='yes' or expected=='no':return False,'Unexpected graph verdict'
        weights=[int(next(tokens)) for i in range(m)]
        if next(tokens,None) is not None or any(not 0<=x<2**31 for x in weights):return False,'Bad edge-weight output'
        graph=[[] for i in range(n)]
        for (u,v,f),a in zip(edges,weights):
            if a>0:graph[u-1].append(v-1);graph[v-1].append(u-1)
        component=[-1]*n
        for root in range(n):
            if component[root]>=0:continue
            component[root]=root;queue=deque([root])
            while queue:
                u=queue.popleft()
                for v in graph[u]:
                    if component[v]<0:component[v]=root;queue.append(v)
        for u,v,f in edges:
            actual=0 if component[u-1]==component[v-1] else 1
            if actual!=f:return False,'Constructed graph has a different minimum path mex'
        return True
    except (ValueError,IndexError,StopIteration):return False,'Malformed graph output'

def majority_tree(inp,got,other=None):
    try:
        data=iter(inp.split());tests=int(next(data));tokens=iter(got.split());expected=(other or '').split()
        if len(expected)!=tests:return False,'Missing independent feasibility oracle'
        for case in range(tests):
            n=int(next(data));edges=[(int(next(data))-1,int(next(data))-1) for i in range(n-1)];target=next(data)
            output=next(tokens);possible=expected[case]!='-1'
            if output=='-1':
                if possible:return False,'False impossible tree verdict'
                continue
            if not possible or len(output)!=n or set(output)-set('BW'):return False,'Invalid tree colors'
            black=[0]*n;degree=[0]*n
            for u,v in edges:
                degree[u]+=1;degree[v]+=1;black[u]+=output[v]=='B';black[v]+=output[u]=='B'
            actual=''.join('B' if black[u]*2>degree[u] else 'W' for u in range(n))
            if actual!=target:return False,'Simultaneous neighbor majority differs from target'
        if next(tokens,None) is not None:return False,'Extra tree output'
        return True
    except (ValueError,IndexError,StopIteration):return False,'Malformed tree output'

def blackboard(inp,got,other=None):
    try:
        a,b,target=map(int,inp.split());n=b-a+1;tokens=iter(got.split());first=next(tokens)
        possible=(other or '').strip()!='-1'
        if first=='-1':return True if not possible and next(tokens,None) is None else (False,'False impossible blackboard verdict')
        if not possible:return False,'Oracle says this blackboard goal is impossible'
        # Fenwick order statistics interpret the program's current positions;
        # this is independent of the constructor's nested interval bookkeeping.
        tree=[0]+[i&-i for i in range(1,n+1)];values=list(range(a,b+1));remaining=n
        def kth(k):
            index=0;step=1<<(n.bit_length()-1)
            while step:
                nxt=index+step
                if nxt<=n and tree[nxt]<k:k-=tree[nxt];index=nxt
                step//=2
            return index
        for operation in range(n-1):
            x=int(first) if operation==0 else int(next(tokens));y=int(next(tokens))
            if not 0<=x<y<remaining:return False,'Current positions not ordered or outside board'
            i,j=kth(x+1),kth(y+1)
            if (values[i]-values[j])%2:return False,'Averaged values have different parity'
            values[i]=(values[i]+values[j])//2
            at=j+1
            while at<=n:tree[at]-=1;at+=at&-at
            remaining-=1
        if next(tokens,None) is not None:return False,'Too many blackboard operations'
        return True if values[kth(1)]==target else (False,'Wrong final blackboard number')
    except (ValueError,IndexError,StopIteration):return False,'Malformed blackboard operations'

def gcd_lcm(inp,got,other=None):
    try:
        data=iter(map(int,inp.split()));tests=next(data);tokens=iter(map(int,got.split()))
        for _ in range(tests):
            a=next(data);b,c,d=[next(tokens) for i in range(3)]
            if not all(1<=x<=1634826193 for x in [b,c,d]):return False,'Construction exceeds required bound'
            if a+b+c+d!=math.gcd(a,b)+math.lcm(c,d):return False,'GCD/LCM equation is false'
        if next(tokens,None) is not None:return False,'Extra GCD/LCM output'
        return True
    except (ValueError,IndexError,StopIteration):return False,'Malformed GCD/LCM output'

def equal_permutations(inp,got,other=None):
    try:
        data=iter(map(int,inp.split()));tests=next(data);tokens=iter(got.split());flags=(other or '').split()
        independent=len(flags)==tests and all(x in ['YES','NO'] for x in flags)
        for case in range(tests):
            n,m=next(data),next(data);first=next(tokens)
            possible=flags[case]=='YES' if independent else (m==1 or (n>1 and (n%2==0 or m%2==1)))
            if first=='-1':
                if possible:return False,'False impossible equal-position verdict'
                continue
            if not possible:return False,'Independent oracle says these permutations are impossible'
            sums=[0]*m;seen=[0]*m
            for row in range(n):
                for position in range(1,m+1):
                    value=int(first) if row==0 and position==1 else int(next(tokens))
                    if not 1<=value<=m or seen[value-1]==row+1:return False,'Row is not a permutation'
                    seen[value-1]=row+1;sums[value-1]+=position
            if len(set(sums))!=1:return False,'Position sums are unequal'
        if next(tokens,None) is not None:return False,'Extra permutation output'
        return True
    except (ValueError,IndexError,StopIteration):return False,'Malformed permutation output'
