from pathlib import Path
import sys
HERE = Path(__file__).resolve().parent
CONTEST = HERE.parents[1]
sys.path.insert(0, str(CONTEST))
import cases
sys.path.insert(0, str(Path.home()/'.dsh/tools'))
from verify import main
gen = cases.gen_c
EDGES = [cases.exhaustive_c(), ('全部为零与单数', '3\n1000000000000000000 0 0 0\n1 7 7 7\n2 7 7 0\n', '0\n7\n49')]
LIMITS = [('最大 T、60 位和大 n', cases.full_c, 2.0)]
if __name__ == '__main__':
    main(solution=str(HERE/'c.cpp'), brute=str(HERE/'c_brute.cpp'), gen=gen,
         edges=EDGES, limits=LIMITS, rounds=500, seed=20261024, letter='C',
         samples_file=str(CONTEST/'_work/samples.py'), log_file=str(CONTEST/'_work/logs/verify_C.log'))
