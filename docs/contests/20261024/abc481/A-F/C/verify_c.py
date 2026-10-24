from pathlib import Path
import sys
HERE = Path(__file__).resolve().parent
CONTEST = HERE.parents[1]
sys.path.insert(0, str(CONTEST))
import cases
sys.path.insert(0, str(Path.home()/'.dsh/tools'))
from verify import main
def gen(rng): return cases.gen('C', rng)
EDGES = cases.EDGES['C']
LIMITS = [('题面最大规模', lambda: cases.full('C'), 2.0)]
if __name__ == '__main__':
    main(solution=str(HERE/'c.cpp'), brute=str(HERE/'c_brute.cpp'), gen=gen,
         edges=EDGES, limits=LIMITS, rounds=300, seed=20261024, letter='C',
         samples_file=str(CONTEST/'_work/samples.py'), log_file=str(CONTEST/'_work/logs/verify_C.log'))
