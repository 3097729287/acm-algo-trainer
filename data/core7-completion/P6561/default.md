## P6561 人

原题：[P6561](https://www.luogu.com.cn/problem/P6561)

### 思路

不相邻选择中，a 个奇数与 b 个偶数的方案数为 C(m−b,a)·C(m−a,b)。预处理阶乘与逆阶乘后，每组常数时间计算。

### 复杂度

预处理 O(max m)，每组 O(1)，空间 O(max m+T)。

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

    int tests;
    cin >> tests;
    vector<array<int, 3>> queries(tests);
    int limit = 0;
    for (auto &q : queries) {
        cin >> q[0] >> q[1] >> q[2];
        limit = max(limit, q[0]);
    }
    const long long mod = 998244353;
    vector<long long> fact(limit + 1, 1), inv(limit + 1, 1);
    for (int i = 1; i <= limit; i++)
        fact[i] = fact[i - 1] * i % mod;
    inv[limit] = power(fact[limit], mod - 2, mod);
    for (int i = limit; i; i--)
        inv[i - 1] = inv[i] * i % mod;
    auto choose = [&](int n, int k) {
        if (k < 0 || k > n)
            return 0LL;
        return fact[n] * inv[k] % mod * inv[n - k] % mod;
    };
    for (auto q : queries) {
        auto [m, a, b] = q;
        cout << choose(m - b, a) * choose(m - a, b) % mod << '\n';
    }

    return 0;
}
```

### 实现提醒

a、b 区分奇偶；组合数是 m−b 选 a 与 m−a 选 b；乘法及时取模。
