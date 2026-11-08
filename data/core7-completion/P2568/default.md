## P2568 GCD

原题：[P2568](https://www.luogu.com.cn/problem/P2568)

### 思路

若 gcd(x,y)=p，令 x=pa、y=pb，则 a、b 在一到 floor(n/p) 中互质。这个范围的有序互质对数为 2·Σφ(i)−1，筛出欧拉函数前缀和后对所有质数求和。

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
