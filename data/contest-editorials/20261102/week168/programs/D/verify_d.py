import os, sys
from pathlib import Path
sys.path.insert(0, os.path.expanduser('~/.dsh/tools'))
from verify import main
HERE=Path(__file__).resolve().parent

def gen(rng):
    n=rng.randint(1,30);m=rng.randint(1,n)
    return f'{n} {m}\n'+' '.join(str(rng.randint(-100,100)) for _ in range(n))+'\n'+' '.join(str(rng.randint(0,1000000000)) for _ in range(m))+'\n'
EDGES=[('单格','1 1\n-7\n1000000000\n','-7 1\n'),('绕回首部','4 4\n1 2 3 4\n3 0 0 0\n','10 3\n'),('只移动一次','5 1\n1 2 3 4 5\n4\n','5 5\n')]
LIMITS=[('最大规模连续跳过',lambda:'200000 200000\n'+'1000000000 '*200000+'\n'+'0 '*200000+'\n',2.0)]

if __name__ == '__main__':
    ok=main(solution=str(HERE/'d.cpp'),brute=str(HERE/'d_brute.cpp'),
        gen=gen,edges=EDGES,limits=LIMITS,rounds=1000,seed=26110202,
        log_file=str(HERE/'../../_work/logs/verify_d.log'))
    sys.exit(0 if ok else 1)
