import sys
from pathlib import Path
sys.path.insert(0,str(Path.home()/'.dsh/tools'))
from verify import main
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))

from check_b import checker
def gen(rng):
    n=rng.randint(1,7);x=rng.randint(0,n);y=rng.randint(0,n-x);z=n-x-y
    return f'1\n{x} {y} {z}\n'
EDGES=[('只有石头','1\n1 0 0\n','P\n'),('三者并列','1\n1 1 1\n','PPP\n'),('两者并列且有零','1\n0 2 2\n','RRRR\n'),('只出布','1\n0 0 3\n','SSS\n')]
LIMITS=[('最大组数与最长输出',lambda:'1000\n'+'100 100 100\n'*1000,2.0)]
ROUNDS=300

if __name__=='__main__':
    ok=main(solution=str(HERE/'b.cpp'),brute=str(HERE/'b_brute.cpp'),
        gen=gen,edges=EDGES,limits=LIMITS,rounds=ROUNDS,seed=227801,
        checker=checker,log_file=str(HERE/'../../_work/logs/verify_b.log'))
    sys.exit(0 if ok else 1)
