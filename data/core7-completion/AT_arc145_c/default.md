## AT_arc145_c Split and Maximize

原题：[AT_arc145_c](https://www.luogu.com.cn/problem/AT_arc145_c)

### 思路

全局最大得分必须配对 (1,2)、(3,4)、……。这些配对在排列中的两个端点不能相互嵌套；不嵌套匹配由 Catalan 数计数，再乘 N! 种配对标签排列及 2^N 种内部方向。

### 复杂度

时间 O(N+log MOD)，空间 O(1)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    const long long P = 998244353;
    auto powmod = [&](long long a, long long b) {
        long long r = 1;
        for (; b; b >>= 1, a = a * a % P)
            if (b & 1)
                r = r * a % P;
        return r;
    };
    long long factorial = 1, denominator = 1;
    for (int i = 1; i <= 2 * n; i++) {
        factorial = factorial * i % P;
        if (i <= n + 1)
            denominator = denominator * i % P;
    }
    cout << factorial * powmod(denominator, P - 2) % P * powmod(2, n) % P << '\n';

    return 0;
}
```

### 实现提醒

禁止的是端点嵌套，允许交错；两侧子序列都要保持顺序；N! 不能遗漏。
