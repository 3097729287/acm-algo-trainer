"""Portable independent literal oracles and closed-form maximum cases."""

from itertools import combinations,permutations,product

from collections import deque,Counter

import random

IDS={'P3531', 'P5677', 'P11656', 'P14521', 'CF44C', 'P2161', 'P4939', 'P1714', 'P10235', 'CF1194E', 'P14379', 'P4064', 'P8201', 'P3149', 'P5367', 'P1966', 'P7149', 'CF961E'}

def inv(a):
    return sum((a[i] > a[j] for i in range(len(a)) for j in range(i + 1, len(a))))

def line(a):
    return ' '.join(map(str, a)) + '\n'

def adjacent(a, b):
    queue = deque([(a, 0)])
    seen = {a}
    while queue:
        s, d = queue.popleft()
        if s == b:
            return d
        for i in range(len(s) - 1):
            if s[i] == s[i + 1]:
                continue
            t = s[:i] + s[i + 1] + s[i] + s[i + 2:]
            if t not in seen:
                seen.add(t)
                queue.append((t, d + 1))
    raise AssertionError('not anagrams')

def pasture(points):
    answer = 1
    for mask in range(1, 1 << len(points)):
        selected = [p for i, p in enumerate(points) if mask >> i & 1]
        l = min((x for x, y in selected))
        r = max((x for x, y in selected))
        b = min((y for x, y in selected))
        t = max((y for x, y in selected))
        answer += sum((1 << i for i, (x, y) in enumerate(points) if l <= x <= r and b <= y <= t)) == mask
    return answer

def split_inversions(a, k):
    best = 10 ** 9
    for count in range(k):
        for cuts in combinations(range(1, len(a)), count):
            endpoints = (0,) + cuts + (len(a),)
            best = min(best, max((inv(a[l:r]) for l, r in zip(endpoints, endpoints[1:]))))
    return best

def paths(n, edges):
    graph = [[] for _ in range(n)]
    for a, b in edges:
        graph[a].append(b)
        graph[b].append(a)
    result = {}
    for root in range(n):
        queue = [(root, -1, [root])]
        for u, p, path in queue:
            result[root, u] = path
            for v in graph[u]:
                if v != p:
                    queue.append((v, u, path + [v]))
    return result

def xor_path(weights, path):
    answer = 0
    for p in path:
        answer ^= weights[p]
    return answer

def spray(a, k):
    n = len(a)
    for count in range(1, n + 1):
        for chosen in combinations(range(n), count):
            for signs in product([-1, 1], repeat=count):
                directions = dict(zip(chosen, signs))
                covered = set(chosen)
                valid = True
                for i in chosen:
                    strength = k[i]
                    direction = directions[i]
                    for t in range(1, a[i]):
                        j = i + t * direction
                        if not 0 <= j < n:
                            break
                        if j in directions:
                            if directions[j] != direction:
                                valid = False
                                break
                            if strength == 0:
                                break
                            strength -= 1
                        covered.add(j)
                    if not valid:
                        break
                if valid and len(covered) == n:
                    return count

def mex(a):
    values = set(a)
    x = 1
    while x in values:
        x += 1
    return x

def fuel(a):
    return sum((any((mex(a[l:c]) != mex(a[c:r]) for c in range(l + 1, r))) for l in range(len(a)) for r in range(l + 2, len(a) + 1)))

def rectangle(segments):
    horizontal = []
    vertical = []
    for x1, y1, x2, y2 in segments:
        if y1 == y2:
            horizontal.append((min(x1, x2), max(x1, x2), y1))
        else:
            vertical.append((x1, min(y1, y2), max(y1, y2)))

    def meets(h, v):
        return h[0] <= v[0] <= h[1] and v[1] <= h[2] <= v[2]
    return sum((all((meets(h, v) for h in hs for v in vs)) for hs in combinations(horizontal, 2) for vs in combinations(vertical, 2)))

