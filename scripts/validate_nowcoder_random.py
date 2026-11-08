"""Independent small exhaustive oracles and a maximum-size tree regression."""
from functools import lru_cache
import itertools
import json
import math
import random
import subprocess
import time

from nowcoder_editorials import CONTENT, OUT, read, sha, write

RNG = random.Random(20261108)
RESULTS = {}


def run(number, input_text, expected, *, timeout=8, cases=1):
    executable = OUT / 'compiled' / str(number) / 'main.exe'
    start = time.perf_counter()
    process = subprocess.run([str(executable)], input=input_text.encode(), capture_output=True, timeout=timeout)
    actual = process.stdout.decode('utf-8')
    assert process.returncode == 0 and actual.split() == str(expected).split(), (number, input_text[:1000], expected, actual[:1000])
    group = RESULTS.setdefault(str(number), {'cases': 0, 'seconds': 0})
    group['cases'] += cases
    group['seconds'] += time.perf_counter() - start


def stack_maximum():
    for n in range(1, 8):
        for repeat in range(8):
            a = list(range(1, n + 1))
            RNG.shuffle(a)
            @lru_cache(None)
            def enumerate_states(pos, stack):
                if pos == n and not stack:
                    return ()
                candidates = []
                if pos < n:
                    candidates.append(enumerate_states(pos + 1, stack + (a[pos],)))
                if stack:
                    candidates.append((stack[-1],) + enumerate_states(pos, stack[:-1]))
                return max(candidates)
            expected = enumerate_states(0, ())
            run(14893, str(n) + '\n' + ' '.join(map(str, a)), ' '.join(map(str, expected)))


def chocolates():
    for repeat in range(35):
        n = RNG.randint(1, 8)
        k = RNG.randint(0, n)
        a, b = [[RNG.randint(0, 30) for _ in range(n)] for _ in range(2)]
        expected = max(sum(a[i] if i in selected else b[i] for i in range(n))
                       for selected in map(set, itertools.combinations(range(n), k)))
        run(14721, f'{n} {k}\n' + ' '.join(map(str, a)) + '\n' + ' '.join(map(str, b)), expected)


def curling():
    groups, answers = [], []
    for repeat in range(100):
        n, m = RNG.randint(1, 6), RNG.randint(1, 6)
        a, b = [RNG.randint(1, 15) for _ in range(n)], [RNG.randint(1, 15) for _ in range(m)]
        boundaries = sorted({x + y for x in a for y in b})
        centers = {2 * v for v in boundaries}
        centers.update(x + y for x, y in zip(boundaries, boundaries[1:]))
        centers.update([2 * boundaries[0] - 4, 2 * boundaries[-1] + 4])
        expected = max(sum(abs(c - 4 * x) < min(abs(c - 4 * y) for y in b) for x in a) for c in centers)
        groups.append(f'{n} {m}\n' + ' '.join(map(str, a)) + '\n' + ' '.join(map(str, b)))
        answers.append(str(expected) if expected else 'Impossible')
    run(216012, str(len(groups)) + '\n' + '\n'.join(groups), '\n'.join(answers), cases=len(groups))


def queue_honesty():
    groups, answers = [], []
    for repeat in range(50):
        count = RNG.randint(1, 25)
        queue, lines, next_id, honest = [], [], 0, 0
        while queue or next_id < count:
            if next_id < count and (not queue or RNG.random() < .6):
                name = 'P' + str(next_id)
                next_id += 1
                position = RNG.randrange(len(queue) + 1)
                honest += position == len(queue)
                queue.insert(position, name)
                lines.append('in ' + name)
            else:
                lines.append('out ' + queue.pop(0))
        groups.append(str(len(lines)) + '\n' + '\n'.join(lines))
        answers.append(str(honest))
    run(13822, str(len(groups)) + '\n' + '\n'.join(groups), '\n'.join(answers), cases=len(groups))


def fingerprints():
    for k in [1, 3, 10, 100]:
        values, lines, answers = set(), [], []
        for i in range(200):
            op, x = RNG.choice(['add', 'del', 'query']), RNG.randint(1, 100)
            close = {v for v in values if abs(v - x) <= k}
            if op == 'add' and not close:
                values.add(x)
            elif op == 'del':
                values -= close
            elif op == 'query':
                answers.append('Yes' if close else 'No')
            lines.append(f'{op} {x}' + (' // sample-style annotation' if i % 17 == 0 else ''))
        run(17508, f'{len(lines)} {k}\n' + '\n'.join(lines), '\n'.join(answers), cases=len(lines))


