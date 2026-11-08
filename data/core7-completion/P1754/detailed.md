## P1754 球迷购票问题

原题：[P1754](https://www.luogu.com.cn/problem/P1754)

### 从问题到算法

把五十元球迷记为左括号，一百元球迷记为右括号。售票处初始没有零钱，每位一百元球迷都要找回五十元，所以任意前缀中左括号数必须不少于右括号数；最终两者各 n 个。这与合法括号序列一一对应。

由反射原理，全部 C(2n,n) 个等量括号序列中，不合法的有 C(2n,n−1) 个，相减得到 Catalan(n)=C(2n,n)/(n+1)。相邻项约分可得 C_i=C_(i−1)·(4i−2)/(i+1)，C_0=1，每次先乘后除且精确整除。

原题把同面值球迷视为同类，不再乘 n!。n≤20，答案最大 6564120420，超出三十二位但能放入 long long；递推乘法的中间值也在六十四位范围内，无需高精度结构。

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
