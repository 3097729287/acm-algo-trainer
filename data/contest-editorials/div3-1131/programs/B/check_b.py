from functools import lru_cache

def valid(inp,text):
    data=list(map(int,inp.split()));t=data[0]
    cases=[tuple(data[1+3*i:4+3*i]) for i in range(t)]
    lines=text.split()
    if len(lines)!=t:return False,'输出行数不对'
    moves='RSP'
    for counts,s in zip(cases,lines):
        if len(s)!=sum(counts) or any(c not in moves for c in s):return False,'长度或手势字符不合法'
        @lru_cache(None)
        def worst(x,y,z):
            i=len(s)-x-y-z
            if i==len(s):return 0
            best=10**9
            for a,left in enumerate((x,y,z)):
                if not left:continue
                rest=[x,y,z];rest[a]-=1
                b=moves.index(s[i]);score=0 if b==a else (1 if (b,a) in [(0,1),(1,2),(2,0)] else -1)
                best=min(best,score+worst(*rest))
            return best
        if worst(*counts)<0:return False,'存在 Alice 排列能使 Bob 输局更多'
    return True,''

def checker(inp,got,other):
    first=valid(inp,got)
    if not first[0]:return first
    if other:
        second=valid(inp,other)
        if not second[0]:return False,'独立基准或样例输出不合法：'+second[1]
    return True,''
