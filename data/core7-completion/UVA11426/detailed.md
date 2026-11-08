## UVA11426 拿行李（极限版） GCD - Extreme (II)

原题：[UVA11426](https://www.luogu.com.cn/problem/UVA11426)

### 从问题到算法

目标是所有 1<=i<j<=n 的 gcd 和。固定较大的 j，若 gcd(i,j)=d，写 i=dt、j=dk，那么 1<=t<k 且 gcd(t,k)=1。k>1 时满足条件的 t 有 φ(k) 个，因此这组贡献 dφ(k)。

预处理欧拉函数后，枚举 d，再枚举 k>=2，把 dφ(k) 加到 j=d·k 的单点贡献中。每一对 (i,j) 按其唯一 gcd 恰好计一次。

最后对 j 的贡献做前缀和，预处理到所有输入的最大 n。输入以零结束，结果可能很大，使用 long long。筛 phi 时先将 phi[i]=i，再对每个质数的倍数应用乘法公式。

### 复杂度

时间 O(A log A)，空间 O(A)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    vector<int> queries;
    int n, maximum = 0;
    while (cin >> n && n) {
        queries.push_back(n);
        maximum = max(maximum, n);
    }
    vector<int> phi(maximum + 1);
    iota(phi.begin(), phi.end(), 0);
    for (int p = 2; p <= maximum; p++)
        if (phi[p] == p)
            for (int j = p; j <= maximum; j += p)
                phi[j] = phi[j] / p * (p - 1);
    vector<long long> sum(maximum + 1);
    for (int d = 1; d <= maximum / 2; d++)
        for (int j = d + d; j <= maximum; j += d)
            sum[j] += 1LL * d * phi[j / d];
    for (int i = 1; i <= maximum; i++)
        sum[i] += sum[i - 1];
    for (int x : queries)
        cout << sum[x] << '\n';

    return 0;
}
```

### 实现提醒

只统计 i<j，倍数系数从 2 起；先求单个右端贡献，再做前缀和。
