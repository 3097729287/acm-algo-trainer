import os, sys
sys.path.insert(0, os.path.expanduser('~/.dsh/tools'))
from verify import main
HERE = os.path.dirname(os.path.abspath(__file__))

def gen(rng):
    n = rng.randint(1, 11)
    p = list(range(1, n + 1)); rng.shuffle(p)
    mode = rng.randrange(4)
    if mode == 0:
        pos = {v: i for i, v in enumerate(p, 1)}
        k = rng.randint(0, n + 1)
        q = sorted(p, key=lambda v: (pos[v] + k * v, pos[v]))
    elif mode == 1:
        q = p[:]
    elif mode == 2:
        q = sorted(p)
    else:
        q = p[:]; rng.shuffle(q)
    return '1\n%d\n%s\n%s\n' % (n, ' '.join(map(str, p)), ' '.join(map(str, q)))

EDGES = [('单元素无穷', '1\n1\n1\n1\n', 'inf'),
         ('相等时原下标优先', '1\n2\n2 1\n2 1\n', '2'),
         ('严格早醒', '1\n2\n2 1\n1 2\n', 'inf'),
         ('永远不能倒序', '1\n2\n1 2\n2 1\n', '0'),
         ('上下界恰好相交', '1\n4\n4 2 1 3\n2 1 4 3\n', '1')]
LIMITS = [('最大规模正序', lambda: '1\n200000\n' + ' '.join(map(str, range(1, 200001))) + '\n' + ' '.join(map(str, range(1, 200001))) + '\n', 1.0),
          ('最大规模逆序原样输出', lambda: '1\n200000\n' + ' '.join(map(str, range(200000, 0, -1))) + '\n' + ' '.join(map(str, range(200000, 0, -1))) + '\n', 1.0)]
if __name__ == '__main__':
    main(solution=os.path.join(HERE, 'e.cpp'), brute=os.path.join(HERE, 'e_brute.cpp'),
         gen=gen, edges=EDGES, limits=LIMITS, rounds=1000, seed=13905,
         log_file=os.path.join(HERE, '../../_work/logs/verify_e.log'))
