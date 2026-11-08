## P1967 货车运输

原题：[P1967](https://www.luogu.com.cn/problem/P1967)

### 思路

按边权降序做 Kruskal，得到最大生成森林。原图两点间能承受的最大瓶颈，等于森林中路径最小边。用倍增维护祖先和沿途最小值回答多次查询。

### 复杂度

时间 O(m log m+(n+q) log n)，空间 O(m+n log n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

struct DSU {
    vector<int> p, size;
    explicit DSU(int n) : p(n), size(n, 1) { iota(p.begin(), p.end(), 0); }
    int find(int x) {
        while (p[x] != x) {
            p[x] = p[p[x]];
            x = p[x];
        }
        return x;
    }
    bool join(int a, int b) {
        a = find(a);
        b = find(b);
        if (a == b)
            return false;
        if (size[a] < size[b])
            swap(a, b);
        p[b] = a;
        size[a] += size[b];
        return true;
    }
};

struct TreePaths {
    int n, levels;
    vector<int> depth, root;
    vector<vector<int>> up;
    vector<vector<long long>> minimum;
    TreePaths(const vector<vector<pair<int, long long>>> &g)
        : n(g.size()), levels(1), depth(n, -1), root(n) {
        while ((1 << levels) <= n)
            levels++;
        up.assign(levels, vector<int>(n));
        minimum.assign(levels, vector<long long>(n, LLONG_MAX));
        for (int start = 0; start < n; start++)
            if (depth[start] < 0) {
                depth[start] = 0;
                root[start] = start;
                for (int j = 0; j < levels; j++)
                    up[j][start] = start;
                vector<int> q = {start};
                for (int i = 0; i < (int)q.size(); i++) {
                    int v = q[i];
                    for (auto [u, w] : g[v])
                        if (depth[u] < 0) {
                            depth[u] = depth[v] + 1;
                            root[u] = start;
                            up[0][u] = v;
                            minimum[0][u] = w;
                            for (int j = 1; j < levels; j++) {
                                up[j][u] = up[j - 1][up[j - 1][u]];
                                minimum[j][u] =
                                    min(minimum[j - 1][u], minimum[j - 1][up[j - 1][u]]);
                            }
                            q.push_back(u);
                        }
                }
            }
    }
    int lca(int a, int b) const {
        if (depth[a] < depth[b])
            swap(a, b);
        int difference = depth[a] - depth[b];
        for (int j = 0; j < levels; j++)
            if ((difference >> j) & 1)
                a = up[j][a];
        if (a == b)
            return a;
        for (int j = levels - 1; j >= 0; j--)
            if (up[j][a] != up[j][b]) {
                a = up[j][a];
                b = up[j][b];
            }
        return up[0][a];
    }
    long long bottleneck(int a, int b) const {
        if (a == b)
            return 0;
        long long answer = LLONG_MAX;
        if (depth[a] < depth[b])
            swap(a, b);
        int difference = depth[a] - depth[b];
        for (int j = 0; j < levels; j++)
            if ((difference >> j) & 1) {
                answer = min(answer, minimum[j][a]);
                a = up[j][a];
            }
        if (a == b)
            return answer;
        for (int j = levels - 1; j >= 0; j--)
            if (up[j][a] != up[j][b]) {
                answer = min({answer, minimum[j][a], minimum[j][b]});
                a = up[j][a];
                b = up[j][b];
            }
        return min({answer, minimum[0][a], minimum[0][b]});
    }
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    cin >> n >> m;
    vector<tuple<long long, int, int>> edges(m);
    for (auto &[w, a, b] : edges) {
        cin >> a >> b >> w;
        a--;
        b--;
    }
    sort(edges.rbegin(), edges.rend());
    DSU d(n);
    vector<vector<pair<int, long long>>> g(n);
    for (auto [w, a, b] : edges)
        if (d.join(a, b)) {
            g[a].push_back({b, w});
            g[b].push_back({a, w});
        }
    TreePaths paths(g);
    int q;
    cin >> q;
    while (q--) {
        int a, b;
        cin >> a >> b;
        a--;
        b--;
        if (d.find(a) != d.find(b))
            cout << -1 << '\n';
        else
            cout << paths.bottleneck(a, b) << '\n';
    }

    return 0;
}
```

### 实现提醒

最大生成树按权值降序；查询取路径最小边；先判断是否连通。
