## P13831 比亚多西

原题：[P13831](https://www.luogu.com.cn/problem/P13831)

### 思路

二分查找形成近完全二叉搜索树。令 k=floor(log2(n+1))，前 k 层满，剩余点在第 k+1 层，可得 f(n)=(k+1)n−2^(k+1)+k+2。按 k 相同的 n 区间用等差数列求前缀和。

### 复杂度

每组时间 O(log R)，空间 O(1)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int tests;
    cin >> tests;
    const long long mod = 998244353, inv2 = (mod + 1) / 2;
    auto solve = [&](long long n) {
        long long ans = 0;
        for (long long power = 4, k = 1; power / 2 - 1 <= n; power *= 2, k++) {
            long long l = max(1LL, power / 2 - 1), r = min(n, power - 2);
            if (l <= r) {
                long long count = (r - l + 1) % mod,
                          sum = (l % mod + r % mod) % mod * count % mod * inv2 % mod;
                long long constant = (-power % mod + k + 2 + mod) % mod;
                ans = (ans + (k + 1) * sum + constant * count) % mod;
            }
        }
        return ans;
    };
    while (tests--) {
        long long l, r;
        cin >> l >> r;
        cout << (solve(r) - solve(l - 1) + mod) % mod << '\n';
    }

    return 0;
}
```

### 实现提醒

分界是 n+1 的最高位；L=1 时 F(0)=0；模减法规范化。
