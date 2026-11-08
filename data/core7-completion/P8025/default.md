## P8025 Związek Harcerstwa Bajtockiego

原题：[P8025](https://www.luogu.com.cn/problem/P8025)

### 思路

设当前位置为 u，目标为 v，公共祖先为 l。步数够走完整条路径就到 v；否则若步数不超过 u 到 l 的距离，直接向上跳；再否则从 v 反向跳到本次应停的位置。

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
