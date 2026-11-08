## P2858 Treats for the Cows G/S

原题：[P2858](https://www.luogu.com.cn/problem/P2858)

### 思路

剩余区间长度确定今天是第几天。每次只能卖左端或右端，取两种选择的较大收益。按区间长度递增计算，可压缩为一维。

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
