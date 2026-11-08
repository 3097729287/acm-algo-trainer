"""Independent exhaustive oracles for newly authored nontrivial algorithms."""
from functools import lru_cache
import itertools
import random
import subprocess

from nowcoder_editorials import CONTENT, OUT, read, write

RNG = random.Random(2026110802)
RESULTS = {}


def run(number, data, answer, cases=1):
    process = subprocess.run([str(OUT / 'compiled' / str(number) / 'main.exe')],
                             input=data.encode(), capture_output=True, timeout=8)
    actual = process.stdout.decode()
    assert process.returncode == 0 and actual.split() == str(answer).split(), (number, data[:500], answer, actual[:500])
    RESULTS[str(number)] = RESULTS.get(str(number), 0) + cases


def simulation():
    groups, answers = [], []
    for _ in range(60):
        n, m = RNG.randint(1, 14), RNG.randint(0, 15)
        g = [RNG.randrange(2) for _ in range(n)]
        b = [RNG.randint(1, 12) for _ in range(n)]
        times = [RNG.randrange(n) for _ in range(m)]
        strength, alive = b[:], [True] * n
        for i in range(n):
            for j in range(i):
                if g[j] != g[i] and strength[j] < strength[i]:
                    alive[j] = False
            for j in range(i + 1):
                strength[j] += times.count(i)
        groups.append(f'{n} {m}\n' + '\n'.join(f'{x} {y}' for x, y in zip(g, b)) + '\n' + '\n'.join(str(t + 1) for t in times))
        answers.append(str(sum(alive)))
    run(14583, str(len(groups)) + '\n' + '\n'.join(groups), '\n'.join(answers), len(groups))


def candies():
    best = [0] * 201
    for n in range(2, 201):
        best[n] = min(best[a] + best[n - a] + abs(n - 2 * a) for a in range(1, n))
    run(50038, '201\n' + '\n'.join(map(str, range(201))), '\n'.join(map(str, best)), 201)


def closest_and_rank():
    for _ in range(45):
        n = RNG.randint(2, 30)
        a = [RNG.randint(-30, 30) for _ in range(n)]
        prefix = list(itertools.accumulate(a))
        answer = min((i - j) ** 2 + (prefix[i] - prefix[j]) ** 2
                     for i in range(n) for j in range(i))
        run(15052, str(n) + '\n' + ' '.join(map(str, a)), answer)
        ranks = []
        for k in range(3):
            values = list(range(1, n + 1))
            RNG.shuffle(values)
            ranks.append(values)
        answer = sum(any(ranks[k][i] < ranks[k][j] for k in range(3)) and
                     any(ranks[k][j] < ranks[k][i] for k in range(3))
                     for i in range(n) for j in range(i))
        run(13947, str(n) + '\n' + '\n'.join(' '.join(map(str, row)) for row in zip(*ranks)), answer)


def cuts_and_matrix():
    groups, answers = [], []
    for _ in range(35):
        n, energy = RNG.randint(1, 7), RNG.randint(0, 12)
        obstacles = [(RNG.randint(0, 12), RNG.randint(0, 12)) for _ in range(n)]
        feasible = False
        for order in itertools.permutations(range(n)):
            current = energy
            for i in order:
                loss, gain = obstacles[i]
                if current < loss:
                    break
                current += gain - loss
            else:
                feasible = True
                break
        groups.append(f'{n} {energy}\n' + '\n'.join(f'{a} {b}' for a, b in obstacles))
        answers.append('Yes' if feasible else 'No')
        n, m = RNG.randint(1, 4), RNG.randint(1, 4)
        k = RNG.randint(1, n + m)
        a = [[RNG.randint(1, 20) for _ in range(m)] for _ in range(n)]
        answer = 0
        for rows in range(1 << n):
            for columns in range(1 << m):
                if rows.bit_count() + columns.bit_count() <= k:
                    answer = max(answer, sum(a[r][c] for r in range(n) for c in range(m)
                                             if rows >> r & 1 or columns >> c & 1))
        run(285890, f'{n} {m} {k}\n' + '\n'.join(' '.join(map(str, row)) for row in a), answer)
        n = RNG.randint(1, 8)
        a = [RNG.randint(-5, 5) for _ in range(n)]
        @lru_cache(None)
        def remove(mask):
            if not mask:
                return 0
            result, index = 10 ** 9, 0
            for i in range(n):
                if mask >> i & 1:
                    index += 1
                    result = min(result, index * a[i] + remove(mask ^ (1 << i)))
            return result
        run(19838, str(n) + '\n' + ' '.join(map(str, a)), remove((1 << n) - 1))
    run(53681, str(len(groups)) + '\n' + '\n'.join(groups), '\n'.join(answers), len(groups))


def windows():
    for _ in range(45):
        n = RNG.randint(2, 12)
        a = [RNG.randint(1, 20) for _ in range(n)]
        prefix = [0] + list(itertools.accumulate(a))
        total = sum(a)
        answer = max(min(prefix[j] - prefix[i], total - prefix[j] + prefix[i])
                     for i in range(n) for j in range(i + 1, n))
        run(285845, str(n) + '\n' + '\n'.join(map(str, a)), answer)
        n, budget = RNG.randint(1, 8), RNG.randint(0, 20)
        a = [RNG.randint(1, 20) for _ in range(n)]
        answer = 0
        for size in range(1, n + 1):
            for subset in itertools.combinations(a, size):
                median = sorted(subset)[size // 2]
                if sum(abs(v - median) for v in subset) <= budget:
                    answer = size
        run(224938, f'{n} {budget}\n' + ' '.join(map(str, a)), answer)


def flip_elimination():
    for _ in range(45):
        n, m = RNG.randint(1, 4), RNG.randint(1, 5)
        a = [[RNG.randrange(2) for _ in range(m)] for _ in range(n)]
        matrix = []
        for r in range(n):
            for c in range(m):
                equation = a[r][c] << (n * m)
                for dr, dc in [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)]:
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < n and 0 <= cc < m:
                        equation |= 1 << (rr * m + cc)
                matrix.append(equation)
        pivot = 0
        for bit in range(n * m):
            row = next((i for i in range(pivot, len(matrix)) if matrix[i] >> bit & 1), None)
            if row is None:
                continue
            matrix[pivot], matrix[row] = matrix[row], matrix[pivot]
            for i in range(pivot + 1, len(matrix)):
                if matrix[i] >> bit & 1:
                    matrix[i] ^= matrix[pivot]
            pivot += 1
        possible = (1 << (n * m)) not in matrix
        run(285340, f'{n} {m}\n' + '\n'.join(''.join(map(str, row)) for row in a), 'YES' if possible else 'NO')


if __name__ == '__main__':
    simulation()
    candies()
    closest_and_rank()
    cuts_and_matrix()
    windows()
    flip_elimination()
    ledger = read(CONTENT / 'reviewed.json')
    report = {'passed': True, 'randomSeed': 2026110802, 'cases': sum(RESULTS.values()),
              'problems': {k: {'cases': v, 'programSha256': ledger['nowcoder-global::' + k]['programSha256']}
                           for k, v in RESULTS.items()}}
    write(OUT / 'divide-independent-validation.json', report)
    print(report)
