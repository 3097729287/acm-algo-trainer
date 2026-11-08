## P2656 采蘑菇

原题：[P2656](https://www.luogu.com.cn/problem/P2656)

### 从问题到算法

在强连通块内，可以从任意位置绕回任意边，也能在收集完后到达指定出口。恢复系数小于一，非零蘑菇在有限次经过后归零，因此能收完全部内部边，不存在互斥选择。逐边模拟 w=floor(w·k) 的衰减，把所有采集值相加为块权。

跨块边不能再返回，否则两个块应当属于同一个 SCC，所以只能使用一次，贡献是初始 w。缩点图为 DAG，设 dp[c] 是到达 c 并收完 c 内蘑菇的最大总数，用 dp[next]=max(dp[next],dp[c]+跨边数量+块权[next]) 转移。只初始化起点所属块，其它块保持不可达。

恢复系数最多一位小数，将它转成整数十分比再乘除，避免 0.7 等浮点误差影响向下取整。

### 复杂度

时间 O(n+m log W)，其中 W 为初始边权上界；空间 O(n+m)。

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
    struct E {
        int u, v, w, k;
    };
    vector<E> edges;
    for (int i = 0; i < m; i++) {
        int u, v, w;
        string k;
        cin >> u >> v >> w >> k;
        u--;
        v--;
        int rate = 0;
        auto dot = k.find('.');
        if (dot != string::npos && dot + 1 < k.size())
            rate = k[dot + 1] - '0';
        edges.push_back({u, v, w, rate});
        s.edge(u, v);
    }
    int start;
    cin >> start;
    start--;
    s.build();
    vector<long long> value(s.count), dp(s.count, LLONG_MIN / 4);
    vector<vector<pair<int, int>>> g(s.count);
    vector<int> in(s.count);
    for (auto e : edges) {
        int u = s.component[e.u], v = s.component[e.v];
        if (u == v) {
            long long w = e.w;
            while (w) {
                value[u] += w;
                w = w * e.k / 10;
            }
        } else {
            g[u].push_back({v, e.w});
            in[v]++;
        }
    }
    queue<int> q;
    for (int i = 0; i < s.count; i++)
        if (!in[i])
            q.push(i);
    dp[s.component[start]] = value[s.component[start]];
    long long ans = dp[s.component[start]];
    while (!q.empty()) {
        int v = q.front();
        q.pop();
        ans = max(ans, dp[v]);
        for (auto [u, w] : g[v]) {
            if (dp[v] >= 0)
                dp[u] = max(dp[u], dp[v] + w + value[u]);
            if (!--in[u])
                q.push(u);
        }
    }
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

内部边累加全部衰减值；跨块边只取一次；不可达块不参与转移。
