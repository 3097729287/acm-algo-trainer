## P2568 GCD

原题：[P2568](https://www.luogu.com.cn/problem/P2568)

### 从问题到算法

按 gcd 的素数值 p 分类，各类互不重叠。除去 p 后，需要统计一到 t=floor(n/p) 的有序互质对。

最大值为 i>1 时，小于 i 且与 i 互质的数有 φ(i) 个，它们可放在两个位置，贡献 2φ(i)。最大值为一只有 (1,1) 一对，所以总数为 1+2Σ(i=2..t)φ(i)=2Σ(i=1..t)φ(i)−1。

用线性筛同时求质数表和 φ。若 p|i，则 φ(ip)=pφ(i)；否则 φ(ip)=(p−1)φ(i)。把 φ 数组原地改成六十四位前缀和，再枚举质数 p≤n 累加公式。

### 复杂度

时间 O(n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<long long> phi(n + 1);
    vector<bool> composite(n + 1);
    vector<int> primes;
    phi[1] = 1;
    for (int i = 2; i <= n; i++) {
        if (!composite[i]) {
            primes.push_back(i);
            phi[i] = i - 1;
        }
        for (int p : primes) {
            long long x = 1LL * i * p;
            if (x > n)
                break;
            composite[x] = true;
            if (i % p == 0) {
                phi[x] = phi[i] * p;
                break;
            }
            phi[x] = phi[i] * (p - 1);
        }
    }
    for (int i = 1; i <= n; i++)
        phi[i] += phi[i - 1];
    long long ans = 0;
    for (int p : primes)
        ans += 2 * phi[n / p] - 1;
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

统计有序点对；φ(1)=1；前缀和和答案用 long long。
