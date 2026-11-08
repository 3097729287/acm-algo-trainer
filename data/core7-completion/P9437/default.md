## P9437 一棵树

原题：[P9437](https://www.luogu.com.cn/problem/P9437)

### 思路

每个点维护从它出发的路径值总和，以及各路径十进制倍率总和。先自底向上合并子树，再扣除孩子分支得到外部量，向孩子换根，最后累加所有起点的路径值。

### 复杂度

时间 O(n log A)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    const long long mod = 998244353;
    vector<long long> a(n + 1), p(n + 1), f(n + 1), g(n + 1), allf, allg;
    for (int i = 1; i <= n; i++) {
        cin >> a[i];
        p[i] = 10;
        for (long long x = a[i]; x >= 10; x /= 10)
            p[i] = p[i] * 10 % mod;
        f[i] = a[i] % mod;
        g[i] = p[i];
    }
    vector<int> parent(n + 1);
    for (int i = 2; i <= n; i++)
        cin >> parent[i];
    for (int v = n; v >= 2; v--) {
        int u = parent[v];
        f[u] = (f[u] + f[v] + a[u] * g[v]) % mod;
        g[u] = (g[u] + p[u] * g[v]) % mod;
    }
    allf = f;
    allg = g;
    long long ans = allf[1];
    for (int v = 2; v <= n; v++) {
        int u = parent[v];
        long long outsideF = (allf[u] - f[v] - a[u] * g[v] % mod + 2 * mod) % mod,
                  outsideG = (allg[u] - p[u] * g[v] % mod + mod) % mod;
        allf[v] = (f[v] + outsideF + a[v] * outsideG) % mod;
        allg[v] = (g[v] + p[v] * outsideG) % mod;
        ans = (ans + allf[v]) % mod;
    }
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

0 的十进制长度为 1；保留子树量供扣除；减法取模防负数；计有向路径及单点。
