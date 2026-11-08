## AT_dp_t Permutation

原题：[AT_dp_t](https://www.luogu.com.cn/problem/AT_dp_t)

### 从问题到算法

处理长度 i 的相对大小排列，下一元素最终排名 j 在零到 i 之间。把旧排列插入新排名后，旧末元素若原排名 k<j，它仍排在新元素之前；否则它被挤到新元素之后。

因此符号为 < 时新 dp[j]=Σ(k<j)old[k]，符号为 > 时新 dp[j]=Σ(k≥j)old[k]。旧状态的前缀和能一次性查询这两种区间。

长度一只有一个排列，初值 dp[0]=1。每步只保留上一长度，最终所有末排名相加。相对排名完整确定一到 n 的排列，不需要再乘阶乘。

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
