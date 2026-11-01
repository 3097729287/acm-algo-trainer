"""Case generators and structural output checks for Gym 728862."""
from collections import deque
from pathlib import Path
import itertools
import json

ROOT = Path(__file__).resolve().parent.parent

def gen_case(letter, rng):
    if letter == 'A': return f'{rng.randint(1000,9000)}\n'
    if letter == 'B': return f'{rng.randint(1,2000)}\n'
    if letter in 'CFL':
        n=rng.randint(1,12 if letter=='F' else 30)
        a=[rng.randint(1,100 if letter=='F' else 15) for _ in range(n)]
        first=str(n)
        if letter=='C': first+=' '+str(rng.randint(1,n))
        if letter=='L': first+=' '+str(rng.randint(1,sum(a)+10))
        return first+'\n'+' '.join(map(str,a))+'\n'
    if letter=='D':
        rows=[]
        for _ in range(rng.randint(1,15)):
            a,b=rng.randint(1,25),rng.randint(1,25)
            rows.append(f'{a} {b} {rng.randint(1,a)} {rng.randint(1,b)} {rng.randint(1,55)}')
        return str(len(rows))+'\n'+'\n'.join(rows)+'\n'
    if letter=='E':
        a=[rng.randint(1,10000) for _ in range(rng.randint(1,30))]
        return str(len(a))+'\n'+' '.join(map(str,a))+'\n'
    if letter=='G':
        alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        # The official input guarantees a nonempty result.
        return 'b'+''.join(rng.choice(alphabet) for _ in range(rng.randint(0,99)))+'\n'
    if letter=='H':
        a,b,c=[rng.randint(1,25) for _ in range(3)]
        n=a*rng.randint(0,4)+b*rng.randint(0,4)+c*rng.randint(0,4)
        if n==0:n=a
        return f'{n} {a} {b} {c}\n'
    if letter=='I':
        points=rng.sample(list(itertools.product(range(1,7),repeat=2)),rng.randint(1,15))
        return str(len(points))+'\n'+''.join(f'{x} {y}\n' for x,y in points)
    if letter=='J':
        n=rng.randint(1,8)
        return (str(n)+'\n'+''.join(f'{rng.randint(1,10)} {rng.randint(1,10)}\n' for _ in range(n))
            +' '.join(str(rng.randint(1,50)) for _ in range(n))+'\n'
            +' '.join(str(rng.randint(1,20)) for _ in range(n))+'\n')
    if letter=='K':
        n=rng.randint(2,7);pairs=list(itertools.combinations(range(1,n+1),2));rng.shuffle(pairs)
        es=[]
        for u,v in pairs[:rng.randint(1,min(12,len(pairs)))]:
            if rng.randrange(2):u,v=v,u
            es.append(f'{rng.randrange(2)} {u} {v}')
        return f'1\n{n} {len(es)}\n'+'\n'.join(es)+'\n'
    raise ValueError(letter)

