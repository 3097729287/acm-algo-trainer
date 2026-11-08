## P1516 青蛙的约会

原题：[P1516](https://www.luogu.com.cn/problem/P1516)

### 从问题到算法

两只青蛙位置分别为 x+mt、y+nt，首尾相接表示两者相差 L 的整数倍，所以得到线性同余方程。记 a=m−n、b=y−x，g=gcd(|a|,L)。只有 g 整除 b 时有解。

扩展欧几里得求出 |a|u+Lv=g；若 a 为负，将 u 取反。乘上 b/g 得到一个 t 解。所有解相差 L/g，将它规范化到零至 L/g−1 就得到首次相遇的非负次数。

若步长相同，方程左边恒为零：初始位置模 L 相同则答案零，否则不可能。代码统一处理为 g=L。乘解系数时用 __int128，避免中间乘积溢出。

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
