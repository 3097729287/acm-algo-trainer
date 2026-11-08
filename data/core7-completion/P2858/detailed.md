## P2858 Treats for the Cows G/S

原题：[P2858](https://www.luogu.com.cn/problem/P2858)

### 从问题到算法

设 dp[l][r] 是只剩区间 l..r 时还能得到的最大收益。已经卖掉 n−(r−l+1) 个，所以今天是 day=n−长度+1。转移取 a[l]·day+dp[l+1][r] 与 a[r]·day+dp[l][r−1] 的较大值。

单个点最后在第 n 天卖出，初值为 a[i]n。按长度从二到 n 枚举，左右端选择正好覆盖所有合法出售次序。

一维 dp[l] 保存上一长度的结果。对固定长度从左向右更新，dp[l+1] 尚未改变，dp[l] 也仍是旧值，因此两项都能正确读取。

### 复杂度

时间 O(n²)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<long long> a(n), dp(n);
    for (int i = 0; i < n; i++) {
        cin >> a[i];
        dp[i] = a[i] * n;
    }
    for (int len = 2; len <= n; len++) {
        long long day = n - len + 1;
        for (int l = 0; l + len <= n; l++) {
            int r = l + len - 1;
            dp[l] = max(a[l] * day + dp[l + 1], a[r] * day + dp[l]);
        }
    }
    cout << dp[0] << '\n';

    return 0;
}
```

### 实现提醒

年龄从一开始增加；单点是在第 n 天卖；一维左端必须递增枚举。
