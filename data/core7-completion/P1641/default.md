## P1641 生成字符串

原题：[P1641](https://www.luogu.com.cn/problem/P1641)

### 思路

全部字符串数为 C(n+m,m)。把首次出现 0 多于 1 的前缀反转，可将非法串与含 n+1 个 1、m−1 个 0 的串一一对应，所以答案为 C(n+m,m)−C(n+m,m−1)。

### 复杂度

时间 O(n+m+log MOD)，空间 O(n+m)。

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

    int n, m;
    cin >> n >> m;
    const long long mod = 20100403;
    int total = n + m;
    vector<long long> fact(total + 1, 1), inv(total + 1, 1);
    for (int i = 1; i <= total; i++)
        fact[i] = fact[i - 1] * i % mod;
    inv[total] = power(fact[total], mod - 2, mod);
    for (int i = total; i; i--)
        inv[i - 1] = inv[i] * i % mod;
    auto choose = [&](int k) {
        if (k < 0 || k > total)
            return 0LL;
        return fact[total] * inv[k] % mod * inv[total - k] % mod;
    };
    cout << (choose(m) - choose(m - 1) + mod) % mod << '\n';

    return 0;
}
```

### 实现提醒

非法数对应 m−1；模减法加模数；不是只要求最终 1 不少于 0。
