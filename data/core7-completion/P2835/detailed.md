## P2835 刻录光盘

原题：[P2835](https://www.luogu.com.cn/problem/P2835)

### 从问题到算法

若两名营员互相可达，资料可以沿转交链在他们之间传播，因此整个强连通分量只需一个人先获得资料。缩点后不再有环。

入度为零的分量没有外部资料来源，必须至少刻录一张给它，这给出下界。反过来，DAG 的每个结点都可以沿反向边追溯到某个源点，所以给所有源分量各一张即可覆盖全图，达到这个下界。

按调查表方向建边：i 愿意让 j 拷贝，就建 i 到 j。多条跨分量边不影响“入度是否为零”的判断。

### 复杂度

时间 O(N+E)，空间 O(N+E)。

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
    vector<char> in(s.count);
    for (int i = 0; i < n; i++)
        for (int j : s.g[i])
            if (s.component[i] != s.component[j])
                in[s.component[j]] = 1;
    cout << count(in.begin(), in.end(), 0) << '\n';

    return 0;
}
```

### 实现提醒

有向边按资料传播方向；统计源分量，不是汇分量；每行以零结束。
