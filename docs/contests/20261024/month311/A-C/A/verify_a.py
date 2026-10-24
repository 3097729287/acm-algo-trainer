from pathlib import Path
import sys
HERE = Path(__file__).resolve().parent
CONTEST = HERE.parents[1]
sys.path.insert(0, str(CONTEST))
import cases
sys.path.insert(0, str(Path.home()/'.dsh/tools'))
from verify import main
gen = cases.gen_a
checker = cases.check_a
EDGES = [(f'无解 n={n}', f'{n}\n', '-1') for n in range(1, 5)] + [('最小可行长度', '5\n', '1 3 5 2 4\n3 5 2 4 1')]
LIMITS = [('题面最大规模', lambda: '1000000\n', 1.0)]
if __name__ == '__main__':
    main(solution=str(HERE/'a.cpp'), brute=str(HERE/'a_brute.cpp'), gen=gen, checker=checker,
         edges=EDGES, limits=LIMITS, rounds=300, seed=20261024, letter='A',
         samples_file=str(CONTEST/'_work/samples.py'), log_file=str(CONTEST/'_work/logs/verify_A.log'))