def cases_for(pid):
    R=random.Random(2026103111656);result=[]
    def check(inp,expected):result.append((f'独立校验 {len(result)+1}',str(inp),str(expected)))
    for test in range(180):
        if pid == 'CF44C':
            n = R.randint(1, 25)
            m = R.randint(1, 20)
            intervals = sorted(((R.randint(1, n), R.randint(1, n)) for _ in range(m)))
            intervals = [(min(l, r), max(l, r)) for l, r in intervals]
            intervals = sorted(intervals)
            intervals = []
            previous = 1
            for _ in range(m):
                l = R.randint(previous, n)
                r = R.randint(l, n)
                intervals.append((l, r))
                previous = r
            count = [sum((l <= i <= r for l, r in intervals)) for i in range(1, n + 1)]
            bad = next((i for i, x in enumerate(count) if x != 1), None)
            check(f'{n} {m}\n' + ''.join((f'{l} {r}\n' for l, r in intervals)), 'OK' if bad is None else f'{bad + 1} {count[bad]}')
        elif pid == 'P1714':
            n = R.randint(1, 20)
            m = R.randint(1, n)
            a = [R.randint(-500, 500) for _ in range(n)]
            check(f'{n} {m}\n' + line(a), max((sum(a[l:r]) for l in range(n) for r in range(l + 1, min(n, l + m) + 1))))
        elif pid == 'P3531':
            n = R.randint(1, 8)
            a = ''.join((R.choice('ABC') for _ in range(n)))
            b = list(a)
            R.shuffle(b)
            b = ''.join(b)
            check(f'{n}\n{a}\n{b}\n', adjacent(a, b))
        elif pid == 'P2161':
            commands = []
            answers = []
            kept = []
            for _ in range(30):
                if R.randrange(4) == 0:
                    commands.append('B')
                    answers.append(len(kept))
                    continue
                l, r = sorted(R.sample(range(1, 30), 2))
                commands.append(f'A {l} {r}')
                survivors = [(a, b) for a, b in kept if b < l or r < a]
                answers.append(len(kept) - len(survivors))
                kept = survivors + [(l, r)]
            check('30\n' + '\n'.join(commands) + '\n', line(answers))
        elif pid == 'P4939':
            n = R.randint(1, 30)
            commands = []
            answers = []
            a = [0] * n
            for _ in range(35):
                if R.randrange(3) == 0:
                    p = R.randint(1, n)
                    commands.append(f'1 {p}')
                    answers.append(a[p - 1])
                else:
                    l = R.randint(1, n)
                    r = R.randint(l, n)
                    commands.append(f'0 {l} {r}')
                    for i in range(l - 1, r):
                        a[i] += 1
            check(f'{n} 35\n' + '\n'.join(commands) + '\n', line(answers))
        elif pid == 'P5367':
            n = R.randint(1, 7)
            a = list(range(1, n + 1))
            R.shuffle(a)
            rank = next((i + 1 for i, p in enumerate(permutations(range(1, n + 1))) if list(p) == a))
            check(str(n) + '\n' + line(a), rank)
        elif pid == 'P7149':
            n = R.randint(1, 9)
            xs = R.sample(range(30), n)
            ys = R.sample(range(30), n)
            points = list(zip(xs, ys))
            check(str(n) + '\n' + ''.join((f'{x} {y}\n' for x, y in points)), pasture(points))
        elif pid == 'P10235':
            n = R.randint(1, 10)
            k = R.randint(1, n)
            a = [R.randint(-5, 5) for _ in range(n)]
            check(f'1\n{n} {k}\n' + line(a), split_inversions(a, k))
        elif pid == 'P14521':
            n = R.randint(1, 14)
            q = 12
            parent = [0, 0] + [R.randrange(1, i) for i in range(2, n + 1)]
            bounds = [(0, 0)] * 2 + [tuple(sorted([R.randint(-20, 20), R.randint(-20, 20)])) for _ in range(2, n + 1)]
            delta = [0] + [R.randint(-15, 15) for _ in range(n)]
            queries = [R.randint(-20, 20) for _ in range(q)]
            answers = []
            for x in queries:
                current = [None] * (n + 1)
                current[1] = x + delta[1]
                for i in range(2, n + 1):
                    value = current[parent[i]]
                    l, r = bounds[i]
                    if value is not None and l <= value <= r:
                        current[i] = value + delta[i]
                answers.append(sum((v is not None for v in current[1:])))
            inp = f'{n} {q}\n' + ''.join((f'{parent[i]} {bounds[i][0]} {bounds[i][1]}\n' for i in range(2, n + 1))) + ''.join((f"{('+' if d >= 0 else '-')} {abs(d)}\n" for d in delta[1:])) + ''.join((str(x) + '\n' for x in queries))
            check(inp, line(answers))
        elif pid == 'CF961E':
            n = R.randint(1, 25)
            a = [R.randint(1, 40) for _ in range(n)]
            answer = sum((j + 1 <= a[i] and i + 1 <= a[j] for i in range(n) for j in range(i + 1, n)))
            check(str(n) + '\n' + line(a), answer)
        elif pid == 'P1966':
            n = R.randint(1, 6)
            a = R.sample(range(100), n)
            b = R.sample(range(100), n)
            possibilities = []
            for perm in permutations(range(n)):
                cost = sum(((a[i] - b[perm[i]]) ** 2 for i in range(n)))
                possibilities.append((cost, inv(perm)))
            check(str(n) + '\n' + line(a) + line(b), min(possibilities)[1])
        elif pid == 'P3149':
            n = R.randint(1, 18)
            m = 12
            a = [R.randint(1, 10) for _ in range(n)]
            original = list(a)
            queries = [R.randrange(n) for _ in range(m)]
            answers = [inv(a)]
            for k in queries:
                value = a[k]
                positions = [i for i, x in enumerate(a) if x <= value]
                selected = sorted((a[i] for i in positions))
                for p, x in zip(positions, selected):
                    a[p] = x
                answers.append(inv(a))
            check(f'{n} {m}\n' + line(original) + ''.join((str(k + 1) + '\n' for k in queries)), line(answers))
        elif pid == 'P4064':
            n = R.randint(1, 6)
            all_intervals = [(l, r) for l in range(n) for r in range(l, n)]
            m = R.randint(1, min(8, len(all_intervals)))
            intervals = R.sample(all_intervals, m)
            k = R.randint(1, m)
            increment = R.randint(1, 10)
            a = [R.randint(1, 15) for _ in range(n)]
            best = 0
            for selected in combinations(intervals, k):
                best = max(best, min((a[i] + increment * sum((l <= i <= r for l, r in selected)) for i in range(n))))
            check(f'1\n{n} {m} {k} {increment}\n' + line(a) + ''.join((f'{l + 1} {r + 1}\n' for l, r in intervals)), best)
        elif pid == 'P5677':
            n = R.randint(1, 16)
            m = 12
            a = R.sample(range(1, 100), n)
            pairs = []
            for i, x in enumerate(a):
                if n == 1:
                    continue
                distance = min((abs(x - y) for j, y in enumerate(a) if i != j))
                pairs.extend(((i, j) for j, y in enumerate(a) if i != j and abs(x - y) == distance))
            queries = [tuple(sorted([R.randrange(n), R.randrange(n)])) for _ in range(m)]
            answer = sum(((id + 1) * sum((l <= i <= r and l <= j <= r for i, j in pairs)) for id, (l, r) in enumerate(queries)))
            check(f'{n} {m}\n' + line(a) + ''.join((f'{l + 1} {r + 1}\n' for l, r in queries)), answer)
        elif pid == 'P8201':
            n = R.randint(2, 15)
            m = 12
            weights = [R.randrange(16) for _ in range(n)]
            edges = [(R.randrange(i), i) for i in range(1, n)]
            routes = paths(n, edges)
            queries = []
            answers = []
            for _ in range(m):
                a, b = R.sample(range(n), 2)
                k = R.randrange(32)
                queries.append((a, b, k))
                answers.append('Yes' if any((xor_path(weights, routes[t, a]) ^ xor_path(weights, routes[t, b]) == k for t in range(n))) else 'No')
            check(f'{n} {m}\n' + line(weights) + ''.join((f'{a + 1} {b + 1}\n' for a, b in edges)) + ''.join((f'{a + 1} {b + 1} {k}\n' for a, b, k in queries)), '\n'.join(answers))
        elif pid == 'P11656':
            n = R.randint(1, 8)
            a = [R.randint(1, n + 2) for _ in range(n)]
            k = [R.randrange(n + 1) for _ in range(n)]
            check(str(n) + '\n' + line(a) + line(k), spray(a, k))
        elif pid == 'P14379':
            n = R.randint(1, 9)
            q = 12
            a = [R.randint(1, 5) for _ in range(n)]
            original = list(a)
            queries = []
            answers = []
            for _ in range(q):
                p = R.randrange(n)
                v = R.randint(1, 5)
                queries.append((p, v))
                a[p] = v
                answers.append(fuel(a))
            check(f'{n} {q}\n' + line(original) + ''.join((f'{p + 1} {v}\n' for p, v in queries)), line(answers))
        elif pid == 'CF1194E':
            h = R.randint(0, 6)
            v = R.randint(0, 6)
            if h + v == 0:
                h = 1
            ys = R.sample(range(-6, 7), h)
            xs = R.sample(range(-6, 7), v)
            segments = []
            for y in ys:
                l, r = sorted(R.sample(range(-7, 8), 2))
                segments.append((l, y, r, y))
            for x in xs:
                l, r = sorted(R.sample(range(-7, 8), 2))
                segments.append((x, l, x, r))
            R.shuffle(segments)
            check(str(len(segments)) + '\n' + ''.join((line(s) for s in segments)), rectangle(segments))
    result.extend(boundary_cases(pid))
    if pid in {'P2161','P4939','P14521','P3149','P14379'}:
        result=[(name,inp,'\n'.join(expected.split())+'\n') for name,inp,expected in result]
    return result


