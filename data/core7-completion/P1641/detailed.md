## P1641 生成字符串

原题：[P1641](https://www.luogu.com.cn/problem/P1641)

### 从问题到算法

把 1 看作向上一步、0 看作向下一步，要求所有前缀高度非负。全部安排有 C(n+m,m) 种，直接扣去走到负高度的安排。

对一条非法路径，找到第一次到达 −1 的位置，把此前所有上、下步互换。这个前缀原来下步比上步多一个，互换后总的上步增加一、下步减少一，得到 n+1 个上步和 m−1 个下步的任意路径。

反变换是找到第一次到达 +1 的位置并再次反转，因此这是双射，非法路径数恰为 C(n+m,m−1)。阶乘与逆阶乘预处理到 n+m，模数 20100403 为质数且比范围大，可以用费马小定理求逆。

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
