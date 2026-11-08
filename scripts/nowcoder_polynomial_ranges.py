"""Reviewed polynomial, capacity and ordered-transition range structures."""
from nowcoder_editorials import CONTENT, add, read
from nowcoder_matrix_support import matrix_tree


def run():
    existing = read(CONTENT / 'reviewed.json')

    def put(n, *args, **kwargs):
        if f'nowcoder-global::{n}' not in existing:
            add(n, *args, **kwargs)

    put(226172, 2100, ['树状数组', '多项式', '区间修改'], '区间依次加一、四、九等平方数，并查询区间和模 10^9+7。',
        '一次 [l,r] 修改给位置 i 加 (i-l+1)²，展开为 Ai²+Bi+C，其中 A=1、B=2(1-l)、C=(1-l)²。令 F(t)=A*t(t+1)(2t+1)/6+B*t(t+1)/2+C*t，则更新对前缀和的贡献在 l<=x<=r 时为 F(x)-F(l-1)，x>r 时为常数 F(r)-F(l-1)。\n\n用四棵树状数组维护前缀函数的四个系数：在 l 加 (A,B,C,-F(l-1))，在 r+1 加 (-A,-B,-C,F(r))。查询 x 时取四个系数前缀和，代入平方和、自然数和、x、常数一，即得整个数组的前缀和；相减得到区间和。模数为固定奇素数，可使用二和六的逆元。',
        r'''const long long mod = 1000000007; int n, m; cin >> n >> m; vector<array<long long,4>> tree(n + 1);
        auto first = [&](long long x) { return x * (x + 1) % mod * 500000004 % mod; };
        auto second = [&](long long x) { return x * (x + 1) % mod * (2 * x + 1) % mod * 166666668 % mod; };
        auto mark = [&](int p, array<long long,4> values) { for (int i = p; i <= n; i += i & -i) for (int k = 0; k < 4; k++) { tree[i][k] += values[k]; if (tree[i][k] >= mod) tree[i][k] -= mod; } };
        auto prefix = [&](int p) { array<long long,4> coefficient{}; for (int i = p; i > 0; i -= i & -i) for (int k = 0; k < 4; k++) { coefficient[k] += tree[i][k]; if (coefficient[k] >= mod) coefficient[k] -= mod; }
            return (coefficient[0] * second(p) + coefficient[1] * first(p) + coefficient[2] * p + coefficient[3]) % mod; };
        while (m--) { int op, l, r; cin >> op >> l >> r; if (op == 2) cout << (prefix(r) - prefix(l - 1) + mod) % mod << '\n';
            else { long long b = (2LL * (1 - l) % mod + mod) % mod, c = (1LL - l) * (1LL - l) % mod;
                auto f = [&](int x) { return (second(x) + b * first(x) + c * x) % mod; };
                mark(l, {1, b, c, (mod - f(l - 1)) % mod}); mark(r + 1, {mod - 1, (mod - b) % mod, (mod - c) % mod, f(r)}); } }''',
        '平方从修改左端重新计为一，不是直接给位置 i 加 i²。右端取消标记在 r+1。所有负系数先规范到模数范围。',
        complexity=r'每个操作 $O(\log n)$，空间 $O(n)$。')
    put(226170, 1700, ['线段树', '二分定位'], '每堆鸡蛋放入编号最小、剩余容量足够且未达 k 堆限制的篮子。',
        '线段树每个叶子保存篮子的可用容量，若已经放了 k 堆就记为 -1；内部维护最大可用容量。根最大值小于当前鸡蛋数，说明没有篮子能装。否则从根向下，左子树最大值够用就走左边，不够才走右边，得到最小可行编号。更新该篮子容量和堆数，沿途重算最大值。',
        r'''int tests; cin >> tests; while (tests--) { int n, capacity, limit; cin >> n >> capacity >> limit; vector<int> maximum(4 * n + 4, capacity), used(n + 1);
            function<int(int,int,int,int)> place = [&](int p, int l, int r, int amount) { if (l == r) { maximum[p] -= amount; if (++used[l] == limit) maximum[p] = -1; return l; } int mid = (l + r) / 2, answer;
                if (maximum[p * 2] >= amount) answer = place(p * 2, l, mid, amount); else answer = place(p * 2 + 1, mid + 1, r, amount); maximum[p] = max(maximum[p * 2], maximum[p * 2 + 1]); return answer; };
            for (int i = 0; i < n; i++) { int amount; cin >> amount; cout << (maximum[1] < amount ? -1 : place(1, 1, n, amount)) << '\n'; } }''',
        '篮子有容量和堆数两项限制。某堆超过所有篮子的容量时输出 -1，不能把它拆成多堆，也不能改变后面鸡蛋的顺序。',
        complexity=r'每组时间 $O(n\log n)$，空间 $O(n)$。')
    cubes = r'''struct CubeTree {
        static const long long mod = 1000000007;
        struct Node { array<long long,8> sum{}; array<long long,3> lazy{}; };
        int n; vector<Node> tree;
        explicit CubeTree(int count) : n(count), tree(4 * count + 4) { build(1, 1, n); }
        void build(int p, int l, int r) { tree[p].sum.fill(r - l + 1); if (l == r) return; int mid = (l + r) / 2; build(p * 2, l, mid); build(p * 2 + 1, mid + 1, r); }
        void apply(int p, int axis, long long value) { for (int mask = 1; mask < 8; mask++) if (mask >> axis & 1) tree[p].sum[mask] = (tree[p].sum[mask] + value * tree[p].sum[mask ^ (1 << axis)]) % mod; tree[p].lazy[axis] = (tree[p].lazy[axis] + value) % mod; }
        void push(int p) { for (int axis = 0; axis < 3; axis++) if (tree[p].lazy[axis]) { apply(p * 2, axis, tree[p].lazy[axis]); apply(p * 2 + 1, axis, tree[p].lazy[axis]); tree[p].lazy[axis] = 0; } }
        void change(int p, int l, int r, int ql, int qr, int axis, long long value) {
            if (ql <= l && r <= qr) { apply(p, axis, value); return; } push(p); int mid = (l + r) / 2; if (ql <= mid) change(p * 2, l, mid, ql, qr, axis, value); if (qr > mid) change(p * 2 + 1, mid + 1, r, ql, qr, axis, value);
            for (int mask = 0; mask < 8; mask++) tree[p].sum[mask] = (tree[p * 2].sum[mask] + tree[p * 2 + 1].sum[mask]) % mod;
        }
        long long query(int p, int l, int r, int ql, int qr) { if (ql <= l && r <= qr) return tree[p].sum[7]; push(p); int mid = (l + r) / 2; long long answer = 0; if (ql <= mid) answer += query(p * 2, l, mid, ql, qr); if (qr > mid) answer += query(p * 2 + 1, mid + 1, r, ql, qr); return answer % mod; }
    };'''
    put(226167, 2300, ['线段树', '懒标记', '状态设计'], '立方体各边初始一，支持某维度区间增加，并查询体积总和。',
        '只维护 xyz 不够，因为给 x 加 a 时，体积增加 a*yz。于是对每个节点保存八种乘积的和：1、x、y、xy、z、xz、yz、xyz，其中一的和就是区间长度。用三位掩码表示是否含 x、y、z。给某维 d 增加 a 时，每个包含 d 的乘积 sum[mask] 增加 a*sum[mask 去掉 d]，不含 d 的量保持不变。右边的量本次没有被修改，所以可直接逐项更新。\n\n三个懒标记分别累计三个维度的增加量，推给儿子时依次应用即可；不同时段修改的交叉项会随着 xy、xz、yz 的维护自然产生。初始化所有边为一，所以八项和最初都等于节点长度。',
        r'''int n, m; cin >> n >> m; CubeTree tree(n); while (m--) { char op; int l, r; cin >> op >> l >> r; if (op == 'q') cout << tree.query(1, 1, n, l, r) << '\n'; else { long long value; cin >> value; int axis = op == 'x' ? 0 : op == 'y' ? 1 : 2; tree.change(1, 1, n, l, r, axis, value % CubeTree::mod); } }''',
        '区间长度是 sum[0]，不是零。连续修改不同维度时必须维护低阶乘积，否则会漏掉交叉项。',
        declarations=cubes, complexity=r'每个操作 $O(8\log n)$，空间 $O(8n)$。')
    put(226052, 2200, ['线段树', '矩阵乘法', '动态规划'], '两塔的楼梯方向与长度可改，查询从一层一侧到更高层指定侧的最短路。',
        '每层到上一层只涉及左右两个状态，建二乘二转移矩阵：同塔上楼分别填左、右楼梯长度；斜楼梯按方向填入 (左,右) 或 (右,左)，不存在的转移记无穷。连续两段组合使用最小加法乘积 C[i][j]=min_k(A[i][k]+B[k][j])，对应枚举中间层所在侧，具有结合律。线段树维护从下向上的有序矩阵积，改单层只更新一个叶子，查询 hs 到 ht 就取 [hs,ht-1] 的积。',
        r'''int n, m; string direction; cin >> n >> m >> direction; vector<array<long long,3>> cost(n); for (int h = 1; h < n; h++) cin >> cost[h][0] >> cost[h][1] >> cost[h][2];
        auto leaf = [&](int h) { Matrix a; a.value[0][0] = cost[h][0]; a.value[1][1] = cost[h][1]; if (direction[h - 1] == '/') a.value[0][1] = cost[h][2]; else a.value[1][0] = cost[h][2]; return a; };
        vector<Matrix> initial; initial.reserve(n - 1); for (int h = 1; h < n; h++) initial.push_back(leaf(h)); MatrixTree tree(initial);
        while (m--) { int op; cin >> op; if (op == 0) { int h; char c; cin >> h >> c; direction[h - 1] = c; tree.change(h - 1, leaf(h)); }
            else if (op == 1) { int h; array<long long,3> values; cin >> h >> values[0] >> values[1] >> values[2]; if (h < n) { cost[h] = values; tree.change(h - 1, leaf(h)); } }
            else { int hs, ht, ps, pt; cin >> hs >> ht >> ps >> pt; long long answer = tree.query(hs - 1, ht - 1).value[ps][pt]; cout << (answer == Empty ? -1 : answer) << '\n'; } }''',
        '矩阵积顺序不能颠倒；迭代查询用左右两个累积矩阵分别拼接。顶层没有向上楼梯，若输入修改顶层长度则读完参数后忽略。无穷项不参与加法，防止伪造可达路径。',
        declarations=matrix_tree(True), complexity=r'每次操作 $O(2^3\log n)$，空间 $O(n)$。')
    put(226043, 2100, ['线段树', '矩阵乘法', '计数 DP'], '两塔斜楼梯方向可改，查询从指定层与侧到更高层指定侧的上楼方案数。',
        '每层对应一个二乘二计数转移矩阵，同塔两条边的转移数为一；若斜楼梯为 /，再加左到右的一；若为反斜线，则加右到左的一。两段路径方案数按普通矩阵乘法组合：枚举中间侧，前后方案数相乘再相加。线段树维护有序矩阵积，修改只换一个叶子。查询 hs 到 ht 使用楼层 hs 到 ht-1 的矩阵，取起点侧、终点侧对应元素。',
        r'''int n, m; string direction; cin >> n >> m >> direction; auto leaf = [&](char c) { Matrix a; a.value[0][0] = a.value[1][1] = 1; if (c == '/') a.value[0][1] = 1; else a.value[1][0] = 1; return a; };
        vector<Matrix> initial; initial.reserve(n - 1); for (char c : direction) initial.push_back(leaf(c)); MatrixTree tree(initial);
        while (m--) { int op; cin >> op; if (op == 0) { int h; char c; cin >> h >> c; tree.change(h - 1, leaf(c)); } else { int hs, ht, ps, pt; cin >> hs >> ht >> ps >> pt; cout << tree.query(hs - 1, ht - 1).value[ps][pt] << '\n'; } }''',
        '矩阵乘法有方向，不能把查询中的分段任意交换。不可达时方案数自然为零，单位矩阵表示不跨任何楼层时留在原侧的一种空路径。',
        declarations=matrix_tree(False), complexity=r'每次操作 $O(2^3\log n)$，空间 $O(n)$。')


if __name__ == '__main__':
    run()
    print('Registered five reviewed polynomial, capacity and tower articles.')
