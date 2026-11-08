## CF1178C Tiles

原题：[CF1178C](https://www.luogu.com.cn/problem/CF1178C)

### 从问题到算法

可以从每块砖在横向和纵向边界上的相位来描述摆放。相邻位置需要一致拼接，选好首行与首列的相位后，其余位置的选择都被左侧和上侧确定。

边界总共提供 h+w 个独立的二元选择，每一种边界配置恰好扩展为一份合法铺法，不同边界配置得到不同铺法。因此方案数为 2 的 h+w 次方。

使用快速幂：把指数按二进制拆开，当前位为一时乘入对应的 2^(2^k)，每轮底数平方、指数右移。每次乘法立即取模。

### 复杂度

时间 O(log(h+w))，空间 O(1)。

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

    long long h, w;
    cin >> h >> w;
    cout << power(2, h + w, 998244353) << '\n';

    return 0;
}
```

### 实现提醒

指数是 h+w；模数为 998244353。
