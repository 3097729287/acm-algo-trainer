"""Independent small exhaustive checks; every executable is bound to its source."""
from collections import deque
from fractions import Fraction
from itertools import combinations, permutations, product
import json
import random
import subprocess

from nowcoder_editorials import CONTENT, OUT, ROOT, program, read, sha, write

RNG = random.Random(2026110808)
LEDGER = read(CONTENT / 'reviewed.json')
COUNTS = {}


def check(number, data, expected, tolerance=0):
    key = str(number)
    entry = LEDGER['nowcoder-global::' + key]
    reference = program((ROOT / entry['articles']['default']).read_text(encoding='utf-8'))
    assert sha(reference) == entry['programSha256']
    folder = OUT / 'compiled' / key
    assert reference.strip() in (folder / 'main.cpp').read_text(encoding='utf-8')
    run = subprocess.run([str(folder / 'main.exe')], input=data, text=True, capture_output=True, timeout=8)
    assert run.returncode == 0, (number, run.stderr)
    if tolerance:
        ok = abs(float(run.stdout.strip()) - float(expected)) <= tolerance
    else:
        wanted = expected if isinstance(expected, str) else ' '.join(map(str, expected)) if isinstance(expected, list) else str(expected)
        ok = run.stdout.split() == wanted.split()
    assert ok, (number, data, expected, run.stdout)
    COUNTS[key] = COUNTS.get(key, 0) + 1


def graph(n, edges):
    result = [[] for _ in range(n)]
    for a, b in edges:
        result[a].append(b)
        result[b].append(a)
    return result


def connected(mask, adjacency):
    if not mask:
        return False
    first = (mask & -mask).bit_length() - 1
    seen = 1 << first
    queue = [first]
    for u in queue:
        for v in adjacency[u]:
            if mask >> v & 1 and not seen >> v & 1:
                seen |= 1 << v
                queue.append(v)
    return seen == mask


def heaps_and_matching():
    for _ in range(25):
        n, m = RNG.randint(1, 7), RNG.randint(1, 5)
        ours = [(RNG.randint(1, 8), RNG.randint(1, 8)) for _ in range(n)]
        enemies = [(RNG.randint(1, 8), RNG.randint(1, 8)) for _ in range(m)]
        best = -1
        for assignment in permutations(range(n), m):
            if all(ours[i][0] >= enemies[j][1] for j, i in enumerate(assignment)):
                dead = sum(ours[i][1] <= enemies[j][0] for j, i in enumerate(assignment))
                best = max(best, n - dead)
        data = f'1\n{n} {m}\n' + ''.join(f'{a} {b}\n' for a, b in ours + enemies)
        check(251572, data, f'Case #1: {best}')
        soldiers = [(RNG.randint(1, 9), RNG.randint(1, n)) for _ in range(n)]
        best = max((sum(v for j, (v, _) in enumerate(soldiers) if mask >> j & 1)
                    for mask in range(1, 1 << n)
                    if all(mask.bit_count() <= limit for j, (_, limit) in enumerate(soldiers) if mask >> j & 1)), default=0)
        check(50439, str(n) + '\n' + ''.join(f'{v} {s}\n' for v, s in soldiers), best)
        points = [(RNG.randint(0, 5), RNG.randint(0, 5)) for _ in range(15)]
        counts = [sum(not any((bx <= ax and by <= ay and (bx, by) != (ax, ay))
                             for bx, by in points[:end]) for ax, ay in points[:end]) for end in range(1, 16)]
        check(251558, '1\n15\n' + ''.join(f'{x} {y}\n' for x, y in points), 'Case #1:\n' + '\n'.join(map(str, counts)))
    for _ in range(20):
        n = RNG.randint(1, 5)
        tasks = [(RNG.randint(1, 5), RNG.randint(1, 3), RNG.randint(1, 7)) for _ in range(n)]
        tasks.sort(key=lambda t: t[2])
        optimum = None
        for removal in product(*(range(t[1] + 1) for t in tasks)):
            elapsed = 0
            valid = True
            for (z, x, deadline), remove in zip(tasks, removal):
                elapsed += x - remove
                valid &= elapsed <= deadline
            if valid:
                cost = sum((Fraction(remove, t[0]) for t, remove in zip(tasks, removal)), Fraction())
                optimum = cost if optimum is None else min(optimum, cost)
        check(22604, str(n) + '\n' + ''.join(f'{z} {x} {d}\n' for z, x, d in tasks), float(optimum), 0.05000001)


