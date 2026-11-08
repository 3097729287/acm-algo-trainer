## P4819 杀人游戏

原题：[P4819](https://www.luogu.com.cn/problem/P4819)

### 从问题到算法

强连通分量内任意两点互相可达，分量之间压缩后形成有向无环图。代码用两遍非递归 DFS：先在原图记录退出顺序，再按退出顺序逆序遍历反图，每次搜索恰好得到一个分量。显式栈记录当前顶点与下一条待访问边，保证记录的是退出顺序。

查证一个平民后，可以沿认识关系继续获得信息。每个源分量没有来自外部的认识关系，通常至少查证其中一个人；选择哪个人遇到杀手的概率都是 1/n，所以应最小化必须冒险查证的人数。

最后剩下一个未确定身份的人时，可以直接推断他是杀手，无需查证。要省下一次源分量查证，这个源必须是单点；若包含多人，仍有多个候选无法区分。同时，跳过它后其余所有分量必须仍能被其它源覆盖。在缩点 DAG 上，这等价于它的每个出邻居的入度都至少为二。

跨分量的重边先去重，避免同一个源重复指向一个分量被误算成多个来源。满足条件的单点源只需存在一个，就能把它留到最后，最多省一次。概率为 1−风险人数/n；n=1 时可以直接确定唯一的人。

### 复杂度

时间 O((n+m) log m)，空间 O(n+m)。

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
        int a, b;
        cin >> a >> b;
        s.edge(a - 1, b - 1);
    }
    s.build();
    vector<int> size(s.count), in(s.count);
    vector<pair<int, int>> edges;
    for (int v = 0; v < n; v++) {
        size[s.component[v]]++;
        for (int u : s.g[v])
            if (s.component[v] != s.component[u])
                edges.push_back({s.component[v], s.component[u]});
    }
    sort(edges.begin(), edges.end());
    edges.erase(unique(edges.begin(), edges.end()), edges.end());
    vector<vector<int>> g(s.count);
    for (auto [a, b] : edges) {
        g[a].push_back(b);
        in[b]++;
    }
    int risk = count(in.begin(), in.end(), 0);
    for (int c = 0; c < s.count; c++)
        if (!in[c] && size[c] == 1) {
            bool ok = true;
            for (int u : g[c])
                if (in[u] == 1)
                    ok = false;
            if (ok) {
                risk--;
                break;
            }
        }
    cout << fixed << setprecision(6) << 1.0 - (double)risk / n << '\n';

    return 0;
}
```

### 实现提醒

统计不同来源的入边，重边去重；最多省一次；输出六位小数。
