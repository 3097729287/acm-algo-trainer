## P4884 多少个 1？

原题：[P4884](https://www.luogu.com.cn/problem/P4884)

### 从问题到算法

N 位全一数乘九后等于 10^N−1，因此原条件推出 10^N≡9K+1。反过来，因为 m 是至少七的质数，与九互质，可以消去九，所以两条件完全等价。这里若随意对合数模数消去九就可能出错。

用 BSGS 将 N 拆成 iB+j，预存 10^j，再枚举 (9K+1)·(10^B)^(−i)。表中保留每个余数最小的小步指数，首次命中得到最小解。

K 在 1 到 m−1 内，9K+1 不可能模 m 等于一，所以不会错误地取到 N=0；原题保证有解。m 可达十的十一次方，两个余数相乘会超出六十四位，中间乘法使用 __int128。

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
