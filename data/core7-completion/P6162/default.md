## P6162 四角链

原题：[P6162](https://www.luogu.com.cn/problem/P6162)

### 思路

填数字相当于在第 i 列的前 i 行放一辆车，且每列每行至多一辆。阶梯棋盘放 k 辆车的方案数是 S(n,n−k)，用容斥公式求这个第二类 Stirling 数。

### 复杂度

时间 O((n−k) log n)，空间 O(n−k)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

long long power(long long a, long long b, long long mod) {
    long long r = 1;
    for (; b; b >>= 1, a = a * a % mod)
        if (b & 1)
            r = r * a % mod;
    return r;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, k;
    cin >> n >> k;
    const long long mod = 998244353;
    if (k == 0) {
        cout << 1 << '\n';
        return 0;
    }
    int m = n - k;
    vector<long long> fact(m + 1, 1), inv(m + 1, 1);
    for (int i = 1; i <= m; i++)
        fact[i] = fact[i - 1] * i % mod;
    inv[m] = power(fact[m], mod - 2, mod);
    for (int i = m; i; i--)
        inv[i - 1] = inv[i] * i % mod;
    long long ans = 0;
    for (int i = 0; i <= m; i++) {
        long long term = power(i, n, mod) * inv[i] % mod * inv[m - i] % mod;
        if ((m - i) & 1)
            ans = (ans - term + mod) % mod;
        else
            ans = (ans + term) % mod;
    }
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

是 S(n,n−k)；容斥正负按 m−i；k=0 时答案为 1。
