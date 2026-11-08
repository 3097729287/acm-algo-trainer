## P1726 上白泽慧音

原题：[P1726](https://www.luogu.com.cn/problem/P1726)

### 思路

双向道路建两条边，求强连通分量。按编号顺序收集成员，选择人数最多、并列时字典序最小的一组。

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
    while (m--) {
        int a, b, t;
        cin >> a >> b >> t;
        s.edge(a - 1, b - 1);
        if (t == 2)
            s.edge(b - 1, a - 1);
    }
    s.build();
    vector<vector<int>> groups(s.count);
    for (int v = 0; v < n; v++)
        groups[s.component[v]].push_back(v + 1);
    vector<int> ans;
    for (auto &v : groups)
        if (v.size() > ans.size() || (v.size() == ans.size() && v < ans))
            ans = v;
    cout << ans.size() << '\n';
    for (int v : ans)
        cout << v << ' ';
    cout << '\n';

    return 0;
}
```

### 实现提醒

t=2 要建双向边；并列按升序成员表比较。
