import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path[:0]=[str(Path.home()/'.dsh/tools'),str(ROOT/'_work')]
from verify import main
from validation import gen_case,EDGES as ALL_EDGES,limit_cases,CHECKERS
EDGES=ALL_EDGES['G']
LIMITS=limit_cases('G')
def gen(rng):return gen_case('G',rng)
if __name__=='__main__':
    ok=main(solution=str(HERE/'g.cpp'),brute=str(HERE/'g_brute.cpp'),gen=gen,edges=EDGES,limits=LIMITS,letter='G',rounds=300,seed=728862,samples_file=str(ROOT/'_work/samples.py'),checker=CHECKERS.get('G'),log_file=str(ROOT/'_work/logs/verify_g.log'))
    sys.exit(0 if ok else 1)