def choose(n):return n*(n-1)//2

def boundary_cases(pid):
    result=[]
    def check(problem,name,inp,expected):result.append(('最大范围 '+name,str(inp),str(expected)))
    if pid=='CF44C':
        check('CF44C', 'all-days', '100 100\n' + ''.join((f'{i} {i}\n' for i in range(1, 101))), 'OK')
        check('CF44C', 'shared-closed-endpoint', '100 2\n1 50\n50 100\n', '50 2')
    if pid=='P1714':
        n = 500000
        check('P1714', 'all-positive', f'{n} {n}\n' + line([500] * n), n * 500)
        check('P1714', 'nonempty-negative', f'{n} {n}\n' + line([-500] * n), -500)
    if pid=='P3531':
        n = 1000000
        check('P3531', 'reverse-equal-groups', f'{n}\n' + 'A' * (n // 2) + 'B' * (n // 2) + '\n' + 'B' * (n // 2) + 'A' * (n // 2) + '\n', (n // 2) ** 2)
        check('P3531', 'same-repeated', f'{n}\n' + 'ABCDEF' * (n // 6) + 'A' * (n % 6) + '\n' + 'ABCDEF' * (n // 6) + 'A' * (n % 6) + '\n', 0)
    if pid=='P2161':
        commands = [f'A {i} {i}' for i in range(1, 100001)] + ['B', 'A 1 100000', 'B'] + ['A 1 100000'] * 99997
        check('P2161', 'all-cancel-once', '200000\n' + '\n'.join(commands) + '\n', line([0] * 100000 + [100000, 100000, 1] + [1] * 99997))
        check('P2161', 'cancel-original-not-union', '4\nA 1 10\nA 20 30\nA 9 21\nA 29 29\n', '0\n0\n2\n0')
    if pid=='P4939':
        check('P4939', 'full-range-last-event', '10000000 400000\n' + '0 1 10000000\n' * 200000 + '1 10000000\n' * 100000 + '1 1\n' * 100000, line([200000] * 200000))
        check('P4939', 'no-update-events', '10000000 400000\n' + '1 10000000\n' * 400000, line([0] * 400000))
    if pid=='P5367':
        n = 1000000
        check('P5367', 'first-permutation', str(n) + '\n' + line(range(1, n + 1)), 1)
        factorial = 1
        for i in range(1, n + 1):
            factorial = factorial * i % 998244353
        check('P5367', 'last-permutation', str(n) + '\n' + line(range(n, 0, -1)), factorial)
    if pid=='P7149':
        n = 2500
        check('P7149', 'increasing-diagonal', str(n) + '\n' + ''.join((f'{i} {i}\n' for i in range(n))), n * (n + 1) // 2 + 1)
        check('P7149', 'decreasing-diagonal', str(n) + '\n' + ''.join((f'{i} {n - i}\n' for i in range(n))), n * (n + 1) // 2 + 1)
    if pid=='P10235':
        n = 100000
        for k in [1, 317, n]:
            check('P10235', 'descending-k' + str(k), f'1\n{n} {k}\n' + line(range(n, 0, -1)), choose((n + k - 1) // k))
        check('P10235', 'equal-high-zero', f'1\n{n} 1\n' + line([1000000000] * n), 0)
        check('P10235', 'alternating-ties', f'1\n{n} 1\n' + line([1, 0] * (n // 2)), n // 2 * (n // 2 + 1) // 2)
    if pid=='P14521':
        n = 500000
        q = 1000000
        bound = 10 ** 18
        check('P14521', 'unreachable-chain-must-not-accumulate', f'{n} {q}\n' + ''.join((f'{i - 1} {-bound} {bound}\n' for i in range(2, n + 1))) + f'+ {bound}\n' * n + ''.join((str(x) + '\n' for x in [-bound, 0, bound, -bound + 1] * (q // 4))), line([3, 2, 1, 2] * (q // 4)))
        check('P14521', 'negative-operands-closed-star', f'{n} 4\n' + f'1 {-bound} {bound}\n' * (n - 1) + f'+ {-bound}\n' * n + f'{-bound}\n0\n{bound}\n1\n', line([1, n, n, n]))
    if pid=='CF961E':
        n = 200000
        check('CF961E', 'all-pairs', str(n) + '\n' + line([1000000000] * n), choose(n))
        check('CF961E', 'only-one-episode', str(n) + '\n' + line([1] * n), 0)
        check('CF961E', 'odd-full-even-one', str(n) + '\n' + line([n, 1] * (n // 2)), choose(n // 2) + n // 2)
    if pid=='P1966':
        n = 100000
        check('P1966', 'reverse-large-heights', str(n) + '\n' + line(range(n)) + line(range(2147483647, 2147483647 - n, -1)), choose(n) % 99999997)
        check('P1966', 'ordered-large-heights', str(n) + '\n' + line(range(n)) + line(range(2147483647 - n, 2147483647)), 0)
    if pid=='P3149':
        n = m = 300000
        check('P3149', 'descending-growing-current-threshold', f'{n} {m}\n' + line(range(n, 0, -1)) + ''.join((str(n - i) + '\n' for i in range(m))), line([choose(n)] + [choose(n) - choose(i + 1) for i in range(m)]))
        check('P3149', 'duplicates-current-slot', f'{n} {m}\n' + line([2, 1] * (n // 2)) + '2\n' * (m // 2) + '1\n' * (m // 2), line([n // 2 * (n // 2 + 1) // 2] * (m // 2 + 1) + [0] * (m // 2)))
    if pid=='P4064':
        n = m = 200000
        check('P4064', 'all-prefixes-exact-k', f'1\n{n} {m} {m} 100\n' + line([1] * n) + ''.join((f'1 {r}\n' for r in range(1, n + 1))), 101)
        check('P4064', 'singletons-insufficient-k', f'1\n{n} {m} {m - 1} 100\n' + line([1] * n) + ''.join((f'{i} {i}\n' for i in range(1, n + 1))), 1)
        check('P4064', 'singletons-all-k', f'1\n{n} {m} {m} 100\n' + line([100000000] * n) + ''.join((f'{i} {i}\n' for i in range(1, n + 1))), 100000100)
    if pid=='P5677':
        n = m = 300000
        check('P5677', 'directed-both-neighbors', f'{n} {m}\n' + line(range(2, 2 * n + 1, 2)) + f'1 {n}\n' * m, (n - 1) * m * (m + 1))
        check('P5677', 'one-position-no-pair', f'{n} {m}\n' + line(range(n, 0, -1)) + '1 1\n' * m, 0)
    if pid=='P8201':
        n = m = 500000
        check('P8201', 'deep-zero-paths', f'{n} {m}\n' + line([0] * n) + ''.join((f'{i - 1} {i}\n' for i in range(2, n + 1))) + f'1 {n} 0\n1 {n} 1\n' * (m // 2), 'Yes\nNo\n' * (m // 2))
        check('P8201', 'deep-repeated-nonzero', f'{n} {m}\n' + line([10000000] * n) + ''.join((f'{i - 1} {i}\n' for i in range(2, n + 1))) + f'1 {n} 10000000\n1 {n} 0\n' * (m // 2), 'Yes\nNo\n' * (m // 2))
        check('P8201', 'above-lca-is-not-on-path', '4 3\n7 1 2 4\n1 2\n2 3\n3 4\n2 4 0\n2 4 6\n2 4 3\n', 'No\nYes\nYes')
    if pid=='P11656':
        n = 500000
        check('P11656', 'unit-distance', str(n) + '\n' + line([1] * n) + line([0] * n), n)
        check('P11656', 'entire-line', str(n) + '\n' + line([n] * n) + line([n] * n), 1)
        check('P11656', 'two-cells-any-strength', str(n) + '\n' + line([2] * n) + line([i % 7 for i in range(n)]), (n + 1) // 2)
        distance = [1] * n
        distance[n // 2] = n
        check('P11656', 'one-long-middle', str(n) + '\n' + line(distance) + line([n] * n), 1 + min(n // 2, n - n // 2 - 1))
    if pid=='P14379':
        n = q = 1000000
        p = n // 2
        queries = ''.join((f'{p} {v}\n' for v in [1, 2, 3, 1] * (q // 4)))
        answer = p * (n - p + 1) - 1
        check('P14379', 'single-one-category-changes', f'{n} {q}\n' + line([3] * n) + queries, line([answer, 0, 0, answer] * (q // 4)))
        queries = ''.join((f'{p} {v}\n' for v in [2, 3, 1, 1] * (q // 4)))
        check('P14379', 'single-two-endpoint-cases', f'{n} {q}\n' + line([1] * n) + queries, line([answer, n - 1, 0, 0] * (q // 4)))
    if pid=='CF1194E':
        h = v = 2500
        check('CF1194E', 'full-grid', str(h + v) + '\n' + ''.join((f'-5000 {y} 5000 {y}\n' for y in range(h))) + ''.join((f'{x} -5000 {x} 5000\n' for x in range(v))), choose(h) * choose(v))
        check('CF1194E', 'same-orientation', str(5000) + '\n' + ''.join((f'-5000 {y} 5000 {y}\n' for y in range(5000))), 0)
        check('CF1194E', 'closed-corners', '4\n0 0 1 0\n0 1 1 1\n0 0 0 1\n1 0 1 1\n', 1)
        check('CF1194E', 'same-x-disjoint-parts', '5\n0 0 1 0\n0 2 1 2\n0 0 0 2\n1 0 1 1\n1 2 1 3\n', 0)
    return result
