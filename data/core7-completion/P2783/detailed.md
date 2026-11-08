## P2783 有机化学之神偶尔会做作弊

原题：[P2783](https://www.luogu.com.cn/problem/P2783)

### 从问题到算法

题目特别规定两个点之间的平行边不构成环。因此先将端点排序、去掉重复无向边，之后才做 lowlink；直接把重边当返祖边会错误合并两个碳。

简单无向图中，一条边不是桥当且仅当它位于某个环上。合并所有非桥边的端点，正好执行“同环顶点合并”，多个相交环也会按传递性合为一个结点。剩下的桥构成树。

原点映射到压缩结点，路径边数为 depth[u]+depth[v]−2depth[lca]，题目统计包含两端的顶点数，所以加一。反复取最低二进制位后倒序输出，不能把十进制数字当作二进制拼接。

### 复杂度

时间 O(m log m+(n+q) log n)，空间 O(n+m)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

struct Lowlink {
    int n, timer = 0;
    vector<vector<pair<int, int>>> g;
    vector<pair<int, int>> edges;
    vector<int> tin, low, parent, parentEdge, children, size;
    vector<char> bridge, cut;
    vector<vector<int>> blocks;
    Lowlink(int n)
        : n(n), g(n), tin(n), low(n), parent(n, -1), parentEdge(n, -1), children(n), size(n, 1),
          cut(n) {}
    void edge(int a, int b) {
        int id = edges.size();
        edges.push_back({a, b});
        g[a].push_back({b, id});
        g[b].push_back({a, id});
    }
    void build() {
        bridge.assign(edges.size(), 0);
        vector<int> vertices;
        for (int root = 0; root < n; root++)
            if (!tin[root]) {
                vector<pair<int, int>> st = {{root, 0}};
                tin[root] = low[root] = ++timer;
                vertices.push_back(root);
                while (!st.empty()) {
                    int v = st.back().first;
                    int &next = st.back().second;
                    if (next < (int)g[v].size()) {
                        auto [u, id] = g[v][next++];
                        if (id == parentEdge[v])
                            continue;
                        if (!tin[u]) {
                            parent[u] = v;
                            parentEdge[u] = id;
                            children[v]++;
                            tin[u] = low[u] = ++timer;
                            vertices.push_back(u);
                            st.push_back({u, 0});
                        } else
                            low[v] = min(low[v], tin[u]);
                    } else {
                        st.pop_back();
                        int p = parent[v];
                        if (p >= 0) {
                            size[p] += size[v];
                            low[p] = min(low[p], low[v]);
                            bridge[parentEdge[v]] = low[v] > tin[p];
                            if (low[v] >= tin[p]) {
                                if (parent[p] >= 0)
                                    cut[p] = 1;
                                vector<int> block = {p};
                                while (true) {
                                    int u = vertices.back();
                                    vertices.pop_back();
                                    block.push_back(u);
                                    if (u == v)
                                        break;
                                }
                                blocks.push_back(move(block));
                            }
                        } else {
                            cut[v] = children[v] > 1;
                            if (children[v] == 0)
                                blocks.push_back({v});
                            vertices.pop_back();
                        }
                    }
                }
            }
    }
};

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

    int n, m;
    cin >> n >> m;
    vector<pair<int, int>> e;
    while (m--) {
        int a, b;
        cin >> a >> b;
        a--;
        b--;
        if (a > b)
            swap(a, b);
        if (a != b)
            e.push_back({a, b});
    }
    sort(e.begin(), e.end());
    e.erase(unique(e.begin(), e.end()), e.end());
    Lowlink graph(n);
    for (auto [a, b] : e)
        graph.edge(a, b);
    graph.build();
    DSU d(n);
    for (int i = 0; i < (int)e.size(); i++)
        if (!graph.bridge[i])
            d.join(e[i].first, e[i].second);
    vector<int> ids(n, -1), belong(n);
    int z = 0;
    for (int i = 0; i < n; i++) {
        int r = d.find(i);
        if (ids[r] < 0)
            ids[r] = z++;
        belong[i] = ids[r];
    }
    vector<vector<int>> g(z);
    for (int i = 0; i < (int)e.size(); i++)
        if (graph.bridge[i]) {
            int a = belong[e[i].first], b = belong[e[i].second];
            g[a].push_back(b);
            g[b].push_back(a);
        }
    HLD tree(g);
    int q;
    cin >> q;
    while (q--) {
        int a, b;
        cin >> a >> b;
        int value = tree.distance(belong[a - 1], belong[b - 1]) + 1;
        string ans;
        while (value) {
            ans += char('0' + value % 2);
            value /= 2;
        }
        reverse(ans.begin(), ans.end());
        cout << ans << '\n';
    }

    return 0;
}
```

### 实现提醒

先去重再判桥；相同压缩点的答案为二进制 1；路径点数需要加一。
