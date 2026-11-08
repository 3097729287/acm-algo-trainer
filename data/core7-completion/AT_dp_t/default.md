## AT_dp_t Permutation

原题：[AT_dp_t](https://www.luogu.com.cn/problem/AT_dp_t)

### 思路

dp[j] 表示当前排列末元素在已用数中排名 j 的方案数。加入一个新排名时，若要求上升就累加更小旧排名，下降就累加不小于新排名的旧排名；前缀和使每态常数时间。

### 复杂度

时间 O(n²)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

const long long MOD = 1000000007;
long long power(long long a, long long b) {
    long long r = 1;
    for (; b; b >>= 1, a = a * a % MOD)
        if (b & 1)
            r = r * a % MOD;
    return r;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    string s;
    if (n > 1)
        cin >> s;
    vector<long long> dp(1, 1);
    for (int len = 1; len < n; len++) {
        vector<long long> prefix(len + 1), next(len + 1);
        for (int j = 0; j < len; j++)
            prefix[j + 1] = (prefix[j] + dp[j]) % MOD;
        for (int j = 0; j <= len; j++)
            next[j] = s[len - 1] == '<' ? prefix[j] : (prefix[len] - prefix[j] + MOD) % MOD;
        dp.swap(next);
    }
    long long ans = 0;
    for (auto x : dp)
        ans = (ans + x) % MOD;
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

排名从零开始；下降取旧排名≥j；只维护相对大小即可。
