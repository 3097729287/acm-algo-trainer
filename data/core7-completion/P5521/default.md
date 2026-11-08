## P5521 梅深不见冬

原题：[P5521](https://www.luogu.com.cn/problem/P5521)

### 思路

设 f[v] 为完成孩子 v 的最少花数，完成后只需保留 w[v]。按 f[v]−w[v] 从大到小处理孩子，维护已保留花数；最后还要同时放上当前点的 w[u]。

### 复杂度

时间 O(n log n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<vector<int>> g(n);
    for (int i = 1; i < n; i++) {
        int p;
        cin >> p;
        g[p - 1].push_back(i);
    }
    vector<long long> w(n), f(n);
    for (auto &x : w)
        cin >> x;
    for (int v = n - 1; v >= 0; v--) {
        sort(g[v].begin(), g[v].end(), [&](int a, int b) { return f[a] - w[a] > f[b] - w[b]; });
        long long saved = 0, best = 0;
        for (int u : g[v]) {
            best = max(best, saved + f[u]);
            saved += w[u];
        }
        f[v] = max(best, saved + w[v]);
    }
    for (int i = 0; i < n; i++)
        cout << f[i] << (i + 1 == n ? '\n' : ' ');

    return 0;
}
```

### 实现提醒

先完成孩子且保留其根；最终要同时拥有孩子与当前点的花；按 f−w 而非 f 排序。
