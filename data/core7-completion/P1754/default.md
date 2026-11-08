## P1754 球迷购票问题

原题：[P1754](https://www.luogu.com.cn/problem/P1754)

### 思路

手持五十元的球迷让零钱加一张，手持一百元的球迷需要消耗一张。任意队列前缀中五十元人数不少于一百元人数，恰好对应合法括号序列，答案为第 n 个 Catalan 数。

### 复杂度

时间 O(n)，空间 O(1)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    long long ans = 1;
    for (int i = 1; i <= n; i++)
        ans = ans * (4 * i - 2) / (i + 1);
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

同面值视作同类；C_0=1；先乘后整除；使用 long long。