def random_tree(n):
    left, right = [0] * (n + 1), [0] * (n + 1)
    slots = [(1, 0), (1, 1)]
    for child in range(2, n + 1):
        parent, side = slots.pop(RNG.randrange(len(slots)))
        (left if side == 0 else right)[parent] = child
        slots.extend([(child, 0), (child, 1)])
    return left, right


def symmetric_trees():
    for repeat in range(50):
        n = RNG.randint(1, 30)
        left, right = random_tree(n)
        value = [0] + [RNG.randint(1, 3) for _ in range(n)]
        def same(a, b):
            if not a or not b:
                return a == b
            return value[a] == value[b] and same(left[a], right[b]) and same(right[a], left[b])
        def size(u):
            return 0 if not u else 1 + size(left[u]) + size(right[u])
        expected = max(size(u) for u in range(1, n + 1) if same(u, u))
        raw = str(n) + '\n' + ' '.join(map(str, value[1:])) + '\n'
        raw += '\n'.join(f'{left[i] or -1} {right[i] or -1}' for i in range(1, n + 1))
        run(21241, raw, expected)
    n = 1_000_000
    raw = str(n) + '\n' + '1 ' * n + '\n' + ''.join(f'{i + 1} -1\n' for i in range(1, n)) + '-1 -1\n'
    run(21241, raw, 1, timeout=12)
    RESULTS['21241']['maximumChainNodes'] = n


def native_tree_interface():
    for repeat in range(35):
        n = RNG.randint(1, 30)
        left, right = random_tree(n)
        for u in range(1, n + 1):
            if not left[u] and right[u]:
                left[u], right[u] = right[u], 0
        pre, post, mid = [], [], []
        def visit(u):
            if not u:
                return
            pre.append(u)
            visit(left[u])
            mid.append(u)
            visit(right[u])
            post.append(u)
        visit(1)
        raw = f'{n},' + json.dumps(pre) + ',' + json.dumps(post)
        run(204382, raw, json.dumps(mid).replace(' ', ''))


def expression_modulo():
    expressions, answers = [], []
    mod = 65536
    for repeat in range(150):
        length = RNG.randint(1, 7)
        literals = [(RNG.randrange(10), RNG.random() < .25) for _ in range(length)]
        operators = [RNG.choice('+-*/^') for _ in range(length - 1)]
        source = ''.join(str(value) + ('!' if factorial else '') + (operators[i] if i < length - 1 else '')
                         for i, (value, factorial) in enumerate(literals))
        values = [(math.factorial(v) if f else v) % mod for v, f in literals]
        ops = operators[:]
        error = False
        for group in ['^', '*/', '+-']:
            i = 0
            while i < len(ops):
                if ops[i] not in group:
                    i += 1
                    continue
                a, b, op = values[i], values[i + 1], ops[i]
                if op == '/' and b == 0:
                    error = True
                    break
                if op == '^': result = pow(a, b, mod)
                elif op == '*': result = a * b
                elif op == '/': result = (abs(a) // abs(b)) * (-1 if (a < 0) != (b < 0) else 1)
                elif op == '+': result = a + b
                else: result = a - b
                result = result % mod if result >= 0 else -((-result) % mod)
                values[i:i + 2] = [result]
                ops.pop(i)
            if error:
                break
        expressions.append(source)
        answers.append('ArithmeticException' if error else str(values[0]))
    run(21181, str(len(expressions)) + '\n' + '\n'.join(expressions), '\n'.join(answers), cases=len(expressions))


if __name__ == '__main__':
    stack_maximum()
    chocolates()
    curling()
    queue_honesty()
    fingerprints()
    symmetric_trees()
    native_tree_interface()
    expression_modulo()
    ledger = read(CONTENT / 'reviewed.json')
    for number, value in RESULTS.items():
        value['programSha256'] = ledger['nowcoder-global::' + number]['programSha256']
    report = {'seed': 20261108, 'allPassed': True, 'results': RESULTS,
               'totalCasesOrOperations': sum(x['cases'] for x in RESULTS.values()),
               'officialSubmissionsSent': 0}
    write(OUT / 'independent-validation.json', report)
    print(json.dumps(report))
