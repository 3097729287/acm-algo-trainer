## P3007 The Continental Cowngress G

原题：[P3007](https://www.luogu.com.cn/problem/P3007)

### 从问题到算法

每头牛的要求是两个文字的析取，按非 A→B 与非 B→A 建图。先求强连通分量，某议案的 Y、N 同属一分量时整体无解。

接着判断某个取值是否会造成矛盾。如果从文字 N 能沿蕴含边到 Y，那么假设 N 为真会同时推出它的否定，故 N 不可取，所有解都只能取 Y。对 Y 到 N 的情形同理。

如果两个方向都不可达，则都存在可扩展成完整解的赋值，这是可满足 2-SAT 蕴含图的性质：加入单个文字为真的条件只有在它能推出自身否定时才会破坏可满足性。顶点不超过两千，可以对每个议案的两个文字分别遍历图，无需建立巨大传递闭包。

### 复杂度

时间 O(n(n+m))，空间 O(n+m)。

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
    SCC s(2 * n);
    while (m--) {
        int a, b;
        char x, y;
        cin >> a >> x >> b >> y;
        int u = 2 * (a - 1) + (x == 'Y'), v = 2 * (b - 1) + (y == 'Y');
        s.edge(u ^ 1, v);
        s.edge(v ^ 1, u);
    }
    s.build();
    for (int i = 0; i < n; i++)
        if (s.component[2 * i] == s.component[2 * i + 1]) {
            cout << "IMPOSSIBLE\n";
            return 0;
        }
    auto reach = [&](int a, int b) {
        vector<char> seen(2 * n);
        vector<int> st = {a};
        seen[a] = 1;
        while (!st.empty()) {
            int v = st.back();
            st.pop_back();
            if (v == b)
                return true;
            for (int u : s.g[v])
                if (!seen[u]) {
                    seen[u] = 1;
                    st.push_back(u);
                }
        }
        return false;
    };
    for (int i = 0; i < n; i++)
        cout << (reach(2 * i, 2 * i + 1) ? 'Y' : reach(2 * i + 1, 2 * i) ? 'N' : '?');
    cout << '\n';

    return 0;
}
```

### 实现提醒

无解先输出 IMPOSSIBLE；可行时强制方向不能反；未知输出 ?。
