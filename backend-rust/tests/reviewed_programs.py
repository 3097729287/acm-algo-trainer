"""Independent user programs for native execution tests, never backend code.

These solve the fixed problem semantics with efficient algorithms rather than
reading frozen answers or importing the old test generators/checkers.
"""
import bisect
from collections import Counter, defaultdict, deque
from array import array
import math
import re
import sys


def interval_sets(data):
    it = iter(map(int, data.split())); n = next(it); q = next(it)
    groups = defaultdict(list)
    for _ in range(q):
        l, r, x = next(it), next(it), next(it); groups[x].append((l, r))
    delta = [0] * (n + 2)
    for intervals in groups.values():
        intervals.sort(); left, right = intervals[0]
        for l, r in intervals[1:]:
            if l <= right + 1: right = max(right, r)
            else: delta[left] += 1; delta[right + 1] -= 1; left, right = l, r
        delta[left] += 1; delta[right + 1] -= 1
    answer = []; value = 0
    for i in range(1, n + 1): value += delta[i]; answer.append(str(value))
    return ' '.join(answer)


def inequalities(data):
    it = iter(map(int, data.split())); n, q = next(it), next(it)
    graph = [[] for _ in range(n)]; reverse = [[] for _ in range(n)]; edges = []
    for _ in range(q):
        w, u, v = next(it), next(it) - 1, next(it) - 1
        graph[u].append(v); reverse[v].append(u); edges.append((u, v, w))
    seen = bytearray(n); order = []
    for root in range(n):
        if seen[root]: continue
        stack = [root]
        while stack:
            u = stack.pop()
            if u < 0: order.append(~u); continue
            if seen[u]: continue
            seen[u] = 1; stack.append(~u)
            stack.extend(v for v in graph[u] if not seen[v])
    component = [-1] * n; count = 0
    for root in reversed(order):
        if component[root] >= 0: continue
        component[root] = count; stack = [root]
        while stack:
            for v in reverse[stack.pop()]:
                if component[v] < 0: component[v] = count; stack.append(v)
        count += 1
    dag = [[] for _ in range(count)]; degree = [0] * count
    for u, v, w in edges:
        a, b = component[u], component[v]
        if a == b:
            if w: return 'No'
        else: dag[a].append((b, w)); degree[b] += 1
    distance = [1] * count; queue = deque(i for i in range(count) if not degree[i])
    while queue:
        u = queue.popleft()
        for v, w in dag[u]:
            distance[v] = max(distance[v], distance[u] + w); degree[v] -= 1
            if not degree[v]: queue.append(v)
    return 'Yes\n' + ' '.join(str(distance[component[u]]) for u in range(n))


def transformed_array(data):
    it = iter(map(int, data.split())); answers = []
    for _ in range(next(it)):
        n, m = next(it), next(it); a = [next(it) for _ in range(n)]; b = sorted(next(it) for _ in range(m))
        previous = -10**30; possible = True
        for value in a:
            p = bisect.bisect_left(b, previous + value)
            selected = min(value if value >= previous else 10**30, b[p] - value if p < m else 10**30)
            if selected == 10**30: possible = False; break
            previous = selected
        answers.append('YES' if possible else 'NO')
    return '\n'.join(answers)


def array_scores(data):
    it = iter(map(int, data.split())); answers = []
    for _ in range(next(it)):
        n, m = next(it), next(it); rows = []
        for _ in range(n):
            total = score = 0
            for _ in range(m): total += next(it); score += total
            rows.append((total, score))
        carry = answer = 0
        for total, score in sorted(rows, reverse=True): answer += carry * m + score; carry += total
        answers.append(str(answer))
    return '\n'.join(answers)


