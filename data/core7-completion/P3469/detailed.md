## P3469 BLO-Blockade

原题：[P3469](https://www.luogu.com.cn/problem/P3469)

### 从问题到算法

在 DFS 树中，tin[u] 是首次访问顺序，low[u] 是从 u 的子树沿树边向下、再经至多一条返祖边能到达的最早顺序。处理完孩子 v 后，若 low[v]>=tin[u]，它的子树无法绕过 u 到达更早祖先，形成一个点双块的分界；若严格大于，则父子边还是桥。

代码用显式栈保存当前顶点与下一条邻边，模拟递归进入和退出。无向边按边编号识别，只跳过同一条父边，避免把平行边全部跳过。

图原本连通，删除 u 后，满足 low[v]>=tin[u] 的孩子子树会分别成为独立分块，其余未分离部分合在一起。用子树大小即可得出每块点数。

对一个大小为 s 的块，它与剩下 n−1−s 个点之间有 s(n−1−s) 个以本块为起点的有序点对。对所有块求和，每个跨块无向点对自然按两个方向各计一次。最后还有所有以 u 为起点或终点的 2(n−1) 个点对，它们也因 u 被封锁而不可通行。

累计分离孩子大小及对应贡献，再用剩余大小 n−1−sum 补上最后一块。根也可以统一这样计数，因为它没有祖先侧，其所有孩子都形成分离块，剩余大小自然为零。

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

    vector<long long> answer(n, 2LL * (n - 1)), separated(n);
    for (int v = 0; v < n; v++) {
        int p = graph.parent[v];
        if (p >= 0 && graph.low[v] >= graph.tin[p]) {
            long long s = graph.size[v];
            answer[p] += s * (n - 1 - s);
            separated[p] += s;
        }
    }
    for (int v = 0; v < n; v++) {
        long long rest = n - 1 - separated[v];
        answer[v] += rest * (n - 1 - rest);
        cout << answer[v] << '\n';
    }

    return 0;
}
```

### 实现提醒

统计有序点对；包含被封锁点作为端点的情况；答案用 long long。
