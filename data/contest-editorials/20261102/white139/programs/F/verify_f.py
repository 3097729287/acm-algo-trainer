import os, sys
sys.path.insert(0, os.path.expanduser('~/.dsh/tools'))
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from verify import main
from check_f import checker

def gen(rng):
    n = rng.randint(4, 9)
    order = list(range(1, n + 1)); rng.shuffle(order)
    mode = rng.randrange(4)
    edges = []
    for i in range(1, n):
        parent = 0 if mode == 0 else (i - 1 if mode == 1 else rng.randrange(i))
        w = 2 if mode == 2 else rng.choice([1, 2, 3, 10**9])
        edges.append((order[parent], order[i], w))
    rng.shuffle(edges)
    return '1\n%d\n%s\n' % (n, '\n'.join('%d %d %d' % e for e in edges))

EDGES = [('等权路径可行', '1\n4\n1 2 2\n2 3 2\n3 4 2\n', 'Yes'),
         ('孤立最轻边不可行', '1\n4\n1 2 1\n2 3 5\n3 4 5\n', 'No'),
         ('等权星形', '1\n4\n1 2 1\n1 3 1\n1 4 1\n', 'Yes'),
         ('先遇重边仍须找到轻邻边', '1\n4\n3 4 7\n2 3 1\n1 2 1\n', 'Yes'),
         ('最大权值', '1\n4\n1 2 1000000000\n1 3 1000000000\n1 4 1000000000\n', 'Yes')]

def large(kind):
    n = 200000
    if kind == 'chain': es = [(i, i + 1, 10**9) for i in range(1, n)]
    elif kind == 'star': es = [(1, i, 1) for i in range(2, n + 1)]
    else: es = [(i, i + 1, 1 if i % 2 else 2) for i in range(1, n)]
    return '1\n%d\n%s\n' % (n, '\n'.join('%d %d %d' % e for e in es))

LIMITS = [('最大规模等权链', lambda: large('chain'), 4.0),
          ('最大规模星形与补边', lambda: large('star'), 4.0),
          ('最大规模不可行', lambda: large('no'), 4.0)]
if __name__ == '__main__':
    main(solution=os.path.join(HERE, 'f.cpp'), brute=os.path.join(HERE, 'f_brute.cpp'),
         gen=gen, edges=EDGES, limits=LIMITS, checker=checker, rounds=1000, seed=13906,
         log_file=os.path.join(HERE, '../../_work/logs/verify_f.log'))
