## B3609 强连通分量

原题：[B3609](https://www.luogu.com.cn/problem/B3609)

### 从问题到算法

强连通分量内任意两点互相可达，分量之间压缩后形成有向无环图。代码用两遍非递归 DFS：先在原图记录退出顺序，再按退出顺序逆序遍历反图，每次搜索恰好得到一个分量。显式栈记录当前顶点与下一条待访问边，保证记录的是退出顺序。

第一遍的退出顺序能把缩点图中较靠前的分量优先留给第二遍；第二遍沿反边无法越过尚未处理的前驱，所以一次搜索不会混入别的分量。

算法内部产生的分量编号不一定符合题目输出顺序。求完编号后，按 1 到 n 顺序收集各组成员，组内天然有序。再按每组最小成员排序，得到题目要求的“先输出最小未输出顶点所在组”。重边与自环不会影响访问标记。

### 复杂度

时间 O(n+m+n log n)，空间 O(n+m)。

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
    vector<vector<int>> groups(s.count);
    for (int v = 0; v < n; v++)
        groups[s.component[v]].push_back(v + 1);
    sort(groups.begin(), groups.end(), [](const auto &a, const auto &b) { return a[0] < b[0]; });
    cout << s.count << '\n';
    for (auto &group : groups) {
        for (int v : group)
            cout << v << ' ';
        cout << '\n';
    }
    return 0;
}
```

### 实现提醒

输出顺序要单独整理；第一遍记录退出顺序；重边和自环不重复访问。