def scheduling_and_grids():
    for _ in range(25):
        n, limit = RNG.randint(1, 6), RNG.randint(1, 10)
        dishes = [(RNG.randint(-4, 20), RNG.randint(0, 5), RNG.randint(1, limit)) for _ in range(n)]
        best = -10**12
        for size in range(1, n + 1):
            for order in permutations(range(n), size):
                time = score = 0
                for i in order:
                    a, b, c = dishes[i]
                    time += c
                    score += a - time * b
                if time <= limit:
                    best = max(best, score)
        data = f'{n} {n} {limit}\n' + ' '.join(str(b) for a, b, c in dishes) + '\n'
        data += ''.join(f'{i + 1} {a} {c}\n' for i, (a, b, c) in enumerate(dishes))
        check(14704, data, best)
        rows, cols = RNG.randint(1, 4), RNG.randint(1, 4)
        cells = [[RNG.randint(0, 1) for _ in range(cols)] for _ in range(rows)]
        square = rectangle = 0
        for top in range(rows):
            for bottom in range(top, rows):
                for left in range(cols):
                    for right in range(left, cols):
                        valid = all(cells[r][c] != cells[r + 1][c] for r in range(top, bottom) for c in range(left, right + 1))
                        valid &= all(cells[r][c] != cells[r][c + 1] for r in range(top, bottom + 1) for c in range(left, right))
                        if valid:
                            area = (bottom - top + 1) * (right - left + 1)
                            rectangle = max(rectangle, area)
                            if bottom - top == right - left:
                                square = max(square, area)
        check(20471, f'{rows} {cols}\n' + '\n'.join(' '.join(map(str, row)) for row in cells), [square, rectangle])
        rows, cols = RNG.randint(1, 4), RNG.randint(1, 2)
        values = [RNG.randint(-5, 7) for _ in range(rows * cols)]
        rectangles = []
        for top in range(rows):
            for bottom in range(top, rows):
                for left in range(cols):
                    for right in range(left, cols):
                        mask = sum(1 << (r * cols + c) for r in range(top, bottom + 1) for c in range(left, right + 1))
                        rectangles.append((mask, sum(v for i, v in enumerate(values) if mask >> i & 1)))
        k = RNG.randint(1, min(3, rows * cols))
        best = -10**9
        for chosen in combinations(rectangles, k):
            union = 0
            score = 0
            for mask, value in chosen:
                if union & mask:
                    break
                union |= mask
                score += value
            else:
                best = max(best, score)
        check(20242, f'{rows} {cols} {k}\n' + ' '.join(map(str, values)), best)
    for _ in range(35):
        length, s, t = RNG.randint(1, 1000), RNG.randint(1, 9), RNG.randint(1, 10)
        s, t = min(s, t), max(s, t)
        stones = sorted(RNG.sample(range(1, length), RNG.randint(0, min(20, length - 1))))
        bad = set(stones)
        dp = [10**6] * (length + t)
        dp[0] = 0
        for p in range(1, len(dp)):
            dp[p] = min((dp[p - step] + (p in bad) for step in range(s, t + 1) if p >= step), default=10**6)
        check(16655, f'{length}\n{s} {t} {len(stones)}\n' + ' '.join(map(str, stones)), min(dp[length:]))
    for _ in range(25):
        n, m = RNG.randint(2, 6), RNG.randint(2, 7)
        moves = [(RNG.randint(1, m), RNG.randint(1, m)) for _ in range(n)]
        pipes = {p: tuple(sorted(RNG.sample(range(m + 1), 2))) for p in range(1, n + 1) if RNG.random() < 0.5}
        states = {h: 0 for h in range(1, m + 1)}
        passed = 0
        for x, (rise, fall) in enumerate(moves, 1):
            new = {}
            for h, cost in states.items():
                outcomes = [(h - fall, cost)] + [(min(m, h + clicks * rise), cost + clicks) for clicks in range(1, m + 1)]
                for height, value in outcomes:
                    low, high = pipes.get(x, (0, m + 1))
                    if 1 <= height <= m and low < height < high:
                        new[height] = min(new.get(height, 10**9), value)
            if not new:
                expected = [0, passed]
                break
            states = new
            passed += x in pipes
        else:
            expected = [1, min(states.values())]
        data = f'{n} {m} {len(pipes)}\n' + ''.join(f'{a} {b}\n' for a, b in moves)
        data += ''.join(f'{p} {a} {b}\n' for p, (a, b) in pipes.items())
        check(16496, data, expected)


