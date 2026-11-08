## P9437 一棵树

原题：[P9437](https://www.luogu.com.cn/problem/P9437)

### 从问题到算法

在数字 x 前拼接 a，会得到 a·10^(x的位数)+x。因此只存路径值和不够，还要存路径总位数对应的 10 的幂之和。记 P[u]=10^(a[u]位数)，F[u] 为从 u 到子树各终点的拼接值之和，G[u] 为这些路径的倍率之和。

初始 F[u]=a[u]、G[u]=P[u]。合并孩子 v 时，加入 F[v]+a[u]G[v] 到 F[u]，加入 P[u]G[v] 到 G[u]。这是把 a[u] 统一拼在每条孩子路径前面。

换根时，父亲全树结果中先扣去通向 v 的分支：外部路径值 A=全F[u]−F[v]−a[u]G[v]，外部倍率 B=全G[u]−P[u]G[v]。在这些路径前拼接 a[v] 后，全F[v]=F[v]+A+a[v]B，全G[v]=G[v]+P[v]B。

输入保证父编号更小，可以直接倒序做子树合并、正序做换根，不需要邻接表。数字零的位数仍是一，倍率为十。所有运算对 998244353 规范取模。

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
