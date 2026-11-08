"""Eligible problems found while reviewing the advanced lists."""
from nowcoder_editorials import CONTENT, add, read
from nowcoder_divide import FAST


def run():
    existing = read(CONTENT / 'reviewed.json')
    if 'nowcoder-global::229662' not in existing:
        add(229662, 1800, ['最近公共祖先', '倍增'], '树结构固定，每次指定一个新根，再查询两点的最近公共祖先。',
            '任选一号点作为预处理根，求所有点深度与倍增祖先。对查询 (root,x,y)，分别计算 a=LCA(x,y)、b=LCA(x,root)、c=LCA(y,root)，返回三者中在固定根下最深的点。\n\n理由是三个点之间的三条路径有唯一交汇点，它正是以 root 为根时 x、y 的公共祖先中距离 root 最远者。固定根下的这三个两两 LCA 中，两个相同且较浅，另一个就是该交汇点；因此取最深者。树从未改边，不必针对每个查询重新预处理。用迭代遍历建立父子与深度，兼容十万结点长链。',
            r'''int n; cin >> n; const int log = 18; vector<vector<int>> edges(n + 1); for (int i = 1; i < n; i++) { int u, v; cin >> u >> v; edges[u].push_back(v); edges[v].push_back(u); }
            vector<array<int,log>> up(n + 1); vector<int> depth(n + 1), order{1}; for (size_t i = 0; i < order.size(); i++) { int u = order[i]; for (int v : edges[u]) if (v != up[u][0]) { up[v][0] = u; depth[v] = depth[u] + 1; for (int b = 1; b < log; b++) up[v][b] = up[up[v][b - 1]][b - 1]; order.push_back(v); } }
            auto lca = [&](int x, int y) { if (depth[x] < depth[y]) swap(x, y); int difference = depth[x] - depth[y]; for (int b = 0; b < log; b++) if (difference >> b & 1) x = up[x][b]; if (x == y) return x;
                for (int b = log - 1; b >= 0; b--) if (up[x][b] != up[y][b]) { x = up[x][b]; y = up[y][b]; } return up[x][0]; };
            int m; cin >> m; while (m--) { int root, x, y; cin >> root >> x >> y; int answer = lca(x, y); for (int candidate : {lca(x, root), lca(y, root)}) if (depth[candidate] > depth[answer]) answer = candidate; cout << answer << '\n'; }''',
            '取的是预处理根下深度最大的候选，不是编号最大。查询改根不会改变实际边，所有倍增表始终共用。',
            complexity=r'预处理 $O(n\log n)$，每次查询 $O(\log n)$，空间 $O(n\log n)$。')
    if 'nowcoder-global::20325' not in existing:
        add(20325, 1800, ['树状数组', '离线查询'], '多次查询静态颜色数组中，闭区间包含多少种不同颜色。',
            '将查询按右端点升序排列，依次把数组扫到当前右端。树状数组只在每种颜色最后出现的位置放一，较早的同色位置清零。这样，对于当前右端 R，颜色出现在 [L,R] 中，当且仅当它最后出现的位置不小于 L；树状数组的闭区间和就是不同颜色数。答案存回原查询编号，最后按输入顺序输出。',
            r'''FastInput input; int n = input.next(); vector<int> a(n + 1); for (int i = 1; i <= n; i++) a[i] = input.next(); int m = input.next(); struct Query { int left, right, id; }; vector<Query> queries(m); for (int i = 0; i < m; i++) queries[i] = {input.next(), input.next(), i};
            sort(queries.begin(), queries.end(), [](const Query &a, const Query &b) { return a.right < b.right; }); vector<int> tree(n + 1), last(1000001), answer(m);
            auto change = [&](int position, int value) { for (int i = position; i <= n; i += i & -i) tree[i] += value; }; auto sum = [&](int position) { int result = 0; for (int i = position; i > 0; i -= i & -i) result += tree[i]; return result; };
            int right = 0; for (auto query : queries) { while (right < query.right) { right++; if (last[a[right]]) change(last[a[right]], -1); change(right, 1); last[a[right]] = right; } answer[query.id] = sum(query.right) - sum(query.left - 1); }
            for (int value : answer) cout << value << '\n';''',
            '按题面备注中更大的范围支持一百万元素与询问，并支持颜色零。不能直接把每个出现位置都加一，那会得到长度而非种类数。',
            declarations=FAST, complexity=r'时间 $O(m\log m+(n+m)\log n)$，空间 $O(n+m+V)$，颜色值域 $V=10^6$。')


if __name__ == '__main__':
    run()
    print('Registered changed-root LCA and offline distinct-color queries.')
