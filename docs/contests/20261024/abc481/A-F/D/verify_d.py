from pathlib import Path
import sys
HERE = Path(__file__).resolve().parent
CONTEST = HERE.parents[1]
sys.path.insert(0, str(CONTEST))
import cases
sys.path.insert(0, str(Path.home()/'.dsh/tools'))
from verify import main
def gen(rng): return cases.gen('D', rng)
EDGES = cases.EDGES['D']
LIMITS = [('题面最大规模', lambda: cases.full('D'), 2.0)]
if __name__ == '__main__':
    main(solution=str(HERE/'d.cpp'), brute=str(HERE/'d_brute.cpp'), gen=gen,
         edges=EDGES, limits=LIMITS, rounds=500, seed=20261024, letter='D',
         samples_file=str(CONTEST/'_work/samples.py'), log_file=str(CONTEST/'_work/logs/verify_D.log'))
