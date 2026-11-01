"""独立按输出图校验：边数/简单图/唯一MST/逐条删边后的实际MST。"""
def read_cases(inp):
    it = iter(map(int, inp.split()))
    cases = []
    for _ in range(next(it)):
        n = next(it)
        edges = [(next(it) - 1, next(it) - 1, next(it)) for _ in range(n - 1)]
        cases.append((n, edges))
    return cases

def mst(n, edges, ban=None):
    parent = list(range(n))
    def find(x):
        while x != parent[x]:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    count = 0; total = 0
    for u, v, w in sorted(edges, key=lambda e: e[2]):
        if ban is not None and (min(u, v), max(u, v)) == ban:
            continue
        a, b = find(u), find(v)
        if a != b:
            parent[a] = b; count += 1; total += w
    return total if count == n - 1 else None

def parse_verdicts(tokens, cases):
    it = iter(tokens); result = []
    for n, _ in cases:
        word = next(it).lower(); result.append(word)
        if word == 'yes':
            # 暴力只输出判定；官方样例还附带构造，二者分别处理。
            pass
    return result

def checker(inp, got, other):
    try:
        if isinstance(got, bytes): got = got.decode()
        if isinstance(other, bytes): other = other.decode()
        cases = read_cases(inp)
        expected_tokens = other.split()
        # 暴力结果只有 Yes/No；官方输出则有三元组。
        if all(t.lower() in ('yes', 'no') for t in expected_tokens):
            expected = [t.lower() for t in expected_tokens]
        else:
            expected = []; it = iter(expected_tokens)
            for n, _ in cases:
                word = next(it).lower(); expected.append(word)
                if word == 'yes':
                    for _ in range(3 * (n - 1)): next(it)
        if len(expected) != len(cases): return False, '基准判定数量错误'
        it = iter(got.split())
        for case_id, ((n, tree), want) in enumerate(zip(cases, expected), 1):
            word = next(it).lower()
            if word != want: return False, '第%d组可行性与基准不符' % case_id
            if word == 'no': continue
            if word != 'yes': return False, '缺少Yes/No'
            added = [(int(next(it)) - 1, int(next(it)) - 1, int(next(it))) for _ in range(n - 1)]
            used = {(min(u, v), max(u, v)) for u, v, _ in tree}
            g = [[] for _ in range(n)]
            for u, v, w in tree:
                g[u].append((v, w)); g[v].append((u, w))
            for u, v, w in added:
                if not (0 <= u < n and 0 <= v < n and u != v and 1 <= w <= 2 * 10**9):
                    return False, '端点或权值越界'
                pair = (min(u, v), max(u, v))
                if pair in used: return False, '出现重边或原树边'
                used.add(pair)
                # 在原树直接找路径，检查新增边严格重于路径最大边。
                stack = [(u, -1, 0)]; pathmax = None
                while stack:
                    a, p, mx = stack.pop()
                    if a == v: pathmax = mx; break
                    for b, t in g[a]:
                        if b != p: stack.append((b, a, max(mx, t)))
                if w <= pathmax: return False, '原树不是唯一MST'
            base = sum(w for _, _, w in tree)
            for u, v, _ in tree:
                if mst(n, tree + added, (min(u, v), max(u, v))) != base + 1:
                    return False, '删去树边后的MST权值不等于x+1'
        try:
            next(it)
            return False, '输出有多余内容'
        except StopIteration:
            return True, ''
    except (StopIteration, ValueError, TypeError) as e:
        return False, '输出解析失败：' + type(e).__name__
