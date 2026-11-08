## CF1000E We Need More Bosses

原题：[CF1000E](https://www.luogu.com.cn/problem/CF1000E)

### 从问题到算法

在 DFS 树中，tin[u] 是首次访问顺序，low[u] 是从 u 的子树沿树边向下、再经至多一条返祖边能到达的最早顺序。处理完孩子 v 后，若 low[v]>=tin[u]，它的子树无法绕过 u 到达更早祖先，形成一个点双块的分界；若严格大于，则父子边还是桥。

代码用显式栈保存当前顶点与下一条邻边，模拟递归进入和退出。无向边按边编号识别，只跳过同一条父边，避免把平行边全部跳过。

删除非桥不会让图分开，桥才可能成为两个位置之间无法绕开的必经连接。把所有非桥边连接的点压成一个块，块之间的边都是桥，缩点图是树。

对于任意两点，其间必经桥的数量正好等于所属块在树上的距离。要让这个数量最大，就是求树直径。任选一块 BFS 得到最远块 A，再从 A BFS，最大距离即为直径。

原图没有桥时全部缩成一个块，直径为零。并查集合并非桥边后，可直接把代表元作为树顶点编号，不必重新分配连续编号。

### 复杂度

时间 O(n+m)，空间 O(n+m)。

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

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    cin >> n >> m;
    Lowlink graph(n);
    for (int i = 0; i < m; i++) {
        int a, b;
        cin >> a >> b;
        graph.edge(a - 1, b - 1);
    }
    graph.build();

    DSU d(n);
    for (int i = 0; i < (int)graph.edges.size(); i++)
        if (!graph.bridge[i])
            d.join(graph.edges[i].first, graph.edges[i].second);
    vector<vector<int>> tree(n);
    for (int i = 0; i < (int)graph.edges.size(); i++)
        if (graph.bridge[i]) {
            auto [a, b] = graph.edges[i];
            a = d.find(a);
            b = d.find(b);
            tree[a].push_back(b);
            tree[b].push_back(a);
        }
    auto farthest = [&](int start) {
        vector<int> distance(n, -1);
        queue<int> q;
        q.push(start);
        distance[start] = 0;
        int best = start;
        while (!q.empty()) {
            int v = q.front();
            q.pop();
            if (distance[v] > distance[best])
                best = v;
            for (int u : tree[v])
                if (distance[u] < 0) {
                    distance[u] = distance[v] + 1;
                    q.push(u);
                }
        }
        return pair<int, int>{best, distance[best]};
    };
    auto [a, unused] = farthest(d.find(0));
    cout << farthest(a).second << '\n';

    return 0;
}
```

### 实现提醒

只合并非桥；树距离按边数；没有桥时输出 0。
