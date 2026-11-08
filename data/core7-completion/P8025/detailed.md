## P8025 Związek Harcerstwa Bajtockiego

原题：[P8025](https://www.luogu.com.cn/problem/P8025)

### 从问题到算法

树上最短路唯一，由 u 向上到 lca(u,v)，再向下到 v。记两段长度为 A、B，总长 D=A+B。若 t≥D，当前位置变为 v。

当 t<D 且 t≤A，答案是 u 的第 t 级祖先；当 A<t<D，答案在向下段，等价于 v 的第 D−t 级祖先。这样每条指令只需一次 LCA 与一次祖先查询。

重链上的顶点按深度连续编号。在一条链内可以直接用数组定位祖先，跨链时跳到链首的父亲；每次跨过轻边，所在子树大小至少翻倍，所以最多跨 O(log n) 条链。全部预处理采用迭代遍历，以适应百万点长链。

### 复杂度

预处理 O(n)，每条指令 O(log n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

struct HLD {
    int n;
    vector<int> parent, depth, size, heavy, head, pos, at, order;
    HLD(const vector<vector<int>> &g, int root = 0)
        : n(g.size()), parent(n, -1), depth(n), size(n, 1), heavy(n, -1), head(n), pos(n), at(n) {
        parent[root] = root;
        order = {root};
        for (int i = 0; i < (int)order.size(); i++) {
            int v = order[i];
            for (int u : g[v])
                if (parent[u] < 0) {
                    parent[u] = v;
                    depth[u] = depth[v] + 1;
                    order.push_back(u);
                }
        }
        for (int i = n - 1; i > 0; i--) {
            int v = order[i], p = parent[v];
            size[p] += size[v];
            if (heavy[p] < 0 || size[v] > size[heavy[p]])
                heavy[p] = v;
        }
        vector<pair<int, int>> st = {{root, root}};
        int timer = 0;
        while (!st.empty()) {
            auto [v, h] = st.back();
            st.pop_back();
            for (; v >= 0; v = heavy[v]) {
                head[v] = h;
                pos[v] = timer;
                at[timer++] = v;
                for (int u : g[v])
                    if (parent[u] == v && u != heavy[v])
                        st.push_back({u, u});
            }
        }
    }
    int lca(int a, int b) const {
        while (head[a] != head[b]) {
            if (depth[head[a]] < depth[head[b]])
                swap(a, b);
            a = parent[head[a]];
        }
        return depth[a] < depth[b] ? a : b;
    }
    int jump(int v, int d) const {
        while (d > depth[v] - depth[head[v]]) {
            d -= depth[v] - depth[head[v]] + 1;
            v = parent[head[v]];
        }
        return at[pos[v] - d];
    }
    int distance(int a, int b) const { return depth[a] + depth[b] - 2 * depth[lca(a, b)]; }
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, u, k;
    cin >> n >> u >> k;
    u--;
    vector<vector<int>> g(n);
    for (int i = 1; i < n; i++) {
        int a, b;
        cin >> a >> b;
        a--;
        b--;
        g[a].push_back(b);
        g[b].push_back(a);
    }
    HLD tree(g);
    while (k--) {
        int v;
        long long t;
        cin >> v >> t;
        v--;
        int l = tree.lca(u, v), A = tree.depth[u] - tree.depth[l],
            D = A + tree.depth[v] - tree.depth[l];
        if (t >= D)
            u = v;
        else if (t <= A)
            u = tree.jump(u, t);
        else
            u = tree.jump(v, D - t);
        cout << u + 1 << (k ? ' ' : '\n');
    }

    return 0;
}
```

### 实现提醒

t 可能超过路径长；每条指令以上一次停点为起点；数组编号从零转换。
