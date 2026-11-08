## CF1777E Edge Reverse

原题：[CF1777E](https://www.luogu.com.cn/problem/CF1777E)

### 思路

权值不超过 x 的边允许反转，就先把它视作双向边。存在能到达全图的起点，当且仅当该图缩点后只有一个入度为零的分量。按阈值二分最小 x。

### 复杂度

每组时间 O((n+m) log W)，空间 O(n+m)。

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

    int tests;
    cin >> tests;
    while (tests--) {
        int n, m;
        cin >> n >> m;
        vector<tuple<int, int, int>> edges(m);
        int maximum = 0;
        for (auto &[a, b, w] : edges) {
            cin >> a >> b >> w;
            a--;
            b--;
            maximum = max(maximum, w);
        }
        auto ok = [&](int limit) {
            SCC s(n);
            for (auto [a, b, w] : edges) {
                s.edge(a, b);
                if (w <= limit)
                    s.edge(b, a);
            }
            s.build();
            vector<char> in(s.count);
            for (auto [a, b, w] : edges) {
                if (s.component[a] != s.component[b]) {
                    in[s.component[b]] = 1;
                    if (w <= limit)
                        in[s.component[a]] = 1;
                }
            }
            return count(in.begin(), in.end(), 0) == 1;
        };
        if (!ok(maximum)) {
            cout << -1 << '\n';
            continue;
        }
        int l = 0, r = maximum;
        while (l < r) {
            int mid = l + (r - l) / 2;
            if (ok(mid))
                r = mid;
            else
                l = mid + 1;
        }
        cout << l << '\n';
    }

    return 0;
}
```

### 实现提醒

判定唯一源而非唯一汇；阈值含等号；最大阈值仍不连通则无解。
