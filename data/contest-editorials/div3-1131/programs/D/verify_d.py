import sys
from pathlib import Path
sys.path.insert(0,str(Path.home()/'.dsh/tools'))
from verify import main
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))

def gen(rng):
    n=rng.randint(2,4)
    return f'1\n{n}\n'+' '.join(str(rng.randint(-2,2)) for _ in range(n))+'\n'
EDGES=[('全相等','1\n3\n-5 -5 -5\n','0 0\n'),('奇数中位数','1\n3\n1 2 3\n','2 2\n'),('偶数中间区间','1\n4\n0 0 10 10\n','20 10\n'),('极端值','1\n2\n-1000000000 1000000000\n','2000000000 2000000000\n'),('重复值','1\n4\n1 1 1 9\n','8 8\n')]
LIMITS=[('最大绝对成本',lambda:'1\n200000\n'+'-1000000000 '*100000+'1000000000 '*100000+'\n',2.0)]
ROUNDS=1000

if __name__=='__main__':
    ok=main(solution=str(HERE/'d.cpp'),brute=str(HERE/'d_brute.cpp'),
        gen=gen,edges=EDGES,limits=LIMITS,rounds=ROUNDS,seed=227803,
        checker=None,log_file=str(HERE/'../../_work/logs/verify_d.log'))
    sys.exit(0 if ok else 1)
