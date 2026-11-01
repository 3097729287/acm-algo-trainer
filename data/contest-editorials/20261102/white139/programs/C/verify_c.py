import os, sys
sys.path.insert(0, os.path.expanduser('~/.dsh/tools'))
from verify import main
HERE = os.path.dirname(os.path.abspath(__file__))

def gen(rng):
    n = rng.randint(1, 13)
    x = rng.choice([1, n, rng.randint(1, n)])
    return '1\n%d %d\n%s\n' % (n, x, ' '.join(str(rng.choice([1, 2, 10**9, rng.randint(1, 100)])) for _ in range(n)))

EDGES = [('不用改判', '1\n1 1\n100\n', '0'),
         ('必须回选旧轮', '1\n3 1\n1 100 100\n', '1'),
         ('偶数轮且上限一', '1\n4 1\n1 2 3 4\n', '-1'),
         ('全相等且允许落后', '1\n5 1\n2 2 2 2 2\n', '4'),
         ('答案超过int', '1\n7 1\n1000000000 1000000000 1000000000 1000000000 1000000000 1000000000 1000000000\n', '3000000000')]
LIMITS = [('最大规模堆操作', lambda: '1\n199999 1\n' + '1000000000 ' * 199999 + '\n', 1.0),
          ('最大规模不改判', lambda: '1\n200000 200000\n' + '1 ' * 200000 + '\n', 1.0)]
if __name__ == '__main__':
    main(solution=os.path.join(HERE, 'c.cpp'), brute=os.path.join(HERE, 'c_brute.cpp'),
         gen=gen, edges=EDGES, limits=LIMITS, rounds=1000, seed=13903,
         log_file=os.path.join(HERE, '../../_work/logs/verify_c.log'))
