## H. Cut Ribbon

### 题意

把长度为 $n$ 的带子恰好切成若干段，每段长度只能为 $a,b,c$，求最多段数。所有参数不超过 $4000$，保证有解。

### 从零讲：vector 的创建与初值

**用数组表示状态。** `std::vector<int> dp(n+1, -1000000)` 创建下标零至 $n$ 的状态表，并设置统一初值。负值表示不可达，零表示可达且段数为零，二者不能混用。`std::max(old,candidate)` 只选数值较大者，状态是否合法须先由条件判断保证。

### 思路

设 $dp[len]$ 为“恰好用完长度 $len$ 时的最多段数”。初始化 $dp[0]=0$，其他状态不可达。最后一段长度只能为 $a,b,c$，所以从可达的 $dp[len-cut]$ 转移：

$$dp[len]=\max_{cut\in\{a,b,c\},\ len\ge cut,\ dp[len-cut]\ge0}(dp[len-cut]+1).$$

![最后一段对应的状态来源](assets/h-dp.svg)

所有来源长度都更小，按长度递增计算即可。每个合法切法都有最后一段，反过来给合法前缀添一段仍合法，所以转移完整。时间 $O(n)$，空间 $O(n)$。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, a, b, c;
    cin >> n >> a >> b >> c;
    vector<int> dp(n + 1, -1000000);
    dp[0] = 0;  // 长度零恰好切成零段，其余长度起初不可达。
    for (int len = 1; len <= n; ++len) {
        for (int cut : {a, b, c}) {
            if (len >= cut && dp[len - cut] >= 0) {
                dp[len] = max(dp[len], dp[len - cut] + 1);
            }
        }
    }
    cout << dp[n] << '\n';
}
```

### 易错点

必须恰好用完；不可达状态不能初始化为零；长度重复不影响转移。
