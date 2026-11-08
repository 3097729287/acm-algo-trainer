## P3197 越狱

原题：[P3197](https://www.luogu.com.cn/problem/P3197)

### 从问题到算法

直接统计至少一对相邻者相同，会让同时出现多对相同的方案被重复计算。改为统计补集：所有相邻位置都不同。

第一人可以属于任意一个教派，有 m 种。固定前一个人的教派后，当前人只能避开这一种，因此始终有 m−1 种，不受更早位置影响。由乘法原理，补集大小为 m·(m−1)^(n−1)。

所有安排为 m^n，两者相减就是至少存在一对相邻相同的方案数。分别快速幂取模，最后加上模数再取余，避免负数。

### 复杂度

时间 O(log n)，空间 O(1)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

long long power(long long a, long long b, long long mod) {
    long long r = 1;
    for (; b; b >>= 1, a = a * a % mod)
        if (b & 1)
            r = r * a % mod;
    return r;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    long long m, n;
    cin >> m >> n;
    const long long mod = 100003;
    cout << (power(m % mod, n, mod) - (m % mod) * power((m - 1) % mod, n - 1, mod) % mod + mod) %
                mod
         << '\n';

    return 0;
}
```

### 实现提醒

模数为 100003；减法规范化；n=1 时答案为 0。
