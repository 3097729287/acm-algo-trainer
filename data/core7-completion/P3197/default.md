## P3197 越狱

原题：[P3197](https://www.luogu.com.cn/problem/P3197)

### 思路

全部安排有 m^n 种。没有相邻同教派的安排中，第一个人有 m 种选择，后面每个人有 m−1 种，所以答案为 m^n−m(m−1)^(n−1)。

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
