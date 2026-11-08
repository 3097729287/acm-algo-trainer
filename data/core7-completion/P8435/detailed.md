## P8435 点双连通分量

原题：[P8435](https://www.luogu.com.cn/problem/P8435)

### 从问题到算法

在 DFS 树中，tin[u] 是首次访问顺序，low[u] 是从 u 的子树沿树边向下、再经至多一条返祖边能到达的最早顺序。处理完孩子 v 后，若 low[v]>=tin[u]，它的子树无法绕过 u 到达更早祖先，形成一个点双块的分界；若严格大于，则父子边还是桥。

代码用显式栈保存当前顶点与下一条邻边，模拟递归进入和退出。无向边按边编号识别，只跳过同一条父边，避免把平行边全部跳过。

顶点栈保存尚未归入完整块的搜索分支。当 low[v]>=tin[u] 时，v 子树的这一段无法绕到 u 之前，它与 u 恰好形成一个最大无割点子图。弹出直至 v，把 u 加入这一块；u 本身仍留在栈中，便能参与其它相邻块。

P8435 要求保留孤立点。一个 DFS 根没有树孩子时，直接输出它自身作为单点块；这同样覆盖只有自环的单点。普通自环不会产生新的跨点关系，也不会额外拆出一个已被更大块包含的单点块。

平行边用边编号区分，第二条到父亲的边是合法返祖边。不同原连通分量分别搜索。

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

    cout << graph.blocks.size() << '\n';
    for (auto &block : graph.blocks) {
        cout << block.size();
        for (int v : block)
            cout << ' ' << v + 1;
        cout << '\n';
    }

    return 0;
}
```

### 实现提醒

不要误写成边双分量；割点可以重复出现在多个块；按本题约定处理孤立点。
