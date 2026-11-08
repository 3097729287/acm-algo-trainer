## P2303 Longge 的问题

原题：[P2303](https://www.luogu.com.cn/problem/P2303)

### 思路

若 gcd(i,n)=d，约去 d 后共有 φ(n/d) 个合法 i，所以答案为 Σ(d|n) d·φ(n/d)。成对枚举约数并计算欧拉函数即可。

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
