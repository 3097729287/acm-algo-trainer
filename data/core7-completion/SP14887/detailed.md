## SP14887 GOODA - Good Travels

原题：[SP14887](https://www.luogu.com.cn/problem/SP14887)

### 从问题到算法

强连通分量内任意两点互相可达，分量之间压缩后形成有向无环图。代码用两遍非递归 DFS：先在原图记录退出顺序，再按退出顺序逆序遍历反图，每次搜索恰好得到一个分量。显式栈记录当前顶点与下一条待访问边，保证记录的是退出顺序。

一个分量内允许重复经过城市，且快乐值只收集一次。由于全部点权非负，可以先在分量内部绕行访问所有城市，再到达需要的出口，不会损失收益，所以缩点后的权值就是分量内快乐值之和。

缩点图没有环，一条路线经过的分量也不会重复。令 dp[c] 表示从起点分量出发到 c 时的最大快乐值。仅把起点初始化为自身点权，其它点为负无穷；按拓扑顺序，对每条 c→d 用 dp[c]+weight[d] 更新 dp[d]。

拓扑队列处理全部分量，但不可达分量不能参与数值转移。终点所属分量的 dp 就是答案；即使起终点同属一分量，也能先绕行收集整块再结束。

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

    int n, m, start, goal;
    cin >> n >> m >> start >> goal;
    start--;
    goal--;
    vector<long long> w(n);
    for (auto &x : w)
        cin >> x;
    SCC s(n);
    while (m--) {
        int a, b;
        cin >> a >> b;
        s.edge(a - 1, b - 1);
    }
    s.build();
    vector<long long> weight(s.count);
    vector<vector<int>> g(s.count);
    vector<int> in(s.count);
    for (int v = 0; v < n; v++) {
        weight[s.component[v]] += w[v];
        for (int u : s.g[v])
            if (s.component[u] != s.component[v]) {
                g[s.component[v]].push_back(s.component[u]);
                in[s.component[u]]++;
            }
    }
    const long long neg = LLONG_MIN / 4;
    vector<long long> dp(s.count, neg);
    dp[s.component[start]] = weight[s.component[start]];
    queue<int> q;
    for (int c = 0; c < s.count; c++)
        if (!in[c])
            q.push(c);
    while (!q.empty()) {
        int v = q.front();
        q.pop();
        for (int u : g[v]) {
            if (dp[v] != neg)
                dp[u] = max(dp[u], dp[v] + weight[u]);
            if (--in[u] == 0)
                q.push(u);
        }
    }
    cout << dp[s.component[goal]] << '\n';

    return 0;
}
```

### 实现提醒

点权为非负是整块求和的依据；不能从不可达状态转移；总和用 long long。
