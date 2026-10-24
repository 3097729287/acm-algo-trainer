"""Independent small oracles, explicit edges and full-size inputs for ABC 481."""
from math import gcd


def graph_input(n, edges, start=None, target=None):
    first = f'{n} {len(edges)}' + (f' {start} {target}' if start is not None else '')
    return first + '\n' + '\n'.join(' '.join(map(str, e)) for e in edges) + '\n'


def gen(letter, rng):
    if letter == 'A':
        return f'{rng.randint(1, 9)} {rng.randint(1, 9)}\n'
    if letter == 'B':
        n = rng.randint(2, 16)
        a = [rng.randint(1, 8)]
        for _ in range(n - 1):
            a.append(rng.choice([v for v in range(1, 9) if v != a[-1]]))
        return f'{n} {rng.randint(1, 8)}\n' + ' '.join(map(str, a)) + '\n'
    if letter == 'C':
        names = ['a', 'z', 'pumpkin', 'ghost', 'aab', 'aba', 'abcdefghij']
        a = [rng.choice(names) for _ in range(rng.randint(1, 40))]
        return str(len(a)) + '\n' + '\n'.join(a) + '\n'
    if letter == 'D':
        n = rng.randint(2, 10)
        edges = [tuple(rng.sample(range(1, n + 1), 2)) for _ in range(rng.randint(1, 35))]
        s, t = rng.sample(range(1, n + 1), 2)
        return graph_input(n, edges, s, t)
    if letter == 'E':
        points, directions = [], set()
        for _ in range(rng.randint(1, 22)):
            while True:
                x, y = rng.randint(-20, 20), rng.randint(-20, 20)
                if x == y == 0:
                    continue
                g = gcd(x, y)
                u, v = x // g, y // g
                if u < 0 or (u == 0 and v < 0):
                    u, v = -u, -v
                if (u, v) not in directions:
                    directions.add((u, v))
                    points.append((x, y))
                    break
        return '1\n' + str(len(points)) + '\n' + '\n'.join(f'{x} {y}' for x, y in points) + '\n'
    n = rng.randint(2, 10)
    edges = [(rng.randint(1, v - 1), v, rng.randint(1, 9)) for v in range(2, n + 1)]
    edges += [(rng.randint(1, n), rng.randint(1, n), rng.randint(1, 9)) for _ in range(rng.randint(0, 25))]
    rng.shuffle(edges)
    return graph_input(n, edges)


EDGES = {
    'A': [(f'全部合法输入 {a}+{b}', f'{a} {b}\n', str(len(str(a + b)))) for a in range(1, 10) for b in range(1, 10)],
    'B': [('折点相切只算一次', '3 3\n1 3 1\n', '1'), ('两个端点', '3 3\n3 1 3\n', '2'), ('内部交点', '2 2\n1 3\n', '1'), ('完全不相交', '2 5\n1 3\n', '0')],
    'C': [('名字重复且编号按出现顺序', '5\nz\na\nz\nb\na\n', '1\n2\n1\n3\n2'), ('一个账户', '1\na\n', '1')],
    'D': [('有向不可达', '2 1 2 1\n1 2\n', '-1'), ('自动驾驶陷入环需付费', '4 4 1 4\n1 2\n1 3\n2 1\n3 4\n', '1'), ('全程免费', '3 2 1 3\n1 2\n2 3\n', '0'), ('重边同价', '2 2 1 2\n1 2\n1 2\n', '0')],
    'E': [('单星', '1\n1\n1 0\n', '1'), ('跨越角度起点', '1\n3\n3 -1\n2 1\n1 2\n', '3'), ('分散三方向', '1\n3\n1 0\n-1 2\n-1 -2\n', '2'), ('叉积接近上界', '1\n2\n1000000000 999999999\n-999999999 1000000000\n', '2')],
    'F': [('相同前缀合组后再排序', '4 4\n1 2 1\n1 3 1\n2 4 9\n3 4 2\n', '1\n1\n12'), ('位数优先于字典序', '3 3\n1 2 1\n1 3 9\n2 3 1\n', '1\n9'), ('同组目标重复', '3 5\n1 2 1\n1 2 1\n2 3 2\n2 3 1\n2 2 1\n', '1\n11')],
}


def full(letter):
    if letter == 'A':
        return '9 9\n'
    if letter == 'B':
        return '100 50\n' + '1 100 ' * 50 + '\n'
    if letter == 'C':
        names = []
        for i in range(200000):
            digits = []
            for _ in range(5):
                digits.append(chr(97 + i % 26))
                i //= 26
            names.append(''.join(digits))
        return '200000\n' + '\n'.join(names) + '\n'
    if letter == 'D':
        return graph_input(200000, [(i, i + 1) for i in range(1, 200000)] + [(1, 200000)], 1, 200000)
    if letter == 'E':
        return '1\n200000\n' + '\n'.join(f'{x} 1' for x in range(1, 200001)) + '\n'
    return graph_input(200000, [(i, i + 1, i % 9 + 1) for i in range(1, 200000)] + [(1, 1, 1)])
