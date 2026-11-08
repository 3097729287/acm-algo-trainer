## CF1101D GCD Counting

原题：[CF1101D](https://www.luogu.com.cn/problem/CF1101D)

### 从问题到算法

合法路径至少存在一个质因子 p，使路径上所有值均被 p 整除。反过来，只要这个条件成立，路径 gcd 就至少为 p。

为每个点分解出不同质因子列表，令 down[u][p] 为从 u 向子树延伸且全部被 p 整除的最长链，长度按顶点数。初始化为一，合并孩子时只有双方都含 p 才能连接；先以当前链长加孩子链长更新跨分支答案，再将当前链长更新为孩子链长加一。

一个不超过二十万的数不同质因子数量很小，直接双重遍历两个短列表即可。值为一的点没有任何状态，不能出现在合法路径里；若全部为一，答案为零。

### 复杂度

设每数不同质因子个数最多为 F，时间 O(V+nF²)，空间 O(V+nF)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<int> a(n);
    int V = 1;
    for (int &x : a) {
        cin >> x;
        V = max(V, x);
    }
    vector<int> spf(V + 1);
    for (int p = 2; p <= V; p++)
        if (!spf[p])
            for (int j = p; j <= V; j += p)
                if (!spf[j])
                    spf[j] = p;
    vector<vector<int>> f(n), dp(n);
    for (int i = 0; i < n; i++) {
        int x = a[i];
        while (x > 1) {
            int p = spf[x];
            f[i].push_back(p);
            while (x % p == 0)
                x /= p;
        }
        dp[i].assign(f[i].size(), 1);
    }
    vector<vector<int>> g(n);
    for (int i = 1; i < n; i++) {
        int u, v;
        cin >> u >> v;
        u--;
        v--;
        g[u].push_back(v);
        g[v].push_back(u);
    }
    vector<int> parent(n, -1), order = {0};
    parent[0] = 0;
    for (int i = 0; i < n; i++)
        for (int u : g[order[i]])
            if (parent[u] < 0) {
                parent[u] = order[i];
                order.push_back(u);
            }
    int ans = 0;
    for (int i = n - 1; i >= 0; i--) {
        int v = order[i];
        for (int x : dp[v])
            ans = max(ans, x);
        for (int u : g[v])
            if (parent[u] == v)
                for (int j = 0; j < (int)f[v].size(); j++)
                    for (int k = 0; k < (int)f[u].size(); k++)
                        if (f[v][j] == f[u][k]) {
                            ans = max(ans, dp[v][j] + dp[u][k]);
                            dp[v][j] = max(dp[v][j], dp[u][k] + 1);
                        }
    }
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

链长按顶点计数；一没有质因子；同质因子才能拼接。
