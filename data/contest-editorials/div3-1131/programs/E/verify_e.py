import sys
from pathlib import Path
sys.path.insert(0,str(Path.home()/'.dsh/tools'))
from verify import main
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))

def gen(rng):
    n=rng.randint(1,7)
    return f'1\n{n}\n'+' '.join(str(rng.randint(-4,4)) for _ in range(n))+'\n'
EDGES=[('负单点不允许变号','1\n1\n-3\n','-3\n'),('不能直接取绝对值','1\n2\n6 -7\n','1\n'),('含零奇数长度','1\n5\n-10 1 0 1 -10\n','18\n'),('全零','1\n4\n0 0 0 0\n','0\n'),('绝对值总和超 int','1\n4\n1000000000 -1000000000 1000000000 -1000000000\n','0\n')]
LIMITS=[('最大数量与边界值',lambda:'1\n200000\n'+('1000000000 -1000000000 '*100000)+'\n',2.0)]
ROUNDS=1000

if __name__=='__main__':
    ok=main(solution=str(HERE/'e.cpp'),brute=str(HERE/'e_brute.cpp'),
        gen=gen,edges=EDGES,limits=LIMITS,rounds=ROUNDS,seed=227804,
        checker=None,log_file=str(HERE/'../../_work/logs/verify_e.log'))
    sys.exit(0 if ok else 1)
