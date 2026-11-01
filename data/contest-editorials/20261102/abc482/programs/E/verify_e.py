import os, sys
from pathlib import Path
sys.path.insert(0, os.path.expanduser('~/.dsh/tools'))
from verify import main
HERE=Path(__file__).resolve().parent

def gen(rng):
    n=rng.randint(2,22);es=[(i,rng.randrange(1,i)) for i in range(2,n+1)]
    rng.shuffle(es)
    return str(n)+'\n'+'\n'.join(f'{i} {j}' for i,j in es)+'\n'+' '.join(str(rng.randint(1,n)) for _ in range(n))+'\n'
EDGES=[('两点同色','2\n1 2\n1 1\n','1\n'),('两点异色','2\n1 2\n1 2\n','0\n'),('单中心三个分支','4\n1 2\n1 3\n1 4\n1 2 2 2\n','3\n'),('双中心四对','6\n1 2\n1 3\n1 4\n2 5\n2 6\n1 1 2 2 2 2\n','4\n'),('同分支不能配','5\n1 2\n2 3\n2 4\n1 5\n1 1 2 2 3\n','0\n')]
def large(star):
    n=200000
    return str(n)+'\n'+''.join(f'{1 if star else i-1} {i}\n' for i in range(2,n+1))+'1 '*n+'\n'
LIMITS=[('最大链避免递归栈',lambda:large(False),2.0),('最大同色星形答案超 int',lambda:large(True),2.0)]

if __name__ == '__main__':
    ok=main(solution=str(HERE/'e.cpp'),brute=str(HERE/'e_brute.cpp'),
        gen=gen,edges=EDGES,limits=LIMITS,rounds=1000,seed=26110209,
        log_file=str(HERE/'../../_work/logs/verify_e.log'))
    sys.exit(0 if ok else 1)
