## P2341 受欢迎的牛 G

原题：[P2341](https://www.luogu.com.cn/problem/P2341)

### 思路

能被所有牛到达的顶点必须位于缩点图的汇分量。只有一个出度为零的分量时，答案是它的大小；有多个时答案为零。

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
    int target = -1;
    for (int c = 0; c < s.count; c++)
        if (!out[c]) {
            if (target != -1) {
                cout << 0 << '\n';
                return 0;
            }
            target = c;
        }
    cout << size[target] << '\n';
    return 0;
}
```

### 实现提醒

判断出度，不是入度；多个汇分量时输出 0。
