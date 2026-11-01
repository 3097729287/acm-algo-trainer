import os, sys
from pathlib import Path
sys.path.insert(0, os.path.expanduser('~/.dsh/tools'))
from verify import main
HERE=Path(__file__).resolve().parent

def gen(rng):
    h,w=rng.randint(1,10),rng.randint(1,10);n=rng.randint(1,min(h*w,25));q=rng.randint(1,30)
    points=rng.sample([(i,j) for i in range(1,h+1) for j in range(1,w+1)],n)
    queries=[]
    for _ in range(q):
        t=rng.randint(1,2);lo=rng.randint(1,h if t==1 else w);hi=rng.randint(lo,h if t==1 else w);queries.append(f'{t} {lo} {hi}')
    return f'{h} {w} {n} {q}\n'+'\n'.join(f'{i} {j}' for i,j in points)+'\n'+'\n'.join(queries)+'\n'
EDGES=[('唯一坐标','1 1 1 2\n1 1\n1 1 1\n2 1 1\n','1\n1\n'),('重复行与空区间','10 10 3 4\n2 1\n2 2\n8 3\n1 2 2\n1 3 7\n1 1 10\n2 1 2\n','2\n0\n3\n2\n')]
def large():
    n=300000
    return f'1000000000 1000000000 {n} {n}\n'+''.join(f'{i} {i}\n' for i in range(1,n+1))+'1 1 1000000000\n'*n
LIMITS=[('最大点数与查询数',large,2.0)]

if __name__ == '__main__':
    ok=main(solution=str(HERE/'c.cpp'),brute=str(HERE/'c_brute.cpp'),
        gen=gen,edges=EDGES,limits=LIMITS,rounds=300,seed=26110207,
        log_file=str(HERE/'../../_work/logs/verify_c.log'))
    sys.exit(0 if ok else 1)
