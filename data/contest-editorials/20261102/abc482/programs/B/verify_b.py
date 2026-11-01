import os, sys
from pathlib import Path
sys.path.insert(0, os.path.expanduser('~/.dsh/tools'))
from verify import main
HERE=Path(__file__).resolve().parent

def gen(rng):
    return '\n'.join(''.join(rng.choice('.o') for _ in range(5)) for _ in range(5))+'\n'
EDGES=[('全空',('.'*5+'\n')*5,'5\n'),('已有斜线','o....\n.o...\n..o..\n...o.\n....o\n','0\n'),('反斜线差一个','....o\n...o.\n.....\n.o...\no....\n','1\n')]
LIMITS=[('固定最大棋盘',lambda:('.'*5+'\n')*5,2.0)]

if __name__ == '__main__':
    ok=main(solution=str(HERE/'b.cpp'),brute=str(HERE/'b_brute.cpp'),
        gen=gen,edges=EDGES,limits=LIMITS,rounds=300,seed=26110206,
        log_file=str(HERE/'../../_work/logs/verify_b.log'))
    sys.exit(0 if ok else 1)
