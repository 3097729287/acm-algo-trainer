import sys
from pathlib import Path
sys.path.insert(0,str(Path.home()/'.dsh/tools'))
from verify import main
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))

def gen(rng):
    n=rng.randint(1,8);edges=[(i,rng.randrange(1,i)) for i in range(2,n+1)]
    x=''.join(rng.choice('01') for _ in range(n))
    if rng.randrange(2):
        children=[[] for _ in range(n)]
        for a,b in edges:children[b-1].append(a-1)
        y=list(x)
        for _ in range(rng.randrange(1<<n)):
            active=[0]
            for u in active:
                if y[u]=='0':y[u]='1'
                else:y[u]='0';active.extend(children[u])
        y=''.join(y)
    else:y=''.join(rng.choice('01') for _ in range(n))
    return f'1\n{n}\n'+''.join(f'{a} {b}\n' for a,b in edges)+x+'\n'+y+'\n'
EDGES=[('初态即终态','1\n1\n1\n1\n','0\n'),('单点从一到零','1\n1\n1\n0\n','1\n'),('同层矛盾','1\n3\n1 2\n1 3\n000\n010\n','-1\n'),('保留原不可达分支输入','1\n5\n1 2\n1 3\n2 4\n3 5\n01000\n00010\n','-1\n'),('不同分支进位不同','1\n5\n1 2\n1 3\n2 4\n3 5\n01000\n00110\n','2\n'),('三位进位','1\n3\n1 2\n2 3\n111\n000\n','1\n'),('超六十四位', '1\n66\n'+''.join(f'{i} {i+1}\n' for i in range(1,66))+'0'*66+'\n'+'0'*65+'1\n',str(pow(2,65,998244353))+'\n')]
def large(star):
    n=200000;es=''.join(f'{1 if star else i-1} {i}\n' for i in range(2,n+1))
    return '1\n'+str(n)+'\n'+es+'0'*n+'\n'+('0'+'1'*(n-1) if star else '0'*(n-1)+'1')+'\n'
LIMITS=[('最大深度与超大答案',lambda:large(False),2.0),('最大同层数量',lambda:large(True),2.0)]
ROUNDS=1000

if __name__=='__main__':
    ok=main(solution=str(HERE/'g.cpp'),brute=str(HERE/'g_brute.cpp'),
        gen=gen,edges=EDGES,limits=LIMITS,rounds=ROUNDS,seed=227806,
        checker=None,log_file=str(HERE/'../../_work/logs/verify_g.log'))
    sys.exit(0 if ok else 1)
