## P2303 Longge 的问题

原题：[P2303](https://www.luogu.com.cn/problem/P2303)

### 从问题到算法

要求所有 gcd 的和，可以把产生同一个 gcd 的整数放在一起。固定 n 的因数 d，令 i=dj，则 gcd(i,n)=d 等价于 j 与 n/d 互质。在 1 到 n/d 中有 φ(n/d) 个这样的 j，每个贡献 d。

因此答案是所有因数 d 对应的 d·φ(n/d) 之和。先分解 n 得到不同质因数。计算某个因数的欧拉函数时，仅检查这些质因数，按 φ(x)=x·∏(1−1/p) 依次先除 p 再乘 p−1。

枚举到平方根时，同时处理 d 和 n/d，二者相等时只处理一次。乘法和答案使用 long long。

### 复杂度

时间 O(sqrt n + τ(n)·ω(n))，空间 O(ω(n))，τ 是约数数，ω 是不同质因数数。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    long long n;
    cin >> n;
    long long x = n;
    vector<long long> primes;
    for (long long p = 2; p <= x / p; p++)
        if (x % p == 0) {
            primes.push_back(p);
            while (x % p == 0)
                x /= p;
        }
    if (x > 1)
        primes.push_back(x);
    auto phi = [&](long long x) {
        long long r = x;
        for (long long p : primes)
            if (x % p == 0)
                r = r / p * (p - 1);
        return r;
    };
    long long ans = 0;
    for (long long d = 1; d <= n / d; d++)
        if (n % d == 0) {
            ans += d * phi(n / d);
            if (d != n / d)
                ans += (n / d) * phi(d);
        }
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

平方因数只算一次；φ(1)=1；先除再乘。
