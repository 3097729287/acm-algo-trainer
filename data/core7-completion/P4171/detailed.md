## P4171 满汉全席

原题：[P4171](https://www.luogu.com.cn/problem/P4171)

### 从问题到算法

每种材料只有两种互斥做法，可以用一个布尔变量表示。评审仅在两种喜好都未满足时淘汰选手，所以对应逻辑条件 A∨B。这个条件等价于：若 A 不成立，就必须 B 成立；若 B 不成立，就必须 A 成立。

把每个文字及其否定作为两个顶点，用相邻编号表示，异或一就得到相反做法。对每位评审加入两条蕴含边。若某变量与其否定互相蕴含，它们位于同一强连通分量，任意取值都会推出矛盾。

反过来，当每个变量的两个文字处于不同分量时，按缩点图逆拓扑方向选择尚未赋值的分量即可得到满足所有子句的取值，因此该条件也是充分的。本题只判断是否存在，不必输出具体菜单。

### 复杂度

每组时间 O(n+m)，空间 O(n+m)。

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
        SCC s(2 * n);
        while (m--) {
            string a, b;
            cin >> a >> b;
            auto id = [](string v) { return 2 * (stoi(v.substr(1)) - 1) + (v[0] == 'm'); };
            int x = id(a), y = id(b);
            s.edge(x ^ 1, y);
            s.edge(y ^ 1, x);
        }
        s.build();
        bool ok = true;
        for (int i = 0; i < n; i++)
            if (s.component[2 * i] == s.component[2 * i + 1])
                ok = false;
        cout << (ok ? "GOOD" : "BAD") << '\n';
    }

    return 0;
}
```

### 实现提醒

m 表示满式，h 表示汉式；否定文字用 ^1；每组重新建图。
