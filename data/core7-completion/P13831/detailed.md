## P13831 比亚多西

原题：[P13831](https://www.luogu.com.cn/problem/P13831)

### 从问题到算法

每个目标被比较的次数就是它在二分搜索决策树中的深度。长度 n 的区间每次按中点分成大小相差至多一的两段，因此前 k=floor(log2(n+1)) 层均为满层，第 k+1 层容纳余下节点。

满层贡献 Σ(d=1..k)d·2^(d−1)=(k−1)2^k+1，最后一层有 n−(2^k−1) 个点，每点深度 k+1。整理得 f(n)=(k+1)n−2^(k+1)+k+2。

k 在 n∈[2^k−1,2^(k+1)−2] 内不变，所以 f(n) 是一次函数。求 F(N)=Σ(n=1..N)f(n) 时，枚举至多六十段，对 n 求等差和、常数乘段长，再取模。最终回答 F(R)−F(L−1)。所有分段端点使用六十四位整数，模乘使用先取模后的值。

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