def paint_and_partition():
    for _ in range(22):
        n = RNG.randint(1, 5)
        k = RNG.randint(1, n)
        target = tuple(RNG.randint(1, 3) for _ in range(n))
        start = (0,) * n
        distance = {start: 0}
        queue = deque([start])
        while queue:
            state = queue.popleft()
            if state == target:
                best = distance[state]
                break
            for left in range(n):
                for right in range(left + 1, min(n, left + k) + 1):
                    for color in set(target):
                        new = state[:left] + (color,) * (right - left) + state[right:]
                        if new not in distance:
                            distance[new] = distance[state] + 1
                            queue.append(new)
        check(16129, f'{n} {k}\n' + ' '.join(map(str, target)), best)
        rows, cols = RNG.randint(1, 3), RNG.randint(1, 4)
        targets = [tuple(RNG.randint(0, 1) for _ in range(cols)) for _ in range(rows)]
        budget = RNG.randint(0, rows * cols)
        options = []
        for row in targets:
            gain = {}
            for state in product((-1, 0, 1), repeat=cols):
                strokes = sum(color != -1 and (i == 0 or state[i - 1] != color) for i, color in enumerate(state))
                score = sum(a == b for a, b in zip(state, row))
                gain[strokes] = max(gain.get(strokes, 0), score)
            options.append(list(gain.items()))
        best = max(sum(score for strokes, score in chosen) for chosen in product(*options)
                   if sum(strokes for strokes, score in chosen) <= budget)
        data = f'{rows} {cols} {budget}\n' + '\n'.join(''.join(map(str, row)) for row in targets)
        check(20273, data, best)
    for a, b in [(1, 4), (2, 2), (2, 3), (3, 3), (3, 4)]:
        adjacency = graph(a * b, [(r * b + c, rr * b + cc) for r in range(a) for c in range(b)
                                   for rr, cc in [(r + 1, c), (r, c + 1)] if rr < a and cc < b])
        boundary = sum(1 << (r * b + c) for r in range(a) for c in range(b)
                       if r == 0 or r == a - 1 or c == 0 or c == b - 1)
        all_mask = (1 << (a * b)) - 1
        best = 0
        for mask in range(1, all_mask):
            other = all_mask ^ mask
            if mask < other and mask & boundary and other & boundary and connected(mask, adjacency) and connected(other, adjacency):
                best += 1
        check(19910, f'{a} {b}', best)


def trees():
    for _ in range(25):
        n = RNG.randint(1, 9)
        edges = [(RNG.randrange(v), v) for v in range(1, n)]
        adjacency = graph(n, edges)
        sets = [mask for mask in range(1, 1 << n) if connected(mask, adjacency)]
        check(19782, str(n) + '\n' + ''.join(f'{a + 1} {b + 1}\n' for a, b in edges),
              [sum(mask >> u & 1 for mask in sets) for u in range(n)])
        towers = min(mask.bit_count() for mask in range(1 << n)
                     if all(mask >> u & 1 or any(mask >> v & 1 for v in adjacency[u]) for u in range(n)))
        check(24953, str(n) + '\n' + ''.join(f'{a + 1} {b + 1}\n' for a, b in edges), towers)
        k = RNG.randint(1, n)
        cuts = 0
        for removed in range(1 << len(edges)):
            adj = graph(n, [edge for j, edge in enumerate(edges) if not removed >> j & 1])
            seen = set()
            valid = True
            for u in range(n):
                if u not in seen:
                    component = {u}
                    queue = [u]
                    for v in queue:
                        for w in adj[v]:
                            if w not in component:
                                component.add(w)
                                queue.append(w)
                    seen |= component
                    valid &= len(component) <= k
            cuts += valid
        check(20811, f'{n} {k}\n' + ''.join(f'{a + 1} {b + 1}\n' for a, b in edges), cuts)
        weights = [RNG.randint(0, 8) for _ in edges]
        distance = [[0] * n for _ in range(n)]
        weighted = [[] for _ in range(n)]
        for (a, b), w in zip(edges, weights):
            weighted[a].append((b, w)); weighted[b].append((a, w))
        for source in range(n):
            queue = [(source, -1)]
            for u, p in queue:
                for v, w in weighted[u]:
                    if v != p:
                        distance[source][v] = distance[source][u] + w
                        queue.append((v, u))
        black = RNG.randint(0, n)
        best = max(sum(distance[a][b] for a in range(n) for b in range(a + 1, n)
                       if bool(mask >> a & 1) == bool(mask >> b & 1))
                   for mask in range(1 << n) if mask.bit_count() == black)
        check(19996, f'{n} {black}\n' + ''.join(f'{a + 1} {b + 1} {w}\n' for (a, b), w in zip(edges, weights)), best)
        best_flow = 0
        terminals = {u for u in range(n) if len(adjacency[u]) == 1}
        for source in range(n):
            cheapest = 10**9
            for removed in range(1 << len(edges)):
                adj = graph(n, [edge for j, edge in enumerate(edges) if not removed >> j & 1])
                seen = {source}; queue = [source]
                for u in queue:
                    for v in adj[u]:
                        if v not in seen:
                            seen.add(v); queue.append(v)
                if not (seen & (terminals - {source})):
                    cheapest = min(cheapest, sum(w for j, w in enumerate(weights) if removed >> j & 1))
            best_flow = max(best_flow, cheapest)
        check(51180, '1\n' + str(n) + '\n' + ''.join(f'{a + 1} {b + 1} {w}\n' for (a, b), w in zip(edges, weights)), best_flow)


