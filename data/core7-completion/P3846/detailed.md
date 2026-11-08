## P3846 BSGS / [TJOI2007] 可爱的质数

原题：[P3846](https://www.luogu.com.cn/problem/P3846)

### 从问题到算法

模数 p 为质数且 b 非零，因此 b 存在逆元。取 B≈sqrt(p)，任何可能的最小指数都可分为大步 iB 与小步 j，其中 0<=j<B。

等式 b^(iB+j)=n 可以改写为 b^j=n·(b^B)^(−i)。先将所有小步值 b^j 放入表，重复值只保留最小 j。再从 n 开始，每轮乘 b^B 的逆元，查找对应小步。

同一个大步内最小 j 最优，不同大步按 i 递增互不交叠，所以首次命中就是最小非负指数。模 p 的非零乘法群大小为 p−1，搜索范围足够覆盖全部可能。未命中时按原题输出 no solution。

### 复杂度

平均时间 O(sqrt p)，空间 O(sqrt p)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

long long multiply(long long a, long long b, long long mod) { return (__int128)a * b % mod; }
long long modularPower(long long a, long long b, long long mod) {
    long long ans = 1;
    for (; b; b >>= 1, a = multiply(a, a, mod))
        if (b & 1)
            ans = multiply(ans, a, mod);
    return ans;
}
long long logarithm(long long base, long long target, long long mod) {
    long long block = sqrt((long double)mod) + 1;
    unordered_map<long long, int> baby;
    baby.reserve(2 * block);
    long long value = 1;
    for (int j = 0; j < block; j++) {
        baby.emplace(value, j);
        value = multiply(value, base, mod);
    }
    long long inverse = modularPower(value, mod - 2, mod);
    value = target;
    for (long long i = 0; i <= block; i++) {
        auto it = baby.find(value);
        if (it != baby.end())
            return i * block + it->second;
        value = multiply(value, inverse, mod);
    }
    return -1;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    long long p, b, n;
    cin >> p >> b >> n;
    long long answer = logarithm(b, n, p);
    if (answer < 0)
        cout << "no solution\n";
    else
        cout << answer << '\n';

    return 0;
}
```

### 实现提醒

允许指数 0；重复 baby 值保留最小指数；逆元依赖 p 为质数。
