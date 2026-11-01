import os, sys
from pathlib import Path
sys.path.insert(0, os.path.expanduser('~/.dsh/tools'))
from verify import main
HERE=Path(__file__).resolve().parent

def gen(rng):
    n=rng.randint(1,25)
    return f'{n} {rng.randint(1,20)}\n'+' '.join(str(rng.randint(-30,30)) for _ in range(n))+'\n'
EDGES=[('负数单点','1 7\n-5\n','1\n'),('模一','4 1\n-3 0 9 -7\n','4\n'),('同余负余数','3 5\n-1 5 4\n','1\n')]
LIMITS=[('最大规模正负交替',lambda:'200000 1000000000\n'+('1000000000 -1000000000 '*100000)+'\n',2.0)]

if __name__ == '__main__':
    ok=main(solution=str(HERE/'c.cpp'),brute=str(HERE/'c_brute.cpp'),
        gen=gen,edges=EDGES,limits=LIMITS,rounds=300,seed=26110201,
        log_file=str(HERE/'../../_work/logs/verify_c.log'))
    sys.exit(0 if ok else 1)
