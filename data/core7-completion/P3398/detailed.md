## P3398 仓鼠找 sugar

原题：[P3398](https://www.luogu.com.cn/problem/P3398)

### 从问题到算法

设两条路径为 a—b 与 c—d，最高点分别为 x=lca(a,b)、y=lca(c,d)。若它们相交，取交集中的一个点 z。x、y 都是 z 的祖先，必然可比较深度；较深的那个最高点位于从较浅最高点到 z 的路径上，所以属于两条路径的交集。反向结论显然成立。

点 v 在 u—w 路径上，等价于 dist(u,v)+dist(v,w)=dist(u,w)。树上路径唯一，走出路径再折回一定多走正步数。

代码用重链维护 LCA，避免递归遍历深链。若 x 在 c—d 上或 y 在 a—b 上，输出 Y，否则输出 N。

### 复杂度

预处理 O(n)，每问 O(log n)，空间 O(n)。

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

    int n, q;
    cin >> n >> q;
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
    auto on = [&](int v, int a, int b) {
        return tree.distance(a, v) + tree.distance(v, b) == tree.distance(a, b);
    };
    while (q--) {
        int a, b, c, d;
        cin >> a >> b >> c >> d;
        a--;
        b--;
        c--;
        d--;
        cout << (on(tree.lca(a, b), c, d) || on(tree.lca(c, d), a, b) ? 'Y' : 'N') << '\n';
    }

    return 0;
}
```

### 实现提醒

距离按边数；端点相交也算；输出大写 Y 或 N。
