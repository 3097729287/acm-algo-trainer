## P3047 Nearby Cows G

原题：[P3047](https://www.luogu.com.cn/problem/P3047)

### 思路

先求每个点子树内距离恰为 d 的牛数，再向下换根。孩子距离 d 的外部贡献来自父亲距离 d−1 的总量，并扣掉重复落在孩子子树中的距离 d−2 部分。

### 复杂度

时间 O(nK)，空间 O(nK)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, k;
    cin >> n >> k;
    vector<vector<int>> g(n);
    for (int i = 1; i < n; i++) {
        int u, v;
        cin >> u >> v;
        u--;
        v--;
        g[u].push_back(v);
        g[v].push_back(u);
    }
    int width = k + 1;
    vector<int> down(n * width), all(n * width), parent(n, -1), order = {0};
    for (int i = 0; i < n; i++)
        cin >> down[i * width];
    parent[0] = 0;
    for (int i = 0; i < n; i++)
        for (int u : g[order[i]])
            if (u != parent[order[i]]) {
                parent[u] = order[i];
                order.push_back(u);
            }
    for (int i = n - 1; i > 0; i--) {
        int v = order[i], p = parent[v];
        for (int d = 1; d <= k; d++)
            down[p * width + d] += down[v * width + d - 1];
    }
    all = down;
    for (int i = 1; i < n; i++) {
        int v = order[i], p = parent[v];
        for (int d = 1; d <= k; d++)
            all[v * width + d] += all[p * width + d - 1] - (d >= 2 ? down[v * width + d - 2] : 0);
    }
    for (int v = 0; v < n; v++) {
        long long ans = 0;
        for (int d = 0; d <= k; d++)
            ans += all[v * width + d];
        cout << ans << '\n';
    }

    return 0;
}
```

### 实现提醒

距离是边数；d<2 不减子树项；子树数组和全树数组分开。
