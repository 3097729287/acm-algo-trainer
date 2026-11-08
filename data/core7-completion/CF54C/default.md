## CF54C First Digit Law

原题：[CF54C](https://www.luogu.com.cn/problem/CF54C)

### 思路

首位为一的正整数构成 [1,1]、[10,19]、[100,199]……，求它们与每个输入区间的交长得到概率。再 DP 统计恰有 j 个变量成功，累加达到百分比门槛的概率。

### 复杂度

时间 O(N²+19N)，空间 O(N)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<long double> p(n);
    for (int i = 0; i < n; i++) {
        long long l, r;
        cin >> l >> r;
        long long count = 0;
        for (long long power = 1; power <= r;) {
            long long left = max(l, power), right = min((__int128)r, (__int128)power * 2 - 1);
            if (left <= right)
                count += right - left + 1;
            if (power > r / 10)
                break;
            power *= 10;
        }
        p[i] = (long double)count / (r - l + 1);
    }
    int K;
    cin >> K;
    vector<long double> dp(n + 1);
    dp[0] = 1;
    for (int i = 0; i < n; i++)
        for (int j = i + 1; j >= 0; j--)
            dp[j] = dp[j] * (1 - p[i]) + (j ? dp[j - 1] * p[i] : 0);
    int need = (n * K + 99) / 100;
    long double ans = 0;
    for (int j = need; j <= n; j++)
        ans += dp[j];
    cout << fixed << setprecision(12) << ans << '\n';

    return 0;
}
```

### 实现提醒

百分比门槛向上取整；区间两端都计数；十的幂循环避免溢出。
