## P3177 树上染色

原题：[P3177](https://www.luogu.com.cn/problem/P3177)

### 思路

一条边下方有 size 个点，其中 j 个黑点，它对同色点对距离的贡献是 w·[j(k−j)+(size−j)(n−k−size+j)]。树形背包决定每棵子树的黑点数，并累加各边贡献。

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
