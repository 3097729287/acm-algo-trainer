"""Reviewed range aggregates, including prime two and unsigned ring arithmetic."""
from nowcoder_editorials import CONTENT, add, read, review_rating, reviewed_clone
from nowcoder_affine_support import AFFINE_TREE
from nowcoder_divide import FAST


def run():
    existing = read(CONTENT / 'reviewed.json')

    def put(n, *args, **kwargs):
        if f'nowcoder-global::{n}' not in existing:
            add(n, *args, **kwargs)

    if 'nowcoder-global::16564' not in existing:
        reviewed_clone(16564, 287785, '当前两份借教室题面完全相同，包括n/m一百万、零需求、失败时只输出申请人编号，以及全部样例；保留该版本实际输出合同。')
    put(20545, 1900, ['树状数组', '离线查询'], '查询区间中至少出现两次的颜色种数，单独一朵的颜色不采。',
        '查询按右端点排序，扫描前缀时，每种颜色只在它倒数第二次出现的位置放一个一；更早的标记清除。一个颜色在 [L,R] 至少出现两次，当且仅当它在前缀 R 中倒数第二次的位置不小于 L。所以树状数组的 [L,R] 区间和即答案。每次新颜色到来，先删旧的倒数第二位置，再把原最后位置升级为新的倒数第二位置。',
        r'''FastInput input; int n = input.next(), colors = input.next(), m = input.next(); vector<int> a(n + 1); for (int i = 1; i <= n; i++) a[i] = input.next(); struct Query { int l, r, id; }; vector<Query> queries(m); for (int i = 0; i < m; i++) queries[i] = {input.next(), input.next(), i}; sort(queries.begin(), queries.end(), [](auto x, auto y) { return x.r < y.r; });
        vector<int> tree(n + 1), last(colors + 1), second(colors + 1), answers(m); auto change = [&](int p, int v) { for (int i = p; i <= n; i += i & -i) tree[i] += v; }; auto sum = [&](int p) { int answer = 0; for (int i = p; i > 0; i -= i & -i) answer += tree[i]; return answer; };
        int right = 0; for (auto q : queries) { while (right < q.r) { int color = a[++right]; if (second[color]) change(second[color], -1); second[color] = last[color]; if (second[color]) change(second[color], 1); last[color] = right; } answers[q.id] = sum(q.r) - sum(q.l - 1); } for (int x : answers) cout << x << '\n';''',
        '问的是颜色数，不是花朵总数。不能使用“每种颜色最后一次出现”的标记，那会把只出现一次的颜色也算进来。',
        declarations=FAST, complexity=r'时间 $O(m\log m+(n+m)\log n)$，空间 $O(n+m+c)$，支持备注中的二百万规模。')
    put(19246, 2200, ['线段树', '懒标记', '模运算'], '支持区间乘、区间加，以及区间和、平方和查询。',
        '统一把修改写成 x→ax+b。一个长 len 的节点维护 S=Σx、Q=Σx²，应用修改后 S′=aS+b len，Q′=a²Q+2abS+b²len。懒标记也按先后顺序复合：原标记 (m,c) 后再执行 (a,b)，变成 (am,ac+b)。求平方和时必须使用修改前的 S。\n\n题目只保证查询结果落在有符号64位，未保证长时间未查询的中间量与懒乘积不溢出。代码把全部维护量放在模 2^64 的环中：unsigned long long 的加乘溢出有明确定义，所有上述多项式等式仍成立。查询结果既然保证在有符号64位范围，其模 2^64 余数就唯一决定真实答案；最高位为一时按负数的绝对值输出。这也处理先多次放大、再乘零、最后查询等情况。',
        r'''using U = unsigned long long; int n, m; cin >> n >> m; vector<U> a(n + 1); for (int i = 1; i <= n; i++) { long long x; cin >> x; a[i] = (U)x; } AffineTree tree(a, 0);
        while (m--) { int op, l, r; cin >> op >> l >> r; if (op <= 2) { auto result = tree.query(1, 1, n, l, r); U value = op == 1 ? result.first : result.second; if (value <= (U)LLONG_MAX) cout << value << '\n'; else cout << '-' << (~value + 1ULL) << '\n'; }
            else { long long x; cin >> x; if (op == 3) tree.change(1, 1, n, l, r, (U)x, 0); else tree.change(1, 1, n, l, r, 1, (U)x); } }''',
        '有符号整数溢出在 C++ 中不可依赖；这里刻意使用无符号环，最终再根据题目保证还原有符号值。此技巧只因查询输出范围已知且运算全是整数多项式才成立。',
        declarations=AFFINE_TREE, complexity=r'每个操作 $O(\log n)$，空间 $O(n)$。',
        cases=[{'input': '1 4\n0\n3 1 1 1000000000000000000\n3 1 1 1000000000000000000\n4 1 1 -3\n1 1 1', 'output': '-3'}, {'input': '2 3\n1 -1\n3 1 2 1000000000000000000\n1 1 2\n3 1 2 0', 'output': '0'}])
    put(212880, 2200, ['线段树', '懒标记', '模运算'], '支持区间加乘，并查询区间中全部无序两两乘积之和，答案模素数 p。',
        '记区间和为 S、平方和为 Q，则两两乘积和为 (S²-Q)/2。区间仿射修改的维护公式为 S′=aS+b len、Q′=a²Q+2abS+b²len，可用懒线段树维护。\n\np 允许等于二，此时二没有模逆元。为统一处理所有 p，在线段树内部对 2p 取模：因为真实 S²-Q 总是偶数，知道它模 2p 的偶数余数，再用普通整数除二，就恰好得到真实答案模 p。2p 小于 2^32，两个余数相乘仍可放入 unsigned long long。输入可能为负，先规范成非负余数。',
        r'''int tests; cin >> tests; while (tests--) { int n, m; long long p; cin >> n >> m >> p; unsigned long long modulus = 2ULL * p; auto normalize = [&](long long x) { long long value = x % (long long)modulus; if (value < 0) value += modulus; return (unsigned long long)value; };
            vector<unsigned long long> a(n + 1); for (int i = 1; i <= n; i++) { long long x; cin >> x; a[i] = normalize(x); } AffineTree tree(a, modulus);
            while (m--) { int op, l, r; cin >> op >> l >> r; if (op == 3) { auto [sum, squares] = tree.query(1, 1, n, l, r); auto difference = (tree.times(sum, sum) + modulus - squares) % modulus; cout << difference / 2 << '\n'; }
                else { long long x; cin >> x; if (op == 1) tree.change(1, 1, n, l, r, 1, normalize(x)); else tree.change(1, 1, n, l, r, normalize(x), 0); } } }''',
        '不能无条件用 (p+1)/2 当逆元，p=2 会错。内部取模数是 2p，最终的普通除二只做在规范后的偶数余数上。',
        declarations=AFFINE_TREE, complexity=r'每组时间 $O((n+m)\log n)$，空间 $O(n)$。',
        cases=[{'input': '1\n3 3 2\n1 1 1\n3 1 3\n1 1 2 1\n3 1 3', 'output': '1\n0'}])
    review_rating(21758, 2500, '长度与查询各三十万，离散化后不变的值恰为小于该区间mex的原值；需先求区间mex再求低于该mex的元素出现总数。可用持久化值域树同时维护最晚出现位置的最小值和频数，复杂度O((n+m)log n)，空间O(nlog n)，组合难度高于ToBe的2400档静态持久化查询。', knowledge=['可持久化线段树', 'mex', '区间计数'])


if __name__ == '__main__':
    run()
    print('Registered four reviewed range articles and one above-cutoff review.')
