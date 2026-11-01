import os, sys
from pathlib import Path
sys.path.insert(0, os.path.expanduser('~/.dsh/tools'))
from verify import main
HERE=Path(__file__).resolve().parent

def gen(rng):
    n=rng.randint(2,8)
    return f'1\n{n}\n'+' '.join(str(rng.randint(0,n)) for _ in range(n))+'\n'
EDGES=[('全部喝奶且恰好两人','1\n2\n0 0\n','2\n'),('全部不喝奶','1\n4\n4 4 4 4\n','0\n'),('三人都需喝奶','1\n3\n0 0 0\n','0\n'),('恰两名耐辣为零','1\n4\n0 0 4 4\n','24\n')]
LIMITS=[('最大规模阶梯阈值',lambda:'1\n400\n'+' '.join(str(i) for i in range(400))+'\n',2.0)]

if __name__ == '__main__':
    ok=main(solution=str(HERE/'f.cpp'),brute=str(HERE/'f_brute.cpp'),
        gen=gen,edges=EDGES,limits=LIMITS,rounds=1000,seed=26110205,
        log_file=str(HERE/'../../_work/logs/verify_f.log'))
    sys.exit(0 if ok else 1)
