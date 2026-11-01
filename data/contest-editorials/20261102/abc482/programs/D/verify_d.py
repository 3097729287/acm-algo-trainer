import os, sys
from pathlib import Path
sys.path.insert(0, os.path.expanduser('~/.dsh/tools'))
from verify import main
HERE=Path(__file__).resolve().parent

def gen(rng):
    n=rng.randint(1,4);xs=sorted(rng.sample(range(5),n))
    xs=[2*(x-xs[0]) for x in xs]
    return str(n)+'\n'+' '.join(map(str,xs))+'\n'
EDGES=[('单人','1\n1000000000\n','0\n'),('两人','2\n0 10\n','5\n5\n'),('中间两侧同距','3\n0 2 4\n','2\n2\n2\n'),('明显不对称','4\n0 2 4 100\n','50\n49\n49\n50\n')]
LIMITS=[('最大人数',lambda:'200000\n'+' '.join(str(2*i) for i in range(200000))+'\n',2.0)]

if __name__ == '__main__':
    ok=main(solution=str(HERE/'d.cpp'),brute=str(HERE/'d_brute.cpp'),
        gen=gen,edges=EDGES,limits=LIMITS,rounds=300,seed=26110208,
        log_file=str(HERE/'../../_work/logs/verify_d.log'))
    sys.exit(0 if ok else 1)
