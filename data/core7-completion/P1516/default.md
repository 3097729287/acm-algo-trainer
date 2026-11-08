## P1516 青蛙的约会

原题：[P1516](https://www.luogu.com.cn/problem/P1516)

### 思路

跳 t 次后相遇等价于 (m−n)t≡y−x mod L。用扩展欧几里得判断是否有解，再将一个解规范化到模 L/gcd(m−n,L) 的最小非负剩余。

### 复杂度

时间 O(log L)，空间 O(log L) 的递归栈。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

long long exgcd(long long a, long long b, long long &x, long long &y) {
    if (!b) {
        x = 1;
        y = 0;
        return a;
    }
    long long u, v;
    long long g = exgcd(b, a % b, u, v);
    x = v;
    y = u - a / b * v;
    return g;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    long long x, y, m, n, L;
    cin >> x >> y >> m >> n >> L;
    long long a = m - n, b = y - x, u, v, g = exgcd(llabs(a), L, u, v);
    if (b % g) {
        cout << "Impossible\n";
        return 0;
    }
    if (a < 0)
        u = -u;
    long long mod = L / g;
    long long t = (__int128)u * (b / g) % mod;
    if (t < 0)
        t += mod;
    cout << t << '\n';

    return 0;
}
```

### 实现提醒

相对速度可能为负；按 L/g 取模；无解输出 Impossible。
