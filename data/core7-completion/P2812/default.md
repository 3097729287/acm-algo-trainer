## P2812 校园网络 / [IOI 1996 / USACO5.3] 校园网 Network of Schools 加强版

原题：[P2812](https://www.luogu.com.cn/problem/P2812)

### 思路

第一问是缩点图中入度为零的分量数；第二问若只有一个分量为 0，否则是源分量数与汇分量数的较大者。

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

    int n;
    cin >> n;
    SCC s(n);
    for (int i = 0; i < n; i++) {
        int x;
        while (cin >> x && x)
            s.edge(i, x - 1);
    }
    s.build();
    vector<int> in(s.count), out(s.count);
    for (int v = 0; v < n; v++)
        for (int u : s.g[v])
            if (s.component[u] != s.component[v]) {
                in[s.component[u]]++;
                out[s.component[v]]++;
            }
    int a = count(in.begin(), in.end(), 0), b = count(out.begin(), out.end(), 0);
    cout << a << '\n' << (s.count == 1 ? 0 : max(a, b)) << '\n';

    return 0;
}
```

### 实现提醒

每行的 0 只是结束标记；一分量时答案是 1 和 0。
