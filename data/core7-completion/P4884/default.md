## P4884 多少个 1？

原题：[P4884](https://www.luogu.com.cn/problem/P4884)

### 思路

全一数 R_N=(10^N−1)/9，因质数 m≥7，9 在模 m 下可逆，所以原式等价于 10^N≡9K+1(mod m)。用 BSGS 求最小指数。

### 复杂度

平均时间 O(sqrt m)，空间 O(sqrt m)。

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

    long long k, m;
    cin >> k >> m;
    cout << logarithm(10, (9 * k + 1) % m, m) << '\n';

    return 0;
}
```

### 实现提醒

利用质数保证九可逆；模乘使用 __int128；答案要求正整数。