def subsets_and_movies():
    for _ in range(20):
        n = RNG.randint(3, 7)
        edges = [(a, b) for a in range(n) for b in range(a + 1, n) if RNG.random() < 0.45]
        edge_set = {tuple(sorted(e)) for e in edges}
        k = RNG.randint(1, n)
        counts = [0] * k
        for size in range(3, n + 1):
            for vertices in combinations(range(n), size):
                start = vertices[0]
                for rest in permutations(vertices[1:]):
                    if rest[0] > rest[-1]:
                        continue
                    path = (start,) + rest + (start,)
                    if all(tuple(sorted((a, b))) in edge_set for a, b in zip(path, path[1:])):
                        counts[size % k] += 1
        check(16544, f'{n} {len(edges)} {k}\n' + ''.join(f'{a + 1} {b + 1}\n' for a, b in edges), counts)
        m, columns = RNG.randint(1, 3), RNG.randint(1, 4)
        count = 0
        for mask in range(1 << (m * columns)):
            valid = True
            for col in range(columns - 1):
                a = (mask >> (col * m)) & ((1 << m) - 1)
                b = (mask >> ((col + 1) * m)) & ((1 << m) - 1)
                valid &= not (a & b) and bool(a | b)
            count += valid
        check(17890, f'{m} {columns}', count)
    for _ in range(25):
        n, target = RNG.randint(1, 6), RNG.randint(1, 12)
        duration = [RNG.randint(1, target) for _ in range(n)]
        starts = [sorted(RNG.sample(range(target + 1), RNG.randint(1, min(4, target + 1)))) for _ in range(n)]
        best = n + 1
        def dfs(mask, end):
            nonlocal best
            if end >= target:
                best = min(best, mask.bit_count()); return
            if mask.bit_count() >= best:
                return
            for i in range(n):
                if not mask >> i & 1:
                    for start in starts[i]:
                        if start <= end < start + duration[i]:
                            dfs(mask | (1 << i), start + duration[i])
        dfs(0, 0)
        data = f'{n} {target}\n' + ''.join(f'{d} {len(s)} ' + ' '.join(map(str, s)) + '\n' for d, s in zip(duration, starts))
        check(24158, data, -1 if best == n + 1 else best)


if __name__ == '__main__':
    heaps_and_matching()
    scheduling_and_grids()
    paint_and_partition()
    trees()
    subsets_and_movies()
    report = {'passed': True, 'randomSeed': 2026110808, 'fixtures': sum(COUNTS.values()),
              'problems': {number: {'fixtures': count,
                                    'programSha256': LEDGER['nowcoder-global::' + number]['programSha256'],
                                    'executableSha256': sha((OUT / 'compiled' / number / 'main.exe').read_bytes())}
                           for number, count in COUNTS.items()}}
    write(OUT / 'new-dp-independent-validation.json', report)
    print(json.dumps(report, ensure_ascii=False))
