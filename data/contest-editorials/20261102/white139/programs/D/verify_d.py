import os, sys
sys.path.insert(0, os.path.expanduser('~/.dsh/tools'))
from verify import main
HERE = os.path.dirname(os.path.abspath(__file__))

def gen(rng):
    n = rng.randint(3, 55)
    return '1\n%d\n%s\n' % (n, ' '.join(str(rng.randint(-50, 50)) for _ in range(n)))

EDGES = [('最小规模', '1\n3\n1 2 3\n', '6'),
         ('全为负数', '1\n5\n-5 -4 -3 -2 -1\n', '-6'),
         ('长度九可选', '1\n9\n1 1 1 1 1 1 1 1 1\n', '9'),
         ('长度八不能全选', '1\n8\n1 1 1 1 1 1 1 1\n', '3'),
         ('超过int的区间和', '1\n3\n1000000000 1000000000 1000000000\n', '3000000000')]
LIMITS = [('最大规模正负交替', lambda: '1\n200000\n' + '1000000000 -999999999 ' * 100000 + '\n', 1.0),
          ('最大规模全负', lambda: '1\n200000\n' + '-1000000000 ' * 200000 + '\n', 1.0)]
if __name__ == '__main__':
    main(solution=os.path.join(HERE, 'd.cpp'), brute=os.path.join(HERE, 'd_brute.cpp'),
         gen=gen, edges=EDGES, limits=LIMITS, rounds=300, seed=13904,
         log_file=os.path.join(HERE, '../../_work/logs/verify_d.log'))
