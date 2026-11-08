## P2863 The Cow Prom S

原题：[P2863](https://www.luogu.com.cn/problem/P2863)

### 从问题到算法

强连通分量内任意两点互相可达，分量之间压缩后形成有向无环图。代码用两遍非递归 DFS：先在原图记录退出顺序，再按退出顺序逆序遍历反图，每次搜索恰好得到一个分量。显式栈记录当前顶点与下一条待访问边，保证记录的是退出顺序。

每个符合要求的群体中，任意两头牛必须能够互相到达，因此它恰好属于一个强连通分量。不同强连通分量不能合并，否则就与最大互相可达集合的定义矛盾。

题目要求至少两头牛组成群体，所以大小为一的分量不计，即使该顶点带有自环也不能把它当成两头牛。只需累计每个分量的顶点数，再统计大于一的项。

### 复杂度

时间 O(n+m)，空间 O(n+m)。

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
    for (int i = 0; i < m; i++) {
        int a, b;
        cin >> a >> b;
        s.edge(a - 1, b - 1);
    }
    s.build();
    vector<int> size(s.count), in(s.count), out(s.count);
    for (int v = 0; v < n; v++) {
        size[s.component[v]]++;
        for (int u : s.g[v])
            if (s.component[u] != s.component[v]) {
                out[s.component[v]]++;
                in[s.component[u]]++;
            }
    }
    int ans = 0;
    for (int x : size)
        ans += x > 1;
    cout << ans << '\n';
    return 0;
}
```

### 实现提醒

统计分量数，非顶点数；单点自环不构成两牛群体。
