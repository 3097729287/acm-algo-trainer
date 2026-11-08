## P2341 受欢迎的牛 G

原题：[P2341](https://www.luogu.com.cn/problem/P2341)

### 从问题到算法

强连通分量内任意两点互相可达，分量之间压缩后形成有向无环图。代码用两遍非递归 DFS：先在原图记录退出顺序，再按退出顺序逆序遍历反图，每次搜索恰好得到一个分量。显式栈记录当前顶点与下一条待访问边，保证记录的是退出顺序。

同一分量内的牛互相可达，是否被其它分量到达也完全相同，所以答案一定包含整个分量。

在有向无环图中，从任意点不断沿出边走，最终会到达一个出度为零的汇点。若汇点唯一，每个点最终都能到达它，因此该分量内每头牛都受欢迎。若有两个汇点，它们都没有出边，不可能互相到达，更不可能存在被二者共同到达的其它点。

统计跨分量边带来的出度即可，自环和分量内部边不计。只关心是否为零，不需要去重平行边。

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
