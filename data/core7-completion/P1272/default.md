## P1272 重建道路

原题：[P1272](https://www.luogu.com.cn/problem/P1272)

### 思路

dp[u][s] 表示在 u 子树内保留含 u 的 s 个点，需切断多少向下边。初始只保留 u 时切掉所有孩子边；接纳孩子的 j 个点就加入其代价并恢复一条父子边。

### 复杂度

时间 O(NP²)，空间 O(NP)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, P;
    cin >> n >> P;
    vector<vector<int>> g(n);
    for (int i = 1; i < n; i++) {
        int u, v;
        cin >> u >> v;
        g[u - 1].push_back(v - 1);
    }
    const int INF = 1000000;
    vector<vector<int>> dp(n, vector<int>(P + 1, INF));
    vector<int> size(n);
    function<void(int)> dfs = [&](int v) {
        size[v] = 1;
        dp[v][1] = g[v].size();
        for (int u : g[v]) {
            dfs(u);
            vector<int> next = dp[v];
            for (int s = 1; s <= min(P, size[v]); s++)
                for (int j = 1; j <= min(size[u], P - s); j++)
                    next[s + j] = min(next[s + j], dp[v][s] + dp[u][j] - 1);
            dp[v].swap(next);
            size[v] += size[u];
        }
    };
    dfs(0);
    int ans = INF;
    for (int v = 0; v < n; v++)
        ans = min(ans, dp[v][P] + (v != 0));
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

块必须含状态根；接纳孩子减掉一条预切边；非根答案补父边。
