## P1726 上白泽慧音

原题：[P1726](https://www.luogu.com.cn/problem/P1726)

### 从问题到算法

强连通分量内任意两点互相可达，分量之间压缩后形成有向无环图。代码用两遍非递归 DFS：先在原图记录退出顺序，再按退出顺序逆序遍历反图，每次搜索恰好得到一个分量。显式栈记录当前顶点与下一条待访问边，保证记录的是退出顺序。

题目中的“绝对连通”正是互相可达，因此最大绝对连通区域就是最大的强连通分量。单向道路只添加一条边，双向道路添加两个方向。

扫描顶点 1 到 n，把它放入所属组，保证每组成员递增。比较两组时先看大小，大小相同再比较整个 vector 的字典序。分量互不相交，所以并列时也可比较最小成员，但直接比较 vector 更直观。

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