def power_pairs(data):
    it = iter(map(int, data.split())); answers = []
    for _ in range(next(it)):
        k, l1, r1, l2, r2 = [next(it) for _ in range(5)]; power = 1; answer = 0
        while power <= r2 // l1:
            left, right = max(l1, (l2 + power - 1) // power), min(r1, r2 // power)
            answer += max(0, right - left + 1); power *= k
        answers.append(str(answer))
    return '\n'.join(answers)


def semiprime_lcms(data):
    it = iter(map(int, data.split())); answers = []
    for _ in range(next(it)):
        n = next(it); freq = Counter(next(it) for _ in range(n)); spf = list(range(n + 1))
        for p in range(2, math.isqrt(n) + 1):
            if spf[p] == p:
                for value in range(p * p, n + 1, p):
                    if spf[value] == value: spf[value] = p
        primes = [count for value, count in freq.items() if spf[value] == value]
        answer = (sum(primes) ** 2 - sum(count * count for count in primes)) // 2
        for value, count in freq.items():
            p = spf[value]; q = value // p
            if q >= 2 and spf[q] == q:
                answer += count * (count + 1) // 2 + count * freq[p]
                if p != q: answer += count * freq[q]
        answers.append(str(answer))
    return '\n'.join(answers)


def scan_numbers(data):
    value = 0; sign = 1; present = False
    for byte in data:
        if 48 <= byte <= 57: value = value * 10 + byte - 48; present = True
        elif byte == 45: sign = -1
        elif present: yield value * sign; value = 0; sign = 1; present = False
    if present: yield value * sign


def weighted_rectangles(data):
    it = iter(scan_numbers(data)); answers = []
    for _ in range(next(it)):
        n, q = next(it), next(it); stride = n + 1; size = stride * stride
        sums = array('q', [0]) * size; rows = array('q', [0]) * size; cols = array('q', [0]) * size
        for r in range(1, n + 1):
            s = sr = sc = 0; start = r * stride; above = start - stride
            for c in range(1, n + 1):
                value = next(it); s += value; sr += r * value; sc += c * value
                k = start + c; p = above + c; sums[k] = sums[p] + s; rows[k] = rows[p] + sr; cols[k] = cols[p] + sc
        for _ in range(q):
            x1, y1, x2, y2 = next(it), next(it), next(it), next(it)
            a, b, c, d = x2 * stride + y2, (x1 - 1) * stride + y2, x2 * stride + y1 - 1, (x1 - 1) * stride + y1 - 1
            total = sums[a] - sums[b] - sums[c] + sums[d]
            row = rows[a] - rows[b] - rows[c] + rows[d]; col = cols[a] - cols[b] - cols[c] + cols[d]
            width = y2 - y1 + 1
            answers.append(str(width * row + col - (width * x1 + y1 - 1) * total))
    return '\n'.join(answers)


def implication_names(data):
    lines = data.decode().splitlines(); chain = re.split('(<=>|=>|<=)', lines[0]); graph = defaultdict(set)
    for i in range(1, len(chain), 2):
        a, op, b = chain[i - 1:i + 2]
        if op in ('=>', '<=>'): graph[a].add(b)
        if op in ('<=', '<=>'): graph[b].add(a)
    cache = {}; answers = []
    for line in lines[2:2 + int(lines[1])]:
        a, b = line.split()
        if a not in cache:
            seen = {a}; stack = [a]
            while stack:
                for v in graph[stack.pop()]:
                    if v not in seen: seen.add(v); stack.append(v)
            cache[a] = seen
        answers.append('Yes' if b in cache[a] else 'No')
    return '\n'.join(answers)


def separated_double_steps(data):
    n = int(data); dp = [1, 1, 2]
    for value in range(3, n + 1): dp.append(dp[-1] + dp[-3])
    return str(dp[n])


def one_infinite_kind(data):
    it = iter(map(int, data.split())); answers = []
    for _ in range(next(it)):
        n, capacity = next(it), next(it); finite = Counter(); infinite = set()
        for _ in range(n):
            w, v, count = next(it), next(it), next(it)
            if count == 1: finite[w, v] += 1
            else: infinite.add((w, v))
        dp = [0] * (capacity + 1)
        for (w, v), count in finite.items():
            power = 1
            while count:
                take = min(power, count); count -= take; power *= 2; weight, value = w * take, v * take
                for budget in range(capacity, weight - 1, -1): dp[budget] = max(dp[budget], dp[budget - weight] + value)
        answer = dp[capacity]
        for w, v in infinite:
            answer = max(answer, max(value + (capacity - used) // w * v for used, value in enumerate(dp)))
        answers.append(str(answer))
    return '\n'.join(answers)


def fixed_positions(data):
    it = iter(map(int, data.split())); n = next(it); position = [0]
    for _ in range(n - 1): position.append(position[-1] + next(it))
    flags = [next(it) for _ in range(n)]; fixed = [i for i in range(n) if not flags[i]]; answer = 0
    for l, r in zip(fixed, fixed[1:]):
        answer += sum((position[i] - position[l]) * (r - l) != (position[r] - position[l]) * (i - l) for i in range(l + 1, r))
    return str(answer)


def square_divisor_root(value):
    if math.isqrt(value) ** 2 == value: return math.isqrt(value)
    answer = 1; p = 2
    while p * p <= value:
        count = 0
        while value % p == 0: value //= p; count += 1
        answer *= p ** (count // 2); p += 1 if p == 2 else 2
    return answer


def gcd_construction(data):
    it = iter(map(int, data.split())); answers = []
    for _ in range(next(it)):
        x, y = next(it), next(it); common = math.gcd(x, y)
        g = common * square_divisor_root(x // common) * square_divisor_root(y // common)
        answers.append(str(x * y // g) + ' ' + str(g))  # Reverse the frozen constructor.
    return '\n'.join(answers)


def customer_revenue(data):
    it = iter(map(int, data.split())); x, y, money, stock, k = [next(it) for _ in range(5)]
    n = next(it); revenue = [next(it) for _ in range(n)]; basket = [next(it) for _ in range(n)]
    groups = [[], []]
    for a, b in zip(revenue, basket): groups[b].append(a)
    pref = []
    for group in groups:
        sums = [0]
        for value in sorted(group, reverse=True): sums.append(sums[-1] + value)
        pref.append(sums)
    limit = stock // k; answer = 0
    for j in range(min(len(groups[1]), limit, money // (k * x + y)) + 1):
        i = min(len(groups[0]), limit - j, (money - j * (k * x + y)) // (k * x))
        answer = max(answer, pref[1][j] + pref[0][i])
    return str(answer)


def last_tree_edge(data):
    it = iter(map(int, data.split())); n, q = next(it), next(it); edges = []; graph = [[] for _ in range(n)]
    for _ in range(n - 1):
        a, b = next(it) - 1, next(it) - 1; graph[a].append(b); graph[b].append(a); edges.append((a, b))
    parent = [-1] * n; order = [0]
    for u in order:
        for v in graph[u]:
            if v != parent[u]: parent[v] = u; order.append(v)
    size = [1] * n
    for v in reversed(order[1:]): size[parent[v]] += size[v]
    mod = 998244353; product = factorial = 1
    for v in range(1, n): product = product * size[v] % mod; factorial = factorial * v % mod
    inv = [0, 1] + [0] * (n - 1)
    for i in range(2, n + 1): inv[i] = mod - (mod // i) * inv[mod % i] % mod
    ways = [0] * n; ways[0] = factorial * pow(product, mod - 2, mod) % mod
    for v in order[1:]: ways[v] = ways[parent[v]] * size[v] % mod * inv[n - size[v]] % mod
    answers = []
    for _ in range(q):
        a, b = edges[next(it) - 1]
        if parent[a] == b: a, b = b, a
        answers.append(str(2 * ways[a] * size[b] * inv[n - 1] % mod))
    return '\n'.join(answers)


PROGRAMS = {'ABC 478::D': interval_sets, 'ABC 478::E': inequalities,
            'Div.4 1003::C1': transformed_array, 'Div.4 1003::C2': transformed_array,
            'Div.4 1003::D': array_scores, 'Div.4 1003::G': semiprime_lcms,
            'Div.4 993::E': power_pairs, 'Div.4 993::H': weighted_rectangles,
            '入门赛 46::H': implication_names, '入门赛 49::D': separated_double_steps,
            '入门赛 50::F': one_infinite_kind, '周赛 164::C': gcd_construction,
            '周赛 164::D': customer_revenue, '周赛 164::F': last_tree_edge,
            '基础赛 37::B': fixed_positions}

if __name__ == '__main__':
    print(PROGRAMS[sys.argv[1]](sys.stdin.buffer.read()))
