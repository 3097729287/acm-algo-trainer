from pathlib import Path
import sys
HERE = Path(__file__).resolve().parent
CONTEST = HERE.parents[1]
sys.path.insert(0, str(CONTEST))
import cases
sys.path.insert(0, str(Path.home()/'.dsh/tools'))
from verify import main
def gen(rng): return cases.gen('A', rng)
EDGES = cases.EDGES['A']
LIMITS = [('题面最大规模', lambda: cases.full('A'), 2.0)]
if __name__ == '__main__':
    main(solution=str(HERE/'a.cpp'), brute=str(HERE/'a_brute.cpp'), gen=gen,
         edges=EDGES, limits=LIMITS, rounds=300, seed=20261024, letter='A',
         samples_file=str(CONTEST/'_work/samples.py'), log_file=str(CONTEST/'_work/logs/verify_A.log'))