EDGES={
 'A':[('相同数字','1111\n','1203\n'),('已合法但必须增大','1234\n','1235\n'),('上界年份','9000\n','9012\n')],
 'B':[('单个细菌','1\n','1\n'),('二的幂','536870912\n','1\n'),('多个二进制位','7\n','3\n')],
 'C':[('单木板','1 1\n9\n','1\n'),('整段','4 4\n1 2 3 4\n','1\n'),('并列最小','4 2\n1 2 1 2\n','1\n')],
 'D':[('无可减与超额操作','3\n3 4 3 4 9\n10 10 8 5 99\n10 11 2 1 5\n','12\n40\n55\n'),('需要两种顺序','2\n10 10 8 5 3\n12 8 8 7 2\n','70\n77\n'),('大数乘积','1\n1000000000 1000000000 1 1 1\n','999999999000000000\n')],
 'E':[('一与小平方','6\n1 4 9 16 25 36\n','NO\nYES\nYES\nNO\nYES\nNO\n'),('大质数平方邻点','4\n999966000289 999966000288 999966000290 1000000000000\n','YES\nNO\nNO\nNO\n')],
 'F':[('仅一枚','1\n1\n','1\n'),('严格大于','2\n3 3\n','2\n'),('最大一枚足够','4\n9 1 1 1\n','1\n')],
 'G':[('特殊元音Y','YyZ\n','.z\n'),('单辅音','B\n','.b\n'),('大小写混合','aBAcAba\n','.b.c.b\n')],
 'H':[('单位切段','1 1 1 1\n','1\n'),('最短优先失败','7 2 5 5\n','2\n'),('不可达中间态','7 3 4 6\n','2\n')],
 'I':[('单点','1\n1 1\n','0\n'),('三块','3\n1 1\n2 2\n3 3\n','2\n'),('折线连通','3\n1 1\n1 2\n3 2\n','0\n')],
 'J':[('单城市','1\n1 1\n7\n2\n','7'),('重合城市','2\n2 2\n2 2\n5 7\n1 1\n','5'),('全建站','2\n1 1\n100 100\n2 3\n1000 1000\n','5')],
 'K':[('全部无向','1\n3 3\n0 1 2\n0 2 3\n0 3 1\n','YES\n1 2\n2 3\n1 3\n'),('有向环','1\n3 3\n1 1 2\n1 2 3\n1 3 1\n','NO\n'),('非连通','1\n4 2\n1 2 1\n0 4 3\n','YES\n2 1\n4 3\n')],
 'L':[('一本也不够','1 1\n2\n','0\n'),('恰好全读','3 6\n1 2 3\n','3\n'),('中间超长书','5 3\n1 1 10 1 1\n','2\n')]
}

def limit_cases(letter):
    sizes={
      'A':('9000\n',2),'B':('1000000000\n',1),
      'C':('150000 75000\n'+'100 '*150000+'\n',1),
      'D':('20000\n'+'1000000000 1000000000 1 1 1000000000\n'*20000,1),
      'E':('100000\n'+'999966000289 '*100000+'\n',2),
      'F':('100\n'+'100 '*100+'\n',2),'G':('Z'*100+'\n',2),
      'H':('4000 1 1 1\n',1),
      'I':('100\n'+''.join(f'{i} {i}\n' for i in range(1,101)),2),
      'J':('2000\n'+''.join(f'{i} 1\n' for i in range(1,2001))+'1000000000 '*2000+'\n'+'1 '*2000+'\n',2),
      'K':('1\n200000 200000\n'+''.join(f'1 {i} {i+1}\n' for i in range(1,200000))+'0 1 200000\n',3),
      'L':('100000 1000000000\n'+'10000 '*100000+'\n',2)
    }
    inp,tl=sizes[letter]
    return [('官方最大规模',inp,tl)]

def check_c(inp,got,other):
    data=list(map(int,inp.split()));n,k=data[:2];a=data[2:]
    out=got.split()
    if len(out)!=1:return False,'应输出一个左端点'
    j=int(out[0])-1
    return 0<=j<=n-k and sum(a[j:j+k])==min(sum(a[l:l+k]) for l in range(n-k+1))

