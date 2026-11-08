## P3047 Nearby Cows G

原题：[P3047](https://www.luogu.com.cn/problem/P3047)

### 从问题到算法

设 down[u][d] 为 u 子树内与 u 距离恰好 d 的牛数。down[u][0] 是本点牛数，孩子 v 的 down[v][d−1] 可加入 down[u][d]。先按子先父顺序计算。

再令 all[u][d] 为整棵树中与 u 距离 d 的牛数。根的 all 等于 down。对父子 u、v，孩子外部的点到 v 的距离等于到 u 的距离加一，所以候选是 all[u][d−1]。但其中包含 v 子树内距离 u 为 d−1 的点，即 down[v][d−2]，必须扣掉。

因此 all[v][d]=down[v][d]+all[u][d−1]−down[v][d−2]，d=1 时没有扣除项。把 d=0 到 K 累加即可得到范围内总牛数。两个阶段分别使用 down 和 all，避免换根后污染子树原始量。

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
