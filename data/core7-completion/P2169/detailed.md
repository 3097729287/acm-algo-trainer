## P2169 正则表达式

原题：[P2169](https://www.luogu.com.cn/problem/P2169)

### 从问题到算法

强连通分量内任意两点互相可达，分量之间压缩后形成有向无环图。代码用两遍非递归 DFS：先在原图记录退出顺序，再按退出顺序逆序遍历反图，每次搜索恰好得到一个分量。显式栈记录当前顶点与下一条待访问边，保证记录的是退出顺序。

同一个强连通分量内任意两台电脑都可互相到达，按题意内部传输免费，因此可以把整个分量当成一个点。跨分量边仍须付原来的费用，不能因为图中存在一条环外的返回路径就随意消掉某条费用。

每条原边检查两个端点的分量，内部边丢弃，外部边带原权重加入新图。随后用 Dijkstra 求最短路。它每次确定当前距离最小的点，边权非负保证距离不再被未来路线改小。优先队列中旧距离要跳过。

原图点数大，强连通搜索使用显式栈；距离中间量使用 long long。

### 复杂度

时间 O((n+m) log n)，空间 O(n+m)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

struct SCC {
    int n, count = 0;
    vector<vector<int>> g, rev;
    vector<int> component;
    explicit SCC(int n) : n(n), g(n), rev(n), component(n, -1) {}
    void edge(int a, int b) {
        g[a].push_back(b);
        rev[b].push_back(a);
    }
    void build() {
        vector<char> seen(n);
        vector<int> order;
        for (int start = 0; start < n; start++)
            if (!seen[start]) {
                vector<pair<int, int>> st = {{start, 0}};
                seen[start] = true;
                while (!st.empty()) {
                    int v = st.back().first;
                    int &i = st.back().second;
                    if (i < (int)g[v].size()) {
                        int u = g[v][i++];
                        if (!seen[u]) {
                            seen[u] = true;
                            st.push_back({u, 0});
                        }
                    } else {
                        order.push_back(v);
                        st.pop_back();
                    }
                }
            }
        reverse(order.begin(), order.end());
        for (int start : order)
            if (component[start] < 0) {
                vector<int> st = {start};
                component[start] = count;
                while (!st.empty()) {
                    int v = st.back();
                    st.pop_back();
                    for (int u : rev[v])
                        if (component[u] < 0) {
                            component[u] = count;
                            st.push_back(u);
                        }
                }
                count++;
            }
    }
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    cin >> n >> m;
    SCC s(n);
    vector<tuple<int, int, int>> edges;
    while (m--) {
        int a, b, w;
        cin >> a >> b >> w;
        a--;
        b--;
        s.edge(a, b);
        edges.push_back({a, b, w});
    }
    s.build();
    vector<vector<pair<int, int>>> g(s.count);
    for (auto [a, b, w] : edges)
        if (s.component[a] != s.component[b])
            g[s.component[a]].push_back({s.component[b], w});
    const long long inf = LLONG_MAX / 4;
    vector<long long> d(s.count, inf);
    int start = s.component[0], goal = s.component[n - 1];
    d[start] = 0;
    priority_queue<pair<long long, int>, vector<pair<long long, int>>,
                   greater<pair<long long, int>>>
        q;
    q.push({0, start});
    while (!q.empty()) {
        auto [dist, v] = q.top();
        q.pop();
        if (dist != d[v])
            continue;
        for (auto [u, w] : g[v])
            if (d[u] > dist + w) {
                d[u] = dist + w;
                q.push({d[u], u});
            }
    }
    cout << d[goal] << '\n';

    return 0;
}
```

### 实现提醒

只把强连通分量内部费用置零；优先队列过期项跳过。
