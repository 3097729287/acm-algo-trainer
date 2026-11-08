## CF1614D1 Divan and Kostomuksha (easy version)

原题：[CF1614D1](https://www.luogu.com.cn/problem/CF1614D1)

### 从问题到算法

一个排列的前缀 gcd 只能保持或变成自己的约数。若当前 gcd 仍至少含 d，那么所有 d 的倍数都可以先加入，它们不会使 gcd 跌到 d 以下；将这些数尽量提前只会增加或保持前缀 gcd 总和。

设 cnt[d] 为数组中 d 的倍数数量。若不利用更高 gcd，就先按 gcd=d 的下界给出 d·cnt[d]。若先处理 j 的倍数，其中 j 是 d 的真倍数，可以获得 dp[j]；接着把其余 d 的倍数加入，每个至少贡献 d，新增 d(cnt[d]−cnt[j])。枚举所有 j 得到最优。

按 d 从大到小计算，所有依赖已完成。cnt 可由值域频数按倍数求和，转移也按倍数枚举。最终 dp[1] 已包含全部数，即所求最大值。

### 复杂度

时间 O(A log A)，空间 O(A)。

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
    int maximum = 0;
    for (int &x : a) {
        cin >> x;
        maximum = max(maximum, x);
    }
    vector<int> frequency(maximum + 1), count(maximum + 1);
    for (int x : a)
        frequency[x]++;
    for (int d = 1; d <= maximum; d++)
        for (int j = d; j <= maximum; j += d)
            count[d] += frequency[j];
    vector<long long> dp(maximum + 1);
    for (int d = maximum; d >= 1; d--) {
        dp[d] = 1LL * d * count[d];
        for (int j = d + d; j <= maximum; j += d)
            dp[d] = max(dp[d], dp[j] + 1LL * d * (count[d] - count[j]));
    }
    cout << dp[1] << '\n';

    return 0;
}
```

### 实现提醒

输入重复值按次数计；dp 用 long long；倒序计算因数状态。