def check_j(inp,got,other):
    vals=list(map(int,inp.split()));n=vals[0];coords=list(zip(vals[1:1+2*n:2],vals[2:1+2*n:2]));c=vals[1+2*n:1+3*n];k=vals[1+3*n:]
    out=list(map(int,got.split()));idx=0
    def take():
        nonlocal idx
        v=out[idx];idx+=1;return v
    total=take();v=take()
    if not 1<=v<=n:return False,'建站数量非法'
    stations=[take()-1 for _ in range(v)]
    if len(set(stations))!=v or any(not 0<=u<n for u in stations):return False,'建站编号非法'
    count=take()
    if not 0<=count<=n*(n-1)//2:return False,'连线数量非法'
    wires=[(take()-1,take()-1) for _ in range(count)]
    if idx!=len(out):return False,'多余输出'
    seen=set();cost=sum(c[u] for u in stations);graph=[[] for _ in range(n)]
    for u,w in wires:
        if not(0<=u<n and 0<=w<n) or u==w or tuple(sorted((u,w))) in seen:return False,'连线非法'
        seen.add(tuple(sorted((u,w))));graph[u].append(w);graph[w].append(u)
        cost+=(abs(coords[u][0]-coords[w][0])+abs(coords[u][1]-coords[w][1]))*(k[u]+k[w])
    reached=set(stations);q=list(stations)
    for u in q:
        for w in graph[u]:
            if w not in reached:reached.add(w);q.append(w)
    return (len(reached)==n and cost==total==int(other.split()[0]),'核对合法性、实际费用与独立最优值')

def check_k(inp,got,other):
    data=iter(map(int,inp.split()));cases=next(data);outputs=iter(got.split());expected=iter(other.split())
    for _ in range(cases):
        n,m=next(data),next(data);edges=[(next(data),next(data)-1,next(data)-1) for _ in range(m)]
        want=next(expected)
        if want=='YES':
            for _ in range(2*m):next(expected)
        status=next(outputs)
        if status!=want:return False,'与独立可行性基准不一致'
        if status=='NO':continue
        originals={frozenset((u,v)):(t,u,v) for t,u,v in edges};seen=set();graph=[[] for _ in range(n)];ind=[0]*n
        for _ in range(m):
            u,v=int(next(outputs))-1,int(next(outputs))-1;key=frozenset((u,v))
            if key not in originals or key in seen:return False,'边丢失、重复或凭空新增'
            t,a,b=originals[key]
            if t==1 and (u,v)!=(a,b):return False,'改动了固定有向边'
            seen.add(key);graph[u].append(v);ind[v]+=1
        q=deque(u for u in range(n) if not ind[u]);count=0
        while q:
            u=q.popleft();count+=1
            for v in graph[u]:
                ind[v]-=1
                if not ind[v]:q.append(v)
        if count!=n:return False,'输出含有有向环'
    try:next(outputs);return False,'多余输出'
    except StopIteration:return True

CHECKERS={'C':check_c,'J':check_j,'K':check_k}

if __name__=='__main__':
    source=json.loads((ROOT/'_work/source.json').read_text(encoding='utf8'))
    samples=[]
    for p in source['problems']:
        for i,s in enumerate(p['samples'],1):samples.append((p['title'][0]+' 样例'+str(i),s['input'],s['output']))
    (ROOT/'_work/samples.py').write_text('SAMPLES = '+repr(samples)+'\n',encoding='utf8')
    for letter in 'ABCDEFGHIJKL':
        path=ROOT/'A-L'/letter/('verify_'+letter.lower()+'.py')
        if path.exists():raise FileExistsError(path)
        body=f'''import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path[:0]=[str(Path.home()/'.dsh/tools'),str(ROOT/'_work')]
from verify import main
from validation import gen_case,EDGES as ALL_EDGES,limit_cases,CHECKERS
EDGES=ALL_EDGES['{letter}']
LIMITS=limit_cases('{letter}')
def gen(rng):return gen_case('{letter}',rng)
if __name__=='__main__':
    ok=main(solution=str(HERE/'{letter.lower()}.cpp'),brute=str(HERE/'{letter.lower()}_brute.cpp'),gen=gen,edges=EDGES,limits=LIMITS,letter='{letter}',rounds={1000 if letter in 'IJK' else 300},seed=728862,samples_file=str(ROOT/'_work/samples.py'),checker=CHECKERS.get('{letter}'),log_file=str(ROOT/'_work/logs/verify_{letter.lower()}.log'))
    sys.exit(0 if ok else 1)
'''
        path.write_text(body,encoding='utf8')
    print('Generated',len(samples),'official samples and 12 verifier entrypoints')
