import os, sys
from pathlib import Path
sys.path.insert(0, os.path.expanduser('~/.dsh/tools'))
from verify import main
HERE=Path(__file__).resolve().parent

def gen(rng):
    return f'{rng.randint(1,30000)} {rng.randint(1,90)}\n'
EDGES=[('单位模数','1 1\n','1\n'),('N 为一','1 4\n','-1\n1\n-1\n-1\n'),('非互质有零余数','4 8\n','2\n1\n1\n-1\n1\n-1\n-1\n-1\n'),('起点正整数轮次','2 3\n','-1\n1\n1\n')]
LIMITS=[('大素数试除',lambda:'99999999999973 400000\n',2.0),('多因子与最大模数',lambda:'30425026352700 400000\n',2.0),('高重数',lambda:'70368744177664 400000\n',2.0)]

if __name__ == '__main__':
    ok=main(solution=str(HERE/'f.cpp'),brute=str(HERE/'f_brute.cpp'),
        gen=gen,edges=EDGES,limits=LIMITS,rounds=1000,seed=26110210,
        log_file=str(HERE/'../../_work/logs/verify_f.log'))
    sys.exit(0 if ok else 1)
