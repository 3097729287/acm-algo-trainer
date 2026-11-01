import os, sys
sys.path.insert(0, os.path.expanduser('~/.dsh/tools'))
from verify import main
HERE = os.path.dirname(os.path.abspath(__file__))

def gen(rng):
    n = rng.randint(1, 40)
    return '1\n%d\n%s\n' % (n, ' '.join(str(rng.randint(1, 10**6)) for _ in range(n)))

EDGES = [('单元素', '1\n1\n7\n', '7'),
         ('分类方向', '2\n2\n1 5\n2\n5 1\n', '11\n7'),
         ('全相等', '1\n3\n4 4 4\n', '24')]
LIMITS = [('最大规模最大数值', lambda: '1\n200000\n' + '1000000 ' * 200000 + '\n', 1.0)]
if __name__ == '__main__':
    main(solution=os.path.join(HERE, 'b.cpp'), brute=os.path.join(HERE, 'b_brute.cpp'),
         gen=gen, edges=EDGES, limits=LIMITS, rounds=300, seed=13902,
         log_file=os.path.join(HERE, '../../_work/logs/verify_b.log'))
