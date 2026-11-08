## UVA11426 拿行李（极限版） GCD - Extreme (II)

原题：[UVA11426](https://www.luogu.com.cn/problem/UVA11426)

### 思路

固定右端点 j，按 gcd(i,j)=d 分组，其和为 Σ(d|j,d<j)d·φ(j/d)。用倍数枚举一次加入所有 j，再前缀求和，回答多组 n。

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
