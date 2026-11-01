import sys
from pathlib import Path
sys.path.insert(0,str(Path.home()/'.dsh/tools'))
from verify import main
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))

def gen(rng):
    return f'1\n{rng.randint(2,7)} {rng.randint(1,7)}\n'
EDGES=[('长度二最小 m','1\n2 1\n','1\n'),('长度二无解','1\n2 2\n','0\n'),('唯一中间路径','1\n3 2\n','1\n'),('最后二或一','1\n3 1\n','3\n'),('一条路径多种停留','1\n4 1\n','6\n')]
LIMITS=[('最大二维状态',lambda:'1\n4000 4000\n',2.0),('组数上界与总和上界',lambda:'2000\n'+'2 2\n'*2000,2.0)]
ROUNDS=1000

if __name__=='__main__':
    ok=main(solution=str(HERE/'f.cpp'),brute=str(HERE/'f_brute.cpp'),
        gen=gen,edges=EDGES,limits=LIMITS,rounds=ROUNDS,seed=227805,
        checker=None,log_file=str(HERE/'../../_work/logs/verify_f.log'))
    sys.exit(0 if ok else 1)
