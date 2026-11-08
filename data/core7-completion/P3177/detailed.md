## P3177 树上染色

原题：[P3177](https://www.luogu.com.cn/problem/P3177)

### 从问题到算法

两点距离可以拆成路径上各边权值的和。固定一条父子边，只有分居两侧的同色点对会经过它。若孩子子树大小为 s、黑点数为 j，全树恰有 k 个黑点，则跨边黑点对为 j(k−j)，白点对为 (s−j)(n−k−s+j)。

令 dp[u][b] 表示 u 子树恰染 b 个黑点时，已经处理的子树内部各边能取得的最大贡献。初始只含根 u，可选白或黑。合并孩子 v 时枚举它分配的 j，把 dp[u][b]+dp[v][j] 加上 u−v 这条边按 j 计算的贡献。

该贡献中使用的是全树固定黑白总数，因此虽然在子树内计算，也已经准确统计所有跨边点对，不需要知道外部具体染色。每条边只结算一次，根的 dp[k] 即为答案。不可行状态设负无穷，并限制状态不超过实际子树大小与 k。

### 复杂度

时间 O(n²)，空间 O(nk)，实现中按实际子树大小限制状态。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, k;
    cin >> n >> k;
    vector<vector<pair<int, int>>> g(n);
    for (int i = 1; i < n; i++) {
        int u, v, w;
        cin >> u >> v >> w;
        u--;
        v--;
        g[u].push_back({v, w});
        g[v].push_back({u, w});
    }
    vector<int> parent(n, -1), size(n, 1), weight(n), order = {0};
    parent[0] = 0;
    for (int i = 0; i < n; i++)
        for (auto [u, w] : g[order[i]])
            if (u != parent[order[i]]) {
                parent[u] = order[i];
                weight[u] = w;
                order.push_back(u);
            }
    const long long neg = LLONG_MIN / 4;
    vector<vector<long long>> dp(n);
    for (int i = n - 1; i >= 0; i--) {
        int v = order[i];
        if (dp[v].empty()) {
            dp[v] = {0};
            if (k)
                dp[v].push_back(0);
        }
        if (v == 0)
            break;
        int p = parent[v];
        if (dp[p].empty()) {
            dp[p] = {0};
            if (k)
                dp[p].push_back(0);
        }
        vector<long long> next(min(k, size[p] + size[v]) + 1, neg);
        for (int a = 0; a < (int)dp[p].size(); a++)
            if (dp[p][a] != neg)
                for (int b = 0; b < (int)dp[v].size() && a + b <= k; b++)
                    if (dp[v][b] != neg) {
                        long long outsideWhite = n - k - size[v] + b;
                        if (outsideWhite < 0)
                            continue;
                        long long pairs = 1LL * b * (k - b) + 1LL * (size[v] - b) * outsideWhite;
                        next[a + b] = max(next[a + b], dp[p][a] + dp[v][b] + pairs * weight[v]);
                    }
        size[p] += size[v];
        dp[p].swap(next);
        vector<long long>().swap(dp[v]);
    }
    cout << dp[0][k] << '\n';

    return 0;
}
```

### 实现提醒

计无序同色点对；白点外侧数是 n−k−s+j；不可行状态不参与转移。
