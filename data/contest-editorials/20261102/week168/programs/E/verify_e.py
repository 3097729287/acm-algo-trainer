import os, sys
from pathlib import Path
sys.path.insert(0, os.path.expanduser('~/.dsh/tools'))
from verify import main
HERE=Path(__file__).resolve().parent

def gen(rng):
    n,m=rng.randint(1,6),rng.randint(1,6);k=rng.randint(0,n+m)
    a=[(rng.randint(-20,20),rng.randint(0,1)) for _ in range(n+m)]
    return f'1\n{n} {m} {k}\n'+'\n'.join(f'{x} {flag}' for x,flag in a)+'\n'
EDGES=[('空方案','1\n1 1 0\n-9 1\n-8 1\n','0\n'),('不能停在零分','1\n1 1 1\n-9 1\n-8 1\n','-8\n'),('最后标记一不强迫多取','1\n1 1 2\n3 1\n5 1\n','8\n'),('强制换堆却已空','1\n3 1 4\n1 1\n1 1\n1 1\n1 1\n','IMPOSSIBLE\n'),('同堆零连续','1\n3 1 3\n10 0\n11 0\n12 1\n-100 1\n','33\n')]

LIMITS=[('Easy 最大二维规模',lambda:'1\n2000 2000 2000\n'+('1000000000 0\n'*4000),2.0)]

if __name__ == '__main__':
    ok=main(solution=str(HERE/'e.cpp'),brute=str(HERE/'e_brute.cpp'),
        gen=gen,edges=EDGES,limits=LIMITS,rounds=1000,seed=26110203,
        log_file=str(HERE/'../../_work/logs/verify_e.log'))
    sys.exit(0 if ok else 1)
