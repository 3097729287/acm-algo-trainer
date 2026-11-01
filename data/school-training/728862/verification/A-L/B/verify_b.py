import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path[:0]=[str(Path.home()/'.dsh/tools'),str(ROOT/'_work')]
from verify import main
from validation import gen_case,EDGES as ALL_EDGES,limit_cases,CHECKERS
EDGES=ALL_EDGES['B']
LIMITS=limit_cases('B')
def gen(rng):return gen_case('B',rng)
if __name__=='__main__':
    ok=main(solution=str(HERE/'b.cpp'),brute=str(HERE/'b_brute.cpp'),gen=gen,edges=EDGES,limits=LIMITS,letter='B',rounds=300,seed=728862,samples_file=str(ROOT/'_work/samples.py'),checker=CHECKERS.get('B'),log_file=str(ROOT/'_work/logs/verify_b.log'))
    sys.exit(0 if ok else 1)
