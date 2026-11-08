## P5521 梅深不见冬

原题：[P5521](https://www.luogu.com.cn/problem/P5521)

### 从问题到算法

完成一个孩子后，除了该孩子根上的 w[v]，它子树内的花都可以收回。若此前其它孩子已经留下 S 朵，处理 v 的资源峰值为 S+f[v]，完成后保留量增加 w[v]。所有孩子完成后，放当前点需要 Σw[v]+w[u]。

相邻孩子 a、b 交换顺序时，两种峰值为 max(f[a],w[a]+f[b]) 与 max(f[b],w[b]+f[a])，其它已保留量相同。若 f[a]−w[a]≥f[b]−w[b]，前一种不大于后一种。因此按这个差降序可以不断交换到最优顺序。

每个点的答案只涉及自己子树，先在其它子树摆花不能创造额外花朵，也不会改善目标。父编号小于子编号，可以从大到小计算 f；不必递归访问十万层树。

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
