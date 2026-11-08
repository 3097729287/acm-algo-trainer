## CF1614D1 Divan and Kostomuksha (easy version)

原题：[CF1614D1](https://www.luogu.com.cn/problem/CF1614D1)

### 思路

统计每个 d 有多少输入是其倍数。令 dp[d] 为先处理所有 d 倍数的最优贡献；从更大的倍数 j 转移：dp[d]=max(dp[j]+d(cnt[d]−cnt[j]))。倒序枚举 d。

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
