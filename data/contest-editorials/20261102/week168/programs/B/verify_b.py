import os, sys
from pathlib import Path
sys.path.insert(0, os.path.expanduser('~/.dsh/tools'))
from verify import main
HERE=Path(__file__).resolve().parent

def gen(rng):
    n,m=rng.randint(1,9),rng.randint(1,9)
    return f'{n} {m}\n'+'\n'.join(''.join(rng.choice('.#') for _ in range(m)) for _ in range(n))+'\n'
EDGES=[('单格故障','1 1\n#\n','1\n'),('单列','4 1\n#\n.\n#\n#\n','3\n'),('内圈不计','3 3\n...\n.#.\n...\n','0\n')]
LIMITS=[('最大面积',lambda:'200 2000\n'+('#'*2000+'\n')*200,2.0)]

if __name__ == '__main__':
    ok=main(solution=str(HERE/'b.cpp'),brute=str(HERE/'b_brute.cpp'),
        gen=gen,edges=EDGES,limits=LIMITS,rounds=300,seed=26110200,
        log_file=str(HERE/'../../_work/logs/verify_b.log'))
    sys.exit(0 if ok else 1)
