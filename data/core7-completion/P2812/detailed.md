## P2812 校园网络 / [IOI 1996 / USACO5.3] 校园网 Network of Schools 加强版

原题：[P2812](https://www.luogu.com.cn/problem/P2812)

### 从问题到算法

强连通分量内任意两点互相可达，分量之间压缩后形成有向无环图。代码用两遍非递归 DFS：先在原图记录退出顺序，再按退出顺序逆序遍历反图，每次搜索恰好得到一个分量。显式栈记录当前顶点与下一条待访问边，保证记录的是退出顺序。

软件在同一个强连通分量内能够传遍所有学校，因此初始只需在选中的每个分量里放一份。入度为零的源分量无法从其它分量获得软件，必须至少选择一个学校；而从所有源出发就能覆盖整个 DAG，所以源的数量也是充分的。

要使整个图强连通，每个源必须有新入边、每个汇必须有新出边，至少需要两类数量的较大者；把源汇链串成循环可以达到这个下界。已有一个强连通分量时无需加边，但第一问仍需要一份软件。

每所学校的邻接列表以 0 结束，不是逐行读取固定数量的边。

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
